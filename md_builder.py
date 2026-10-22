#!/usr/bin/env python3
"""
Trading Encyclopedia — Markdown Builder
Builds all output files from classified data.
"""
import os, time, shutil
from config import OUTPUT_DIR, CATS_DIR, SDCARD_DIR, CATEGORIES, ACCESS

CAT_LABELS = {
    "A01_Optimization":                   "Optimization & Calibration",
    "A02_Simulation":                     "Simulation & Synthetic Data",
    "A03_Prediction_Forecasting":         "Prediction & Forecasting",
    "A04_Backtesting_Validation":         "Backtesting & Strategy Validation",
    "A05_Probability_Statistics_Econometrics": "Probability, Statistics & Econometrics",
    "B01_Machine_Learning_Finance":       "Machine Learning in Finance",
    "B02_Deep_Learning_Neural_Networks":  "Deep Learning & Neural Networks",
    "B03_Reinforcement_Learning_Control": "Reinforcement Learning & Optimal Control",
    "B04_NLP_Sentiment_Alternative_Data": "NLP, Sentiment & Alternative Data",
    "C01_Market_Microstructure_LOB":      "Market Microstructure & Order Book",
    "C02_Liquidity_OrderFlow_Informed":   "Liquidity, Order Flow & Informed Trading",
    "C03_Market_Impact_Execution":        "Market Impact & Execution",
    "C04_HFT_MarketMaking":               "High-Frequency Trading & Market Making",
    "C05_Algorithmic_Systematic_Trading": "Algorithmic & Systematic Trading",
    "C06_Trade_Lifecycle_Clearing":       "Trade Lifecycle, Clearing & Settlement",
    "C07_Market_Participation_Modes":     "Market Participation Modes & Accounts",
    "D01_Portfolio_Construction_Optimization": "Portfolio Construction & Optimization",
    "D02_Covariance_Factor_Models":       "Covariance Estimation & Factor Models",
    "D03_Risk_Management_Tail_Stress":    "Risk Management, Tail Risk & Stress",
    "D04_Position_Sizing_Kelly_Capital":  "Position Sizing, Kelly & Capital Allocation",
    "D05_Factor_Investing_Alpha_Anomalies": "Factor Investing, Alpha & Anomalies",
    "D06_Performance_Measurement_Attribution": "Performance Measurement & Attribution",
    "D07_Trading_Journal_Development":    "Trading Journal & Trader Development",
    "E01_Derivatives_Options_Volatility": "Derivatives, Options & Volatility",
    "E02_Fixed_Income_Rates_Credit":      "Fixed Income, Rates & Credit",
    "E03_Forex_Commodities_CrossAsset":   "Forex, Commodities & Cross-Asset",
    "E04_Stochastic_Calculus_MathFinance": "Stochastic Calculus & Mathematical Finance",
    "E05_Statistical_Arbitrage_RelativeValue": "Statistical Arbitrage & Relative Value",
    "F01_MarketProfile_AuctionTheory":    "Market Profile & Auction Theory",
    "F02_OrderFlow_Footprint_Tape":       "Order Flow, Footprint & Tape Reading",
    "F03_Wyckoff_VSA":                    "Wyckoff Method & Volume Spread Analysis",
    "F04_SmartMoney_ICT":                 "Smart Money Concepts & ICT",
    "F05_Technical_Analysis_ChartPatterns": "Technical Analysis & Chart Patterns",
    "F06_Harmonic_ElliottWave":           "Harmonic Patterns & Elliott Wave",
    "F07_Specialized_Trading_Schools":    "Specialized Trading Schools",
    "F08_EventDriven_News_Trading":       "Event-Driven & News-Based Trading",
    "F09_Trading_Styles_Timeframes":      "Trading Styles & Timeframes",
    "F10_Chart_Types_Visualization":      "Chart Types & Price Visualization",
    "F11_Market_Scanning_Screening":      "Market Scanning & Signal Discovery",
    "G01_Fundamental_Analysis_Valuation": "Fundamental Analysis & Valuation",
    "G02_Macro_Intermarket_CentralBanking": "Macroeconomics, Intermarket & Central Banking",
    "G03_Behavioral_Finance_Decision":    "Behavioral Finance & Decision Theory",
    "H01_Crypto_DeFi_OnChain":            "Cryptocurrency, DeFi & On-Chain",
    "H02_TradingSystems_Engineering":     "Trading Systems Engineering",
    "H03_Regulation_Compliance_Integrity": "Regulation, Compliance & Market Integrity",
    "H04_PropFirm_Retail_Grid":           "Prop-Firm, Retail Systems & Grid Trading",
    "H05_MarketData_Feeds_Architecture":  "Market Data Levels, Feeds & Architecture",
    "H06_Exchange_Connectivity_API_OMS":  "Exchange Connectivity, APIs & OMS",
    "H07_Network_Infrastructure_DataCenters": "Network Infrastructure & Data Centers",
    "H08_Trading_Platforms_Tools":        "Trading Platforms & Tools",
}

BLOCK_LABELS = {
    "A": "Mathematical & Quantitative",
    "B": "AI & Data Science",
    "C": "Microstructure & Execution",
    "D": "Portfolio & Risk Management",
    "E": "Financial Instruments",
    "F": "Analysis & Trading Methods",
    "G": "Fundamental & Macro",
    "H": "Infrastructure & Regulation",
}

SOURCE_ICONS = {
    "CrossRef": "CR", "OpenAlex": "OA", "SemanticScholar": "S2",
    "Springer": "SP", "Springer-OA": "SO", "arXiv": "AX",
    "CORE": "CO", "EuropePMC": "EP", "DOAJ": "DJ", "RePEC": "RP",
}

ACCESS_ICONS = {
    "OPEN": "OPEN", "PARTIAL": "PARTIAL",
    "GATED": "GATED", "PAYWALL": "PAYWALL", "UNKNOWN": "?",
}

def _safe(text, maxlen=300):
    if not text: return "-"
    return str(text).replace("|","—").replace("\n"," ")[:maxlen].strip() or "-"

def _item_line(item):
    title   = _safe(item.get("title"))
    authors = _safe(item.get("authors"), 150)
    year    = _safe(item.get("year"), 4)
    pages   = _safe(item.get("pages"), 10)
    venue   = _safe(item.get("venue"), 80)
    doc     = _safe(item.get("doc_type"), 30)
    ab      = _safe(item.get("abstract"), 200)
    doi     = _safe(item.get("doi"), 100)
    url     = item.get("url","")
    cited   = str(item.get("cited_by") or 0)
    src     = item.get("source","")
    src_tag = SOURCE_ICONS.get(src, src[:2])
    acc     = item.get("access_level","UNKNOWN")
    acc_tag = ACCESS_ICONS.get(acc, "?")
    kws     = _safe(item.get("keywords"), 150)

    link = "[LINK](" + url + ")" if url and url != "-" else "NO-LINK"

    return (
        "| " + title +
        " | " + authors +
        " | " + year +
        " | " + pages +
        " | " + venue +
        " | " + doc +
        " | " + cited +
        " | " + src_tag +
        " | " + acc_tag +
        " | " + kws +
        " | " + (ab if ab != "-" else "") +
        " | " + link + " |"
    )

TABLE_HEADER = (
    "| Title | Authors | Year | Pages | Venue | Type"
    " | Cited | Src | Access | Keywords | Abstract | Link |\n"
    "|-------|---------|------|-------|-------|------"
    "|-------|-----|--------|---------|----------|------|"
)

def _write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def build_category_file(cat_id, label, items):
    block = cat_id[0]
    block_label = BLOCK_LABELS.get(block, "")
    now = time.strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# " + label)
    lines.append("")
    lines.append("> Block: **" + block + " — " + block_label + "**  ")
    lines.append("> Category ID: `" + cat_id + "`  ")
    lines.append("> Generated: " + now + "  ")
    lines.append("> Items: **" + str(len(items)) + "**")
    lines.append("")
    lines.append("## Access Level Legend")
    lines.append("")
    for k, v in ACCESS.items():
        lines.append("- **" + k.upper() + "**: " + v)
    lines.append("")
    lines.append("---")
    lines.append("")
    if not items:
        lines.append("*No items found for this category.*")
    else:
        lines.append(TABLE_HEADER)
        for item in items:
            lines.append(_item_line(item))
    lines.append("")
    lines.append("---")
    lines.append("*[Back to Index](../INDEX.md)*")
    return "\n".join(lines)

def build_index(categorized, stats):
    now = time.strftime("%Y-%m-%d %H:%M")
    total = stats.get("total", 0)
    unique_records = stats.get("unique_records", sum(stats.get("source_stats", {}).values()))
    category_assignments = stats.get("category_assignments", total)
    unclassified_records = stats.get("unclassified_records", 0)
    src_stats = stats.get("source_stats", {})
    lines = []
    lines.append("# Trading & Financial Markets Encyclopedia")
    lines.append("## Comprehensive Knowledge Base for Quantitative Finance & Trading")
    lines.append("")
    lines.append("> **Generated:** " + now + "  ")
    lines.append("> **Unique Documents:** " + str(unique_records) + "  ")
    lines.append("> **Category Assignments:** " + str(category_assignments) + "  ")
    lines.append("> **Unclassified Documents:** " + str(unclassified_records) + "  ")
    lines.append("> **Categories:** 50  ")
    lines.append("> **Blocks:** 8  ")
    lines.append("> **Sources:** CrossRef · OpenAlex · SemanticScholar · Springer · arXiv · CORE · EuropePMC · DOAJ · RePEC")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Files in This Collection")
    lines.append("")
    lines.append("| File | Description |")
    lines.append("|------|-------------|")
    lines.append("| [INDEX.md](INDEX.md) | This file — master index |")
    lines.append("| [STATISTICS.md](STATISTICS.md) | Detailed statistics |")
    lines.append("| [DOMAINS_GUIDE.md](DOMAINS_GUIDE.md) | Source domains guide |")
    lines.append("| [AUTHORS_INDEX.md](AUTHORS_INDEX.md) | Authors index |")
    lines.append("| [VENUES_INDEX.md](VENUES_INDEX.md) | Journals & venues index |")
    lines.append("| [README.md](README.md) | How to use this collection |")
    lines.append("")
    lines.append("---")
    lines.append("")
    current_block = ""
    for cat_id, label in CAT_LABELS.items():
        block = cat_id[0]
        if block != current_block:
            current_block = block
            lines.append("")
            lines.append("## Block " + block + " — " + BLOCK_LABELS.get(block,""))
            lines.append("")
            lines.append("| Category | Items | File |")
            lines.append("|----------|------:|------|")
        count = len(categorized.get(cat_id, []))
        fname = "categories/" + cat_id + ".md"
        lines.append("| " + label + " | " + str(count) + " | [open](" + fname + ") |")
    lines.append("")
    return "\n".join(lines)

def build_statistics(categorized, stats):
    now = time.strftime("%Y-%m-%d %H:%M")
    src_stats = stats.get("source_stats", {})
    total = stats.get("total", 0)
    unique_records = stats.get("unique_records", sum(stats.get("source_stats", {}).values()))
    category_assignments = stats.get("category_assignments", total)
    unclassified_records = stats.get("unclassified_records", 0)
    lines = []
    lines.append("# Statistics")
    lines.append("")
    lines.append("> Generated: " + now + " UTC")
    lines.append("")
    lines.append("## Collection Counts")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|------:|")
    lines.append("| Unique documents | " + str(unique_records) + " |")
    lines.append("| Category assignments | " + str(category_assignments) + " |")
    lines.append("| Unclassified documents | " + str(unclassified_records) + " |")
    lines.append("")
    lines.append("A document may be assigned to multiple categories. Unique-document counts and category assignments are different measures.")
    lines.append("")
    lines.append("## By Source API")
    lines.append("")
    lines.append("| Source | Items |")
    lines.append("|--------|------:|")
    for src, cnt in sorted(src_stats.items(), key=lambda x: -x[1]):
        lines.append("| " + src + " | " + str(cnt) + " |")
    lines.append("| **UNIQUE SOURCE RECORDS** | **" + str(unique_records) + "** |")
    lines.append("")
    lines.append("## By Category")
    lines.append("")
    lines.append("| Category | Items |")
    lines.append("|----------|------:|")
    for cat_id, label in CAT_LABELS.items():
        cnt = len(categorized.get(cat_id,[]))
        lines.append("| " + label + " | " + str(cnt) + " |")
    lines.append("")
    lines.append("## Access Level Distribution (Across Category Assignments)")
    lines.append("")
    acc_counts = {}
    for items in categorized.values():
        for item in items:
            a = item.get("access_level","UNKNOWN")
            acc_counts[a] = acc_counts.get(a,0) + 1
    lines.append("| Access Level | Items |")
    lines.append("|--------------|------:|")
    for k, v in sorted(acc_counts.items(), key=lambda x:-x[1]):
        lines.append("| " + k + " | " + str(v) + " |")
    lines.append("")
    lines.append("## Top 50 Most Cited Items")
    lines.append("")
    all_items = []
    for items in categorized.values():
        all_items.extend(items)
    from utils import deduplicate
    all_items = deduplicate(all_items)
    top50 = sorted(all_items, key=lambda x: int(x.get("cited_by") or 0), reverse=True)[:50]
    lines.append("| # | Title | Citations | Year | Link |")
    lines.append("|---|-------|----------:|------|------|")
    for i, item in enumerate(top50, 1):
        t = _safe(item.get("title"), 80)
        c = str(item.get("cited_by") or 0)
        y = str(item.get("year") or "")
        u = item.get("url","")
        lnk = "[link](" + u + ")" if u and u!="-" else "-"
        lines.append("| " + str(i) + " | " + t + " | " + c + " | " + y + " | " + lnk + " |")
    lines.append("")
    return "\n".join(lines)

def build_authors_index(categorized):
    from utils import deduplicate
    all_items = deduplicate([i for items in categorized.values() for i in items])
    author_map = {}
    for item in all_items:
        au = item.get("authors","")
        if not au or au == "-": continue
        for name in au.replace(" et al.","").split(";"):
            name = name.strip()
            if len(name) > 2:
                if name not in author_map: author_map[name] = []
                author_map[name].append(item)
    lines = ["# Authors Index", "", str(len(author_map)) + " authors found", ""]
    for name in sorted(author_map.keys()):
        items = author_map[name]
        lines.append("## " + name)
        lines.append("")
        lines.append(str(len(items)) + " item(s)")
        lines.append("")
        for item in items[:5]:
            t = _safe(item.get("title"), 80)
            u = item.get("url","")
            y = str(item.get("year") or "")
            lnk = "[" + t + "](" + u + ")" if u and u!="-" else t
            lines.append("- " + lnk + " (" + y + ")")
        if len(items) > 5:
            lines.append("- ... and " + str(len(items)-5) + " more")
        lines.append("")
    return "\n".join(lines)

def build_venues_index(categorized):
    from utils import deduplicate
    all_items = deduplicate([i for items in categorized.values() for i in items])
    venue_map = {}
    for item in all_items:
        v = str(item.get("venue","")).strip()
        if v and v != "-" and len(v) > 2:
            if v not in venue_map: venue_map[v] = 0
            venue_map[v] += 1
    lines = ["# Venues & Journals Index", "", str(len(venue_map)) + " venues found", ""]
    lines.append("| Venue | Items |")
    lines.append("|-------|------:|")
    for v, cnt in sorted(venue_map.items(), key=lambda x:-x[1])[:200]:
        lines.append("| " + v[:100] + " | " + str(cnt) + " |")
    return "\n".join(lines)

def build_domains_guide():
    lines = ["# Source Domains Guide", ""]
    lines.append("This encyclopedia uses 9 API sources to gather data.")
    lines.append("Below is a guide to access levels and reliability.")
    lines.append("")
    lines.append("## Access Level Explanation")
    lines.append("")
    for k, v in ACCESS.items():
        lines.append("- **" + k.upper() + "**: " + v)
    lines.append("")
    lines.append("## API Sources Used")
    lines.append("")
    sources = [
        ("CrossRef", "crossref.org", "PARTIAL", "150M+ records, metadata always free, DOI links permanent"),
        ("OpenAlex", "openalex.org", "PARTIAL", "250M+ records, open metadata, many OA full texts"),
        ("SemanticScholar", "semanticscholar.org", "PARTIAL", "200M+ papers, AI-powered, citation data"),
        ("Springer Nature", "link.springer.com", "PARTIAL", "Meta API: metadata free; OA API: open access only"),
        ("arXiv", "arxiv.org", "OPEN", "2M+ preprints, 100% free, permanent links"),
        ("CORE", "core.ac.uk", "OPEN", "300M+ OA records, full text often available"),
        ("EuropePMC", "europepmc.org", "OPEN", "Large OA collection, finance and economics included"),
        ("DOAJ", "doaj.org", "OPEN", "Directory of open access journals, 100% free"),
        ("RePEC", "repec.org", "OPEN", "Economics & finance working papers, mostly free"),
    ]
    lines.append("| Source | Domain | Access | Notes |")
    lines.append("|--------|--------|--------|-------|")
    for s in sources:
        lines.append("| " + s[0] + " | " + s[1] + " | " + s[2] + " | " + s[3] + " |")
    lines.append("")
    lines.append("## Tips for Paywalled Content")
    lines.append("")
    lines.append("- Try **Unpaywall** browser extension — finds legal free versions")
    lines.append("- Check **arXiv** for preprint versions of paywalled papers")
    lines.append("- Use **Google Scholar** to find author-hosted PDFs")
    lines.append("- Email the corresponding author directly")
    lines.append("")
    return "\n".join(lines)

def build_readme():
    lines = [
        "# Trading & Financial Markets Encyclopedia",
        "",
        "A comprehensive, auto-generated reference collection covering",
        "quantitative finance, trading strategies, market microstructure,",
        "machine learning in finance, and all related fields.",
        "",
        "## How to Use",
        "",
        "1. Start at [INDEX.md](INDEX.md) to browse all 50 categories",
        "2. Each category file contains a searchable table of items",
        "3. Check [STATISTICS.md](STATISTICS.md) for top-cited papers",
        "4. Check [DOMAINS_GUIDE.md](DOMAINS_GUIDE.md) for access info",
        "",
        "## Column Guide",
        "",
        "| Column | Description |",
        "|--------|-------------|",
        "| Title | Paper/document title |",
        "| Authors | Author names |",
        "| Year | Publication year |",
        "| Pages | Number of pages |",
        "| Venue | Journal or conference |",
        "| Type | Document type |",
        "| Cited | Citation count |",
        "| Src | Source API (CR=CrossRef, OA=OpenAlex, S2=SemanticScholar, etc.) |",
        "| Access | OPEN=free, PARTIAL=abstract free, PAYWALL=subscription needed |",
        "| Keywords | Author-provided keywords |",
        "| Abstract | Short excerpt |",
        "| Link | Direct URL (click to open) |",
        "",
        "## 50 Categories in 8 Blocks",
        "",
    ]
    for block, label in BLOCK_LABELS.items():
        lines.append("**Block " + block + " — " + label + "**")
        for cat_id, cat_label in CAT_LABELS.items():
            if cat_id.startswith(block):
                lines.append("- " + cat_label)
        lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.append("CrossRef · OpenAlex · Semantic Scholar · Springer · arXiv · CORE · EuropePMC · DOAJ · RePEC")
    lines.append("")
    return "\n".join(lines)

def build_all(categorized, stats):
    # Category files
    for cat_id, label in CAT_LABELS.items():
        items = categorized.get(cat_id, [])
        content = build_category_file(cat_id, label, items)
        path = os.path.join(CATS_DIR, cat_id + ".md")
        _write(path, content)
    print("  Category files: " + str(len(CAT_LABELS)) + " written")

    # Index files
    _write(os.path.join(OUTPUT_DIR, "INDEX.md"), build_index(categorized, stats))
    _write(os.path.join(OUTPUT_DIR, "STATISTICS.md"), build_statistics(categorized, stats))
    _write(os.path.join(OUTPUT_DIR, "AUTHORS_INDEX.md"), build_authors_index(categorized))
    _write(os.path.join(OUTPUT_DIR, "VENUES_INDEX.md"), build_venues_index(categorized))
    _write(os.path.join(OUTPUT_DIR, "DOMAINS_GUIDE.md"), build_domains_guide())
    _write(os.path.join(OUTPUT_DIR, "README.md"), build_readme())
    print("  Index files: 6 written")

    # Copy to sdcard
    try:
        import shutil
        for fname in os.listdir(OUTPUT_DIR):
            src = os.path.join(OUTPUT_DIR, fname)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(SDCARD_DIR, fname))
        cats_sd = os.path.join(SDCARD_DIR, "categories")
        os.makedirs(cats_sd, exist_ok=True)
        for fname in os.listdir(CATS_DIR):
            shutil.copy(os.path.join(CATS_DIR, fname), os.path.join(cats_sd, fname))
        print("  Copied to: " + SDCARD_DIR)
    except Exception as e:
        print("  sdcard copy skipped: " + str(e)[:50])

    print("  Output: " + OUTPUT_DIR)
