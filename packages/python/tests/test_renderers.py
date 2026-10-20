import pytest
from localops_ui.adapters import AdapterRegistry
from localops_ui.gallery import operator_workspace_snapshot
from localops_ui.models import PathResolution, TaskSnapshot
from localops_ui.renderers.rich import RichRenderer, run_cli_sync
from localops_ui.web import manifest
from rich.console import Console


@pytest.mark.asyncio
async def test_rich_renderer_is_deterministic_without_tty() -> None:
    console = Console(record=True, force_terminal=False, width=60)
    await RichRenderer(console=console, interactive=False).render(operator_workspace_snapshot())
    output = console.export_text()
    assert "LocalOps Component Gallery" in output
    assert "Inputs" in output
    assert "Workers: 4" in output
    assert "Example records" in output
    assert "Processing" in output
    assert "Example values" in output


@pytest.mark.asyncio
async def test_rich_renderer_uses_registered_path_and_task_adapters() -> None:
    class Paths:
        async def resolve(self, path: str, kind: str) -> PathResolution:
            return PathResolution(input=path, resolved="/resolved/workspace", exists=True, valid=True, kind=kind)

    class Tasks:
        async def get_snapshot(self) -> TaskSnapshot:
            return TaskSnapshot(id="gallery-task", phase="succeeded", label="Adapter task", progress=100)

    registry = AdapterRegistry()
    registry.register("paths", "paths", Paths())
    registry.register("tasks", "tasks", Tasks())
    console = Console(record=True, force_terminal=False, width=60)
    await RichRenderer(console=console, interactive=False).render(operator_workspace_snapshot(), registry)
    output = console.export_text()
    assert "/resolved/workspace" in output
    assert "Adapter task" in output


@pytest.mark.asyncio
async def test_sync_cli_wrapper_rejects_active_loop() -> None:
    with pytest.raises(RuntimeError, match="active event loop"):
        run_cli_sync(operator_workspace_snapshot(), interactive=False)


def test_web_manifest_is_versioned() -> None:
    encoded = manifest(operator_workspace_snapshot())
    assert '"schema_version":"1"' in encoded
    assert '"component-gallery"' in encoded


@pytest.mark.asyncio
async def test_textual_gallery_composes() -> None:
    pytest.importorskip("textual")
    from localops_ui.renderers.textual import textual_app

    app = textual_app(operator_workspace_snapshot())
    async with app.run_test(size=(60, 24)) as pilot:
        await pilot.pause()
        assert app.query("Input")
        assert app.query("DataTable")
