#!/usr/bin/env python3
"""Fail when tracked repository text contains Arabic-script characters.

The project language policy is English-only. The check is intentionally conservative:
it flags Arabic-script Unicode blocks, which include Persian characters as well as
Arabic and related writing systems. It scans text files and text members in ZIP
archives without executing or extracting archive contents to disk.
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARABIC_SCRIPT_PATTERN = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF"
    r"\uFE70-\uFEFE\U00010E60-\U00010E7F\U0001EE00-\U0001EEFF]"
)
KNOWN_TEXT_SUFFIXES = {
    ".md", ".py", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".sh",
    ".txt", ".cff", ".ini", ".cfg", ".csv", ".tsv", ".xml", ".html",
    ".rst", ".sql", ".ps1", ".bat", ".properties", ".example",
}
KNOWN_TEXT_NAMES = {".gitignore", ".env.example", "Dockerfile", "Makefile"}


def inspect_text(path_label: str, raw: bytes) -> list[str]:
    """Scan UTF-8 text efficiently and report precise, bounded character locations."""
    if b"\x00" in raw:
        return []
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return []
    issues = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for match in ARABIC_SCRIPT_PATTERN.finditer(line):
            character = match.group(0)
            issues.append(
                f"{path_label}:{line_number}:{match.start() + 1}: "
                f"Arabic-script character U+{ord(character):04X}"
            )
            if len(issues) >= 100:
                return issues
    return issues


def tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        names = result.stdout.decode("utf-8").split("\x00")
        return [ROOT / name for name in names if name]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        return [
            path for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]


def main() -> int:
    issues: list[str] = []
    for path in tracked_files():
        try:
            relative = path.relative_to(ROOT).as_posix()
            if path.suffix.lower() in KNOWN_TEXT_SUFFIXES or path.name in KNOWN_TEXT_NAMES:
                issues.extend(inspect_text(relative, path.read_bytes()))
            elif path.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(path) as archive:
                        for item in archive.infolist():
                            if item.is_dir() or item.file_size > 20_000_000:
                                continue
                            try:
                                raw = archive.read(item)
                            except (OSError, RuntimeError, zipfile.BadZipFile):
                                continue
                            # Check UTF-8 text members without guessing from their extension.
                            if b"\x00" not in raw:
                                issues.extend(inspect_text(f"{relative}!{item.filename}", raw))
                except (OSError, zipfile.BadZipFile):
                    issues.append(f"{relative}: unable to inspect ZIP archive")
        except OSError as exc:
            issues.append(f"{path.relative_to(ROOT).as_posix()}: read failed ({type(exc).__name__})")

    if issues:
        print("English-only policy check failed:", file=sys.stderr)
        for issue in issues[:500]:
            print(issue, file=sys.stderr)
        if len(issues) > 500:
            print(f"... and {len(issues) - 500} more finding(s)", file=sys.stderr)
        return 1

    print("English-only policy check passed: no Arabic-script characters found in tracked text files or readable ZIP members.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
