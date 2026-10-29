# Source Policy and Evidence Handling

## 1. Principles

- Prefer primary sources for interface semantics, API rules, standards, security requirements, and current product behavior.
- Prefer scholarly indexes, preprint servers, publisher metadata, and institutional repositories for academic discovery.
- Clearly distinguish official documentation, peer-reviewed research, preprints, source code, datasets, tutorials, and community discussions.
- Preserve canonical source links and provider identifiers.
- Respect published terms, licensing, rate limits, authentication requirements, and robots or access restrictions where applicable.
- Never bypass paywalls, credentials, geographical controls, or rate limits.
- Do not mirror full texts unless the source terms and applicable rights explicitly permit it.
- Treat a successful HTTP response as evidence of endpoint reachability, not proof of data quality or source completeness.

## 2. Authority Labels

Authority should be represented as source metadata rather than inferred from popularity alone.

- **Official primary source:** maintained by the provider, publisher, standards body, regulator, or project owner.
- **Scholarly index:** aggregates bibliographic or citation metadata from many publishers and repositories.
- **Research output:** peer-reviewed publication, preprint, working paper, technical report, or thesis. Its publication status must remain explicit where known.
- **Implementation evidence:** source code, tests, issues, benchmarks, or release notes. A repository does not prove the method is correct or suitable for production.
- **Secondary explanation:** tutorials, blogs, videos, courses, or community answers. These can help discovery but should not override primary documentation or high-quality empirical evidence.
- **Unverified resource:** listed as a candidate and not yet reviewed sufficiently for stronger claims.

The curated registry's initial `review_status: seed` is a workflow marker. It is not a quality rating or a claim that the URL has been recently checked.

## 3. Source Onboarding Checklist

Before adding a provider or resource:

1. Record the canonical URL and the organization responsible for it.
2. Identify the resource type, lifecycle stages, and useful query concepts.
3. Review terms of use, API documentation, rate limits, authentication, and attribution requirements.
4. Determine whether content, metadata, or only outbound links may be retained.
5. Define stable identifiers and pagination semantics.
6. Build fixtures from permitted sample responses.
7. Add error, retry, pagination, and empty-result tests.
8. Record expected coverage and known omissions.
9. Add a reproducible smoke test without storing credentials.
10. Mark the source as provisional until it has passed the release's quality gates.

## 4. Source Links and Access Status

A URL is not equivalent to an accessible full-text document. Distinguish landing pages, direct PDF links, repository pages, APIs, and official technical documentation. Access labels should be based on explicit evidence when available and should remain unknown otherwise.

The current domain and provider metadata checks are heuristic. They do not replace visiting the source, confirming publication-specific access, or reviewing its license.

## 5. Refresh and Deprecation

A future automated refresh process should record last-successful-check time, HTTP status category, redirects, content-type changes, deprecation notices, and retry history. It should not assume that a broken link means the source has been withdrawn, or that a redirect means a result is still semantically equivalent.

Provider-specific API versions and documentation paths should be reviewed before production or financial decisions rely on them.
