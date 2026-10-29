#!/usr/bin/env python3
"""Search the curated resource registry and generated publication catalogue locally.

This command performs local discovery only. It does not crawl the Internet or imply
that the registry covers every relevant website, paper, dataset, or implementation.
"""
from __future__ import annotations

import argparse
import heapq
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

from config import DATA_DIR

ROOT = Path(__file__).resolve().parent
DEFAULT_CATALOG = ROOT / "resources" / "catalog.json"
DEFAULT_ARTICLE_DIR = ROOT / "output" / "categories"
DEFAULT_COLLECTED_RECORDS = Path(DATA_DIR) / "resource_records.jsonl"
URL_PATTERN = re.compile(r"\[LINK\]\((https?://[^)\s]+)\)")


def load_catalog(path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict) or not isinstance(value.get("resources"), list):
        raise ValueError("Catalog must be a JSON object containing a resources array.")
    return value


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    resources = catalog.get("resources")
    if not isinstance(resources, list):
        return ["resources must be a list"]

    seen_ids: set[str] = set()
    seen_urls: dict[str, str] = {}
    for index, item in enumerate(resources):
        prefix = f"resources[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue

        resource_id = item.get("id")
        if not isinstance(resource_id, str) or not resource_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif resource_id in seen_ids:
            errors.append(f"duplicate resource id: {resource_id}")
        else:
            seen_ids.add(resource_id)

        for field in ("name", "description", "type"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")

        url = item.get("url")
        if not isinstance(url, str):
            errors.append(f"{prefix}.url must be a string")
        else:
            try:
                parsed = urlsplit(url)
                if parsed.scheme not in {"https", "http"} or not parsed.hostname:
                    errors.append(f"{prefix}.url must be an absolute HTTP(S) URL")
                if parsed.username is not None or parsed.password is not None:
                    errors.append(f"{prefix}.url must not embed credentials")
                previous = seen_urls.get(url.rstrip("/"))
                if previous:
                    errors.append(f"duplicate URL shared by {previous} and {resource_id}")
                else:
                    seen_urls[url.rstrip("/")] = str(resource_id)
            except ValueError:
                errors.append(f"{prefix}.url is malformed")

        for field in ("lifecycle_stages", "tags"):
            value = item.get(field)
            if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
                errors.append(f"{prefix}.{field} must be a list of non-empty strings")

    known_stages = set(catalog.get("lifecycle_stages", []))
    if not known_stages:
        errors.append("lifecycle_stages must contain supported stage identifiers")
    for index, item in enumerate(resources):
        if not isinstance(item, dict) or not isinstance(item.get("lifecycle_stages"), list):
            continue
        for stage in item["lifecycle_stages"]:
            if stage not in known_stages:
                errors.append(f"resources[{index}] references unknown lifecycle stage: {stage}")
    return errors


def _normalise(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").casefold()))


def _matches(record: dict[str, Any], query: str) -> tuple[int, bool]:
    searchable_fields = (
        "name", "url", "description", "type", "tags", "lifecycle_stages",
        "topics", "categories", "source", "category", "row_text", "metadata", "provider", "search_query", "provider_id",
    )
    haystack = _normalise(" ".join(str(record.get(field, "")) for field in searchable_fields))
    terms = _normalise(query).split()
    if not terms or not all(term in haystack for term in terms):
        return 0, False
    score = sum(haystack.count(term) for term in terms)
    if _normalise(query) and _normalise(query) in haystack:
        score += len(terms) * 3
    return score, True


def _push_top_k(heap: list[tuple[int, int, dict[str, Any]]],
                record: dict[str, Any], query: str, limit: int, serial: int) -> int:
    score, matched = _matches(record, query)
    if not matched:
        return serial
    record["_search_score"] = score
    entry = (score, serial, record)
    serial += 1
    if len(heap) < limit:
        heapq.heappush(heap, entry)
    elif entry[:2] > heap[0][:2]:
        heapq.heapreplace(heap, entry)
    return serial


def search_registry(catalog: dict[str, Any], query: str, limit: int = 25,
                    resource_type: str | None = None,
                    stage: str | None = None) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    heap: list[tuple[int, int, dict[str, Any]]] = []
    serial = 0
    for source in catalog["resources"]:
        if resource_type and source.get("type") != resource_type:
            continue
        if stage and stage not in source.get("lifecycle_stages", []):
            continue
        record = dict(source)
        record["result_kind"] = "curated-resource"
        serial = _push_top_k(heap, record, query, limit, serial)
    return [entry[2] for entry in sorted(heap, key=lambda entry: (-entry[0], entry[1]))]


def search_articles(query: str, category_dir: Path = DEFAULT_ARTICLE_DIR,
                    limit: int = 25) -> list[dict[str, Any]]:
    """Search generated category tables line-by-line with bounded result memory."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not category_dir.is_dir():
        return []

    heap: list[tuple[int, int, dict[str, Any]]] = []
    serial = 0
    for path in sorted(category_dir.glob("*.md")):
        try:
            handle = path.open("r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                if not line.startswith("|") or "[LINK](" not in line:
                    continue
                link_match = URL_PATTERN.search(line)
                if not link_match:
                    continue
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) < 2:
                    continue
                title = cells[0]
                if title.casefold() == "title" or set(title) <= {"-", " "}:
                    continue
                record: dict[str, Any] = {
                    "id": "",
                    "name": title,
                    "title": title,
                    "url": link_match.group(1),
                    "type": "scholarly-record",
                    "category": path.stem,
                    "lifecycle_stages": ["research"],
                    "description": "A publication record from the generated local category index.",
                    "result_kind": "indexed-publication",
                }
                if len(cells) > 1:
                    record["authors"] = cells[1]
                if len(cells) > 2:
                    record["year"] = cells[2]
                # Include all row text for matching without parsing every schema version.
                record["row_text"] = line
                serial = _push_top_k(heap, record, query, limit, serial)
    return [entry[2] for entry in sorted(heap, key=lambda entry: (-entry[0], entry[1]))]



def search_collected_records(query: str, records_path: Path = DEFAULT_COLLECTED_RECORDS,
                             limit: int = 25) -> list[dict[str, Any]]:
    """Search collected resource metadata without loading the whole JSONL corpus into RAM."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not records_path.is_file():
        return []

    heap: list[tuple[int, int, dict[str, Any]]] = []
    serial = 0
    with records_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSONL in {records_path} at line {line_number}")
            if not isinstance(value, dict):
                continue
            record = dict(value)
            record["result_kind"] = "collected-resource"
            record["row_text"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
            if not record.get("name") and record.get("title"):
                record["name"] = record["title"]
            serial = _push_top_k(heap, record, query, limit, serial)
    return [entry[2] for entry in sorted(heap, key=lambda entry: (-entry[0], entry[1]))]


def _markdown_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def export_markdown(catalog: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resources = sorted(catalog["resources"], key=lambda item: (item.get("type", ""), item.get("name", "")))
    lines = [
        "# Curated Resource Index",
        "",
        "> This is a maintained discovery seed, not an exhaustive index of the Internet.",
        "> Verify URLs, access terms, API limits, and current documentation before relying on them.",
        "",
        f"**Resources:** {len(resources)}",
        "",
        "| Resource | Type | Lifecycle stages | Description | Link |",
        "|---|---|---|---|---|",
    ]
    for item in resources:
        stages = ", ".join(item.get("lifecycle_stages", []))
        url = str(item.get("url", ""))
        lines.append(
            "| " + _markdown_escape(item.get("name")) +
            " | " + _markdown_escape(item.get("type")) +
            " | " + _markdown_escape(stages) +
            " | " + _markdown_escape(item.get("description")) +
            " | [Open](" + url.replace(")", "%29") + ") |"
        )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_results(results: list[dict[str, Any]]) -> None:
    if not results:
        print("No matching resources or indexed records were found.")
        return
    for number, item in enumerate(results, start=1):
        label = item.get("name") or item.get("title") or item.get("id") or "Untitled"
        print(f"{number}. {label}")
        print(f"   Type: {item.get('type', 'unknown')}")
        if item.get("provider"):
            print(f"   Provider: {item['provider']}")
        if item.get("review_status"):
            print(f"   Review status: {item['review_status']}")
        if item.get("category"):
            print(f"   Category: {item['category']}")
        if item.get("lifecycle_stages"):
            print("   Lifecycle: " + ", ".join(item["lifecycle_stages"]))
        description = item.get("description", "")
        if description:
            print("   " + str(description).strip())
        print("   " + str(item.get("url", "")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search curated resources, collected metadata, and generated publication records")
    search_parser.add_argument("query", nargs="+", help="Search terms")
    search_parser.add_argument("--limit", type=int, default=25)
    mode = search_parser.add_mutually_exclusive_group()
    mode.add_argument("--registry-only", action="store_true", help="Search only the curated static registry")
    mode.add_argument("--articles-only", action="store_true", help="Search only generated scholarly publication tables")
    mode.add_argument("--collected-only", action="store_true", help="Search only locally collected public resource metadata")
    search_parser.add_argument("--category-dir", type=Path, default=DEFAULT_ARTICLE_DIR)
    search_parser.add_argument("--collected-path", type=Path, default=DEFAULT_COLLECTED_RECORDS)

    list_parser = subparsers.add_parser("list", help="List curated resources with optional filters")
    list_parser.add_argument("--type", dest="resource_type")
    list_parser.add_argument("--stage")
    list_parser.add_argument("--limit", type=int, default=100)

    export_parser = subparsers.add_parser("export", help="Export the curated registry as a Markdown index")
    export_parser.add_argument("--output", type=Path, default=ROOT / "output" / "RESOURCE_INDEX.md")

    validate_parser = subparsers.add_parser("validate", help="Validate registry structure and metadata")
    validate_parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)

    args = parser.parse_args(argv)
    try:
        catalog_path = getattr(args, "catalog", DEFAULT_CATALOG)
        catalog = load_catalog(catalog_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Unable to load registry: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        errors = validate_catalog(catalog)
        if errors:
            for error in errors:
                print("ERROR: " + error)
            return 1
        print(f"Registry valid: {len(catalog['resources'])} resources; {len(catalog['lifecycle_stages'])} lifecycle stages.")
        return 0

    if args.command == "export":
        errors = validate_catalog(catalog)
        if errors:
            for error in errors:
                print("ERROR: " + error)
            return 1
        try:
            export_markdown(catalog, args.output)
        except OSError as exc:
            print(f"Export failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        print(f"Exported {len(catalog['resources'])} resources to {args.output}")
        return 0

    if args.command == "list":
        if args.limit < 1:
            parser.error("--limit must be at least 1")
        if args.resource_type and not any(x.get("type") == args.resource_type for x in catalog["resources"]):
            print(f"Unknown resource type: {args.resource_type}", file=sys.stderr)
            return 2
        known_stages = set(catalog.get("lifecycle_stages", []))
        if args.stage and args.stage not in known_stages:
            print(f"Unknown lifecycle stage: {args.stage}", file=sys.stderr)
            return 2
        results = []
        for item in catalog["resources"]:
            if args.resource_type and item.get("type") != args.resource_type:
                continue
            if args.stage and args.stage not in item.get("lifecycle_stages", []):
                continue
            results.append(dict(item))
        print_results(results[:args.limit])
        print(f"\nDisplayed {min(len(results), args.limit)} of {len(results)} matching registry resources.")
        return 0

    query = " ".join(args.query).strip()
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    results: list[dict[str, Any]] = []
    try:
        if not args.articles_only and not args.collected_only:
            results.extend(search_registry(catalog, query, limit=args.limit))
        if not args.registry_only and not args.collected_only:
            results.extend(search_articles(query, args.category_dir, limit=args.limit))
        if not args.registry_only and not args.articles_only:
            results.extend(search_collected_records(query, args.collected_path, limit=args.limit))
    except (OSError, ValueError) as exc:
        print(f"Local search failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    results.sort(key=lambda item: (-int(item.get("_search_score", 0)), item.get("result_kind", ""), item.get("name", "")))
    deduplicated: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for item in results:
        url = str(item.get("url", ""))
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        deduplicated.append(item)
        if len(deduplicated) >= args.limit:
            break
    print_results(deduplicated)
    print(f"\nDisplayed {len(deduplicated)} results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
