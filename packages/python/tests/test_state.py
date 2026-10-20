import pytest
from localops_ui.adapters import AdapterRegistry
from localops_ui.gallery import operator_workspace_snapshot
from localops_ui.models import StatePatch, UIEvent
from localops_ui.state import StaleRevisionError, UIState


def test_revisioned_patch_rejects_stale_base() -> None:
    snapshot = operator_workspace_snapshot()
    state = UIState(snapshot.spec, dict(snapshot.state))
    state.apply(StatePatch(base_revision=0, revision=1, changes={"workers": 8}))
    assert state.values["workers"] == 8
    with pytest.raises(StaleRevisionError):
        state.apply(StatePatch(base_revision=0, revision=2, changes={"workers": 9}))


@pytest.mark.asyncio
async def test_value_event_uses_explicit_state_key() -> None:
    snapshot = operator_workspace_snapshot()
    state = UIState(snapshot.spec, dict(snapshot.state))
    event = UIEvent(
        event_id="test-1",
        component_id="worker-count",
        state_key="workers",
        kind="value_changed",
        value=6,
        revision=0,
    )
    await state.dispatch(event, AdapterRegistry())
    assert state.values["workers"] == 6
    assert state.revision == 1


@pytest.mark.asyncio
async def test_command_registry_is_explicit_and_isolated() -> None:
    first = AdapterRegistry()
    second = AdapterRegistry()
    first.register("commands", "run", lambda event: {"source": event.component_id})
    assert "run" not in second.commands

    snapshot = operator_workspace_snapshot()
    state = UIState(snapshot.spec, dict(snapshot.state))
    response = await state.dispatch(
        UIEvent(
            event_id="test-2",
            component_id="run-action",
            command_id="run",
            kind="command",
            revision=0,
        ),
        first,
    )
    assert response.result == {"source": "run-action"}
    assert response.update.base_revision == 0
    assert response.update.revision == 1


def test_snapshot_state_is_detached_from_live_state() -> None:
    snapshot = operator_workspace_snapshot()
    state = UIState(snapshot.spec, dict(snapshot.state))
    detached = state.snapshot()
    with pytest.raises(TypeError, match="immutable"):
        detached.state["workers"] = 99
    assert state.values["workers"] == 4


@pytest.mark.asyncio
async def test_failed_command_rolls_back_state_and_revision() -> None:
    snapshot = operator_workspace_snapshot()
    state = UIState(snapshot.spec, dict(snapshot.state))
    registry = AdapterRegistry()

    def fail(_event: UIEvent) -> None:
        raise RuntimeError("rejected")

    registry.register("commands", "fail", fail)
    with pytest.raises(RuntimeError, match="rejected"):
        await state.dispatch(
            UIEvent(
                event_id="test-fail",
                component_id="worker-count",
                kind="value_changed",
                state_key="workers",
                value=9,
                command_id="fail",
                revision=0,
            ),
            registry,
        )
    assert state.values["workers"] == 4
    assert state.revision == 0
