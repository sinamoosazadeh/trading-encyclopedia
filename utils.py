import os, re, time, json, logging, threading, unicodedata

log = logging.getLogger("encyclopedia")
log.setLevel(os.getenv("TE_LOG_LEVEL", "INFO").upper())
log.propagate = False
if not log.handlers:
    log.addHandler(logging.StreamHandler())

def configure_logging():
    """Opt in to file logging with TRADING_ENCYCLOPEDIA_LOG; never create files on import."""
    target = os.getenv("TRADING_ENCYCLOPEDIA_LOG", "").strip()
    if not target:
        return
    directory = os.path.dirname(os.path.abspath(os.path.expanduser(target)))
    os.makedirs(directory, exist_ok=True)
    if not any(isinstance(handler, logging.FileHandler) for handler in log.handlers):
        log.addHandler(logging.FileHandler(os.path.expanduser(target), encoding="utf-8"))

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
    """Validate an absolute HTTP(S) URL without accepting malformed hostnames."""
    from urllib.parse import urlsplit
    if not isinstance(url, str) or len(url.strip()) < 10:
        return False
    try:
        parsed = urlsplit(url.strip())
        return (
            parsed.scheme.lower() in ("http", "https")
            and bool(parsed.hostname)
            and "." in parsed.hostname
            and parsed.username is None
            and parsed.password is None
        )
    except (TypeError, ValueError):
        return False

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
    """Return a conservative access label based on explicit evidence and exact hosts."""
    from urllib.parse import urlsplit
    from config import OPEN_DOMAINS, PAYWALL_DOMAINS
    url = str(item.get("url", "") or "").strip()
    if item.get("open_access") is True or item.get("unpaywall_pdf"):
        return "OPEN"
    try:
        host = (urlsplit(url).hostname or "").lower().rstrip(".")
    except (TypeError, ValueError):
        host = ""
    if not host:
        return "UNKNOWN"
    def matches_domain(domain):
        domain = domain.lower().strip(".")
        if host == domain or host.endswith("." + domain):
            return True
        # A few registries use a provider name without a full registrable domain.
        return domain == "onlinelibrary" and host.startswith("onlinelibrary.")
    if any(matches_domain(d) for d in OPEN_DOMAINS):
        return "OPEN"
    if any(matches_domain(d) for d in PAYWALL_DOMAINS):
        return "PARTIAL"
    return "UNKNOWN"

def _normalise_doi(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.strip().rstrip(" .;/)")


def _normalise_title(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _normalise_authors(value):
    if isinstance(value, (list, tuple)):
        value = ";".join(str(v) for v in value)
    return " ".join(re.sub(r"[^\w]+", " ", str(value or "")).casefold().split())


def _record_identity(item):
    """Prefer stable identifiers; otherwise use complete bibliographic identity.

    Do not truncate titles and do not automatically merge records with distinct DOIs.
    Fuzzy-title matching is intentionally left to a separately reviewable workflow.
    """
    doi = _normalise_doi(item.get("doi"))
    if doi:
        return ("doi", doi)
    title = _normalise_title(item.get("title"))
    if not title:
        return None
    authors = _normalise_authors(item.get("authors"))
    year = str(item.get("year") or "").strip()
    venue = _normalise_title(item.get("venue"))
    if authors and year:
        return ("bibliographic", title, authors, year)
    if year and venue:
        return ("bibliographic", title, year, venue)
    # Title-only matching is too aggressive for a research catalogue.
    return None


def deduplicate(items):
    """Conservatively merge exact identities while preserving complementary fields."""
    unique = []
    positions = {}
    for original in items:
        if not isinstance(original, dict):
            continue
        item = dict(original)
        identity = _record_identity(item)
        if identity is None or identity not in positions:
            if identity is not None:
                positions[identity] = len(unique)
            unique.append(item)
            continue

        target = unique[positions[identity]]
        # Preserve the original record but fill missing values from the duplicate.
        for key, value in item.items():
            if key.startswith("_"):
                if key not in target or not target[key]:
                    target[key] = value
                continue
            if target.get(key) in (None, "", [], {}, "-") and value not in (None, "", [], {}, "-"):
                target[key] = value
        # Preserve source provenance without changing the legacy display field.
        provenance = target.setdefault("source_provenance", [])
        for source in (target.get("source"), item.get("source")):
            if source and source not in provenance:
                provenance.append(source)
        if identity[0] == "doi" and target.get("doi"):
            target["doi"] = _normalise_doi(target["doi"])
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
