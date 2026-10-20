#!/usr/bin/env python3
"""Validate canonical browser assets without a JavaScript toolchain."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

IMPORT_PATTERN = re.compile(r"(?:from\s+|import\()\s*[\"']([^\"']+)[\"']")
ABSOLUTE_PATH_PATTERN = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)")
FORBIDDEN_IMPORT_PATTERN = re.compile(r"(?:from|import)\s+[\"']?(?:forge|nicegui)(?:[./\"']|$)", re.IGNORECASE)
FORBIDDEN_DOMAIN_PATTERN = re.compile(
    r"\b(?:mlx|quantization|model conversion|code-analysis finding|fastapi|daemon shutdown)\b",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://[^\"'\s)]+")
ALLOWED_URLS = {"http://www.w3.org/2000/svg"}


def validate(repository: Path) -> list[str]:
    errors: list[str] = []
    package = repository / "packages" / "web"
    static = package / "static"
    manifest = json.loads((package / "assets.json").read_text(encoding="utf-8"))
    expected = set(manifest["modules"]) | {manifest["stylesheet"]}
    actual = {path.name for path in static.iterdir() if path.is_file()}
    if actual != expected:
        errors.append(f"asset manifest mismatch: expected={sorted(expected)} actual={sorted(actual)}")

    for module_name in manifest["modules"]:
        module = static / module_name
        text = module.read_text(encoding="utf-8")
        if "sourceMappingURL" in text:
            errors.append(f"{module}: source map reference is forbidden")
        if ABSOLUTE_PATH_PATTERN.search(text):
            errors.append(f"{module}: contains an absolute developer path")
        if FORBIDDEN_IMPORT_PATTERN.search(text):
            errors.append(f"{module}: contains a forbidden consumer/runtime import")
        if FORBIDDEN_DOMAIN_PATTERN.search(text):
            errors.append(f"{module}: contains consumer-specific domain terminology")
        for url in URL_PATTERN.findall(text):
            if url not in ALLOWED_URLS:
                errors.append(f"{module}: embeds a non-standard URL {url!r}")
        for imported in IMPORT_PATTERN.findall(text):
            if not imported.startswith("."):
                errors.append(f"{module}: non-relative import {imported!r}")
                continue
            target = (module.parent / imported).resolve()
            if target.parent != static.resolve() or not target.is_file():
                errors.append(f"{module}: unresolved or escaping import {imported!r}")

    forbidden_suffixes = (".ts", ".d.ts", ".map")
    for root in (package, repository / "tests", repository / "examples"):
        for path in root.rglob("*"):
            if path.is_file() and path.name.endswith(forbidden_suffixes):
                errors.append(f"provisional JavaScript-toolchain artifact remains: {path.relative_to(repository)}")

    scan_roots = [static, repository / "packages" / "python", repository / "packages" / "python-testkit"]
    for root in scan_roots:
        for path in root.rglob("*"):
            if not path.is_file() or any(
                part in {"__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "dist"} for part in path.parts
            ):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if ABSOLUTE_PATH_PATTERN.search(text):
                errors.append(f"{path.relative_to(repository)}: contains an absolute developer path")
    return errors


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    errors = validate(repository)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("canonical browser asset validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
