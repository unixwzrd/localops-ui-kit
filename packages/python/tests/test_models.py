import pytest
from localops_ui.compiler import Backend, LayoutCompiler, Support
from localops_ui.gallery import operator_workspace_snapshot
from localops_ui.models import ContentPanelState, PageSpec, StackSpec, StatePatch, TextSpec, UISpec
from pydantic import ValidationError


def test_snapshot_round_trips_through_json() -> None:
    snapshot = operator_workspace_snapshot()
    restored = type(snapshot).model_validate_json(snapshot.model_dump_json())
    assert restored == snapshot


def test_content_panel_state_is_closed_strict_and_frozen() -> None:
    state = ContentPanelState.model_validate_json('{"open":true,"expanded":false}')
    assert state.open and not state.expanded
    with pytest.raises(ValidationError):
        ContentPanelState(open=1, expanded=False)
    with pytest.raises(ValidationError):
        ContentPanelState.model_validate({"open": True, "expanded": False, "route": "not-owned"})
    with pytest.raises(ValidationError):
        state.open = False


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        TextSpec.model_validate({"type": "text", "id": "message", "text": "Hello", "classes": "q-pa-md"})


def test_public_models_reject_coercion_and_empty_identity() -> None:
    with pytest.raises(ValidationError):
        StatePatch(base_revision=False, revision=1)
    with pytest.raises(ValidationError):
        TextSpec(id="", text="Hello")


def test_duplicate_component_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate public ID"):
        UISpec(
            id="duplicate",
            pages=(
                PageSpec(
                    id="page",
                    title="Duplicate",
                    body=StackSpec(
                        id="root",
                        children=(TextSpec(id="same", text="One"), TextSpec(id="same", text="Two")),
                    ),
                ),
            ),
        )


def test_all_backends_compile_with_declared_fallbacks() -> None:
    snapshot = operator_workspace_snapshot()
    for backend in Backend:
        plan = LayoutCompiler().compile(snapshot.spec, backend)
        assert plan.roots
        assert all(item.support is not Support.UNSUPPORTED for item in plan.capabilities)
    rich = LayoutCompiler().compile(snapshot.spec, Backend.RICH)
    assert any(item.support is Support.FALLBACK for item in rich.capabilities)


def test_web_assets_are_exposed_as_safe_resources() -> None:
    from localops_ui import web_asset, web_assets

    assert web_assets().is_dir()
    assert web_asset("index.js").read_text(encoding="utf-8").startswith("export *")
    with pytest.raises(ValueError, match="safe relative path"):
        web_asset("../README.md")
    with pytest.raises(FileNotFoundError):
        web_asset("missing.js")
