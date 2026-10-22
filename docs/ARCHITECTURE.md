# Architecture

## 1. Current Pipeline

The current implementation contains several major modules:

1. `config.py` defines provider settings, a keyword/query taxonomy, paths, and execution limits.
2. The `api_*.py` modules query scholarly metadata providers and normalize results into a common record shape.
3. `master.py` schedules provider queries and stores query results in JSON cache files.
4. `utils.py` provides normalization, URL validation, deduplication, access labels, logging, and retries.
5. `classifier.py` assigns one or more categories based on patterns and contextual evidence.
6. `merge.py` or `merge_light.py` consolidates cached records, classifies them, computes metrics, and invokes the renderer.
7. `md_builder.py` creates category pages, indexes, statistics, and optional export copies.
8. `resource_catalog.py` searches the curated registry and, when available, the generated Markdown publication tables.

The generated Markdown remains useful for browsing, but it should be treated as a materialized view of source data, not as the primary source of truth.

## 2. Curated Resource Registry

`resources/catalog.json` is a separately maintained registry of useful resource entry points. It includes scholarly discovery APIs, exchange and market-data documentation, trading engines, data and compute libraries, testing frameworks, operational tooling, standards, and security guidance.

Each entry has a stable local identifier, a source URL, a resource type, lifecycle-stage tags, search tags, a description, and a review status. The registry is not a list of every page at each provider; entries point to useful starting locations. URL health checking and review dates are not yet automated.

The local CLI provides registry search and can search generated category tables without network requests. Its result ordering is a lightweight textual relevance heuristic, not a trained ranking model or a calibrated probability.

## 3. Configuration and Runtime Paths

Provider credentials are loaded from environment variables or a local ignored `.env` file. Paths and request settings are configurable. Importing `config.py` no longer creates data directories; runtime commands call `ensure_runtime_dirs()` explicitly.

The default runtime home remains `~/encyclopedia` for compatibility with the previous Termux workflow. When the checkout itself should contain generated `output/` files, set `TRADING_ENCYCLOPEDIA_HOME` to the repository path before executing collection and merge commands.

## 4. Target Architecture

The desired evolution is toward a single auditable pipeline with these boundaries:

- **Provider adapters:** one module per source with a common result contract, documented pagination, bounded retries, source-specific limits, and explicit authentication.
- **Raw observations:** retain provider IDs, query text, request time, HTTP status, adapter version, and error state.
- **Normalization:** normalize stable identifiers and metadata without discarding source-specific values.
- **Entity resolution:** merge only high-confidence duplicate identities and preserve a trace to every contributing source record.
- **Classification:** assign taxonomy labels from evidence in a document's title, abstract, tags, or other permitted metadata. Never infer relevance solely from the query bucket used to discover the record.
- **Canonical store:** store documents, source observations, query runs, classification evidence, access observations, and errors with explicit schemas.
- **Quality validation:** measure duplicate rates, source failures, relevance precision/recall, missingness, link validity, and reproducibility.
- **Exports:** generate Markdown and machine-readable views from the canonical data through one renderer.
- **Search interface:** unify curated resource links and indexed records while retaining type, provenance, freshness, and access labels.

SQLite is a suitable initial canonical store for single-device and mobile workflows. It is portable and does not require a database server. A remote service should be considered only if measured scale or collaboration needs justify the operational cost.

## 5. Current Architectural Limitations

- The academic provider adapters do not cover every class of useful web resource.
- The curated registry contains a useful starter set, not exhaustive source coverage.
- Query state is represented in JSON caches and does not yet provide a complete state machine distinguishing every success, empty result, failure, retry exhaustion, and interrupted run.
- Existing static category files are historical generated output. They have not been rebuilt automatically by a code change and must be regenerated and reviewed before being treated as corrected.
- Search ranks local text matches. It does not query the live Internet or execute a semantic search model.
- Scheduled source health checks, registry link monitoring, release snapshots, and calibrated category metrics remain future work.
