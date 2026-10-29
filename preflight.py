#!/usr/bin/env python3
"""Local readiness checks for the Trading Encyclopedia research index.

Network checks are opt-in. This script never embeds, prints, or transmits API keys
unless the user explicitly configures a provider's normal runtime environment.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

RESULTS = {"pass": 0, "warn": 0, "fail": 0}
CHECKS = []


def check(name: str, status: str, detail: str = "") -> None:
    status = status.upper()
    if status not in {"PASS", "WARN", "FAIL", "SKIP"}:
        raise ValueError("Unsupported check status")
    if status in {"PASS", "WARN", "FAIL"}:
        RESULTS[status.lower()] += 1
    CHECKS.append({"name": name, "status": status, "detail": detail})
    suffix = f" - {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")


def check_import(module_name: str, package_name: str | None = None) -> None:
    package_name = package_name or module_name
    found = importlib.util.find_spec(module_name) is not None
    check(
        f"Python dependency: {package_name}",
        "PASS" if found else "FAIL",
        "" if found else f"Install with: python -m pip install {package_name}",
    )


def check_local_paths() -> None:
    try:
        from config import BASE_DIR, DATA_DIR, OUTPUT_DIR, CATS_DIR
    except Exception as exc:
        check("Load runtime configuration", "FAIL", type(exc).__name__)
        return

    base = Path(BASE_DIR).expanduser()
    ancestor = base
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if ancestor.exists() and os.access(ancestor, os.W_OK | os.X_OK):
        check("Runtime home parent is writable", "PASS", str(ancestor))
    else:
        check("Runtime home parent is writable", "FAIL", "Choose a writable TRADING_ENCYCLOPEDIA_HOME")

    for label, path in (("Data path", DATA_DIR), ("Output path", OUTPUT_DIR), ("Category output path", CATS_DIR)):
        if Path(path).exists():
            check(label, "PASS", "exists")
        else:
            check(label, "WARN", "will be created by a runtime command")

    try:
        from config import API_KEYS
        configured = [name for name, value in API_KEYS.items() if value]
        missing_optional = [name for name, value in API_KEYS.items() if not value]
        check("Provider credentials", "PASS" if configured else "WARN",
              f"{len(configured)} configured; {len(missing_optional)} optional providers have no key")
    except Exception as exc:
        check("Provider credentials", "FAIL", type(exc).__name__)


def check_network() -> None:
    try:
        import requests
    except ImportError:
        check("Optional network checks", "SKIP", "Install requests to enable --network")
        return

    probes = [
        ("Crossref query endpoint", "https://api.crossref.org/works?query.title=trading&rows=1"),
        ("GitHub REST API", "https://api.github.com/rate_limit"),
        ("arXiv API", "https://export.arxiv.org/api/query?search_query=ti%3Atrading&max_results=1"),
    ]
    for name, url in probes:
        try:
            response = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "TradingEncyclopedia-Preflight/3.0"},
            )
            if response.status_code == 200:
                check(name, "PASS", "HTTP 200")
            elif response.status_code == 429:
                check(name, "WARN", "HTTP 429; the endpoint is rate-limiting this client")
            elif response.status_code in (401, 403):
                check(name, "WARN", f"HTTP {response.status_code}; public probe was not authorized")
            else:
                check(name, "FAIL", f"HTTP {response.status_code}")
        except Exception as exc:
            # Deliberately avoid printing exception text, which may contain request URLs.
            check(name, "FAIL", type(exc).__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", action="store_true", help="Run bounded unauthenticated connectivity probes")
    parser.add_argument("--write-report", action="store_true", help="Write JSON report to the configured data directory")
    args = parser.parse_args()

    print("\n" + "=" * 64)
    print("TRADING ENCYCLOPEDIA - PREFLIGHT")
    print("=" * 64)
    check("Python version", "PASS" if sys.version_info >= (3, 10) else "FAIL",
          sys.version.split()[0])
    check_import("requests")
    check_import("langdetect")
    check("Git executable", "PASS" if shutil.which("git") else "WARN",
          shutil.which("git") or "Git is optional for local catalogue generation")
    check_local_paths()

    if args.network:
        check_network()
    else:
        check("Network probes", "SKIP", "Run with --network to opt in")

    print("\n" + "=" * 64)
    print(f"PASS: {RESULTS['pass']} | WARN: {RESULTS['warn']} | FAIL: {RESULTS['fail']}")
    print("=" * 64)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "python": sys.version,
        "results": RESULTS,
        "checks": CHECKS,
        "network_checks_requested": args.network,
    }
    if args.write_report:
        from config import DATA_DIR, ensure_runtime_dirs
        ensure_runtime_dirs()
        report_path = Path(DATA_DIR) / "preflight_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written: {report_path}")

    return 1 if RESULTS["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
