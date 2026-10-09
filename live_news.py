import urllib.parse
import feedparser
import pandas as pd

def fetch_headlines(company: str, n: int = 10) -> pd.DataFrame:
    """Live headlines from Google News RSS (no API key needed)."""
    q = urllib.parse.quote(f'"{company}" ESG OR pollution OR emissions OR governance OR labour OR fraud')
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    rows = [{"company": company, "headline": e.title} for e in feed.entries[:n]]
    return pd.DataFrame(rows, columns=["company", "headline"])

// akshat mishra
