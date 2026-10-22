# Changelog

Changes are recorded by release or under the unreleased development section. Historical generated files and provider coverage should not be assumed to change merely because source code changes.

## Unreleased - Research Index Quality Upgrade

- Added a product vision for a lifecycle-oriented discovery index spanning research, implementation, validation, and operations.
- Added a curated registry of 67 resource entry points across scholarly discovery, exchange APIs, trading frameworks, data tools, ML tooling, testing, observability, standards, and security.
- Added a local CLI to search the registry and generated publication tables, validate registry metadata, and export a Markdown resource index.
- Removed embedded API credentials from the current configuration and switched provider keys to environment-backed settings.
- Made runtime directory creation explicit.
- Made URL validation stricter and source-domain matching exact.
- Made record identity more conservative by avoiding truncated-title merges and preserving records with insufficient identity fields.
- Changed classification so the original query category does not force an assignment; added inspectable match evidence and contextual filtering.
- Bounded CORE rate-limit retries and added Retry-After handling.
- Unified Markdown export behavior across the two merge entry points.
- Separated unique-record counts from category-assignment counts.
- Changed generated timestamps to UTC.
- Reworked Git helper behavior to avoid shell interpolation, destructive remote replacement, and overwriting root project documentation.
- Added project metadata, dependency declarations, quality documentation, source policy, release checklist, and automated tests.

### Known Limitations

- Provider credentials that appeared in earlier repository history must still be rotated; this change does not rewrite Git history.
- The historical generated category tables have not been rebuilt and audited by this branch. They may still contain the output of the previous classifier.
- The resource registry is a seed collection, not exhaustive Internet coverage, and automated URL-health monitoring is not yet implemented.
- Provider-query state, full provenance tracking, an adjudicated classification benchmark, and calibrated quality metrics remain incomplete.
- No repository-wide code/data license has been selected because code, generated metadata, third-party records, and the unreviewed archive require separate rights analysis.
