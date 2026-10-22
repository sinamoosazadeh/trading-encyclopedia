#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
cd "$REPO_DIR"

if ! command -v git >/dev/null 2>&1; then
    echo "Git is required. Install it with your operating system package manager."
    exit 1
fi

if [[ ! -d .git ]]; then
    git init
fi

EXPECTED_REMOTE="https://github.com/sinamoosazadeh/trading-encyclopedia.git"
CURRENT_REMOTE="$(git remote get-url origin 2>/dev/null || true)"

if [[ -z "$CURRENT_REMOTE" ]]; then
    git remote add origin "$EXPECTED_REMOTE"
elif [[ "$CURRENT_REMOTE" != "$EXPECTED_REMOTE" ]]; then
    echo "An origin remote already exists and was not changed:"
    echo "  $CURRENT_REMOTE"
    echo "If that is intentional, keep it. To change it explicitly, run:"
    echo "  git remote set-url origin <your-repository-url>"
fi

if ! git config user.name >/dev/null; then
    git config user.name "Trading Encyclopedia Contributor"
fi
if ! git config user.email >/dev/null; then
    git config user.email "contributor@example.invalid"
fi

echo "Git repository is ready."
echo "Remote: $(git remote get-url origin)"
echo
echo "For GitHub HTTPS authentication, use GitHub CLI:"
echo "  gh auth login --hostname github.com --git-protocol https --web"
echo "  gh auth setup-git --hostname github.com"
echo
echo "Never put passwords, personal access tokens, or API keys in source files."
