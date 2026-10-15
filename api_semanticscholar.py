import requests, time
from utils import retry_get, clean_title, clean_authors, is_english, is_valid_url, get_access_level, log
from config import API_KEYS, RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,authors,externalIds,url,venue,openAccessPdf,publicationDate,citationCount,abstract"

def search(query, limit=RESULTS_PER_QUERY):
    key = API_KEYS.get("semantic_scholar", "")
    headers = {}
    if key: headers["x-api-key"] = key
    session = requests.Session()
    session.headers.update(headers)
    results = []
    offset = 0
    batch = min(limit, 100)
    while len(results) < limit:
        params = {"query": query, "fields": FIELDS, "limit": batch, "offset": offset}
        r = retry_get(session, BASE, params=params)
        if not r: break
        data = r.json().get("data", [])
        if not data: break
        for paper in data:
            title = clean_title(paper.get("title", ""))
            if not title or not is_english(title): continue
            ids = paper.get("externalIds") or {}
            doi = ids.get("DOI", "")
            pdf = (paper.get("openAccessPdf") or {}).get("url", "")
            url = pdf or paper.get("url", "") or ("https://doi.org/" + doi if doi else "")
            if not is_valid_url(url): continue
            ab = str(paper.get("abstract") or "")[:250]
            rec = {
                "source": "SemanticScholar",
                "title": title,
                "authors": clean_authors(paper.get("authors", [])),
                "year": str((paper.get("publicationDate") or "")[:4]),
                "pages": "-",
                "venue": paper.get("venue", ""),
                "doc_type": "journal_article",
                "abstract": ab,
                "doi": doi,
                "url": url,
                "cited_by": paper.get("citationCount", 0) or 0,
                "language": "en",
                "open_access": bool(pdf),
                "keywords": "",
            }
            rec["access_level"] = get_access_level(rec)
            results.append(rec)
        offset += batch
        if len(data) < batch: break
        time.sleep(REQUEST_DELAY * 2)
    return results[:limit]
