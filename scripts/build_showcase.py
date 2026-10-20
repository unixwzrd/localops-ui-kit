#!/usr/bin/env python3
"""Assemble an allowlisted browser-only site without running JavaScript tooling."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

GALLERY_FILES = (
    "index.html",
    "gallery.js",
    "gallery.css",
    "code-editor.html",
    "content-panel.html",
    "result-reader.html",
    "result-reader.js",
)
SHOWCASE_FILES = ("index.html", "showcase.css")


def build(repository: Path, output: Path) -> list[str]:
    """Copy only approved assets into a new output directory; refuse overwrites."""
    manifest = json.loads((repository / "packages/web/assets.json").read_text())
    files = [Path("packages/web/static") / name for name in [*manifest["modules"], manifest["stylesheet"]]]
    files.extend(Path("examples/component-gallery") / name for name in GALLERY_FILES)
    files.extend(Path("examples/showcase") / name for name in SHOWCASE_FILES)
    for relative in files:
        source = repository / relative
        if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(repository.resolve()):
            raise ValueError(f"Invalid showcase source: {relative}")
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Invalid showcase destination: {relative}")
    output.mkdir(parents=True, exist_ok=False)
    for relative in files:
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / relative, target)
    (output / ".nojekyll").touch()
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0;url=examples/showcase/">'
        "<title>LocalOps UI Kit showcase</title></head><body>"
        '<a href="examples/showcase/">Open widget showcase</a></body></html>\n'
    )
    return [str(relative) for relative in files]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("_site"))
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    files = build(repository, args.output)
    print(f"Static showcase: {len(files)} allowlisted source files; output={args.output}")


if __name__ == "__main__":
    main()
