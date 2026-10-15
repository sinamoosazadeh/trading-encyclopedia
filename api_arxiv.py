import requests, time
import xml.etree.ElementTree as ET
from utils import retry_get, clean_title, clean_authors, is_english, is_valid_url, get_access_level, log
from config import RESULTS_PER_QUERY, REQUEST_DELAY

BASE = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

def search(query, limit=RESULTS_PER_QUERY):
    session = requests.Session()
    results = []
    start = 0
    batch = min(limit, 100)
    while len(results) < limit:
        params = {
            "search_query": "ti:" + query + " OR abs:" + query,
            "start": start, "max_results": batch,
            "sortBy": "relevance", "sortOrder": "descending"
        }
        r = retry_get(session, BASE, params=params, timeout=45)
        if not r: break
        try: root = ET.fromstring(r.content)
        except: break
        entries = root.findall("atom:entry", NS)
        if not entries: break
        for entry in entries:
            raw = (entry.findtext("atom:title", "", NS) or "").replace("\n", " ")
            title = clean_title(raw)
            if not title or not is_english(title): continue
            author_els = entry.findall("atom:author", NS)
            authors = clean_authors([{"name": el.findtext("atom:name", "", NS)} for el in author_els])
            entry_id = entry.findtext("atom:id", "", NS).strip()
            arxiv_id = entry_id.split("/abs/")[-1].split("v")[0]
            doi_el = entry.find("arxiv:doi", NS)
            doi = doi_el.text.strip() if doi_el is not None else ""
            pdf_url = ""
            for lnk in entry.findall("atom:link", NS):
                if lnk.get("title") == "pdf":
                    pdf_url = lnk.get("href", "")
                    break
            url = pdf_url or ("https://doi.org/" + doi if doi else "https://arxiv.org/abs/" + arxiv_id)
            if not is_valid_url(url): continue
            pub_date = entry.findtext("atom:published", "", NS)[:4]
            ab = clean_title(entry.findtext("atom:summary", "", NS))[:250]
            cat_el = entry.find("arxiv:primary_category", NS)
            venue = cat_el.get("term", "arXiv") if cat_el is not None else "arXiv"
            rec = {
                "source": "arXiv",
                "title": title,
                "authors": authors,
                "year": pub_date,
                "pages": "-",
                "venue": venue,
                "doc_type": "preprint",
                "abstract": ab,
                "doi": doi,
                "url": url,
                "cited_by": 0,
                "language": "en",
                "open_access": True,
                "keywords": "",
            }
            rec["access_level"] = "OPEN"
            results.append(rec)
        start += batch
        if len(entries) < batch: break
        time.sleep(REQUEST_DELAY * 3)
    return results[:limit]
