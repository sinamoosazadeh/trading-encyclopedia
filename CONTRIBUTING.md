# Contributing

Contributions are welcome for resource discovery, provider adapters, taxonomy design, data quality, tests, documentation, and reproducibility.

## Before Opening a Pull Request

1. Explain the user problem and expected benefit.
2. Identify affected resource types, lifecycle stages, providers, and outputs.
3. Check existing entries and issues for duplicates.
4. Verify official source URLs and note relevant terms, authentication, rate limits, and access restrictions.
5. Add or update tests for changes in code behavior.
6. Run the local checks listed below.
7. Describe what was tested and what remains unverified.

## Local Checks

From the repository root:

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
python resource_catalog.py validate
python resource_catalog.py search "order book" --registry-only --limit 10
```

The primary test suite must not require live API credentials or depend on network availability. Optional network diagnostics belong behind an explicit command-line option.

## Adding a Resource

Resource entries belong in `resources/catalog.json`. Each entry must have:

- A unique stable identifier.
- A canonical HTTP(S) URL without credentials embedded in the URL.
- A useful title and specific description.
- A controlled resource type.
- One or more valid lifecycle-stage identifiers.
- Search tags that improve discoverability without keyword stuffing.
- An honest review state.

Prefer official documentation for APIs, standards, libraries, and platform behavior. If the entry is a paper, tutorial, community discussion, or secondary explanation, represent that type honestly. Do not imply that a link was verified recently unless it was checked.

## Adding a Provider Adapter

Document endpoint, pagination, authentication, rate limits, provider-specific identifiers, error behavior, and known omissions. Use bounded retries and timeouts. Add tests for successful responses, empty results, invalid payloads, timeouts, rate limits, and retry exhaustion. Never place API keys in test fixtures or source code.

## Data and Classification Changes

Do not force a document into a category because of the query bucket that found it. Update the relevance evidence and tests. When changing normalization or duplicate identity, include both duplicate and non-duplicate test cases and explain any expected change to collection counts.

## Style and Language

Repository-authored code, comments, documentation, metadata descriptions, and user-facing strings must be English-only. Keep wording precise and avoid unsupported claims of exhaustive coverage, quality, or production readiness.
