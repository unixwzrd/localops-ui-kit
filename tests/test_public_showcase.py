"""Exercise only the allowlisted static-site output, including project subpaths."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from localops_ui_testkit import assert_layout, measure_layout
from playwright.sync_api import expect

REPOSITORY = Path(__file__).resolve().parents[1]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, REPOSITORY / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def showcase(tmp_path_factory):
    parent = tmp_path_factory.mktemp("static-site")
    output = parent / "project-prefix"
    load_script("build_showcase").build(REPOSITORY, output)

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=parent))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/project-prefix", output
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def test_site_allowlist_and_reference_completeness(showcase):
    _, output = showcase
    assert sorted(str(path.relative_to(output)) for path in (output / "docs").rglob("*") if path.is_file()) == [
        "docs/assets/localops-ui-kit-banner.png"
    ]
    assert (output / "docs/assets/localops-ui-kit-banner.png").read_bytes() == (
        REPOSITORY / "docs/assets/localops-ui-kit-banner.png"
    ).read_bytes()
    assert not (output / "examples/component-gallery/negative-control.html").exists()
    assert not (output / "examples/component-gallery/manifest.html").exists()
    manifest = json.loads((REPOSITORY / "packages/web/assets.json").read_text())
    for name in [*manifest["modules"], manifest["stylesheet"]]:
        assert (output / "packages/web/static" / name).read_bytes() == (
            REPOSITORY / "packages/web/static" / name
        ).read_bytes()
    guide = (REPOSITORY / "docs/widget-guide.md").read_text()
    for name in manifest["exports"]:
        assert f"### {name}\n" in guide, name
    with pytest.raises(FileExistsError):
        load_script("build_showcase").build(REPOSITORY, output)


def test_publication_guard_detects_private_material():
    guard = load_script("check_publication")
    home = "/".join(["", "Users", "example", "private"])
    assert "home path" in guard.inspect_text("sample", home)[0]
    assert guard.inspect_text("sample", "ordinary widget documentation") == []
    assert "docs/consumer-handoffs/" in guard.PRIVATE_PREFIXES


def test_publication_guard_pins_reviewed_banner_bytes(tmp_path):
    guard = load_script("check_publication")
    name = "docs/assets/localops-ui-kit-banner.png"
    data = (REPOSITORY / name).read_bytes()
    assert guard.inspect_binary(name, data) == []
    assert guard.inspect_binary(name, data + b"modified")
    assert guard.inspect_binary("unreviewed.png", data)
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    replacement = tmp_path / name
    replacement.parent.mkdir(parents=True)
    replacement.write_text("Text masquerading as the approved image")
    assert guard.check(tmp_path) == [f"Binary requires manual publication review: {name}"]


def test_public_snapshot_refuses_private_paths_and_overwrites(tmp_path):
    exporter = load_script("export_public")
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("Public documentation")
    private = source / "docs/consumer-handoffs"
    private.mkdir(parents=True)
    (private / "journal.md").write_text("Private coordination")
    output = tmp_path / "public"
    with pytest.raises(ValueError, match="Not an approved public source"):
        exporter.copy_snapshot(source, output, ["README.md", "docs/consumer-handoffs/journal.md"])
    assert not output.exists()
    assert exporter.copy_snapshot(source, output, ["README.md"]) == 1
    assert not (output / ".git").exists()
    with pytest.raises(FileExistsError):
        exporter.copy_snapshot(source, output, ["README.md"])
    with pytest.raises(ValueError):
        exporter.copy_snapshot(source, tmp_path / "other", ["../escape"])


@pytest.mark.parametrize("viewport", [(1440, 900), (820, 1024), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_showcase_responsive_theme_and_links(page, showcase, viewport, theme):
    base, _ = showcase
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: errors.append(response.url) if response.status >= 400 else None)
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(f"{base}/")
    expect(page.get_by_role("heading", name="Widgets you can try.")).to_be_visible()
    banner = page.get_by_role("img", name="LocalOps UI Kit — Python-first · WebUI · Textual · Rich")
    expect(banner).to_be_visible()
    assert banner.evaluate("image => image.complete && image.naturalWidth === 1983")
    page.get_by_role("button", name="Dark mode").focus()
    if theme == "dark":
        page.keyboard.press("Space")
    assert page.locator("html").get_attribute("data-theme") == theme
    assert_layout(measure_layout(page, mode="reachability"), label=f"showcase-{theme}")
    page.get_by_role("button", name="Dark mode").focus()
    expect(page.get_by_role("button", name="Dark mode")).to_be_focused()
    assert page.evaluate("getComputedStyle(document.activeElement).outlineStyle") != "none"
    links = page.locator('main a[href^="../"]').evaluate_all("nodes => nodes.map(node => node.href)")
    assert len(links) == 6
    for url in dict.fromkeys(links):
        response = page.goto(url)
        assert response and response.ok
        page.wait_for_selector(".lui-shell")
    assert not errors


def test_generated_gallery_interactions(page, showcase):
    base, _ = showcase
    page.goto(f"{base}/examples/component-gallery/")
    page.get_by_role("button", name="Confirm", exact=True).click()
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_be_hidden()
    page.get_by_role("tab", name="Overview").focus()
    page.keyboard.press("End")
    expect(page.get_by_role("tab", name="History")).to_have_attribute("aria-selected", "true")
    page.get_by_role("button", name="Cancel", exact=True).click()
    expect(page.get_by_role("button", name="Retry", exact=True)).to_be_enabled()
    page.get_by_role("button", name="Retry", exact=True).click()
    expect(page.get_by_role("button", name="Cancel", exact=True)).to_be_enabled()
    page.goto(f"{base}/examples/component-gallery/content-panel.html")
    page.get_by_role("button", name="Open help").click()
    expect(page.get_by_role("dialog", name="Document help")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("button", name="Open help")).to_be_focused()
    page.goto(f"{base}/examples/component-gallery/code-editor.html")
    editor = page.get_by_role("textbox", name="Session draft", exact=True)
    editor.fill("Edited in the static demo")
    expect(editor).to_have_value("Edited in the static demo")
