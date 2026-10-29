# Roadmap

This roadmap separates correctness and trust prerequisites from new breadth and advanced features. The sequence is deliberate: expanding the catalogue before fixing source provenance, relevance, and measurement would scale noise rather than value.

## Phase 0 - Safety and Baseline

**Status in the current upgrade branch: implemented in source; operational follow-up still required.**

- Remove embedded provider keys from the active configuration.
- Move provider credentials to environment-backed configuration.
- Document that previously committed credentials must be rotated.
- Add ignored local configuration files and avoid printing request URLs or secrets in preflight diagnostics.
- Make runtime directory creation explicit rather than an import-time side effect.
- Bound CORE rate-limit retries and respect a numeric Retry-After value where possible.
- Make Git helper behavior non-destructive and avoid shell interpolation.

**Exit criteria:** relevant credentials rotated, no live secrets in current tracked files, and security scan clean for the current tree. History cleanup is a separate potentially disruptive action and must be evaluated independently.

## Phase 1 - Product Identity and Local Discovery

**Status in the current upgrade branch: implemented as a first increment.**

- Define the product as a lifecycle-oriented discovery index, not a claim to mirror the entire Internet.
- Add a root README, scope documentation, roadmap, data-quality policy, and source policy.
- Add a curated registry with 67 seed links across research, data, trading frameworks, engineering tools, standards, security, and operations.
- Add a local CLI to search registry records and generated publication tables, validate registry structure, and export a Markdown resource index.
- Add standard dependency metadata.

**Exit criteria:** registry validation succeeds, local search tests pass, CLI examples work on a clean checkout, and no undocumented capability is claimed.

## Phase 2 - Classification and Data Integrity

**Status in the current upgrade branch: first code corrections implemented; benchmark and full corpus rebuild remain pending.**

- Stop query-bucket metadata from forcing category assignment.
- Require finance/trading context or specific domain evidence for current rule-based classifications.
- Expose matched patterns to make assignment decisions inspectable.
- Use more conservative record identity; stop truncating titles to a fixed prefix.
- Separate unique-record metrics from category-assignment metrics.
- Use a single renderer from both merge entry points.
- Regenerate historical output from local raw caches and manually review representative records.

**Exit criteria:** reviewed benchmark with category-level metrics, reconciled counts, sample-page audit, and reproducible export manifest.

## Phase 3 - Testability and Automation

**Planned for this release sequence.**

- Add unit tests for URL validation, identity matching, classification, registry validation, and search.
- Add mocked adapter tests for success, empty results, invalid responses, timeouts, rate limits, and retry exhaustion.
- Add CI for Python compilation, offline tests, and secret scanning.
- Record query-level status and source-specific failure metrics.
- Add deterministic test fixtures and a known-output integration test.

**Exit criteria:** CI passes on a clean environment without live keys or network access for the primary test suite.

## Phase 4 - Data Model and Provenance

**Planned.**

- Introduce explicit document, provider observation, query run, classification assignment, access observation, and error schemas.
- Preserve provider-specific identifiers and source fields.
- Record query version, adapter version, timestamps in UTC, and source response status.
- Distinguish unknown counts from zero and page range from page count.
- Store citation counts as source-specific dated observations.
- Evaluate SQLite as the initial canonical store.

**Exit criteria:** records can be traced from export to source observations and their generating run.

## Phase 5 - Broader Resource Coverage

**Planned.**

Add separate, bounded discovery adapters for resource types that scholarly APIs do not cover well:

- Public source-code repositories and release metadata.
- Official developer-documentation portals and standards.
- Dataset registries and research-artifact repositories.
- Model and dataset hubs.
- Technical libraries, testing and validation tools, and operational systems.
- Carefully labeled books, tutorials, and community resources where discovery value warrants inclusion.

Each adapter must have a distinct rate budget, licensing review, schema, source-health report, and acceptance tests. Do not send the full academic query set to rate-limited non-academic APIs without a provider-specific query plan.

## Phase 6 - Search Relevance and Ranking

**Planned.**

- Build an adjudicated reference set from representative user questions.
- Measure precision, recall, reciprocal rank, coverage, and zero-result rates.
- Add vocabulary, synonyms, acronym disambiguation, and concept relationships.
- Introduce semantic retrieval only if evaluation demonstrates improvement over keyword search.
- Keep evidence and source provenance visible regardless of ranking method.

**Exit criteria:** a ranking change demonstrates measurable gains without unacceptable regression in core topics.

## Phase 7 - Release and Community Operations

**Planned.**

- Add release snapshots with manifests and checksums.
- Add a URL-health review process and source deprecation policy.
- Publish reusable data exports with appropriate rights and source attribution.
- Add issue templates, contributor guidance, security reporting, and release notes.
- Build a richer search interface only after the local data model and quality gates are dependable.

## Deferred Until Evidence Justifies Them

- Live Internet crawling or broad web search requiring separate providers and infrastructure.
- Embedding every document or building a vector database without retrieval benchmarks.
- Large language-model-generated summaries as an unreviewed source of truth.
- Automatic deletion of fuzzy duplicates.
- Claims of exhaustive coverage or production-grade classification without measurement.
