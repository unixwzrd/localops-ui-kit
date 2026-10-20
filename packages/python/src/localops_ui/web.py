"""Browser manifest helpers with no server-framework dependency."""

from __future__ import annotations

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path, PurePosixPath

from .compiler import Backend, LayoutCompiler
from .models import UISnapshot


def manifest(snapshot: UISnapshot) -> str:
    LayoutCompiler().compile(snapshot.spec, Backend.WEB)
    return snapshot.model_dump_json(by_alias=True, exclude_none=True)


def web_assets() -> Traversable:
    """Return the installed browser asset tree without assuming a filesystem install."""
    installed = files("localops_ui").joinpath("static")
    if installed.is_dir():
        return installed
    development = Path(__file__).resolve().parents[3] / "web" / "static"
    if development.is_dir():
        return development
    return installed


def web_asset(name: str) -> Traversable:
    """Return one installed browser asset after rejecting unsafe or missing paths."""
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("web asset name must be a safe relative path")
    asset = web_assets().joinpath(*relative.parts)
    if not asset.is_file():
        raise FileNotFoundError(name)
    return asset
