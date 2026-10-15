#!/usr/bin/env python3
"""
Trading Encyclopedia — Git Sync
Pushes output files to GitHub repository.
Usage: python git_sync.py
"""
import os, subprocess, sys, time

OUTPUT_DIR = os.path.expanduser("~/encyclopedia/output")
BASE_DIR   = os.path.expanduser("~/encyclopedia")

def run_cmd(cmd, cwd=BASE_DIR):
    result = subprocess.run(cmd, shell=True, cwd=cwd,
                            capture_output=True, text=True)
    if result.stdout.strip():
        print("  " + result.stdout.strip())
    if result.stderr.strip() and "warning" not in result.stderr.lower():
        print("  STDERR: " + result.stderr.strip()[:200])
    return result.returncode

def sync():
    print("\n" + "="*55)
    print("  TRADING ENCYCLOPEDIA — GIT SYNC")
    print("="*55 + "\n")

    # Check git init
    if not os.path.exists(os.path.join(BASE_DIR, ".git")):
        print("  Git not initialized. Run setup_git.sh first.")
        sys.exit(1)

    # Copy output to root for git
    import shutil
    for fname in os.listdir(OUTPUT_DIR):
        src = os.path.join(OUTPUT_DIR, fname)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(BASE_DIR, fname))

    cats_src = os.path.join(OUTPUT_DIR, "categories")
    cats_dst = os.path.join(BASE_DIR, "categories")
    if os.path.isdir(cats_src):
        os.makedirs(cats_dst, exist_ok=True)
        for fname in os.listdir(cats_src):
            shutil.copy(os.path.join(cats_src, fname), os.path.join(cats_dst, fname))

    # Git operations
    timestamp = time.strftime("%Y-%m-%d %H:%M")
    run_cmd("git add README.md INDEX.md STATISTICS.md AUTHORS_INDEX.md VENUES_INDEX.md DOMAINS_GUIDE.md categories/ *.py .gitignore 2>/dev/null || true")
    run_cmd("git commit -m \"Encyclopedia update: " + timestamp + "\"")
    ret = run_cmd("git push origin main")
    if ret != 0:
        ret = run_cmd("git push origin master")
    if ret == 0:
        print("\n  Successfully pushed to GitHub")
    else:
        print("\n  Push failed — check token and try again")
        print("  Tip: git push origin main")

if __name__ == "__main__":
    sync()
