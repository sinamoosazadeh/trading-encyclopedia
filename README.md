# Trading Encyclopedia

A searchable discovery layer for the scientific, technical, and operational resources needed to design, build, validate, deploy, and operate advanced trading systems.

The goal is to reduce repeated discovery work. Instead of starting from scattered search engines, repositories, publisher APIs, and documentation portals every time, users and AI-assisted workflows can begin with one structured catalogue of resource links and a local index of collected publication metadata. Each result points back to its source.

## Project Goals

- Centralize discovery of research papers, preprints, official API documentation, standards, open-source frameworks, datasets, software documentation, testing tools, and operations guidance.
- Organize resources around the full system lifecycle: problem definition, architecture, data, research, signal design, model development, backtesting, validation, optimization, risk, execution, deployment, monitoring, and governance.
- Preserve source links so users can inspect the original publisher, repository, provider, or standards body.
- Reduce repetitive search and parsing work for engineers, researchers, and AI agents.
- Make collection, normalization, classification, deduplication, and export auditable and reproducible.
- Keep data freshness, source coverage, uncertainty, and access restrictions visible.

## Important Scope Boundary

This project does **not** claim to index every page on the Internet, and a local result is not a guarantee of correctness, completeness, availability, or permission to reuse the linked material. Current scholarly collectors query a finite set of provider APIs; the curated registry adds useful entry points for official documentation, datasets, standards, and open-source projects. Coverage expands only when a source is added, configured, tested, and measured.

The catalogue is a discovery layer, not a substitute for checking the original source. API limits, licenses, access requirements, versions, and exchange rules can change.

## Current Components

| Component | Responsibility |
|---|---|
| `config.py` | Environment-backed provider settings, execution settings, paths, and the existing search-query taxonomy |
| `api_*.py` | Provider-specific scholarly metadata adapters |
| `master.py` | Query scheduling, cache loading, and collection orchestration |
| `utils.py` | Normalization, URL checks, conservative identity matching, access labels, logging, and bounded retries |
| `classifier.py` | Evidence-backed category assignment using document text rather than the search bucket alone |
| `merge.py` | Main merge, deduplication, classification, metric calculation, and export orchestration |
| `merge_light.py` | Lower-overhead merge entry point using the same canonical renderer |
| `md_builder.py` | Markdown category pages, indexes, and statistics |
| `resource_catalog.py` | Local search and validation across curated resources, collected resource metadata, and generated publication tables |
| `web_resource_collector.py` | Bounded, explicit collection of public metadata from GitHub, Hugging Face, and Zenodo |
| `resources/discovery_queries.json` | Versioned query plan for repository, model, dataset, and research-artifact discovery |
| `scripts/check_english_only.py` | Checks tracked text and readable ZIP members for Arabic-script characters, including Persian characters |
| `resources/catalog.json` | Curated starter registry spanning research, market data, trading frameworks, engineering tools, standards, and operations |
| `preflight.py` | Local readiness checks and optional bounded public-endpoint probes |

## Quick Start

Requires Python 3.10 or newer.

1. Clone the repository and enter its root directory.
2. Install runtime dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Create local configuration from the empty template:

   ```bash
   cp .env.example .env
   ```

   Edit only the environment values needed for the providers you intend to use. Empty credentials disable those optional authenticated providers. Never commit `.env`, API keys, or tokens.

4. Point runtime data and output paths at this checkout (recommended when running from a clone):

   ```bash
   export TRADING_ENCYCLOPEDIA_HOME="$PWD"
   ```

5. Run local checks:

   ```bash
   python preflight.py
   python resource_catalog.py validate
   python web_resource_collector.py validate-queries
   python scripts/check_english_only.py
   ```

6. Search the local catalogue:

   ```bash
   python resource_catalog.py search "market microstructure"
   python resource_catalog.py search "exchange websocket" --registry-only
   python resource_catalog.py list --stage exchange-integration
   python resource_catalog.py export --output output/RESOURCE_INDEX.md
   ```

8. Preview the bounded public resource-discovery plan without making any network requests:

   ```bash
   python web_resource_collector.py plan --provider github --max-queries 2
   python web_resource_collector.py plan --provider huggingface_models --max-queries 2
   ```

9. When online collection is intended, explicitly run a small bounded collection:

   ```bash
   python web_resource_collector.py collect --provider github --max-queries 2 --results-per-query 5
   python resource_catalog.py search "market data" --collected-only
   ```

   The collector performs only metadata requests. It does not download full source repositories, model weights, datasets, or article full texts. Provider quotas, query semantics, and terms apply; results remain marked `unreviewed` until reviewed.

7. Run a scholarly provider and rebuild the generated output when configured:

   ```bash
   python master.py --api crossref
   python merge.py
   ```

Use `python master.py --api openalex`, `--api arxiv`, or another provider name supported by `API_MAP` to run a specific adapter. The `--api all` mode can take a long time and should be used only after rate limits, storage, and query scope have been reviewed.

`merge_light.py` provides an alternate entry point for constrained environments. Both merge paths use the shared renderer; benchmark memory use before selecting a default for a particular device.

## Local Search Commands

- Search the curated resource registry and generated publication category files:

  ```bash
  python resource_catalog.py search "order book"
  ```

- Search only official docs, datasets, standards, libraries, and other curated entry points:

  ```bash
  python resource_catalog.py search "websocket" --registry-only
  ```

- Search only generated publication tables:

  ```bash
  python resource_catalog.py search "deflated sharpe" --articles-only
  ```

- Filter curated resources by lifecycle stage or type:

  ```bash
  python resource_catalog.py list --stage risk-management
  python resource_catalog.py list --type market-data-docs
  ```

Search uses local files. It does not issue a web search or download content for each query. A result provides a source link; users should open the source and confirm the relevant version and details.

## Lifecycle Taxonomy

The discovery model should follow the work that a real trading-system team performs:

1. Problem definition, requirements, scope, and constraints.
2. Architecture, design decisions, roadmap, interfaces, and design freeze.
3. Data acquisition, storage, quality, lineage, and real-time pipelines.
4. Quantitative research, market knowledge, strategies, and signal design.
5. Model development, training, calibration, and experiment tracking.
6. Simulation, backtesting, statistical validation, and robustness testing.
7. Portfolio construction, position sizing, limits, and risk controls.
8. Execution, order management, market microstructure, and exchange integration.
9. Testing, packaging, deployment, security, and operational readiness.
10. Observability, incidents, change management, governance, and continuous improvement.

See [the product vision](docs/PRODUCT_VISION.md) and [taxonomy guide](docs/TAXONOMY_AND_DISCOVERY.md).

## Data Quality and Known Limitations

The repository's historical generated tables were created before the current classification and data-quality corrections. Updating code does not retroactively correct those generated files. Rebuild the dataset from available raw query caches and review the regenerated output before describing it as quality-validated.

The local curated registry is a maintained seed, not a complete global resource graph. The registry's `review_status` value is `seed`; this does not mean every URL is continuously monitored. Automated link-health monitoring, broader provider coverage, richer provenance, and calibrated per-category quality metrics remain planned work.

Counts must distinguish unique bibliographic records from category assignments: one document may legitimately appear in multiple categories.

## Security

All provider keys must be supplied through environment variables or a local ignored `.env` file. API credentials previously committed in repository history must be treated as potentially exposed and rotated at the relevant providers. Removing credentials from the current file does not erase historical commits.

See [SECURITY.md](SECURITY.md).

## Documentation

- [Product vision](docs/PRODUCT_VISION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Taxonomy and discovery model](docs/TAXONOMY_AND_DISCOVERY.md)
- [Data quality and validation](docs/DATA_QUALITY.md)
- [Source policy](docs/SOURCE_POLICY.md)
- [Roadmap](docs/ROADMAP.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Reuse and licensing considerations](docs/LICENSING_AND_REUSE.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Contributing

Contributions are welcome for source adapters, resource entries, query taxonomies, relevance rules, tests, documentation, and reproducibility tooling. Changes should include evidence, source-specific constraints, and tests where possible. See [CONTRIBUTING.md](CONTRIBUTING.md).
