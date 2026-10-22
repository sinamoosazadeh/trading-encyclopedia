#!/usr/bin/env python3
"""
Trading Encyclopedia — Merge & Classify
Combines all batch_*.json files, deduplicates,
classifies into 50 categories, builds output.
Usage: python merge.py
"""
import os, json, time
from config import CATEGORIES, DATA_DIR, OUTPUT_DIR, CATS_DIR, SDCARD_DIR, ensure_runtime_dirs
from utils import deduplicate, load_json, save_json, log, is_english
from classifier import classify
import md_builder

def run():
    ensure_runtime_dirs()
    print("\n" + "="*55)
    print("  TRADING ENCYCLOPEDIA — MERGE & BUILD")
    print("="*55)

    # ── Load all batch files ─────────────────────────────
    all_items = []
    batch_files = [f for f in os.listdir(DATA_DIR) if f.startswith("batch_") and f.endswith(".json")]
    batch_files.sort()

    print("\n  Loading batch files...")
    for fname in batch_files:
        path = os.path.join(DATA_DIR, fname)
        data = load_json(path)
        count = 0
        for key, items in data.items():
            cat = key.split("::")[0]
            for item in items:
                if item.get("title") and item.get("url"):
                    item["_src_cat"] = cat
                    all_items.append(item)
                    count += 1
        print("  " + fname + " -> " + str(count) + " items")

    print("\n  Total raw items : " + str(len(all_items)))

    # ── Language filter ──────────────────────────────────
    en_items = [i for i in all_items if is_english(i.get("title",""))]
    print("  After lang filter: " + str(len(en_items)))

    # ── Global deduplication ─────────────────────────────
    unique = deduplicate(en_items)
    print("  After dedup      : " + str(len(unique)))

    # ── Classify into 50 categories ──────────────────────
    print("\n  Classifying...")
    categorized = {cat: [] for cat in CATEGORIES}
    source_stats = {}

    for item in unique:
        context_text = " ".join(str(item.get(k) or "") for k in ("abstract", "keywords"))
        cats = classify(item.get("title", ""), item.get("_src_cat", ""), context_text=context_text)
        for cat in cats:
            if cat in categorized:
                categorized[cat].append(item)
        src = item.get("source","Unknown")
        source_stats[src] = source_stats.get(src, 0) + 1

    # ── Sort by citations ─────────────────────────────────
    for cat in categorized:
        categorized[cat] = sorted(
            deduplicate(categorized[cat]),
            key=lambda x: int(x.get("cited_by") or 0),
            reverse=True
        )

    total_unique = sum(len(v) for v in categorized.values())
    print("  Total classified : " + str(total_unique))

    # ── Save master JSON ──────────────────────────────────
    master_path = os.path.join(DATA_DIR, "master_classified.json")
    stats_obj = {"source_stats": source_stats, "per_category": {k: len(v) for k,v in categorized.items()}, "unique_records": len(unique), "category_assignments": total_unique, "unclassified_records": sum(1 for item in unique if not classify(item.get("title", ""), item.get("_src_cat", ""), context_text=" ".join(str(item.get(k) or "") for k in ("abstract", "keywords")))), "total": total_unique}
    save_json({"categorized": categorized, "stats": stats_obj}, master_path)
    print("  Master JSON: " + master_path)

    # ── Build Markdown output ─────────────────────────────
    print("\n  Building Markdown files...")
    md_builder.build_all(categorized, stats_obj)

    print("\n" + "="*55)
    print("  MERGE COMPLETE")
    print("="*55)
    print("  Items classified : " + str(total_unique))
    print("  Output directory : " + OUTPUT_DIR)
    for cat, items in categorized.items():
        label = cat.split("_",1)[1].replace("_"," & ")
        print("    " + cat[:3] + " " + label[:35].ljust(35) + str(len(items)).rjust(6))

if __name__ == "__main__":
    run()
