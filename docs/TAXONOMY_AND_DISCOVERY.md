# Taxonomy and Discovery Model

## 1. Separate Three Different Taxonomies

The system must not confuse query phrases, resource types, and lifecycle categories.

### Search taxonomy

Search phrases are used to query provider APIs. They are optimized for discovery and recall. A search phrase can be ambiguous and an API can return irrelevant results.

### Resource-type taxonomy

This describes what a result is: scholarly paper, preprint, official API document, standard, dataset, source-code repository, software documentation, book, tutorial, benchmark, regulatory publication, or community discussion.

### Lifecycle taxonomy

This describes why the resource is useful in the user's work: architecture, data ingestion, signal design, backtesting, risk controls, exchange connectivity, deployment, or another stage. A resource may legitimately support several lifecycle stages.

These fields must remain separate in stored records and search results.

## 2. Lifecycle Stages

| Stage | Main questions | Example resource types |
|---|---|---|
| Problem definition | What problem, market, constraints, objectives, and users are in scope? | Research papers, requirements templates, regulatory guidance |
| Architecture | What components, contracts, boundaries, data flows, and failure modes are required? | Architecture references, systems papers, design decision records |
| Design freeze and handoff | What is decided, what is deferred, and how can an implementation team verify the design? | Architecture decision records, interface specifications, acceptance criteria |
| Research | Which theories, methods, strategies, and empirical findings are relevant? | Journals, books, preprints, technical reports |
| Data acquisition | Which market, macro, on-chain, and alternative-data sources exist? | Official API docs, datasets, vendor docs, source catalogs |
| Data engineering | How should time, schemas, lineage, storage, event ordering, and missingness be managed? | Database docs, streaming docs, data-format specifications |
| Signal design | How are hypotheses converted into precise, falsifiable features and rules? | Research papers, technical articles, libraries, strategy references |
| Model development and training | Which models, libraries, data splits, compute options, and experiment procedures are relevant? | Papers, model docs, datasets, ML frameworks |
| Backtesting and simulation | How are market mechanics, fees, funding, fills, latency, and state transitions represented? | Backtest engines, simulation tools, execution papers |
| Validation and robustness | How are leakage, overfitting, selection bias, multiple testing, and regime dependence tested? | Statistical papers, validation libraries, testing frameworks |
| Optimization and calibration | Which parameters, objective functions, constraints, and search procedures are defensible? | Optimization libraries, academic research, experiment platforms |
| Risk management | How are portfolio exposure, tail risk, sizing, limits, and failure states modeled? | Risk research, regulatory material, numerical libraries |
| Execution and market microstructure | How are order types, liquidity, queue position, impact, and fill uncertainty handled? | Microstructure research, exchange specs, FIX standards |
| Exchange integration | What authentication, REST, websocket, timestamp, rate-limit, and order-state rules apply? | Official exchange API docs, SDKs, code examples |
| Testing | Which unit, integration, property, replay, chaos, and acceptance tests are needed? | Test frameworks, fixtures, exchange simulators |
| Deployment and operations | How are releases, secrets, configuration, restarts, reconciliation, and rollback managed? | CI/CD, container, operational, and deployment docs |
| Observability and incidents | Which metrics, logs, traces, alerts, invariants, and incident procedures are required? | Telemetry docs, dashboards, reliability engineering references |
| Security and governance | How are credentials, permissions, auditability, data rights, and AI risks controlled? | Security standards, regulator guidance, governance frameworks |

## 3. Resource Types

Use a controlled set of resource types, including:

- `research-index`, `preprint-server`, and `open-access-index`
- `official-api-docs`, `market-data-docs`, and `official-standard`
- `open-source-framework`, `programming-docs`, and `documentation`
- `data-platform`, `ml-platform`, and research-artifact registries
- `testing-tool`, `observability-tool`, and `security-guidance`
- `book`, `course`, `tutorial`, `technical-article`, and `community-discussion`

The latter types should be added to the structured registry as the relevant connectors and quality controls are implemented. Authority level and resource type must be visible; a source repository, official specification, peer-reviewed article, and community post must not appear as interchangeable evidence.

## 4. Query Design

Provider queries should be stored independently from classification rules. Query terms should have a stable identifier and metadata such as:

- Query phrase and normalized form.
- Intended concepts and lifecycle stages.
- Supported provider list.
- Last evaluated time and query version.
- Expected resource types.
- Known ambiguous terms and negative terms.
- Sample relevant and irrelevant results.

Do not assume that different providers interpret a phrase identically. Source-specific query syntax and pagination should be tested per adapter.

## 5. Classification Rules

Every assignment should be supported by observable evidence. The original query bucket may be retained as discovery provenance but must not by itself force the result into that category.

The current rule-based classifier returns category IDs and can expose matched patterns. Its output is a heuristic candidate set; the matched patterns are not calibrated confidence scores. A future quality pipeline should evaluate precision and recall against a manually reviewed benchmark before defining confidence thresholds.

Ambiguous acronyms need special treatment. Examples include ICT, SMC, VAR, PIN, DOM, RL, and other abbreviations with unrelated meanings. Context should be checked, and uncertain results should remain unclassified or flagged for review rather than forced into a likely-wrong category.

## 6. Search Result Contract

A future unified result should include, where available:

- Stable result ID and canonical title.
- Resource type and lifecycle stages.
- Source name and provider-specific ID.
- Canonical URL and optional direct full-text URL.
- Publication/version information where applicable.
- Query-run and source-observation IDs.
- Relevance evidence and classifier version.
- Access status and evidence for that status.
- Last observed time, link-health state, and known limitations.

The result must retain its source URL. The catalogue should help users discover and evaluate material, not imply that a link has been read or validated when it has not.
