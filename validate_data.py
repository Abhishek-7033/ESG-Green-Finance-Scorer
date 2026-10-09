"""Run before the demo:  python validate_data.py"""
import pandas as pd
from scoring import METRICS

df = pd.read_csv("data/companies.csv")
need = {"company", "sector", "claim_strength", *METRICS}
missing = need - set(df.columns)
assert not missing, f"Missing columns: {missing}"
print(f"{len(df)} companies | sectors: {df.sector.value_counts().to_dict()}")
for s, n in df.sector.value_counts().items():
    if n < 3:
        print(f"WARNING: sector '{s}' has {n} companies; need >=3 for sector-adjusted scoring")
for col in ["renewable_pct", "women_workforce_pct", "turnover_pct", "independent_board_pct", "women_board_pct"]:
    bad = df[(df[col] < 0) | (df[col] > 100)]
    if len(bad): print(f"WARNING: {col} out of 0-100 for {bad.company.tolist()}")
print("nulls:", df.isna().sum()[df.isna().sum() > 0].to_dict() or "none")
