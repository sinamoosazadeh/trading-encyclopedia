#!/usr/bin/env python3
import sys, os, time, json, shutil, importlib, requests

res = {"pass": 0, "fail": 0, "warn": 0}

def chk(n, p, m="", w=False):
    tag = "PASS" if p else ("WARN" if w else "FAIL")
    print("  [" + tag + "]  " + n + (" - " + m if m else ""))
    k = "pass" if p else ("warn" if w else "fail")
    res[k] += 1

print("\n" + "="*55)
print("  PREFLIGHT CHECK - Trading Encyclopedia v2.0")
print("="*55 + "\n")

# --- 1: Python & Packages ---
print("[1/6] Python and Packages")
chk("Python >= 3.8 (have " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + ")", sys.version_info >= (3, 8))
pkgs = ["requests","urllib3","colorama","dateutil","langdetect","lxml","json","xml.etree.ElementTree","concurrent.futures","threading","hashlib","re"]
for p in pkgs:
    try: importlib.import_module(p); chk("Package: " + p, True)
    except: chk("Package: " + p, False, "pip install " + p)

# --- 2: Storage ---
print("\n[2/6] Storage and Permissions")
t, u, fr = shutil.disk_usage(os.path.expanduser("~"))
fm = fr // (1024*1024)
chk("Free storage: " + str(fm) + " MB (need 700+)", fm > 700, "have " + str(fm) + " MB", w=(400 < fm <= 700))
try:
    td = os.path.expanduser("~/encyclopedia/test_wr")
    os.makedirs(td, exist_ok=True)
    with open(td + "/t.txt", "w") as f: f.write("t")
    os.remove(td + "/t.txt"); os.rmdir(td)
    chk("Write: ~/encyclopedia/", True)
except Exception as e: chk("Write: ~/encyclopedia/", False, str(e))
sd = "/sdcard/Download"
try:
    if os.path.isdir(sd):
        with open(sd + "/.et", "w") as f: f.write("t")
        os.remove(sd + "/.et"); chk("Write: /sdcard/Download", True)
    else: chk("Write: /sdcard/Download", False, "run: termux-setup-storage", w=True)
except Exception as e: chk("Write: /sdcard/Download", False, str(e), w=True)

# --- 3: Network ---
print("\n[3/6] Network Connectivity")
def turl(n, u):
    try:
        r = requests.get(u, timeout=15, headers={"User-Agent": "TradingEnc/2.0"})
        chk("Net: " + n + " (HTTP " + str(r.status_code) + ")", r.status_code in (200,301,302,403))
    except Exception as e: chk("Net: " + n, False, str(e)[:50])
turl("Google", "https://www.google.com")
turl("GitHub", "https://api.github.com")
turl("DOI", "https://doi.org/10.1016/j.jfineco.2020.01.001")

# --- 4: APIs ---
print("\n[4/6] API Tests")
def api(name, url, params=None, hdrs=None):
    time.sleep(1.5)
    try:
        h = {"User-Agent": "TradingEnc/2.0 (mailto:test@test.com)"}
        if hdrs: h.update(hdrs)
        r = requests.get(url, params=params, headers=h, timeout=25)
        if r.status_code == 429:
            chk(name + " - rate limited (429 - normal)", True); return
        try: d = r.json()
        except: d = {}
        for key in ["items","results","data","records"]:
            if key in d:
                cnt = len(d[key] if isinstance(d[key], list) else d.get("message", {}).get(key, []))
                chk(name + " - HTTP " + str(r.status_code) + ", " + str(cnt) + " result(s)", r.status_code == 200); return
        chk(name + " - HTTP " + str(r.status_code), r.status_code == 200)
    except Exception as e: chk(name, False, str(e)[:60])

api("CrossRef (no key)", "https://api.crossref.org/works", {"query":"backtest trading","rows":1})
api("OpenAlex (with key)", "https://api.openalex.org/works", {"search":"backtest trading","per_page":1,"api_key":"piwCvXWBWaoWEFT8s8S5CC"})
api("SemanticScholar (no key)", "https://api.semanticscholar.org/graph/v1/paper/search", {"query":"backtest trading","fields":"title","limit":1})
api("Springer Meta (with key)", "https://api.springernature.com/meta/v2/json", {"q":"backtest trading","api_key":"61fd7a8b7327ad2cd1d209e0a3b7ce0c","p":1})
api("Springer OA (with key)", "https://api.springernature.com/openaccess/json", {"q":"trading strategy","api_key":"477aa151e4107f7bb9bdc5f5042acaab","p":1})
api("CORE (with key)", "https://api.core.ac.uk/v3/search/works", {"q":"backtest trading","limit":1}, {"Authorization":"Bearer qXfgGOk4Yh5zAMZLVeo0FmTRlnr8KCH9"})

time.sleep(1.5)
try:
    r = requests.get("http://export.arxiv.org/api/query", params={"search_query":"ti:backtest+trading","max_results":1}, timeout=30)
    found = "found" if "<entry>" in r.text else "empty"
    chk("arXiv (no key) - HTTP " + str(r.status_code) + ", " + found, r.status_code == 200)
except Exception as e: chk("arXiv", False, str(e)[:60])

time.sleep(1.5)
api("EuropePMC (no key)", "https://www.ebi.ac.uk/europepmc/webservices/rest/search", {"query":"trading financial","format":"json","pageSize":1})
api("DOAJ (no key)", "https://doaj.org/api/search/articles/trading%20financial", {"pageSize":1})

# --- 5: Language ---
print("\n[5/6] Language Detection")
try:
    from langdetect import detect
    for txt, exp in [("English paper about trading strategies", "en"), ("Optimizacion de estrategias", "es")]:
        det = detect(txt)
        chk("langdetect: " + txt[:30] + " => " + det, (det=="en") == (exp=="en"))
except: chk("langdetect", False, "pip install langdetect")

# --- 6: Git ---
print("\n[6/6] Git")
chk("Git installed", os.system("git --version > /dev/null 2>&1") == 0, "pkg install git")
import subprocess
v = subprocess.run(["git","--version"], capture_output=True, text=True)
print("    => " + v.stdout.strip())

# --- Summary ---
print("\n" + "="*55)
print("  SUMMARY")
print("="*55)
print("  PASS : " + str(res["pass"]))
print("  WARN : " + str(res["warn"]))
print("  FAIL : " + str(res["fail"]))
if res["fail"] == 0: print("\n  >>> ALL CHECKS PASSED - Ready to start!\n")
elif res["fail"] <= 2: print("\n  >>> MOSTLY OK - fix " + str(res["fail"]) + " issue(s) first\n")
else: print("\n  >>> " + str(res["fail"]) + " FAILURES - fix before proceeding\n")

rpt = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "python": sys.version, "results": res, "storage_free_mb": fm}
with open(os.path.expanduser("~/encyclopedia/preflight_report.json"), "w") as f: json.dump(rpt, f, indent=2)
print("  Report saved: ~/encyclopedia/preflight_report.json\n")