#!/usr/bin/env python3
"""Export a clean, audited source snapshot without private Git ancestry."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PUBLIC_ROOTS = {".github", "compatibility", "docs", "examples", "packages", "scripts", "tests"}
PUBLIC_FILES = {
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "ruff.toml",
    "uv.lock",
}
PRIVATE_ROOTS = {"consumer-handoffs", ".git", "__pycache__", ".venv", "dist", "output", "private", "_site"}


def copy_snapshot(repository: Path, output: Path, names: list[str]) -> int:
    """Validate the complete file list before creating a new, overwrite-free snapshot."""
    for name in names:
        relative = Path(name)
        source = repository / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or PRIVATE_ROOTS.intersection(relative.parts)
            or (name not in PUBLIC_FILES and relative.parts[0] not in PUBLIC_ROOTS)
            or not source.is_file()
            or source.is_symlink()
            or not source.resolve().is_relative_to(repository.resolve())
        ):
            raise ValueError(f"Not an approved public source: {name}")
    output.mkdir(parents=True, exist_ok=False)
    for name in names:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / name, target)
    return len(names)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory; never an existing checkout")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repository)
    if status:
        raise SystemExit("Commit/review development changes first; snapshot export requires a clean worktree.")
    subprocess.run([sys.executable, str(repository / "scripts/check_publication.py")], cwd=repository, check=True)
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=repository).decode().rstrip("\0").split("\0")
    count = copy_snapshot(repository, args.output, names)
    print(f"Exported {count} audited files to {args.output}; no Git metadata or private ancestry copied.")


if __name__ == "__main__":
    main()
