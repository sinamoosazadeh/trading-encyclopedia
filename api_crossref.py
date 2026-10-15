import requests, time
from utils import retry_get, clean_title, clean_authors, parse_pages, is_english, is_valid_url, get_access_level, log
from config import API_KEYS, CONTACT_EMAIL, RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "https://api.crossref.org/works"
HEADERS = {"User-Agent": "TradingEncyclopedia/2.0 (mailto:" + CONTACT_EMAIL + ")"}

def search(query, limit=RESULTS_PER_QUERY):
    session = requests.Session()
    session.headers.update(HEADERS)
    results = []
    offset = 0
    batch = min(limit, 100)
    while len(results) < limit:
        params = {
            "query": query, "rows": batch, "offset": offset,
            "mailto": CONTACT_EMAIL,
            "select": "DOI,title,author,page,URL,container-title,publisher,type,published,abstract,is-referenced-by-count"
        }
        r = retry_get(session, BASE, params=params)
        if not r: break
        items = r.json().get("message", {}).get("items", [])
        if not items: break
        for item in items:
            raw_titles = item.get("title") or []
            title = clean_title(raw_titles[0] if raw_titles else "")
            if not title or not is_english(title): continue
            doi = item.get("DOI", "")
            url = item.get("URL") or ("https://doi.org/" + doi if doi else "")
            if not is_valid_url(url): continue
            venue_list = item.get("container-title") or []
            ab = str(item.get("abstract") or "")[:250]
            rec = {
                "source": "CrossRef",
                "title": title,
                "authors": clean_authors(item.get("author", [])),
                "year": str((item.get("published") or {}).get("date-parts", [[""]])[0][0]),
                "pages": parse_pages(item),
                "venue": venue_list[0] if venue_list else "",
                "doc_type": item.get("type", ""),
                "abstract": ab,
                "doi": doi,
                "url": url,
                "cited_by": item.get("is-referenced-by-count", 0) or 0,
                "language": "en",
                "open_access": False,
                "keywords": "",
            }
            rec["access_level"] = get_access_level(rec)
            results.append(rec)
        offset += len(items)
        if len(items) < batch: break
        time.sleep(REQUEST_DELAY)
    return results[:limit]
