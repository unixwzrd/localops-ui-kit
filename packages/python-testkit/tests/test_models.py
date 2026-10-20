from localops_ui_testkit import LayoutReport, Viewport


def test_report_passed_is_derived_from_issues() -> None:
    report = LayoutReport(viewport=Viewport(width=1280, height=720), mode="static", modal={"open": False, "roots": ()})
    assert report.passed


def test_report_rejects_unknown_public_fields() -> None:
    try:
        LayoutReport.model_validate(
            {
                "viewport": {"width": 1, "height": 1},
                "mode": "static",
                "modal": {"open": False},
                "issues": (),
                "extra": True,
            }
        )
    except ValueError:
        return
    raise AssertionError("unknown report fields must be rejected")
