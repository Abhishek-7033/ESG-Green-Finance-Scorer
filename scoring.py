import numpy as np, pandas as pd

WEIGHTS = {"E": 0.4, "S": 0.3, "G": 0.3}
# metric: (pillar, direction)  direction "low" = lower is better
METRICS = {
    "emissions_intensity": ("E", "low"),
    "renewable_pct": ("E", "high"),
    "women_workforce_pct": ("S", "high"),
    "injury_rate": ("S", "low"),
    "turnover_pct": ("S", "low"),
    "independent_board_pct": ("G", "high"),
    "women_board_pct": ("G", "high"),
    "ceo_pay_ratio": ("G", "low"),
}


def _score(x, ref, direction):
    """Benchmark value -> 50 points. Better than benchmark -> up to 100."""
    if ref == 0:
        return 50.0
    s = 100 - 50 * x / ref if direction == "low" else 50 * x / ref
    return float(np.clip(s, 0, 100))


def score_companies(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for m, (pillar, direction) in METRICS.items():
        sector_med = df.groupby("sector")[m].transform("median")
        counts = df.groupby("sector")[m].transform("count")
        ref = np.where(counts >= 3, sector_med, df[m].median())  # sector-adjusted
        df[f"{m}_score"] = [_score(x, r, direction) for x, r in zip(df[m], ref)]
    for p in "ESG":
        cols = [f"{m}_score" for m, (pp, _) in METRICS.items() if pp == p]
        df[p] = df[cols].mean(axis=1)
    df["base_score"] = sum(df[p] * w for p, w in WEIGHTS.items())
    return df


def explain(row) -> list[str]:
    """Top drivers: best and worst metric scores."""
    items = [(m, row[f"{m}_score"], row[m]) for m in METRICS]
    items.sort(key=lambda t: t[1])
    worst, best = items[:2], items[-2:]
    out = [f"Weak: {m} = {v} (score {s:.0f})" for m, s, v in worst]
    out += [f"Strong: {m} = {v} (score {s:.0f})" for m, s, v in best]
    return out


def rating(score: float) -> str:
    return "Low risk" if score >= 70 else "Medium risk" if score >= 50 else "High risk"
