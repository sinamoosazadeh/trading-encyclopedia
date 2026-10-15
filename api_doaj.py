import requests, time
from utils import retry_get, clean_title, clean_authors, is_english, is_valid_url, get_access_level, log
from config import RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "https://doaj.org/api/search/articles"

def search(query, limit=RESULTS_PER_QUERY):
    session = requests.Session()
    results = []
    page = 1
    batch = min(limit, 100)
    while len(results) < limit:
        params = {
            "search_query": query, "search_field": "title,abstract",
            "page": page, "pageSize": batch, "sort": "score:desc"
        }
        r = retry_get(session, BASE, params=params)
        if not r: break
        data = r.json()
        items = data.get("results", [])
        if not items: break
        for item in items:
            bib = item.get("bibjson", {})
            title = clean_title(bib.get("title", ""))
            if not title or not is_english(title): continue
            raw = bib.get("author", [])
            authors = clean_authors([{"name": a.get("name", "")} for a in raw])
            idents = bib.get("identifier", [])
            doi = next((i.get("id","") for i in idents if i.get("type") == "doi"), "")
            links = bib.get("link", [])
            url = ""
            for lnk in links:
                if lnk.get("type") in ("fulltext","pdf"):
                    url = lnk.get("url", ""); break
            if not url and doi: url = "https://doi.org/" + doi
            if not is_valid_url(url): continue
            sp, ep = bib.get("start_page",""), bib.get("end_page","")
            pages = "-"
            if sp and ep:
                try: pages = str(int(ep) - int(sp) + 1)
                except: pages = str(sp) + "-" + str(ep)
            jrnl = bib.get("journal") or {}
            yr = str(bib.get("year") or "")
            ab = str(bib.get("abstract") or "")[:250]
            kws = [k.get("term","") for k in bib.get("keywords",[]) if k.get("term")]
            rec = {
                "source": "DOAJ",
                "title": title,
                "authors": authors,
                "year": yr,
                "pages": pages,
                "venue": jrnl.get("title", ""),
                "doc_type": "journal_article",
                "abstract": ab,
                "doi": doi,
                "url": url,
                "cited_by": 0,
                "language": "en",
                "open_access": True,
                "keywords": "; ".join(kws[:8]),
            }
            rec["access_level"] = "OPEN"
            results.append(rec)
        total = data.get("total", 0)
        page += 1
        if (page-1)*batch >= total or len(items) < batch: break
        time.sleep(REQUEST_DELAY)
    return results[:limit]
