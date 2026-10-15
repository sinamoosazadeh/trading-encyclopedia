import requests, time
from utils import retry_get, clean_title, clean_authors, is_english, is_valid_url, get_access_level, log
from config import API_KEYS, RESULTS_PER_QUERY, REQUEST_DELAY

BASE_META = "https://api.springernature.com/meta/v2/json"
BASE_OA   = "https://api.springernature.com/openaccess/json"

def _parse(item, source="Springer"):
    title = clean_title(item.get("title", ""))
    if not title or not is_english(title): return None
    creators = item.get("creators") or []
    authors = clean_authors([{"name": c.get("creator", "")} for c in creators])
    start = item.get("startingPage", "")
    end   = item.get("endingPage", "")
    pages = "-"
    if start and end:
        try: pages = str(int(end) - int(start) + 1)
        except: pages = str(start) + "-" + str(end)
    elif start: pages = str(start)
    doi = item.get("doi", "")
    raw_url = item.get("url", "")
    if isinstance(raw_url, list):
        url = raw_url[0].get("value", "") if raw_url else ""
    else:
        url = raw_url or ("https://doi.org/" + doi if doi else "")
    if not is_valid_url(url): return None
    rec = {
        "source": source,
        "title": title,
        "authors": authors,
        "year": str(item.get("publicationDate", "")[:4]),
        "pages": pages,
        "venue": item.get("publicationName", ""),
        "doc_type": item.get("contentType", ""),
        "abstract": str(item.get("abstract", ""))[:250],
        "doi": doi,
        "url": url,
        "cited_by": 0,
        "language": "en",
        "open_access": source == "Springer-OA",
        "keywords": "",
    }
    rec["access_level"] = get_access_level(rec)
    return rec

def _search_api(base_url, query, key, limit, source):
    session = requests.Session()
    results = []
    start = 1
    while len(results) < limit:
        params = {"q": query, "api_key": key, "s": start, "p": min(50, limit - len(results))}
        r = retry_get(session, base_url, params=params)
        if not r: break
        data = r.json()
        records = data.get("records", [])
        if not records: break
        for item in records:
            parsed = _parse(item, source)
            if parsed: results.append(parsed)
        total = int((data.get("result") or [{}])[0].get("total", "0"))
        start += len(records)
        if start > min(total, limit): break
        time.sleep(REQUEST_DELAY)
    return results

def search(query, limit=RESULTS_PER_QUERY):
    results = []
    meta_key = API_KEYS.get("springer_meta", "")
    oa_key   = API_KEYS.get("springer_oa", "")
    if meta_key:
        results.extend(_search_api(BASE_META, query, meta_key, limit, "Springer"))
    if oa_key:
        results.extend(_search_api(BASE_OA, query, oa_key, min(limit, 30), "Springer-OA"))
    return results[:limit]
