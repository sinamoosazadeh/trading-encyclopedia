import requests, time
from utils import retry_get, clean_title, clean_authors, is_english, is_valid_url, get_access_level, log
from config import RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def search(query, limit=RESULTS_PER_QUERY):
    session = requests.Session()
    results = []
    cursor = "*"
    batch = min(limit, 100)
    while len(results) < limit:
        params = {
            "query": query, "format": "json",
            "resultType": "core", "pageSize": batch,
            "cursorMark": cursor, "sort": "CITED desc"
        }
        r = retry_get(session, BASE, params=params)
        if not r: break
        data = r.json()
        items = data.get("resultList", {}).get("result", [])
        if not items: break
        for item in items:
            title = clean_title(item.get("title", ""))
            if not title or not is_english(title): continue
            raw = (item.get("authorList") or {}).get("author", [])
            authors = clean_authors([{"name": (str(a.get("firstName","")) + " " + str(a.get("lastName",""))).strip()} for a in raw])
            doi = item.get("doi", "") or ""
            url = ("https://doi.org/" + doi if doi else
                   "https://europepmc.org/article/" + str(item.get("source","")) + "/" + str(item.get("id","")))
            if not is_valid_url(url): continue
            ab = str(item.get("abstractText") or "")[:250]
            rec = {
                "source": "EuropePMC",
                "title": title,
                "authors": authors,
                "year": str(item.get("pubYear") or ""),
                "pages": "-",
                "venue": item.get("journalTitle", ""),
                "doc_type": "journal_article",
                "abstract": ab,
                "doi": doi,
                "url": url,
                "cited_by": int(item.get("citedByCount") or 0),
                "language": "en",
                "open_access": item.get("isOpenAccess","N") == "Y",
                "keywords": "",
            }
            rec["access_level"] = get_access_level(rec)
            results.append(rec)
        next_cur = data.get("nextCursorMark", "")
        if not next_cur or next_cur == cursor: break
        cursor = next_cur
        time.sleep(REQUEST_DELAY)
    return results[:limit]
