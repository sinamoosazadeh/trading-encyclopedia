#!/usr/bin/env python3
"""Commit and push generated catalogue artifacts without shell interpolation."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"


def run_cmd(args: list[str], *, check: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(
        args,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, args, output=result.stdout, stderr=result.stderr
        )
    return result


def sync() -> int:
    if not (BASE_DIR / ".git").exists():
        print("Git is not initialized in the repository directory.", file=sys.stderr)
        print("Run setup_git.sh from the repository root first.", file=sys.stderr)
        return 2
    if not OUTPUT_DIR.is_dir():
        print("The generated output directory does not exist.", file=sys.stderr)
        print("Run merge.py or merge_light.py first.", file=sys.stderr)
        return 2

    branch_result = run_cmd(["git", "branch", "--show-current"])
    branch = branch_result.stdout.strip()
    if branch_result.returncode != 0 or not branch:
        print("Cannot determine the current branch; refusing to push from detached HEAD.", file=sys.stderr)
        return 2

    print(f"Staging generated artifacts under: {OUTPUT_DIR.relative_to(BASE_DIR)}")
    add_result = run_cmd(["git", "add", "--all", "--", "output"])
    if add_result.returncode != 0:
        return add_result.returncode

    diff_result = run_cmd(["git", "diff", "--cached", "--quiet", "--", "output"])
    if diff_result.returncode == 0:
        print("No generated-output changes to commit.")
        return 0
    if diff_result.returncode != 1:
        print("Unable to inspect staged changes; refusing to commit.", file=sys.stderr)
        return diff_result.returncode

    unrelated_result = run_cmd(["git", "diff", "--cached", "--quiet", "--", ".", ":(exclude)output"])
    if unrelated_result.returncode == 1:
        print("Unrelated staged changes exist outside output/. Refusing to include them in the generated-output commit.", file=sys.stderr)
        print("Review or unstage those changes before running this script again.", file=sys.stderr)
        return 2
    if unrelated_result.returncode != 0:
        print("Unable to check staged changes outside output/; refusing to commit.", file=sys.stderr)
        return unrelated_result.returncode

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit_result = run_cmd(["git", "commit", "-m", f"Update generated catalogue: {timestamp}"])
    if commit_result.returncode != 0:
        print("Commit failed. Review the Git output above; nothing was pushed.", file=sys.stderr)
        return commit_result.returncode

    push_result = run_cmd(["git", "push", "--set-upstream", "origin", branch])
    if push_result.returncode != 0:
        print("Push failed. Verify origin and authenticate with GitHub CLI.", file=sys.stderr)
        print("Suggested command: gh auth setup-git --hostname github.com", file=sys.stderr)
        return push_result.returncode

    print(f"Generated catalogue pushed successfully from branch {branch}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(sync())
