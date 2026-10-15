import os, re, time, json, logging, threading, unicodedata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.expanduser("~/encyclopedia/run.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("encyclopedia")
cache_lock = threading.Lock()

def normalize(text):
    if not text: return ""
    text = str(text)
    text = re.sub(r"[-_\s]+", " ", text)
    text = text.lower().strip()
    return text

def is_english(text):
    if not text or len(text.strip()) < 5: return False
    text = str(text)
    latin = sum(1 for c in text if c.isalpha() and ord(c) < 256)
    total = sum(1 for c in text if c.isalpha())
    if total == 0: return False
    ratio = latin / total
    if ratio < 0.80: return False
    try:
        from langdetect import detect
        return detect(text[:300]) == "en"
    except:
        return ratio > 0.85

def is_valid_url(url):
    if not url or not isinstance(url, str): return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    if len(url) < 15: return False
    if "." not in url[8:]: return False
    return True

def clean_title(text):
    if not text: return ""
    text = str(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace("|", "-").replace("\n", " ")
    return text.strip()

def clean_authors(raw):
    if not raw: return "-"
    if isinstance(raw, str): return raw[:200]
    names = []
    for a in raw[:7]:
        if isinstance(a, dict):
            n = (a.get("name") or
                 (str(a.get("given","")) + " " + str(a.get("family",""))).strip() or
                 a.get("display_name","") or
                 a.get("creator",""))
        else:
            n = str(a)
        n = n.strip().replace("|","-")
        if n and n not in names: names.append(n)
    result = "; ".join(names)
    if len(raw) > 7: result += " et al."
    return result or "-"

def parse_pages(item):
    if not isinstance(item, dict): return "-"
    for key in ("page","pages"):
        val = str(item.get(key,"")).strip()
        if val and val != "None":
            if "-" in val:
                parts = val.split("-")
                try: return str(int(parts[-1]) - int(parts[0]) + 1)
                except: return val
            return val
    b = item.get("biblio") or {}
    fp, lp = str(b.get("first_page","")), str(b.get("last_page",""))
    if fp and lp and fp != "None" and lp != "None":
        try: return str(int(lp) - int(fp) + 1)
        except: return fp + "-" + lp
    return "-"

def get_access_level(item):
    from config import OPEN_DOMAINS, PAYWALL_DOMAINS
    url = str(item.get("url","")).lower()
    oa  = item.get("open_access", False)
    if oa: return "OPEN"
    for d in OPEN_DOMAINS:
        if d in url: return "OPEN"
    for d in PAYWALL_DOMAINS:
        if d in url: return "PARTIAL"
    if item.get("unpaywall_pdf"): return "OPEN"
    return "UNKNOWN"

def deduplicate(items):
    seen_doi, seen_title, unique = set(), set(), []
    for item in items:
        doi = re.sub(r"https?://doi\.org/","", str(item.get("doi",""))).lower().strip()
        title_norm = re.sub(r"\W+","", str(item.get("title","")).lower())[:80]
        if doi and doi in seen_doi: continue
        if title_norm and title_norm in seen_title: continue
        if doi: seen_doi.add(doi)
        if title_norm: seen_title.add(title_norm)
        unique.append(item)
    return unique

def save_json(data, path):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def retry_get(session, url, params=None, headers=None, timeout=35, max_retries=4):
    from config import REQUEST_DELAY
    for attempt in range(max_retries):
        try:
            r = session.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code == 200: return r
            if r.status_code == 429:
                wait = (2 ** attempt) * 5
                log.warning("Rate limit 429 — waiting " + str(wait) + "s")
                time.sleep(wait)
            elif r.status_code in (500,502,503,504):
                time.sleep(3 * (attempt+1))
            elif r.status_code == 404:
                return None
            else:
                log.debug("HTTP " + str(r.status_code) + " " + url[:60])
                return None
        except Exception as e:
            log.debug("Connection error attempt " + str(attempt+1) + ": " + str(e)[:50])
            time.sleep(2 * (attempt+1))
    return None

def progress_bar(done, total, width=35):
    pct = int(done / max(total,1) * width)
    bar = "#" * pct + "." * (width - pct)
    print("\r  [" + bar + "] " + str(done) + "/" + str(total), end="", flush=True)
    if done == total: print()
