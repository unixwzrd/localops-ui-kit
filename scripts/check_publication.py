#!/usr/bin/env python3
"""Check prospective public files; optionally report the historical privacy gate."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

PRIVATE_PREFIXES = ("docs/consumer-handoffs/", "private/", "output/", "_site/")
HOME_PATH = re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/")
CHAT_ID = re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b")
SECRET = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{32,})\b")
# Reviewed product illustration only: no blanket exemption for arbitrary binary files.
REVIEWED_BINARIES = {
    "docs/assets/localops-ui-kit-banner.png": "f0b4f47a9432bf2bb0232444df148c1e4278e1d5417f901935941e16cbd1429d",
}


def inspect_binary(name: str, data: bytes) -> list[str]:
    """Accept only the exact manually reviewed illustration bytes."""
    if REVIEWED_BINARIES.get(name) != hashlib.sha256(data).hexdigest():
        return [f"Binary requires manual publication review: {name}"]
    return []


def inspect_text(name: str, text: str) -> list[str]:
    """Return focused privacy findings without printing potentially secret values."""
    errors = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for label, pattern in (("developer home path", HOME_PATH), ("internal identifier", CHAT_ID), ("token", SECRET)):
            if pattern.search(line):
                errors.append(f"{name}:{line_number}: possible {label}")
    return errors


def check(repository: Path, *, history: bool = False) -> list[str]:
    """Inspect tracked and nonignored candidate files without reading ignored journals."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    errors = []
    for name in sorted(set(result.stdout.decode().split("\0")) - {""}):
        if name.startswith(PRIVATE_PREFIXES) or Path(name).name.startswith(".env"):
            if Path(name).name != ".env.example":
                errors.append(f"Private file in public candidate: {name}")
                continue
        path = repository / name
        if not path.is_file():
            continue
        if name in REVIEWED_BINARIES:
            errors.extend(inspect_binary(name, path.read_bytes()))
            continue
        try:
            errors.extend(inspect_text(name, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            errors.extend(inspect_binary(name, path.read_bytes()))
    if history:
        past = subprocess.run(
            ["git", "log", "--all", "--format=%h", "--", "docs/consumer-handoffs/"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )
        if past.stdout.strip():
            errors.append("HISTORY BLOCKER: consumer handoffs remain in historical commits; see docs/public-release.md")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    errors = check(Path(__file__).resolve().parents[1], history=args.history)
    print("\n".join(errors) if errors else "Public candidate privacy checks: PASS (not a comprehensive secret audit)")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
