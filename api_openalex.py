import requests, time
from utils import retry_get, clean_title, clean_authors, parse_pages, is_english, is_valid_url, get_access_level, log
from config import API_KEYS, CONTACT_EMAIL, RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "https://api.openalex.org/works"

def search(query, limit=RESULTS_PER_QUERY):
    key = API_KEYS.get("openalex", "")
    session = requests.Session()
    results = []
    page = 1
    per_pg = min(limit, 200)
    while len(results) < limit:
        params = {
            "search": query, "per_page": per_pg, "page": page,
            "select": "id,display_name,authorships,doi,biblio,primary_location,open_access,publication_year,type,cited_by_count,keywords,abstract_inverted_index"
        }
        if key: params["api_key"] = key
        else: params["mailto"] = CONTACT_EMAIL
        r = retry_get(session, BASE, params=params)
        if not r: break
        works = r.json().get("results", [])
        if not works: break
        for w in works:
            title = clean_title(w.get("display_name", ""))
            if not title or not is_english(title): continue
            doi_raw = w.get("doi", "") or ""
            doi = doi_raw.replace("https://doi.org/", "")
            loc = w.get("primary_location") or {}
            oa = w.get("open_access") or {}
            pdf = loc.get("pdf_url", "") or oa.get("oa_url", "")
            url = pdf or ("https://doi.org/" + doi if doi else w.get("id", ""))
            if not is_valid_url(url): continue
            kws = [k.get("display_name","") for k in (w.get("keywords") or [])]
            ab_inv = w.get("abstract_inverted_index") or {}
            ab = ""
            if ab_inv:
                try:
                    positions = {pos: word for word, pos_list in ab_inv.items() for pos in pos_list}
                    ab = " ".join(positions[i] for i in sorted(positions)[:50])
                except: pass
            rec = {
                "source": "OpenAlex",
                "title": title,
                "authors": clean_authors([{"name": a.get("author",{}).get("display_name","")} for a in (w.get("authorships") or [])]),
                "year": str(w.get("publication_year", "") or ""),
                "pages": parse_pages(w),
                "venue": ((loc.get("source") or {}).get("display_name","") or ""),
                "doc_type": w.get("type", ""),
                "abstract": ab[:250],
                "doi": doi,
                "url": url,
                "cited_by": w.get("cited_by_count", 0) or 0,
                "language": "en",
                "open_access": bool(oa.get("is_oa", False)),
                "keywords": "; ".join(kws[:8]),
            }
            rec["access_level"] = get_access_level(rec)
            results.append(rec)
        page += 1
        if len(works) < per_pg: break
        time.sleep(REQUEST_DELAY)
    return results[:limit]
