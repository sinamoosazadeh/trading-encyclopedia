#!/usr/bin/env python3
"""
Lightweight merge - processes in chunks to save RAM
"""
import os, sys, json, re, gc
sys.path.insert(0, os.path.expanduser("~/encyclopedia"))
from config import CATEGORIES, DATA_DIR, OUTPUT_DIR, CATS_DIR, SDCARD_DIR
from classifier import classify

def is_en(text):
    if not text: return False
    t = str(text)
    latin = sum(1 for c in t if c.isalpha() and ord(c) < 256)
    total = sum(1 for c in t if c.isalpha())
    return (latin/total > 0.80) if total else False

def dedup(items):
    seen_doi, seen_title, out = set(), set(), []
    for item in items:
        doi = re.sub(r"https?://doi.org/","", str(item.get("doi",""))).lower().strip()
        tn = re.sub(r"\W+","", str(item.get("title","")).lower())[:80]
        if doi and doi in seen_doi: continue
        if tn and tn in seen_title: continue
        if doi: seen_doi.add(doi)
        if tn: seen_title.add(tn)
        out.append(item)
    return out

def safe(t, n=300):
    return str(t or "-").replace("|","—").replace("\n"," ")[:n] or "-"

DATA_DIR   = os.path.expanduser("~/encyclopedia/data")
OUTPUT_DIR = os.path.expanduser("~/encyclopedia/output")
CATS_DIR   = os.path.join(OUTPUT_DIR, "categories")
SDCARD_DIR = "/sdcard/Download/trading-encyclopedia"
for d in [OUTPUT_DIR, CATS_DIR, SDCARD_DIR, os.path.join(SDCARD_DIR,"categories")]:
    os.makedirs(d, exist_ok=True)

print("\n" + "="*55)
print("  LIGHTWEIGHT MERGE & BUILD")
print("="*55)

# Step 1: Load, filter, dedup — one file at a time
print("\nStep 1: Loading and filtering...")
all_unique = []
seen_doi_global = set()
seen_title_global = set()

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

    # Dedup against global seen
    added = 0
    for item in items:
        doi = re.sub(r"https?://doi.org/","", str(item.get("doi",""))).lower().strip()
        tn  = re.sub(r"\W+","", str(item.get("title","")).lower())[:80]
        if doi and doi in seen_doi_global: continue
        if tn and tn in seen_title_global: continue
        if doi: seen_doi_global.add(doi)
        if tn:  seen_title_global.add(tn)
        all_unique.append(item)
        added += 1

    print("  " + fname + " -> " + str(added) + " unique kept")
    del data, items
    gc.collect()

print("\nTotal unique items: " + str(len(all_unique)))
del seen_doi_global, seen_title_global
gc.collect()

# Step 2: Classify
print("\nStep 2: Classifying into 50 categories...")
categorized = {cat: [] for cat in CATEGORIES}
src_stats = {}

for item in all_unique:
    cats = classify(item.get("title",""), item.get("_src_cat",""))
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

# Step 3: Save stats
stats = {"total": total, "source_stats": src_stats,
         "per_category": {k: len(v) for k,v in categorized.items()}}
json.dump(stats, open(os.path.join(DATA_DIR, "stats.json"), "w"), indent=2)
print("Stats saved")

# Step 4: Build Markdown — one category at a time
print("\nStep 3: Building Markdown files...")

HDR = ("| Title | Authors | Year | Pages | Venue"
       " | Cited | Src | Access | Link |\n"
       "|-------|---------|------|-------|------"
       "|-------|-----|--------|------|")

CAT_LABELS = {
    "A01_Optimization":"Optimization & Calibration",
    "A02_Simulation":"Simulation & Synthetic Data",
    "A03_Prediction_Forecasting":"Prediction & Forecasting",
    "A04_Backtesting_Validation":"Backtesting & Strategy Validation",
    "A05_Probability_Statistics_Econometrics":"Probability Statistics & Econometrics",
    "B01_Machine_Learning_Finance":"Machine Learning in Finance",
    "B02_Deep_Learning_Neural_Networks":"Deep Learning & Neural Networks",
    "B03_Reinforcement_Learning_Control":"Reinforcement Learning & Control",
    "B04_NLP_Sentiment_Alternative_Data":"NLP Sentiment & Alternative Data",
    "C01_Market_Microstructure_LOB":"Market Microstructure & Order Book",
    "C02_Liquidity_OrderFlow_Informed":"Liquidity Order Flow & Informed Trading",
    "C03_Market_Impact_Execution":"Market Impact & Execution",
    "C04_HFT_MarketMaking":"HFT & Market Making",
    "C05_Algorithmic_Systematic_Trading":"Algorithmic & Systematic Trading",
    "C06_Trade_Lifecycle_Clearing":"Trade Lifecycle Clearing & Settlement",
    "C07_Market_Participation_Modes":"Market Participation Modes & Accounts",
    "D01_Portfolio_Construction_Optimization":"Portfolio Construction & Optimization",
    "D02_Covariance_Factor_Models":"Covariance Estimation & Factor Models",
    "D03_Risk_Management_Tail_Stress":"Risk Management Tail Risk & Stress",
    "D04_Position_Sizing_Kelly_Capital":"Position Sizing Kelly & Capital Allocation",
    "D05_Factor_Investing_Alpha_Anomalies":"Factor Investing Alpha & Anomalies",
    "D06_Performance_Measurement_Attribution":"Performance Measurement & Attribution",
    "D07_Trading_Journal_Development":"Trading Journal & Trader Development",
    "E01_Derivatives_Options_Volatility":"Derivatives Options & Volatility",
    "E02_Fixed_Income_Rates_Credit":"Fixed Income Rates & Credit",
    "E03_Forex_Commodities_CrossAsset":"Forex Commodities & Cross-Asset",
    "E04_Stochastic_Calculus_MathFinance":"Stochastic Calculus & Mathematical Finance",
    "E05_Statistical_Arbitrage_RelativeValue":"Statistical Arbitrage & Relative Value",
    "F01_MarketProfile_AuctionTheory":"Market Profile & Auction Theory",
    "F02_OrderFlow_Footprint_Tape":"Order Flow Footprint & Tape Reading",
    "F03_Wyckoff_VSA":"Wyckoff Method & VSA",
    "F04_SmartMoney_ICT":"Smart Money Concepts & ICT",
    "F05_Technical_Analysis_ChartPatterns":"Technical Analysis & Chart Patterns",
    "F06_Harmonic_ElliottWave":"Harmonic Patterns & Elliott Wave",
    "F07_Specialized_Trading_Schools":"Specialized Trading Schools",
    "F08_EventDriven_News_Trading":"Event-Driven & News-Based Trading",
    "F09_Trading_Styles_Timeframes":"Trading Styles & Timeframes",
    "F10_Chart_Types_Visualization":"Chart Types & Price Visualization",
    "F11_Market_Scanning_Screening":"Market Scanning & Signal Discovery",
    "G01_Fundamental_Analysis_Valuation":"Fundamental Analysis & Valuation",
    "G02_Macro_Intermarket_CentralBanking":"Macroeconomics Intermarket & Central Banking",
    "G03_Behavioral_Finance_Decision":"Behavioral Finance & Decision Theory",
    "H01_Crypto_DeFi_OnChain":"Cryptocurrency DeFi & On-Chain",
    "H02_TradingSystems_Engineering":"Trading Systems Engineering",
    "H03_Regulation_Compliance_Integrity":"Regulation Compliance & Market Integrity",
    "H04_PropFirm_Retail_Grid":"Prop-Firm Retail & Grid Trading",
    "H05_MarketData_Feeds_Architecture":"Market Data Levels Feeds & Architecture",
    "H06_Exchange_Connectivity_API_OMS":"Exchange Connectivity APIs & OMS",
    "H07_Network_Infrastructure_DataCenters":"Network Infrastructure & Data Centers",
    "H08_Trading_Platforms_Tools":"Trading Platforms & Tools",
}

ACCESS_MAP = {
    "OPEN":"OPEN","PARTIAL":"PART","GATED":"GATE","PAYWALL":"PAY","UNKNOWN":"?"
}

import time
now = time.strftime("%Y-%m-%d %H:%M")

for i, (cat_id, label) in enumerate(CAT_LABELS.items()):
    items = categorized.get(cat_id, [])
    lines = ["# " + label, "",
             "> Category: `" + cat_id + "` | Items: **" + str(len(items)) + "** | Generated: " + now,
             "", "---", ""]
    if not items:
        lines.append("*No items found.*")
    else:
        lines.append(HDR)
        for item in items:
            url = item.get("url","")
            link = "[LINK](" + url + ")" if url and url!="-" else "-"
            acc = ACCESS_MAP.get(item.get("access_level","UNKNOWN"),"?")
            src = str(item.get("source",""))[:4]
            row = ("| " + safe(item.get("title"),80) +
                   " | " + safe(item.get("authors"),60) +
                   " | " + safe(item.get("year"),4) +
                   " | " + safe(item.get("pages"),8) +
                   " | " + safe(item.get("venue"),50) +
                   " | " + str(item.get("cited_by") or 0) +
                   " | " + src +
                   " | " + acc +
                   " | " + link + " |")
            lines.append(row)
    content = "\n".join(lines)
    out_path = os.path.join(CATS_DIR, cat_id + ".md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    sd_path = os.path.join(SDCARD_DIR, "categories", cat_id + ".md")
    with open(sd_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [" + str(i+1) + "/50] " + cat_id + " -> " + str(len(items)) + " items")
    del items, lines
    gc.collect()

# Build INDEX
print("\nBuilding INDEX.md...")
idx = ["# Trading & Financial Markets Encyclopedia", "",
       "> Generated: " + now + " | Total: " + str(total), "", "---", ""]
for cat_id, label in CAT_LABELS.items():
    cnt = stats["per_category"].get(cat_id, 0)
    idx.append("- [" + label + "](categories/" + cat_id + ".md) — **" + str(cnt) + "** items")
idx_content = "\n".join(idx)
with open(os.path.join(OUTPUT_DIR, "INDEX.md"), "w") as f: f.write(idx_content)
with open(os.path.join(SDCARD_DIR, "INDEX.md"), "w") as f: f.write(idx_content)

# Build STATISTICS
print("Building STATISTICS.md...")
st = ["# Statistics", "", "> Generated: " + now, "", "## By Category", ""]
st.append("| Category | Items |")
st.append("|----------|------:|")
for cat_id, label in CAT_LABELS.items():
    cnt = stats["per_category"].get(cat_id, 0)
    st.append("| " + label + " | " + str(cnt) + " |")
st.append("")
st.append("## By Source")
st.append("")
st.append("| Source | Items |")
st.append("|--------|------:|")
for src, cnt in sorted(src_stats.items(), key=lambda x:-x[1]):
    st.append("| " + src + " | " + str(cnt) + " |")
st_content = "\n".join(st)
with open(os.path.join(OUTPUT_DIR, "STATISTICS.md"), "w") as f: f.write(st_content)
with open(os.path.join(SDCARD_DIR, "STATISTICS.md"), "w") as f: f.write(st_content)

# Build README
readme = """# Trading & Financial Markets Encyclopedia

Comprehensive knowledge base covering quantitative finance,
trading strategies, market microstructure, machine learning,
and all related fields.

## Structure

- **INDEX.md** — Master index of all 50 categories
- **STATISTICS.md** — Item counts and source breakdown
- **categories/** — One file per category (50 files)

## 50 Categories in 8 Blocks

A: Mathematical & Quantitative (A01-A05)
B: AI & Data Science (B01-B04)
C: Microstructure & Execution (C01-C07)
D: Portfolio & Risk (D01-D07)
E: Financial Instruments (E01-E05)
F: Analysis & Methods (F01-F11)
G: Fundamental & Macro (G01-G03)
H: Infrastructure & Regulation (H01-H08)

## Access Levels

- OPEN: Full text free
- PART: Abstract free, full text may need subscription
- PAY: Subscription required
- ?: Unknown
"""
with open(os.path.join(OUTPUT_DIR, "README.md"), "w") as f: f.write(readme)
with open(os.path.join(SDCARD_DIR, "README.md"), "w") as f: f.write(readme)

print("\n" + "="*55)
print("  BUILD COMPLETE")
print("="*55)
print("  Total items : " + str(total))
print("  Output      : " + OUTPUT_DIR)
print("  sdcard      : " + SDCARD_DIR)
print()
for cat_id, cnt in sorted(stats["per_category"].items(), key=lambda x:-x[1])[:20]:
    label = CAT_LABELS.get(cat_id, cat_id)[:35]
    bar = "#" * min(cnt//500, 25)
    print("  " + label.ljust(35) + str(cnt).rjust(7) + "  " + bar)
print("  ...")
