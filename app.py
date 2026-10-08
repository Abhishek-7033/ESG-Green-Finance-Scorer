import pandas as pd, plotly.graph_objects as go, streamlit as st
from scoring import score_companies, explain, rating
from news import analyze_news, controversy_penalty
from greenwashing import greenwashing_flag, claim_strength_from_pdf

st.set_page_config(page_title="ESG Green Finance Scorer", layout="wide")
st.title("🌱 ESG & Green Finance Scorer")
st.caption("Decision-support tool. Sample data is illustrative only.")

@st.cache_data
def load():
    df = score_companies(pd.read_csv("data/companies.csv"))
    news = analyze_news(pd.read_csv("data/headlines.csv"))
    pens = [controversy_penalty(news, c) for c in df.company]
    df["penalty"] = [p[0] for p in pens]
    df["neg_count"] = [p[1] for p in pens]
    df["final_score"] = (df.base_score - df.penalty).clip(0, 100)
    return df, news

df, news = load()
tab1, tab2 = st.tabs(["Company analysis", "Compare all"])

with tab1:
    company = st.selectbox("Company", df.company)
    row = df[df.company == company].iloc[0]
    claim = row.claim_strength
    pdf = st.file_uploader("Optional: sustainability report PDF (to measure claim strength)", type="pdf")
    if pdf:
        with open("tmp.pdf", "wb") as f: f.write(pdf.read())
        claim = claim_strength_from_pdf("tmp.pdf")
        st.info(f"Claim strength from PDF: {claim}/10")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Final ESG score", f"{row.final_score:.0f}/100", rating(row.final_score))
    c2.metric("Environmental", f"{row.E:.0f}")
    c3.metric("Social", f"{row.S:.0f}")
    c4.metric("Governance", f"{row.G:.0f}")

    fig = go.Figure(go.Bar(x=["E", "S", "G"], y=[row.E, row.S, row.G],
                           marker_color=["#2e7d32", "#1565c0", "#6a1b9a"]))
    fig.update_yaxes(range=[0, 100]); fig.update_layout(height=300, title="Pillar scores")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Why this score?")
        for line in explain(row): st.write("•", line)
        st.write(f"• Controversy penalty: -{row.penalty:.0f} ({int(row.neg_count)} negative news items)")
    with right:
        st.subheader("Greenwashing check")
        level, msg = greenwashing_flag(claim, row.final_score, int(row.neg_count))
        {"HIGH": st.error, "MEDIUM": st.warning, "LOW": st.success}[level](f"{level}: {msg}")
        st.subheader("Green loan eligibility (indicative)")
        ok = row.E >= 60 and row.renewable_pct >= 30 and row.neg_count < 2
        (st.success if ok else st.warning)(
            "Likely eligible for green loan review" if ok else
            "Not eligible yet: needs E score ≥60, renewables ≥30%, <2 controversies")

    st.subheader("News signals")
    st.dataframe(news[news.company == company][["headline", "pillar", "sentiment"]], use_container_width=True)

with tab2:
    show = df[["company", "sector", "E", "S", "G", "final_score", "neg_count"]].sort_values("final_score", ascending=False)
    st.dataframe(show.round(1), use_container_width=True)
    st.plotly_chart(go.Figure(go.Bar(x=show.company, y=show.final_score)).update_layout(title="Final ESG scores"),
                    use_container_width=True)
