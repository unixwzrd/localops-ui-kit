import pytest

from localops_ui_testkit import assert_layout, measure_layout


@pytest.mark.parametrize(
    ("name", "viewport"),
    [
        ("desktop", {"width": 1440, "height": 900}),
        ("tablet", {"width": 820, "height": 1024}),
        ("mobile", {"width": 390, "height": 844}),
    ],
)
def test_gallery_layout_oracle_passes_supported_viewports(page, gallery_url, name, viewport) -> None:
    page.set_viewport_size(viewport)
    page.goto(gallery_url)
    page.wait_for_selector(".lui-shell")
    assert_layout(measure_layout(page, mode="static"), label=f"{name}-static")
    assert_layout(measure_layout(page, mode="reachability"), label=f"{name}-reachability")


def test_negative_control_rejects_fixed_overlay_and_clipped_label(page) -> None:
    page.set_content(
        """
        <style>
          .covered { position: fixed; left: 20px; bottom: 20px; }
          .overlay { position: fixed; left: 0; right: 0; bottom: 0; height: 100px; background: red; z-index: 10; }
          .clipped { display: block; width: 40px; white-space: nowrap; overflow: hidden; }
        </style>
        <main data-layout-pane><label data-layout-label class="clipped">permanently clipped label</label>
        <button class="covered">covered</button></main><div class="overlay">bad overlay</div>
        """
    )
    report = measure_layout(page)
    kinds = {issue.kind for issue in report.issues}
    assert "clipped-label" in kinds
    assert "hit-test" in kinds or "overlay-occlusion" in kinds
    try:
        assert_layout(report, label="negative-control")
    except AssertionError:
        return
    raise AssertionError("negative control must be rejected")


def test_undersized_modal_overlay_does_not_hide_operable_background(page) -> None:
    page.set_content(
        """
        <button id="background">Background action</button>
        <div style="position:fixed;left:300px;top:200px;width:240px;height:160px;background:white">
          <section role="dialog" aria-modal="true" aria-labelledby="title">
            <h2 id="title">Incomplete modal</h2><button>OK</button>
          </section>
        </div>
        """
    )
    report = measure_layout(page)
    assert "modal-background-operable" in {issue.kind for issue in report.issues}
