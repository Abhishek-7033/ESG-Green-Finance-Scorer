from pypdf import PdfReader

CLAIM_WORDS = ["net zero", "carbon neutral", "sustainable", "eco-friendly", "green",
               "climate positive", "responsible", "renewable", "commitment", "pledge"]

def claim_strength_from_pdf(path: str) -> float:
    """Rough 0-10 score: density of marketing-style claims per 1000 words."""
    text = " ".join((p.extract_text() or "") for p in PdfReader(path).pages).lower()
    words = max(len(text.split()), 1)
    hits = sum(text.count(w) for w in CLAIM_WORDS)
    return round(min(10.0, hits / words * 1000 / 2), 1)

def greenwashing_flag(claim_strength: float, final_score: float, neg_count: int):
    """High claims + weak performance or controversies => flag."""
    gap = claim_strength * 10 - final_score
    if claim_strength >= 6 and (gap > 20 or neg_count >= 2):
        return "HIGH", f"Claims {claim_strength}/10 vs score {final_score:.0f}, {neg_count} controversies"
    if claim_strength >= 6 and gap > 5:
        return "MEDIUM", f"Claims {claim_strength}/10 vs score {final_score:.0f}"
    return "LOW", "Claims broadly consistent with performance"
