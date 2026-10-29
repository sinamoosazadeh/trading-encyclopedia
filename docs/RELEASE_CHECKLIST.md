# Release Checklist

Use this checklist before tagging a public release or describing the catalogue as validated.

## Security

- [ ] Rotate credentials previously committed in public history.
- [ ] Verify no live secrets are present in the current tree, test fixtures, sample output, or logs.
- [ ] Review API permissions and keep credentials read-only where possible.
- [ ] Confirm the local environment file remains ignored.
- [ ] Review source-specific terms, rate limits, and redistribution constraints.

## Code and Runtime

- [ ] Install from a clean environment using documented commands.
- [ ] Run `python -m compileall -q .`.
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python resource_catalog.py validate`.
- [ ] Run local search and Markdown export examples.
- [ ] Run `python preflight.py`; use `--network` only when online probes are desired.
- [ ] Confirm the default pipeline terminates after bounded retries and reports failures.
- [ ] Confirm both merge paths use the same renderer.
- [ ] Confirm generated timestamps are UTC.

## Dataset and Relevance

- [ ] Rebuild from a documented raw-cache snapshot.
- [ ] Inspect records from every taxonomy block, including negative controls.
- [ ] Review known failure categories such as Smart Money Concepts / ICT for irrelevant biomedical or unrelated content.
- [ ] Measure classification precision and recall against the reviewed benchmark.
- [ ] Reconcile raw records, unique records, source counts, category assignments, and unclassified records.
- [ ] Check duplicate identities and source provenance.
- [ ] Verify representative source links and access status.
- [ ] Record dataset timestamp, code revision, taxonomy version, and checksums.

## Registry and Documentation

- [ ] Validate registry schema and duplicate IDs/URLs.
- [ ] Review link health for new or changed resources.
- [ ] Ensure each entry has a meaningful description, resource type, lifecycle stage, and tags.
- [ ] Verify that all documented commands work from a clean checkout.
- [ ] Review changelog and explicitly state known limitations.
- [ ] Decide and document separate reuse terms for code and generated data before making permissive license claims.

## Release Decision

- [ ] Do not publish a release if there are unresolved secret exposures, critical classifier failures, irreproducible output, or unreported provider failures.
- [ ] Use a release candidate if the code is ready but the full dataset has not passed its quality audit.
- [ ] State clearly which checks ran and which remain incomplete.
