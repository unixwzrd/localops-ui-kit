import pytest
from localops_ui_testkit import assert_layout, measure_layout

VIEWPORTS = [
    pytest.param({"width": 1440, "height": 900}, id="desktop"),
    pytest.param({"width": 820, "height": 1024}, id="tablet"),
    pytest.param({"width": 390, "height": 844}, id="mobile"),
]


@pytest.mark.parametrize("viewport", VIEWPORTS)
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_layout_at_supported_viewports(page, gallery_url: str, viewport: dict[str, int], theme: str) -> None:
    page.set_viewport_size(viewport)
    page.goto(gallery_url)
    page.locator("html").evaluate("(node, value) => { node.dataset.theme = value; }", theme)
    page.wait_for_selector(".lui-shell")
    assert_layout(measure_layout(page, mode="static"), label=f"{theme}-static")
    assert_layout(measure_layout(page, mode="reachability"), label=f"{theme}-reachability")


def test_tabs_keyboard_model(page, gallery_url: str) -> None:
    page.goto(gallery_url)
    overview = page.get_by_role("tab", name="Overview")
    overview.focus()
    page.keyboard.press("ArrowRight")
    assert page.get_by_role("tab", name="Details").get_attribute("aria-selected") == "true"
    page.keyboard.press("End")
    assert page.get_by_role("tab", name="History").get_attribute("aria-selected") == "true"
    page.keyboard.press("Home")
    assert overview.get_attribute("aria-selected") == "true"
    assert overview.get_attribute("tabindex") == "0"


def test_dialog_focus_trap_escape_and_restoration(page, gallery_url: str) -> None:
    page.goto(gallery_url)
    opener = page.get_by_role("button", name="Confirm", exact=True)
    opener.focus()
    opener.press("Enter")
    dialog = page.get_by_role("dialog")
    assert dialog.get_attribute("aria-modal") == "true"
    assert dialog.get_attribute("aria-labelledby")
    assert dialog.get_attribute("aria-describedby")
    page.keyboard.press("Tab")
    assert dialog.get_by_role("button", name="Cancel").evaluate("node => node === document.activeElement")
    page.keyboard.press("Escape")
    assert dialog.is_hidden()
    assert opener.evaluate("node => node === document.activeElement")


def test_theme_tokens_render_distinct_surfaces_and_visible_focus(page, gallery_url: str) -> None:
    page.goto(gallery_url)
    body = page.locator("body")
    light = body.evaluate("node => getComputedStyle(node).backgroundColor")
    page.get_by_role("button", name="Toggle theme").click()
    dark = body.evaluate("node => getComputedStyle(node).backgroundColor")
    assert light != dark
    page.locator("body").click(position={"x": 1, "y": 1})
    page.keyboard.press("Tab")
    focus_style = page.evaluate(
        """() => ({
          outline: getComputedStyle(document.activeElement).outlineStyle,
          width: getComputedStyle(document.activeElement).outlineWidth,
        })"""
    )
    assert focus_style["outline"] != "none"
    assert focus_style["width"] != "0px"


def test_negative_control_page_is_rejected(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/negative-control.html")
    report = measure_layout(page)
    kinds = {issue.kind for issue in report.issues}
    assert "clipped-label" in kinds
    assert {"hit-test", "overlay-occlusion"} & kinds
    with pytest.raises(AssertionError, match="negative-control failed"):
        assert_layout(report, label="negative-control")
