import requests, time
from utils import retry_get, clean_title, clean_authors, is_english, is_valid_url, get_access_level, log
from config import CONTACT_EMAIL, RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "https://api.repec.org/call.cgi"

def search(query, limit=RESULTS_PER_QUERY):
    session = requests.Session()
    session.headers.update({"User-Agent": "TradingEncyclopedia/2.0 (mailto:" + CONTACT_EMAIL + ")"})
    results = []
    offset = 0
    batch = min(limit, 25)
    while len(results) < limit:
        params = {"code": "jel", "query": query, "limit": batch, "offset": offset, "func": "search"}
        r = retry_get(session, BASE, params=params)
        if not r: break
        try: data = r.json()
        except: break
        items = data if isinstance(data, list) else data.get("items", [])
        if not items: break
        for item in items:
            title = clean_title(item.get("title", ""))
            if not title or not is_english(title): continue
            raw = item.get("authors", "")
            authors = str(raw) if isinstance(raw, str) else clean_authors([{"name": str(a)} for a in raw]) if raw else "-"
            url = item.get("url", "") or item.get("link", "")
            if not is_valid_url(url):
                doi = item.get("doi", "")
                url = "https://doi.org/" + doi if doi else ""
            if not is_valid_url(url): continue
            rec = {
                "source": "RePEC",
                "title": title,
                "authors": authors,
                "year": str(item.get("year") or ""),
                "pages": str(item.get("pages") or "-"),
                "venue": item.get("journal", ""),
                "doc_type": "working_paper",
                "abstract": str(item.get("abstract") or "")[:250],
                "doi": item.get("doi", ""),
                "url": url,
                "cited_by": 0,
                "language": "en",
                "open_access": True,
                "keywords": "",
            }
            rec["access_level"] = "OPEN"
            results.append(rec)
        offset += batch
        if len(items) < batch: break
        time.sleep(REQUEST_DELAY)
    return results[:limit]
