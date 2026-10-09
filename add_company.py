"""Add a company to data/companies.csv by reading its sustainability report.
Usage: python add_company.py "Tata Steel" Materials 30000 data/reports/tata_steel.pdf
        (args: name, sector, revenue in USD millions, report PDF)
Blank cells are left for you to fill from the report; run validate_data.py after."""
import sys, os
import pandas as pd
from rag import load_pdf, chunk, extract_metrics
from greenwashing import claim_strength_from_pdf
from scoring import METRICS

def num(x):
    return float(str(x).replace(",", ""))

def main(name, sector, revenue_musd, pdf):
    chunks = chunk(load_pdf(pdf))
    m = {r["metric"]: r for r in extract_metrics(chunks)}
    row = {c: None for c in ["company", "sector", *METRICS, "claim_strength"]}
    row.update(company=name, sector=sector, claim_strength=claim_strength_from_pdf(pdf))
    if "Women on board (%)" in m:    row["women_board_pct"] = num(m["Women on board (%)"]["value"])
    if "Renewable energy (%)" in m:  row["renewable_pct"] = num(m["Renewable energy (%)"]["value"])
    if "Injury rate (LTIFR)" in m:   row["injury_rate"] = num(m["Injury rate (LTIFR)"]["value"])
    if "Scope 1 emissions" in m and "Scope 2 emissions" in m:
        tot = num(m["Scope 1 emissions"]["value"]) + num(m["Scope 2 emissions"]["value"])
        row["emissions_intensity"] = round(tot / float(revenue_musd), 1)  # tCO2e per $M revenue
    path = "data/companies.csv"
    df = pd.read_csv(path)
    df = df[df.company != name]
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(path, index=False)
    print("Added:", {k: v for k, v in row.items() if v is not None})
    print("Still blank (fill manually):", [k for k, v in row.items() if v is None])
    print("Check units: scope 1/2 should be tCO2e; the extractor takes the first number it finds.")

if __name__ == "__main__":
    main(*sys.argv[1:5])
