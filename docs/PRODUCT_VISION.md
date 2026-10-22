# Product Vision

## 1. The User Problem

Designing an advanced trading system spans far more than choosing a strategy. A serious effort can involve requirements, quantitative theory, market structure, data acquisition, historical data quality, architecture, software design, interfaces, execution mechanics, model development, training, backtesting, statistical validation, risk controls, release management, deployment, monitoring, incident response, and ongoing evolution.

Useful knowledge is scattered across scholarly indexes, preprint servers, publisher portals, official exchange documentation, software projects, standards bodies, datasets, technical documentation, books, and practitioner material. Repeating broad searches across many sources creates duplicated effort and produces inconsistent evidence trails.

The intended user should be able to begin with one discovery interface, search a central catalogue, open relevant source links, and then inspect the original materials. The catalogue should also be usable by AI-assisted workflows, which benefit from structured metadata and direct references rather than re-running the same discovery procedure for every design decision.

## 2. Product Definition

Trading Encyclopedia is intended to become a lifecycle-oriented resource discovery system for quantitative finance and trading-system engineering.

It should combine:

- A structured taxonomy of problems and engineering work.
- A registry of important authoritative entry points.
- Multi-provider discovery and indexing of relevant publications and technical resources.
- Local search across curated links and collected metadata.
- Stable source URLs and provenance for each result.
- Deduplication and relevance classification that can be audited.
- Source coverage, freshness, access, and quality reporting.
- Reproducible data exports and a navigable human-readable interface.

The project's value is not merely the number of stored links. It is the reduction in time and repeated work needed to locate useful resources, together with the ability to understand why a result is present and where it came from.

## 3. A Central Index Is Not the Whole Internet

The intended experience is that a user can begin at one place and discover resources that would otherwise require many separate searches. That goal must not be misrepresented as literal complete coverage of the Internet.

Each source has limits: its corpus, query syntax, access rules, rate limits, indexing delay, metadata quality, and publication types. Some resources are only discoverable through official documentation portals or repository search. Others are maintained by a provider without a stable public API.

Coverage must therefore be explicit and measurable. Every connector should identify its supported resource types, query limits, authentication requirements, last successful run, known omissions, and terms of use. Missing coverage must remain visible rather than being hidden behind a claim of completeness.

## 4. Resource Types

The resource model should support at least:

- Scholarly articles, working papers, preprints, books, chapters, and reviews.
- Official exchange API, market-data, authentication, websocket, and order-management documentation.
- Open-source trading engines, strategy frameworks, libraries, tools, and implementation repositories.
- Historical data, macroeconomic data, on-chain data, benchmark datasets, and synthetic-data resources.
- Programming-language, numerical-computing, storage, streaming, and infrastructure documentation.
- Testing, experiment tracking, model validation, deployment, telemetry, and incident-management tooling.
- Financial-messaging standards, regulatory guidance, security guidance, and AI governance frameworks.
- Tutorials, courses, technical articles, and community knowledge, with authority and confidence labels that distinguish these from primary documentation or peer-reviewed research.

A source being listed does not imply that it is peer reviewed, correct, free to use, complete, or suitable for production. Resource type and authority must be visible in search results.

## 5. The Main User Journey

1. Identify a design question or lifecycle stage.
2. Search the central catalogue by concept, technical term, tool, resource type, or stage.
3. Review ranked results with source type, relevance evidence, provenance, and access notes.
4. Open the original source and confirm the applicable version or publication.
5. Capture the source and the reason it was used in a research or design record.
6. Use the evidence to support architecture decisions, requirements, implementation tasks, test plans, or operational controls.
7. Preserve links and assumptions so later reviewers can reproduce the research.

For AI-assisted users, the system should eventually offer compact machine-readable results and citations with clear distinction between source facts, catalogue metadata, and inferred relevance. It should reduce redundant discovery work without concealing uncertainty or replacing primary-source review.

## 6. Success Measures

Success should be measured by usefulness and quality rather than by catalogue size alone:

- Search precision on representative lifecycle questions.
- Recall against a manually assembled reference set.
- Percentage of records with stable source identifiers and traceable provenance.
- Duplicate and false-merge rates.
- Percentage of results with useful and current links.
- Provider success, failure, empty-result, and rate-limit rates.
- Age of the most recent successful update per source.
- User task completion time for common discovery workflows.
- Percentage of records that are correctly typed and categorized.
- Reproducibility of indexed outputs from fixed inputs and code versions.

A larger catalogue that increases noise or creates false confidence is a regression.

## 7. Product Boundaries

The catalogue is not intended to mirror copyrighted full texts, bypass paywalls, bypass API restrictions, guarantee that a strategy is profitable, or treat community terminology as scientific evidence. It is a discovery and organization layer. The original publisher or provider remains the authority for the content, version, access conditions, and legal terms.
