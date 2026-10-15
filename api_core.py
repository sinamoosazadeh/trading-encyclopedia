import requests, time
from utils import retry_get, clean_title, clean_authors, is_english, is_valid_url, get_access_level, log
from config import API_KEYS, RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "https://api.core.ac.uk/v3/search/works"

def search(query, limit=RESULTS_PER_QUERY):
    key = API_KEYS.get("core", "")
    if not key: return []
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + key})
    results = []
    offset = 0
    batch = min(limit, 100)
    while len(results) < limit:
        payload = {
            "q": query, "limit": batch, "offset": offset,
            "fields": ["title","authors","doi","downloadUrl","links","yearPublished","journals","citationCount","abstract"]
        }
        try:
            r = session.post(BASE, json=payload, timeout=45)
            if r.status_code == 429: time.sleep(30); continue
            if r.status_code != 200: break
            data = r.json()
            items = data.get("results", [])
        except Exception as e:
            log.debug("CORE error: " + str(e)[:50]); break
        if not items: break
        for item in items:
            title = clean_title(item.get("title", ""))
            if not title or not is_english(title): continue
            raw = item.get("authors", []) or []
            if raw and isinstance(raw[0], dict):
                authors = clean_authors(raw)
            else:
                authors = clean_authors([{"name": str(a)} for a in raw])
            doi = str(item.get("doi") or "").replace("https://doi.org/", "")
            dl = item.get("downloadUrl", "") or ""
            links = item.get("links") or []
            link_url = links[0].get("url", "") if links else ""
            url = dl or link_url or ("https://doi.org/" + doi if doi else "")
            if not is_valid_url(url): continue
            jrnls = item.get("journals") or []
            venue = jrnls[0].get("title", "") if jrnls else ""
            ab = str(item.get("abstract") or "")[:250]
            rec = {
                "source": "CORE",
                "title": title,
                "authors": authors,
                "year": str(item.get("yearPublished") or ""),
                "pages": "-",
                "venue": venue,
                "doc_type": "journal_article",
                "abstract": ab,
                "doi": doi,
                "url": url,
                "cited_by": item.get("citationCount", 0) or 0,
                "language": "en",
                "open_access": True,
                "keywords": "",
            }
            rec["access_level"] = "OPEN"
            results.append(rec)
        offset += batch
        total = data.get("totalHits", data.get("total", 0))
        if offset >= total or len(items) < batch: break
        time.sleep(REQUEST_DELAY)
    return results[:limit]
