import pandas as pd
from functools import lru_cache

PILLAR_KW = {
    "E": ["emission", "pollution", "spill", "effluent", "solar", "renewable", "climate",
          "carbon", "waste", "hydrogen", "green", "net zero", "oil"],
    "S": ["worker", "labour", "labor", "accident", "diversity", "community", "safety",
          "privacy", "training", "hiring", "employee"],
    "G": ["board", "governance", "fraud", "bribery", "probe", "sued", "investigat",
          "fined", "misleading", "audit"],
}
NEG = ["fined", "spill", "fatal", "protest", "probe", "sued", "accused", "breach",
       "violation", "misleading", "contaminat", "illegal", "poor", "investigat"]
POS = ["wins", "award", "cuts", "expands", "issues green", "commissions", "strengthens",
       "launches", "plan to cut", "reforms"]

@lru_cache(maxsize=1)
def _finbert():
    try:
        from transformers import pipeline
        return pipeline("text-classification", model="ProsusAI/finbert")
    except Exception:
        return None  # offline / not installed -> keyword fallback

def sentiment(text: str) -> str:
    t = text.lower()
    neg = any(k in t for k in NEG)   # controversy keywords take priority
    if neg:
        return "negative"
    model = _finbert()
    if model is not None:
        return model(text[:512])[0]["label"].lower()
    return "positive" if any(k in t for k in POS) else "neutral"

def pillar(text: str) -> str:
    t = text.lower()
    hits = {p: sum(k in t for k in kws) for p, kws in PILLAR_KW.items()}
    best = max(hits, key=hits.get)
    return best if hits[best] > 0 else "G"

def analyze_news(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sentiment"] = df["headline"].apply(sentiment)
    df["pillar"] = df["headline"].apply(pillar)
    return df

def controversy_penalty(news: pd.DataFrame, company: str) -> tuple[float, int]:
    sub = news[(news.company == company) & (news.sentiment == "negative")]
    return min(20.0, 6.0 * len(sub)), len(sub)
