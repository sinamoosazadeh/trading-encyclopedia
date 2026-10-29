# Security Policy

## Supported Version

Security fixes are developed against the current default branch and the latest reviewed release. Older snapshots may contain known or unresolved issues.

## Reporting a Vulnerability

Do not publish credentials, private data, or an exploitable security report in a public issue. Use GitHub's private vulnerability reporting feature if it is enabled for this repository. Otherwise, contact the maintainer privately through GitHub and provide a concise description, impact, reproduction steps, and a safe way to coordinate a fix.

Do not include working API keys, personal access tokens, account identifiers, or private datasets in a report.

## Secrets and Credentials

- Supply provider API keys through environment variables or a local ignored `.env` file.
- Never commit real credentials, session tokens, private URLs, or API request logs that contain secrets.
- Use the minimum permissions required; read-only credentials should be preferred when available.
- Rotate or revoke any credential that was committed, pasted into a public issue, or otherwise exposed.
- Deleting a secret from the current file does not remove it from Git history and does not revoke it.
- Do not run broad history-rewrite or force-push operations as an ad hoc cleanup; assess the impact and coordinate them separately.
- Do not disable TLS verification to make a provider request succeed.
- Keep network tests bounded and avoid logging complete authenticated request URLs.

## Operational Safety

This project is a research and resource-discovery tool, not an execution authorization system. Its metadata and links do not certify that a strategy is profitable, that a provider is available to a user, or that a code sample is suitable for live trading.
