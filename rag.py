"""Lightweight RAG over a sustainability report: TF-IDF retrieval + regex metric
extraction + optional Claude answer. Every result carries a page citation."""
import os, re
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_pdf(path: str) -> list[tuple[int, str]]:
    return [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(path).pages)]

def chunk(pages, size=120, overlap=30) -> list[dict]:
    out = []
    for page, text in pages:
        words = text.split()
        step = size - overlap
        for i in range(0, max(len(words), 1), step):
            piece = " ".join(words[i:i + size])
            if piece.strip():
                out.append({"page": page, "text": piece})
    return out

class ReportIndex:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vec.fit_transform([c["text"] for c in chunks])

    def search(self, query: str, k: int = 4) -> list[dict]:
        sims = cosine_similarity(self.vec.transform([query]), self.matrix)[0]
        top = sims.argsort()[::-1][:k]
        return [{**self.chunks[i], "score": float(sims[i])} for i in top if sims[i] > 0]

NUM = r"([\d,]+(?:\.\d+)?)"
PATTERNS = {
    "Scope 1 emissions": [rf"scope\s*1[^0-9]{{0,60}}{NUM}"],
    "Scope 2 emissions": [rf"scope\s*2[^0-9]{{0,60}}{NUM}"],
    "Women on board (%)": [rf"women[^0-9]{{0,60}}board[^0-9]{{0,40}}{NUM}\s*%",
                           rf"board[^0-9]{{0,60}}women[^0-9]{{0,40}}{NUM}\s*%"],
    "Renewable energy (%)": [rf"renewable[^0-9]{{0,60}}{NUM}\s*%"],
    "Injury rate (LTIFR)": [rf"(?:ltifr|injury rate)[^0-9]{{0,40}}{NUM}"],
}

def extract_metrics(chunks) -> list[dict]:
    found = []
    for metric, pats in PATTERNS.items():
        for c in chunks:
            hit = next((m for p in pats if (m := re.search(p, c["text"], re.I))), None)
            if hit:
                found.append({"metric": metric, "value": hit.group(1), "page": c["page"],
                              "evidence": c["text"][max(0, hit.start() - 40):hit.end() + 40]})
                break
    return found

def answer(question: str, index: ReportIndex) -> tuple[str, list[dict]]:
    hits = index.search(question)
    if not hits:
        return "No relevant passage found in the report.", []
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        try:
            import anthropic
            ctx = "\n\n".join(f"[p.{h['page']}] {h['text']}" for h in hits)
            prompt = (f"Answer using ONLY the report excerpts below. Cite pages like [p.12]. "
                      f"If the answer is not present, say so.\n\n{ctx}\n\nQuestion: {question}")
            msg = anthropic.Anthropic().messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"), max_tokens=500,
                messages=[{"role": "user", "content": prompt}])
            return msg.content[0].text, hits
        except Exception as e:
            return f"(LLM unavailable: {e}) Showing top passages instead.", hits
    return "Top matching passages (set ANTHROPIC_API_KEY for a written answer):", hits
