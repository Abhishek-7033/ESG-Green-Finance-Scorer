import pandas as pd, plotly.graph_objects as go, streamlit as st
from scoring import score_companies, explain, rating
from news import analyze_news, controversy_penalty
from greenwashing import greenwashing_flag, claim_strength_from_pdf
from live_news import fetch_headlines
from rag import load_pdf, chunk, ReportIndex, extract_metrics, answer

st.set_page_config(page_title="ESG Green Finance Scorer", layout="wide")
st.title("🌱 ESG & Green Finance Scorer")
st.caption("Decision-support tool. Verify scores against primary sources.")

@st.cache_data
def load():
    df = score_companies(pd.read_csv("data/companies.csv"))
    news = analyze_news(pd.read_csv("data/headlines.csv"))
    pens = [controversy_penalty(news, c) for c in df.company]
    df["penalty"] = [p[0] for p in pens]
    df["neg_count"] = [p[1] for p in pens]
    df["final_score"] = (df.base_score - df.penalty).clip(0, 100)
    return df, news

@st.cache_data(ttl=3600)
def live(company):
    return analyze_news(fetch_headlines(company))

df, news = load()
use_live = st.sidebar.toggle("Use live news (Google News)", value=False)
tab1, tab2, tab3 = st.tabs(["Company analysis", "Compare all", "Report Q&A (RAG)"])

with tab1:
    company = st.selectbox("Company", df.company)
    row = df[df.company == company].iloc[0]
    news_c, penalty, neg = news[news.company == company], row.penalty, int(row.neg_count)
    if use_live:
        try:
            news_c = live(company)
            penalty, neg = controversy_penalty(news_c, company)
        except Exception as e:
            st.warning(f"Live news failed ({e}); using sample headlines.")
    final = max(0.0, row.base_score - penalty)

    claim = row.claim_strength
    pdf = st.file_uploader("Optional: sustainability report PDF (measures claim strength)", type="pdf", key="p1")
    if pdf:
        with open("tmp.pdf", "wb") as f: f.write(pdf.read())
        claim = claim_strength_from_pdf("tmp.pdf")
        st.info(f"Claim strength from PDF: {claim}/10")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Final ESG score", f"{final:.0f}/100", rating(final))
    c2.metric("Environmental", f"{row.E:.0f}"); c3.metric("Social", f"{row.S:.0f}"); c4.metric("Governance", f"{row.G:.0f}")
    fig = go.Figure(go.Bar(x=["E", "S", "G"], y=[row.E, row.S, row.G], marker_color=["#2e7d32", "#1565c0", "#6a1b9a"]))
    fig.update_yaxes(range=[0, 100]); fig.update_layout(height=300, title="Pillar scores")
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Why this score?")
        for line in explain(row): st.write("•", line)
        st.write(f"• Controversy penalty: -{penalty:.0f} ({neg} negative news items)")
    with right:
        st.subheader("Greenwashing check")
        level, msg = greenwashing_flag(claim, final, neg)
        {"HIGH": st.error, "MEDIUM": st.warning, "LOW": st.success}[level](f"{level}: {msg}")
        st.subheader("Green loan eligibility (indicative)")
        ok = row.E >= 60 and row.renewable_pct >= 30 and neg < 2
        (st.success if ok else st.warning)("Likely eligible for green loan review" if ok else
            "Not eligible yet: needs E ≥60, renewables ≥30%, <2 controversies")
    st.subheader("News signals" + (" (live)" if use_live else " (sample)"))
    st.dataframe(news_c[["headline", "pillar", "sentiment"]], use_container_width=True)

with tab2:
    show = df[["company", "sector", "E", "S", "G", "final_score", "neg_count"]].sort_values("final_score", ascending=False)
    st.dataframe(show.round(1), use_container_width=True)
    st.plotly_chart(go.Figure(go.Bar(x=show.company, y=show.final_score)).update_layout(title="Final ESG scores"),
                    use_container_width=True)

with tab3:
    st.write("Upload a sustainability report, extract key metrics with page citations, and ask questions.")
    rpdf = st.file_uploader("Sustainability / BRSR report (PDF)", type="pdf", key="p2")
    if rpdf:
        if st.session_state.get("rname") != rpdf.name:
            with open("report.pdf", "wb") as f: f.write(rpdf.read())
            with st.spinner("Indexing report..."):
                chunks = chunk(load_pdf("report.pdf"))
                st.session_state.update(rname=rpdf.name, chunks=chunks, index=ReportIndex(chunks))
        st.subheader("Extracted metrics")
        metrics = extract_metrics(st.session_state.chunks)
        st.dataframe(pd.DataFrame(metrics) if metrics else pd.DataFrame({"info": ["No metrics matched"]}),
                     use_container_width=True)
        q = st.text_input("Ask the report", "What are the company's emission reduction targets?")
        if st.button("Ask") and q:
            text, hits = answer(q, st.session_state.index)
            st.markdown(text)
            for h in hits:
                with st.expander(f"Source: page {h['page']} (relevance {h['score']:.2f})"):
                    st.write(h["text"])
