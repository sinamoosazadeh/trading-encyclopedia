#!/usr/bin/env python3
"""Bounded, opt-in collector for public research and engineering resource metadata.

The default command only validates or displays the collection plan. The network is
used only by the explicit 'collect' command. This tool stores links and metadata;
it does not download full paper, model, dataset, or repository contents.
"""
from __future__ import annotations

import argparse
import email.utils
import html
import json
import os
import re
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests

from config import DATA_DIR, MAX_RETRIES, TIMEOUT, ensure_runtime_dirs

ROOT = Path(__file__).resolve().parent
DEFAULT_QUERY_PLAN = ROOT / "resources" / "discovery_queries.json"
PROVIDERS = ("github", "huggingface_models", "huggingface_datasets", "zenodo")
USER_AGENT = "TradingEncyclopediaResourceCollector/1.0"


class ProviderError(RuntimeError):
    """A provider request failed or returned an unusable response."""


class ProviderQuotaError(ProviderError):
    """The provider signaled an exhausted quota or a persistent rate limit."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_plan(path: Path = DEFAULT_QUERY_PLAN) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)
    if not isinstance(plan, dict) or not isinstance(plan.get("queries"), list):
        raise ValueError("Discovery query plan must contain a queries array.")
    return plan


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = plan.get("execution_policy")
    if not isinstance(policy, dict):
        errors.append("execution_policy must be an object")
        policy = {}
    for key, minimum, maximum in (
        ("max_queries_per_invocation", 1, 50),
        ("default_results_per_query", 1, 20),
        ("maximum_results_per_query", 1, 20),
    ):
        value = policy.get(key)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            errors.append(f"execution_policy.{key} must be an integer from {minimum} to {maximum}")

    known_stages = set(plan.get("lifecycle_stages", []))
    # lifecycle stages may be defined in the central registry rather than duplicated
    # in this query plan. Import lazily to avoid coupling the JSON schema to side effects.
    if not known_stages:
        try:
            catalog_path = ROOT / "resources" / "catalog.json"
            with catalog_path.open("r", encoding="utf-8") as handle:
                known_stages = set(json.load(handle).get("lifecycle_stages", []))
        except (OSError, json.JSONDecodeError, AttributeError):
            errors.append("Cannot load lifecycle stages from resources/catalog.json")

    seen_ids: set[str] = set()
    valid_providers = set(PROVIDERS)
    for index, query in enumerate(plan.get("queries", [])):
        prefix = f"queries[{index}]"
        if not isinstance(query, dict):
            errors.append(f"{prefix} must be an object")
            continue
        query_id = query.get("id")
        if not isinstance(query_id, str) or not query_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif query_id in seen_ids:
            errors.append(f"duplicate query id: {query_id}")
        else:
            seen_ids.add(query_id)
        provider = query.get("provider")
        if provider not in valid_providers:
            errors.append(f"{prefix}.provider is unsupported: {provider}")
        for field in ("query", "resource_type"):
            if not isinstance(query.get(field), str) or not query[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ("tags", "lifecycle_stages"):
            value = query.get(field)
            if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
                errors.append(f"{prefix}.{field} must be a list of non-empty strings")
            elif field == "lifecycle_stages":
                for stage in value:
                    if stage not in known_stages:
                        errors.append(f"{prefix} uses unknown lifecycle stage: {stage}")
    return errors


def select_queries(plan: dict[str, Any], provider: str, max_queries: int,
                   query_ids: list[str] | None = None) -> list[dict[str, Any]]:
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    policy_cap = int(plan["execution_policy"]["max_queries_per_invocation"])
    if not 1 <= max_queries <= min(50, policy_cap):
        raise ValueError(f"max_queries must be between 1 and {min(50, policy_cap)}")
    matching = [q for q in plan["queries"] if q["provider"] == provider]
    if query_ids:
        requested = set(query_ids)
        matching = [q for q in matching if q["id"] in requested]
        missing = requested - {q["id"] for q in matching}
        if missing:
            raise ValueError("Unknown query IDs for provider: " + ", ".join(sorted(missing)))
    return matching[:max_queries]


def _valid_http_url(value: Any) -> bool:
    if not isinstance(value, str) or len(value.strip()) < 10:
        return False
    try:
        parsed = urlsplit(value.strip())
        # Touch .port to ensure malformed ports raise ValueError.
        _ = parsed.port
        return (
            parsed.scheme.lower() in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
        )
    except (TypeError, ValueError):
        return False


def _text(value: Any, maximum: int = 5000) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(item) for item in value)
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:maximum]


def _retry_after_seconds(response: requests.Response, attempt: int) -> float:
    raw = response.headers.get("Retry-After", "").strip()
    if raw:
        try:
            return min(max(float(raw), 1.0), 60.0)
        except ValueError:
            try:
                parsed = email.utils.parsedate_to_datetime(raw)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                seconds = (parsed - datetime.now(timezone.utc)).total_seconds()
                return min(max(seconds, 1.0), 60.0)
            except (TypeError, ValueError, OverflowError):
                pass
    return min(5.0 * (2 ** attempt), 60.0)


def fetch_json(provider: str, url: str, params: dict[str, Any],
               max_retries: int = 3, timeout: float = 30) -> Any:
    """GET a public metadata endpoint with bounded retries and no secret-bearing URLs."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if provider == "github":
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = "Bearer " + token

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            if attempt >= max_retries:
                raise ProviderError(f"{provider}: network failure after {attempt + 1} attempt(s): {type(exc).__name__}") from None
            time.sleep(min(2.0 * (2 ** attempt), 30.0))
            continue

        if response.status_code == 429:
            if attempt >= max_retries:
                raise ProviderQuotaError(f"{provider}: HTTP 429; retry budget exhausted")
            wait_seconds = _retry_after_seconds(response, attempt)
            time.sleep(wait_seconds)
            continue

        if response.status_code in (403, 401):
            body = response.text[:500].casefold()
            remaining = response.headers.get("X-RateLimit-Remaining")
            if response.status_code == 429 or remaining == "0" or "rate limit" in body or "quota" in body:
                raise ProviderQuotaError(f"{provider}: HTTP {response.status_code}; access or rate-limit budget exhausted")
            raise ProviderError(f"{provider}: HTTP {response.status_code}; request is not authorized or allowed")

        if response.status_code in (500, 502, 503, 504):
            if attempt >= max_retries:
                raise ProviderError(f"{provider}: HTTP {response.status_code}; retry budget exhausted")
            time.sleep(min(2.0 * (2 ** attempt), 30.0))
            continue

        if response.status_code != 200:
            raise ProviderError(f"{provider}: HTTP {response.status_code}")

        try:
            return response.json()
        except (ValueError, json.JSONDecodeError):
            raise ProviderError(f"{provider}: HTTP 200 response was not valid JSON") from None

    raise ProviderError(f"{provider}: retry loop ended unexpectedly")


def _base_record(query: dict[str, Any], provider_id: str, name: str, url: str,
                 description: str, resource_type: str,
                 extra: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if not _valid_http_url(url) or not name.strip():
        return None
    metadata = extra or {}
    return {
        "id": f"{query['provider']}:{provider_id}",
        "name": _text(name, 500),
        "title": _text(name, 500),
        "url": url.strip(),
        "description": _text(description, 4000) or f"Discovered through {query['provider']}; review the original source before use.",
        "type": resource_type or query.get("resource_type", "external-resource"),
        "provider": query["provider"],
        "provider_id": str(provider_id),
        "source_api": query["provider"],
        "search_query_id": query["id"],
        "search_query": query["query"],
        "lifecycle_stages": list(query.get("lifecycle_stages", [])),
        "tags": list(query.get("tags", [])),
        "observed_at_utc": utc_now(),
        "review_status": "unreviewed",
        "metadata": metadata,
    }


def normalize_github(item: dict[str, Any], query: dict[str, Any]) -> dict[str, Any] | None:
    full_name = str(item.get("full_name") or "").strip()
    return _base_record(
        query,
        full_name,
        full_name,
        str(item.get("html_url") or ""),
        str(item.get("description") or ""),
        query["resource_type"],
        {
            "stars": item.get("stargazers_count"),
            "forks": item.get("forks_count"),
            "language": item.get("language"),
            "license_spdx_id": (item.get("license") or {}).get("spdx_id") if isinstance(item.get("license"), dict) else None,
            "archived": item.get("archived"),
            "updated_at": item.get("updated_at"),
            "default_branch": item.get("default_branch"),
        },
    )


def normalize_huggingface(item: dict[str, Any], query: dict[str, Any]) -> dict[str, Any] | None:
    repo_id = str(item.get("id") or "").strip()
    is_dataset = query["provider"] == "huggingface_datasets"
    kind = "dataset" if is_dataset else query["resource_type"]
    url = f"https://huggingface.co/datasets/{repo_id}" if is_dataset else f"https://huggingface.co/{repo_id}"
    tags = item.get("tags") if isinstance(item.get("tags"), list) else []
    pipeline = item.get("pipeline_tag")
    description_bits = [f"Hugging Face {'dataset' if is_dataset else 'model'} repository."]
    if pipeline:
        description_bits.append("Pipeline: " + str(pipeline) + ".")
    if tags:
        description_bits.append("Tags: " + ", ".join(str(tag) for tag in tags[:12]) + ".")
    return _base_record(
        query, repo_id, repo_id, url, " ".join(description_bits), kind,
        {
            "downloads": item.get("downloads"),
            "likes": item.get("likes"),
            "last_modified": item.get("lastModified") or item.get("last_modified"),
            "author": item.get("author"),
            "pipeline_tag": pipeline,
            "library_name": item.get("library_name"),
            "tags": tags[:100],
            "gated": item.get("gated"),
            "private": item.get("private"),
        },
    )


def normalize_zenodo(item: dict[str, Any], query: dict[str, Any]) -> dict[str, Any] | None:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    record_id = str(item.get("id") or metadata.get("doi") or "").strip()
    links = item.get("links") if isinstance(item.get("links"), dict) else {}
    url = str(links.get("html") or links.get("self_html") or "")
    if not url and record_id:
        url = "https://zenodo.org/records/" + record_id
    resource = metadata.get("resource_type") if isinstance(metadata.get("resource_type"), dict) else {}
    authors = metadata.get("creators") if isinstance(metadata.get("creators"), list) else []
    author_names = [entry.get("name", "") for entry in authors[:10] if isinstance(entry, dict) and entry.get("name")]
    keywords = metadata.get("keywords") if isinstance(metadata.get("keywords"), list) else []
    title = _text(metadata.get("title") or item.get("title") or "", 500)
    return _base_record(
        query, record_id, title, url,
        str(metadata.get("description") or ""),
        str(resource.get("title") or query["resource_type"]),
        {
            "doi": metadata.get("doi"),
            "publication_date": metadata.get("publication_date"),
            "creators": author_names,
            "keywords": [str(value) for value in keywords[:50]],
            "license": metadata.get("license"),
            "access_right": metadata.get("access_right"),
            "version": metadata.get("version"),
            "publisher": metadata.get("publisher"),
            "resource_type": resource,
            "record_modified": item.get("updated"),
        },
    )


def provider_search(provider: str, query: dict[str, Any], limit: int,
                   timeout: float = 30) -> list[dict[str, Any]]:
    phrase = query["query"]
    if provider == "github":
        data = fetch_json(provider, "https://api.github.com/search/repositories", {
            "q": phrase, "sort": "stars", "order": "desc", "per_page": limit,
        }, timeout=timeout)
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise ProviderError("github: response did not contain an items array")
        normalized = [normalize_github(item, query) for item in data["items"] if isinstance(item, dict)]
    elif provider in ("huggingface_models", "huggingface_datasets"):
        endpoint = "models" if provider == "huggingface_models" else "datasets"
        data = fetch_json(provider, f"https://huggingface.co/api/{endpoint}", {
            "search": phrase, "limit": limit, "sort": "downloads", "direction": -1,
        }, timeout=timeout)
        if not isinstance(data, list):
            raise ProviderError(f"{provider}: response was not a JSON array")
        normalized = [normalize_huggingface(item, query) for item in data if isinstance(item, dict)]
    elif provider == "zenodo":
        data = fetch_json(provider, "https://zenodo.org/api/records", {
            "q": phrase, "size": limit,
        }, timeout=timeout)
        if not isinstance(data, dict) or not isinstance(data.get("hits"), dict) or not isinstance(data["hits"].get("hits"), list):
            raise ProviderError("zenodo: response did not contain hits.hits")
        normalized = [normalize_zenodo(item, query) for item in data["hits"]["hits"] if isinstance(item, dict)]
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    return [item for item in normalized if item is not None]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
            if not isinstance(value, dict) or not isinstance(value.get("id"), str):
                raise ValueError(f"Invalid record at {path}:{line_number}: expected object with string id")
            items.append(value)
    return items


def write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def merge_records(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    merged = {item["id"]: dict(item) for item in existing}
    new_count = 0
    for record in incoming:
        record_id = record["id"]
        if record_id not in merged:
            merged[record_id] = record
            new_count += 1
            continue
        previous = merged[record_id]
        # Preserve historical query provenance before replacing mutable display fields.
        previous_metadata = previous.get("metadata") if isinstance(previous.get("metadata"), dict) else {}
        incoming_metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        old_query_id = previous.get("search_query_id")
        old_queries = previous.get("query_provenance", [])
        if not isinstance(old_queries, list):
            old_queries = []
        previous.update(record)
        previous["metadata"] = {**previous_metadata, **incoming_metadata}
        queries = list(dict.fromkeys(
            [item for item in old_queries if isinstance(item, str) and item]
            + [item for item in (old_query_id, record.get("search_query_id")) if isinstance(item, str) and item]
        ))
        previous["query_provenance"] = queries
    return sorted(merged.values(), key=lambda item: item["id"]), new_count


def run_collection(provider: str, queries: list[dict[str, Any]], result_limit: int,
                   delay: float, timeout: float, data_dir: Path) -> int:
    data_dir.mkdir(parents=True, exist_ok=True)
    records_path = data_dir / "resource_records.jsonl"
    runs_path = data_dir / "resource_collection_runs.jsonl"
    existing = read_jsonl(records_path)
    old_runs = read_jsonl(runs_path)
    run_id = uuid.uuid4().hex
    incoming: list[dict[str, Any]] = []
    run_events: list[dict[str, Any]] = []
    provider_paused = False

    for index, query in enumerate(queries):
        event = {
            "run_id": run_id,
            "provider": provider,
            "query_id": query["id"],
            "query": query["query"],
            "started_at_utc": utc_now(),
            "status": "started",
            "result_count": 0,
            "error": "",
        }
        try:
            results = provider_search(provider, query, result_limit, timeout=timeout)
            incoming.extend(results)
            event["status"] = "success" if results else "empty"
            event["result_count"] = len(results)
        except ProviderQuotaError as exc:
            event["status"] = "quota_exhausted"
            event["error"] = str(exc)
            provider_paused = True
        except (ProviderError, ValueError) as exc:
            event["status"] = "failed"
            event["error"] = str(exc)
        event["finished_at_utc"] = utc_now()
        run_events.append(event)
        print(f"[{event['status'].upper()}] {provider} / {query['id']}: {event['result_count']} record(s)")
        if provider_paused:
            print("Provider collection stopped to respect the quota/access signal.", file=sys.stderr)
            break
        if index < len(queries) - 1 and delay > 0:
            time.sleep(delay)

    merged, new_count = merge_records(existing, incoming)
    write_jsonl_atomic(records_path, merged)
    write_jsonl_atomic(runs_path, (old_runs + run_events)[-10000:])
    successes = sum(event["status"] == "success" for event in run_events)
    empties = sum(event["status"] == "empty" for event in run_events)
    failures = sum(event["status"] in {"failed", "quota_exhausted"} for event in run_events)
    print()
    print(f"Queries attempted: {len(run_events)}")
    print(f"Successful with results: {successes}")
    print(f"Successful but empty: {empties}")
    print(f"Failed or stopped: {failures}")
    print(f"New resource IDs: {new_count}")
    print(f"Stored resource records: {len(merged)}")
    print(f"Records: {records_path}")
    print(f"Run log: {runs_path}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-queries", help="Validate the offline discovery query plan")
    validate_parser.add_argument("--plan", type=Path, default=DEFAULT_QUERY_PLAN)

    plan_parser = subparsers.add_parser("plan", help="Preview selected queries without networking")
    plan_parser.add_argument("--provider", required=True, choices=PROVIDERS)
    plan_parser.add_argument("--max-queries", type=int, default=3)
    plan_parser.add_argument("--query-id", action="append", default=[])
    plan_parser.add_argument("--plan", type=Path, default=DEFAULT_QUERY_PLAN)

    collect_parser = subparsers.add_parser("collect", help="Explicitly query a public metadata API with strict limits")
    collect_parser.add_argument("--provider", required=True, choices=PROVIDERS)
    collect_parser.add_argument("--max-queries", type=int, default=3)
    collect_parser.add_argument("--results-per-query", type=int, default=10)
    collect_parser.add_argument("--delay", type=float, default=None)
    collect_parser.add_argument("--timeout", type=float, default=30.0)
    collect_parser.add_argument("--query-id", action="append", default=[])
    collect_parser.add_argument("--plan", type=Path, default=DEFAULT_QUERY_PLAN)
    collect_parser.add_argument("--data-dir", type=Path, default=Path(DATA_DIR))

    args = parser.parse_args(argv)
    try:
        plan = load_plan(args.plan)
        errors = validate_plan(plan)
        if errors:
            for error in errors:
                print("ERROR: " + error)
            return 1
        if args.command == "validate-queries":
            print(f"Query plan valid: {len(plan['queries'])} queries across {len(PROVIDERS)} providers.")
            return 0
        queries = select_queries(plan, args.provider, args.max_queries, args.query_id or None)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Cannot prepare discovery plan: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.command == "plan":
        print(f"Provider: {args.provider}")
        print("Network requests: 0")
        print(f"Planned queries: {len(queries)}")
        for row in queries:
            print(f"- {row['id']}: {row['query']} ({row['resource_type']}; stages: {', '.join(row['lifecycle_stages'])})")
        return 0

    policy = plan["execution_policy"]
    if not 1 <= args.results_per_query <= int(policy["maximum_results_per_query"]):
        parser.error(f"--results-per-query must be between 1 and {policy['maximum_results_per_query']}")
    if not 1 <= args.max_queries <= min(50, int(policy["max_queries_per_invocation"])):
        parser.error("--max-queries exceeds the enforced invocation limit")
    if not 1 <= args.timeout <= 120:
        parser.error("--timeout must be between 1 and 120 seconds")
    delay = float(policy.get("default_inter_query_delay_seconds", 6)) if args.delay is None else args.delay
    if not 0 <= delay <= 120:
        parser.error("--delay must be between 0 and 120 seconds")

    # Network access is reached only from this explicit subcommand.
    try:
        ensure_runtime_dirs()
        return run_collection(
            args.provider, queries, args.results_per_query,
            delay=delay, timeout=args.timeout, data_dir=args.data_dir,
        )
    except (OSError, ValueError) as exc:
        print(f"Collection could not complete: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
