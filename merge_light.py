#!/usr/bin/env python3
"""
Lightweight merge - processes in chunks to save RAM
"""
import os, sys, json, re, gc
from config import CATEGORIES, DATA_DIR, OUTPUT_DIR, CATS_DIR, SDCARD_DIR, ensure_runtime_dirs
from classifier import classify
from utils import _record_identity, is_english

def is_en(text):
    return is_english(text)

def dedup(items):
    from utils import deduplicate
    return deduplicate(items)

def safe(t, n=300):
    return str(t or "-").replace("|","—").replace("\n"," ")[:n] or "-"


def main():
    ensure_runtime_dirs()

    print("\n" + "="*55)
    print("  LIGHTWEIGHT MERGE & BUILD")
    print("="*55)

    # Step 1: Load, filter, dedup — one file at a time
    print("\nStep 1: Loading and filtering...")
    all_unique = []
    seen_identities = {}

    batch_files = sorted([f for f in os.listdir(DATA_DIR)
                          if f.startswith("batch_") and f.endswith(".json")])

    for fname in batch_files:
        path = os.path.join(DATA_DIR, fname)
        try:
            data = json.load(open(path, encoding="utf-8"))
        except:
            print("  SKIP (bad json): " + fname)
            continue

        items = []
        for key, val in data.items():
            cat = key.split("::")[0]
            for item in val:
                if not isinstance(item, dict): continue
                if not item.get("title") or not item.get("url"): continue
                if not is_en(item.get("title","")): continue
                item["_src_cat"] = cat
                items.append(item)

        # Deduplicate only on stable or complete bibliographic identity.
        # Title prefixes are not identifiers; ambiguous records are retained.
        added = 0
        for item in items:
            identity = _record_identity(item)
            if identity is not None and identity in seen_identities:
                existing = all_unique[seen_identities[identity]]
                for key, value in item.items():
                    if existing.get(key) in (None, "", [], {}, "-") and value not in (None, "", [], {}, "-"):
                        existing[key] = value
                sources = existing.setdefault("source_provenance", [])
                for source in (existing.get("source"), item.get("source")):
                    if source and source not in sources:
                        sources.append(source)
                continue
            if identity is not None:
                seen_identities[identity] = len(all_unique)
            all_unique.append(item)
            added += 1

        print("  " + fname + " -> " + str(added) + " unique kept")
        del data, items
        gc.collect()

    print("\nTotal unique items: " + str(len(all_unique)))
    del seen_identities
    gc.collect()

    # Step 2: Classify
    print("\nStep 2: Classifying into 50 categories...")
    categorized = {cat: [] for cat in CATEGORIES}
    src_stats = {}

    unique_record_count = len(all_unique)
    unclassified_count = 0
    for item in all_unique:
        context_text = " ".join(str(item.get(k) or "") for k in ("abstract", "keywords"))
        cats = classify(item.get("title", ""), item.get("_src_cat", ""), context_text=context_text)
        if not cats:
            unclassified_count += 1
        for cat in cats:
            if cat in categorized:
                categorized[cat].append(item)
        src = item.get("source","?")
        src_stats[src] = src_stats.get(src, 0) + 1

    del all_unique
    gc.collect()

    # Sort by citations
    for cat in categorized:
        categorized[cat].sort(key=lambda x: int(x.get("cited_by") or 0), reverse=True)

    total = sum(len(v) for v in categorized.values())
    print("Total classified items: " + str(total))

    # Step 3: Save metrics and use the canonical renderer shared with merge.py.
    stats = {
        "total": total,
        "unique_records": unique_record_count,
        "category_assignments": total,
        "unclassified_records": unclassified_count,
        "source_stats": src_stats,
        "per_category": {k: len(v) for k, v in categorized.items()},
    }
    with open(os.path.join(DATA_DIR, "stats.json"), "w", encoding="utf-8") as handle:
        json.dump(stats, handle, indent=2)
    print("Metrics saved: " + os.path.join(DATA_DIR, "stats.json"))

    # The same renderer prevents the lightweight path from silently drifting in schema.
    import md_builder
    md_builder.build_all(categorized, stats)

    print("\n" + "=" * 55)
    print("LIGHTWEIGHT MERGE COMPLETE")
    print("=" * 55)
    print("Unique records: " + str(stats["unique_records"]))
    print("Category assignments: " + str(stats["category_assignments"]))
    print("Unclassified records: " + str(stats["unclassified_records"]))
    print("Output: " + OUTPUT_DIR)



if __name__ == "__main__":
    main()
