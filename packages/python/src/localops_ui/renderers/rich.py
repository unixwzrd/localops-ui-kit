"""Rich renderer with deterministic non-interactive behavior."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from io import StringIO
from typing import Any, TextIO

from ..adapters import AdapterRegistry
from ..compiler import Backend, LayoutCompiler
from ..models import (
    ButtonSpec,
    ChartSpec,
    CopyControlSpec,
    DataTableSpec,
    DialogSpec,
    DisclosureSpec,
    GridSpec,
    NodeSpec,
    NumberFieldSpec,
    PanelSpec,
    PathFieldSpec,
    RowSpec,
    SliderFieldSpec,
    StackSpec,
    StateViewSpec,
    StatusBadgeSpec,
    TabsSpec,
    TaskMonitorSpec,
    TextSpec,
    UIEvent,
    UISnapshot,
)
from ..state import UIState


def _rich() -> tuple[Any, ...]:
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import BarColumn, Progress, TextColumn
        from rich.prompt import Confirm, FloatPrompt, Prompt
        from rich.table import Table
        from rich.text import Text
    except ImportError as error:  # pragma: no cover - exercised by dependency-boundary tests
        raise RuntimeError("Install localops-ui[cli] to use the Rich renderer") from error
    return Console, Panel, Progress, BarColumn, TextColumn, Confirm, FloatPrompt, Prompt, Table, Text


class RichRenderer:
    def __init__(
        self,
        *,
        console: Any | None = None,
        interactive: bool | None = None,
        input_stream: TextIO | None = None,
    ) -> None:
        Console, *_ = _rich()
        self.console = console or Console()
        self.interactive = self.console.is_terminal if interactive is None else interactive
        self.input_stream = input_stream

    async def render(self, snapshot: UISnapshot, registry: AdapterRegistry | None = None) -> None:
        LayoutCompiler().compile(snapshot.spec, Backend.RICH)
        registry = registry or AdapterRegistry()
        self.ui_state = UIState(snapshot.spec, dict(snapshot.state), snapshot.revision)
        page_id = snapshot.spec.initial_page_id or snapshot.spec.pages[0].id
        page = next(page for page in snapshot.spec.pages if page.id == page_id)
        self.console.rule(page.title)
        await self._render_node(page.body, snapshot, registry)

    async def _render_node(self, node: NodeSpec, snapshot: UISnapshot, registry: AdapterRegistry) -> None:
        Console, Panel, Progress, BarColumn, TextColumn, Confirm, FloatPrompt, Prompt, Table, Text = _rich()
        if isinstance(node, TextSpec):
            style = {"heading": "bold", "muted": "dim", "code": "cyan"}.get(node.style)
            self.console.print(node.text, style=style)
        elif isinstance(node, StatusBadgeSpec):
            styles = {"neutral": "", "info": "blue", "success": "green", "warning": "yellow", "danger": "red"}
            self.console.print(Text(f"[{node.label}]", style=styles[node.tone]))
        elif isinstance(node, StateViewSpec):
            style = {"error": "red", "warning": "yellow", "loading": "blue", "empty": "dim"}[node.kind]
            self.console.print(Panel(node.message or "", title=node.title, border_style=style))
        elif isinstance(node, ButtonSpec):
            label = f"{node.icon} {node.label}" if node.icon else node.label
            self.console.print(f"[{label}]", style="dim" if node.disabled else "bold")
        elif isinstance(node, DialogSpec):
            self.console.print(f"[{node.trigger_label}]", style="bold")
            if self.interactive:
                if node.kind == "alert":
                    self.console.print(Panel(node.description or "", title=node.title))
                    result: Any = True
                elif node.kind == "confirm":
                    result = Confirm.ask(node.title, console=self.console, stream=self.input_stream)
                else:
                    default = str(snapshot.state.get(node.default_value_key or "", ""))
                    result = Prompt.ask(node.title, default=default, console=self.console, stream=self.input_stream)
                if node.result_key:
                    await self._change(node.id, "dialog_result", node.result_key, result, registry, node.command_id)
        elif isinstance(node, CopyControlSpec):
            self.console.print(str(snapshot.state.get(node.value_key, "")))
        elif isinstance(node, (NumberFieldSpec, SliderFieldSpec)):
            value = snapshot.state.get(node.value_key, node.minimum or 0)
            self.console.print(f"{node.label}: {value}{node.suffix or ''}")
            if self.interactive:
                updated = FloatPrompt.ask(
                    node.label, default=float(value), console=self.console, stream=self.input_stream
                )
                await self._change(node.id, "value_changed", node.value_key, updated, registry)
        elif isinstance(node, PathFieldSpec):
            value = str(snapshot.state.get(node.value_key, ""))
            if self.interactive:
                value = Prompt.ask(node.label, default=value, console=self.console, stream=self.input_stream)
                await self._change(node.id, "value_changed", node.value_key, value, registry)
            adapter = registry.paths.get(node.adapter_id)
            if adapter is not None:
                resolution = await adapter.resolve(value, node.kind)
                status = "valid" if resolution.valid else "invalid"
                self.console.print(f"{node.label}: {resolution.resolved} [{status}]")
            else:
                self.console.print(f"{node.label}: {value}")
        elif isinstance(node, DataTableSpec):
            table = Table(title=node.caption)
            for column in node.columns:
                if column.visible:
                    table.add_column(
                        column.label, justify={"start": "left", "center": "center", "end": "right"}[column.align]
                    )
            rows = snapshot.state.get(node.rows_key, [])
            if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
                self.console.print("Invalid table data", style="red")
            else:
                visible = [column for column in node.columns if column.visible]
                for row in rows:
                    table.add_row(*(str(row.get(column.value_key, "")) for column in visible))
            self.console.print(table)
        elif isinstance(node, TaskMonitorSpec):
            adapter = registry.tasks.get(node.adapter_id)
            value = (
                (await adapter.get_snapshot()).model_dump() if adapter is not None else snapshot.state.get(node.id, {})
            )
            task = value if isinstance(value, Mapping) else {}
            progress = Progress(
                TextColumn("{task.description}"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
                console=self.console,
            )
            progress.add_task(str(task.get("label", "Task")), total=100, completed=float(task.get("progress") or 0))
            self.console.print(progress)
            if task.get("log"):
                self.console.print(str(task["log"]))
        elif isinstance(node, ChartSpec):
            dataset = snapshot.state.get(node.dataset_key)
            if not isinstance(dataset, Mapping) or not dataset.get("points"):
                self.console.print("No chart data", style="dim")
            else:
                chart = Table(title=str(dataset.get("title", "Chart")))
                chart.add_column("Label")
                chart.add_column("Value", justify="right")
                for point in dataset.get("points", []):
                    if isinstance(point, Mapping):
                        chart.add_row(str(point.get("label", "")), str(point.get("value", "—")))
                self.console.print(chart)
        elif isinstance(node, TabsSpec):
            for tab in node.tabs:
                self.console.rule(tab.label, style="dim")
                for child in tab.children:
                    await self._render_node(child, snapshot, registry)
        elif isinstance(node, DisclosureSpec):
            self.console.rule(node.title, style="dim")
            for child in node.children:
                await self._render_node(child, snapshot, registry)
        elif isinstance(node, PanelSpec):
            buffer = StringIO()
            original = self.console
            self.console = Console(file=buffer, force_terminal=False, width=original.width)
            try:
                for child in node.children:
                    await self._render_node(child, snapshot, registry)
            finally:
                self.console = original
            self.console.print(Panel(buffer.getvalue().rstrip(), title=node.title))
        elif isinstance(node, (StackSpec, RowSpec, GridSpec)):
            for child in node.children:
                await self._render_node(child, snapshot, registry)

    async def invoke(self, node: ButtonSpec, snapshot: UISnapshot, registry: AdapterRegistry) -> Any:
        state = UIState(snapshot.spec, dict(snapshot.state), snapshot.revision)
        event = UIEvent(
            event_id=f"cli-{snapshot.revision}-{node.id}",
            component_id=node.id,
            kind="command",
            command_id=node.command_id,
            revision=snapshot.revision,
        )
        return (await state.dispatch(event, registry)).result

    async def _change(
        self,
        component_id: str,
        kind: str,
        state_key: str | None,
        value: Any,
        registry: AdapterRegistry,
        command_id: str | None = None,
    ) -> Any:
        response = await self.ui_state.dispatch(
            UIEvent(
                event_id=f"cli-{self.ui_state.revision}-{component_id}",
                component_id=component_id,
                kind=kind,
                state_key=state_key,
                value=value,
                command_id=command_id,
                revision=self.ui_state.revision,
            ),
            registry,
        )
        return response.result


async def run_cli(snapshot: UISnapshot, *, registry: AdapterRegistry | None = None, **options: Any) -> None:
    await RichRenderer(**options).render(snapshot, registry)


def run_cli_sync(snapshot: UISnapshot, *, registry: AdapterRegistry | None = None, **options: Any) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(run_cli(snapshot, registry=registry, **options))
        return
    raise RuntimeError("run_cli_sync cannot run inside an active event loop; await run_cli instead")
