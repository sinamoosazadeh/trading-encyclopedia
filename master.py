#!/usr/bin/env python3
"""
Trading Encyclopedia — Master Search Engine
Usage:
  python master.py --api crossref
  python master.py --api openalex
  python master.py --api semanticscholar
  python master.py --api springer
  python master.py --api arxiv
  python master.py --api core
  python master.py --api europepmc
  python master.py --api doaj
  python master.py --api repec
  python master.py --api all
"""
import os, sys, time, json, signal, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import CATEGORIES, DATA_DIR, MAX_WORKERS, REQUEST_DELAY, ensure_runtime_dirs
from utils import deduplicate, save_json, load_json, log, cache_lock, progress_bar

import api_crossref, api_openalex, api_semanticscholar
import api_springer, api_arxiv, api_core
import api_europepmc, api_doaj, api_repec

API_MAP = {
    "crossref":        api_crossref.search,
    "openalex":        api_openalex.search,
    "semanticscholar": api_semanticscholar.search,
    "springer":        api_springer.search,
    "arxiv":           api_arxiv.search,
    "core":            api_core.search,
    "europepmc":       api_europepmc.search,
    "doaj":            api_doaj.search,
    "repec":           api_repec.search,
}

_cache = {}
_done = 0
_total = 0

def cache_path(api_name):
    return os.path.join(DATA_DIR, "batch_" + api_name + ".json")

def save_cache(api_name):
    with cache_lock:
        save_json(_cache, cache_path(api_name))

def search_one(api_name, func, category, kw):
    global _done
    key = category + "::" + kw
    try:
        results = func(kw)
        valid = [r for r in results if r.get("title") and r.get("url")]
        for r in valid:
            r["_src_cat"] = category
        with cache_lock:
            existing = _cache.get(key, [])
            _cache[key] = existing + valid
        _done += 1
        return api_name, category, kw, len(valid), None
    except Exception as e:
        _done += 1
        return api_name, category, kw, 0, str(e)

def run(api_name):
    global _cache, _done, _total
    ensure_runtime_dirs()

    func = API_MAP.get(api_name)
    if not func:
        print("Unknown API: " + api_name)
        sys.exit(1)

    print("\n" + "="*55)
    print("  TRADING ENCYCLOPEDIA — API: " + api_name.upper())
    print("="*55)

    # Load existing cache
    _cache = load_json(cache_path(api_name))
    cached_keys = set(_cache.keys())

    # Build task list (skip already done)
    tasks = []
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            key = category + "::" + kw
            if key not in cached_keys:
                tasks.append((api_name, func, category, kw))

    _total = len(tasks)
    _done  = 0

    print("  Cached queries : " + str(len(cached_keys)))
    print("  New queries    : " + str(_total))
    print("  Total keywords : " + str(len(cached_keys) + _total))
    print("  Workers        : " + str(MAX_WORKERS))
    print("  Delay          : " + str(REQUEST_DELAY) + "s")

    if _total == 0:
        print("\n  All queries already cached. Run merge.py to build output.")
        _report(api_name)
        return

    print()

    save_counter = 0

    def sigint_handler(sig, frame):
        print("\n\n  Interrupted — saving cache...")
        save_cache(api_name)
        print("  Cache saved: " + cache_path(api_name))
        print("  Resume with: python master.py --api " + api_name)
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        futures = {exe.submit(search_one, *t): t for t in tasks}
        for future in as_completed(futures):
            an, cat, kw, cnt, err = future.result()
            save_counter += 1
            progress_bar(_done, _total)
            if err:
                log.debug("[" + an + "] ERROR on '" + kw[:30] + "': " + err[:50])
            if save_counter % 30 == 0:
                save_cache(api_name)

    print()
    save_cache(api_name)
    _report(api_name)

def _report(api_name):
    total_items = sum(len(v) for v in _cache.values())
    unique = deduplicate([item for items in _cache.values() for item in items])
    print("\n" + "="*55)
    print("  DONE: " + api_name.upper())
    print("="*55)
    print("  Raw items    : " + str(total_items))
    print("  Unique items : " + str(len(unique)))
    print("  Cache file   : " + cache_path(api_name))
    print("  Next: run same command to continue OR run merge.py\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", required=True,
                        help="API name: crossref|openalex|semanticscholar|springer|arxiv|core|europepmc|doaj|repec|all")
    args = parser.parse_args()

    if args.api == "all":
        for name in API_MAP:
            run(name)
    else:
        run(args.api)
