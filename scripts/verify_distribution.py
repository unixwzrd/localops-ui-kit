#!/usr/bin/env python3
"""Verify wheel/sdist assets and smoke-test installed static serving."""

from __future__ import annotations

import importlib
import json
import sys
import tarfile
import tempfile
import threading
import tomllib
import urllib.request
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FORBIDDEN_PATH_MARKERS = (b"/Users/", b"/home/", b":\\Users\\")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    static = repository / "packages" / "web" / "static"
    manifest = json.loads((repository / "packages" / "web" / "assets.json").read_text(encoding="utf-8"))
    asset_names = sorted(set(manifest["modules"]) | {manifest["stylesheet"]})
    version = tomllib.loads((repository / "pyproject.toml").read_text())["project"]["version"]
    wheel = repository / "dist" / f"localops_ui-{version}-py3-none-any.whl"
    sdist = repository / "dist" / f"localops_ui-{version}.tar.gz"
    testkit_dist = repository / "packages" / "python-testkit" / "dist"
    testkit_wheel = next(testkit_dist.glob("*.whl"))
    testkit_sdist = next(testkit_dist.glob("*.tar.gz"))

    with zipfile.ZipFile(wheel) as archive:
        for archived_name in archive.namelist():
            data = archive.read(archived_name)
            assert not any(marker in data for marker in FORBIDDEN_PATH_MARKERS), archived_name
        for name in asset_names:
            assert archive.read(f"localops_ui/static/{name}") == (static / name).read_bytes(), name

    with tarfile.open(sdist, "r:gz") as archive:
        members = {member.name: member for member in archive.getmembers()}
        prefix = next(name.split("/", 1)[0] for name in members)
        for archived_name, archived_member in members.items():
            if not archived_member.isfile():
                continue
            extracted = archive.extractfile(archived_member)
            assert extracted is not None
            assert not any(marker in extracted.read() for marker in FORBIDDEN_PATH_MARKERS), archived_name
        for name in asset_names:
            member = members[f"{prefix}/packages/web/static/{name}"]
            extracted = archive.extractfile(member)
            assert extracted is not None
            assert extracted.read() == (static / name).read_bytes(), name

    with zipfile.ZipFile(testkit_wheel) as archive:
        for archived_name in archive.namelist():
            data = archive.read(archived_name)
            assert not any(marker in data for marker in FORBIDDEN_PATH_MARKERS), archived_name
    with tarfile.open(testkit_sdist, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            assert extracted is not None
            assert not any(marker in extracted.read() for marker in FORBIDDEN_PATH_MARKERS), member.name

    with tempfile.TemporaryDirectory(prefix="localops-ui-wheel-") as temporary:
        target = Path(temporary) / "site"
        target.mkdir()
        with zipfile.ZipFile(wheel) as archive:
            assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in archive.namelist())
            archive.extractall(target)
        with zipfile.ZipFile(testkit_wheel) as archive:
            assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in archive.namelist())
            archive.extractall(target)
        sys.path.insert(0, str(target))
        for module_name in [name for name in sys.modules if name == "localops_ui" or name.startswith("localops_ui.")]:
            del sys.modules[module_name]
        installed = importlib.import_module("localops_ui")
        testkit = importlib.import_module("localops_ui_testkit")
        assert callable(testkit.measure_layout)
        installed_static = Path(str(installed.web_assets()))
        handler = partial(_QuietHandler, directory=installed_static)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/index.js") as response:
                assert response.read() == (static / "index.js").read_bytes()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            sys.path.remove(str(target))

    print("both wheels/sdists, installed resources, asset equality, and loopback serving: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
