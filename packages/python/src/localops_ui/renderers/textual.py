"""Textual renderer for the shared semantic specification."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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
    TaskSnapshot,
    TextSpec,
    UIEvent,
    UISnapshot,
)
from ..state import UIState

try:
    from textual.app import App, ComposeResult
    from textual.containers import Grid, Horizontal, Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Button, Collapsible, DataTable, Footer, Header, Input, Label, ProgressBar, Static
except ImportError as error:  # pragma: no cover
    raise RuntimeError("Install localops-ui[tui] to use the Textual renderer") from error


class LocalOpsTextualApp(App[None]):
    """Generic Textual host; consumers subclass or pass registries, never services."""

    CSS = """
    .localops-row { layout: horizontal; height: auto; }
    .localops-stack { height: auto; }
    .localops-panel { border: round $primary; padding: 1; height: auto; }
    .localops-danger { color: $error; }
    .localops-warning { color: $warning; }
    """

    def __init__(self, snapshot: UISnapshot, registry: AdapterRegistry | None = None) -> None:
        LayoutCompiler().compile(snapshot.spec, Backend.TEXTUAL)
        super().__init__()
        self.snapshot = snapshot
        self.registry = registry or AdapterRegistry()
        self.ui_state = UIState(snapshot.spec, dict(snapshot.state), snapshot.revision)
        self.dialogs: dict[str, DialogSpec] = {}
        self.buttons: dict[str, ButtonSpec] = {}
        self.inputs: dict[str, str] = {}
        self.tasks: dict[str, TaskMonitorSpec] = {}
        self.paths: dict[str, PathFieldSpec] = {}

    def compose(self) -> ComposeResult:
        page_id = self.snapshot.spec.initial_page_id or self.snapshot.spec.pages[0].id
        page = next(page for page in self.snapshot.spec.pages if page.id == page_id)
        yield Header(show_clock=False)
        yield Static(page.title, classes="localops-title")
        yield self._widget(page.body)
        yield Footer()

    def _widget(self, node: NodeSpec) -> Any:
        if isinstance(node, TextSpec):
            return Static(node.text)
        if isinstance(node, StatusBadgeSpec):
            return Label(f"[{node.label}]", classes=f"localops-{node.tone}")
        if isinstance(node, StateViewSpec):
            return Static(f"{node.title}\n{node.message or ''}", classes=f"localops-{node.kind}")
        if isinstance(node, ButtonSpec):
            self.buttons[node.id] = node
            return Button(
                f"{node.icon} {node.label}" if node.icon else node.label,
                name=f"command:{node.id}",
                disabled=node.disabled,
                variant="error" if node.variant == "danger" else "default",
            )
        if isinstance(node, DialogSpec):
            self.dialogs[node.id] = node
            return Button(
                node.trigger_label, name=f"dialog:{node.id}", variant="error" if node.destructive else "default"
            )
        if isinstance(node, CopyControlSpec):
            return Static(str(self.ui_state.values.get(node.value_key, "")))
        if isinstance(node, SliderFieldSpec):
            # Textual's numeric Input preserves exact shared validation and works at narrow widths.
            self.inputs[node.id] = node.value_key
            return Input(
                value=str(self.ui_state.values.get(node.value_key, node.minimum)),
                placeholder=node.label,
                type="number",
                name=f"state:{node.id}",
            )
        if isinstance(node, NumberFieldSpec):
            self.inputs[node.id] = node.value_key
            return Input(
                value=str(self.ui_state.values.get(node.value_key, node.minimum or 0)),
                placeholder=node.label,
                type="number",
                name=f"state:{node.id}",
            )
        if isinstance(node, PathFieldSpec):
            self.inputs[node.id] = node.value_key
            self.paths[node.id] = node
            actions: list[Any] = [Button("Resolve", name=f"path-resolve:{node.id}")]
            if node.allow_browse:
                actions.append(Button("Browse", name=f"path-browse:{node.id}"))
            if node.allow_create and node.kind != "any":
                actions.append(Button("Create", name=f"path-create:{node.id}"))
            return Vertical(
                Label(node.label),
                Input(
                    value=str(self.ui_state.values.get(node.value_key, "")),
                    placeholder=node.label,
                    name=f"state:{node.id}",
                ),
                Horizontal(*actions),
                Static("", name=f"path-status:{node.id}"),
            )
        if isinstance(node, DataTableSpec):
            table: DataTable[Any] = DataTable(name=node.id)
            visible = [column for column in node.columns if column.visible]
            table.add_columns(*(column.label for column in visible))
            rows = self.ui_state.values.get(node.rows_key, [])
            if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
                table.add_column("Error")
                table.add_row("Invalid table data")
            else:
                for row in rows:
                    table.add_row(
                        *(str(row.get(column.value_key, "")) for column in visible),
                        key=str(row.get(node.row_key, "")),
                    )
            return table
        if isinstance(node, TaskMonitorSpec):
            self.tasks[node.id] = node
            value = self.ui_state.values.get(node.id, {})
            task = value if isinstance(value, Mapping) else {}
            progress = ProgressBar(total=100, name=f"task-progress:{node.id}")
            progress.progress = float(task.get("progress") or 0)
            actions: list[Any] = []
            if node.cancel_command_id:
                actions.append(Button("Cancel", name=f"task-cancel:{node.id}"))
            if node.retry_command_id:
                actions.append(Button("Retry", name=f"task-retry:{node.id}"))
            return Vertical(
                Label(str(task.get("label", "Task")), name=f"task-label:{node.id}"),
                progress,
                Horizontal(*actions),
                Static(str(task.get("log", "")), name=f"task-log:{node.id}"),
            )
        if isinstance(node, ChartSpec):
            dataset = self.ui_state.values.get(node.dataset_key, {})
            if not isinstance(dataset, Mapping) or not dataset.get("points"):
                return Static("No chart data")
            lines = [
                f"{point.get('label', '')}: {point.get('value', '—')}"
                for point in dataset.get("points", [])
                if isinstance(point, Mapping)
            ]
            return Static("\n".join(lines))
        if isinstance(node, TabsSpec):
            sections = []
            for tab in node.tabs:
                sections.append(Collapsible(*(self._widget(child) for child in tab.children), title=tab.label))
            return Vertical(*sections, classes="localops-stack")
        if isinstance(node, DisclosureSpec):
            return Collapsible(
                *(self._widget(child) for child in node.children), title=node.title, collapsed=not node.initially_open
            )
        if isinstance(node, PanelSpec):
            children = [Label(node.title)] if node.title else []
            children.extend(self._widget(child) for child in node.children)
            return Vertical(*children, classes="localops-panel")
        if isinstance(node, RowSpec):
            return Horizontal(*(self._widget(child) for child in node.children), classes="localops-row")
        if isinstance(node, GridSpec):
            grid = Grid(*(self._widget(child) for child in node.children), classes="localops-stack")
            grid.styles.grid_size_columns = node.columns
            return grid
        if isinstance(node, StackSpec):
            return Vertical(*(self._widget(child) for child in node.children), classes="localops-stack")
        raise TypeError(f"unsupported node: {type(node).__name__}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        name = event.button.name or ""
        if name.startswith("dialog:"):
            spec = self.dialogs[name.removeprefix("dialog:")]
            result = await self.push_screen_wait(LocalOpsDialogScreen(spec, self.ui_state.values))
            await self.ui_state.dispatch(
                UIEvent(
                    event_id=f"tui-{self.ui_state.revision}-{spec.id}",
                    component_id=spec.id,
                    kind="dialog_result",
                    command_id=spec.command_id,
                    state_key=spec.result_key,
                    value=result,
                    revision=self.ui_state.revision,
                ),
                self.registry,
            )
        elif name.startswith("command:"):
            spec = self.buttons[name.removeprefix("command:")]
            await self.ui_state.dispatch(
                UIEvent(
                    event_id=f"tui-{self.ui_state.revision}-{spec.id}",
                    component_id=spec.id,
                    kind="command",
                    command_id=spec.command_id,
                    revision=self.ui_state.revision,
                ),
                self.registry,
            )
        elif name.startswith("task-cancel:") or name.startswith("task-retry:"):
            operation, task_id = name.removeprefix("task-").split(":", 1)
            spec = self.tasks[task_id]
            adapter = self.registry.tasks.get(spec.adapter_id)
            if adapter is None:
                raise KeyError(f"unknown task adapter ID: {spec.adapter_id}")
            command_id = spec.cancel_command_id if operation == "cancel" else spec.retry_command_id
            await self.ui_state.dispatch(
                UIEvent(
                    event_id=f"tui-{self.ui_state.revision}-{task_id}-{operation}",
                    component_id=task_id,
                    kind="command",
                    command_id=command_id,
                    revision=self.ui_state.revision,
                ),
                self.registry,
            )
            await self._update_task(task_id, await adapter.get_snapshot())
        elif name.startswith("path-"):
            operation, path_id = name.removeprefix("path-").split(":", 1)
            spec = self.paths[path_id]
            adapter = self.registry.paths.get(spec.adapter_id)
            if adapter is None:
                raise KeyError(f"unknown path adapter ID: {spec.adapter_id}")
            control = self.query_one(f'Input[name="state:{path_id}"]', Input)
            status = self.query_one(f'Static[name="path-status:{path_id}"]', Static)
            if operation == "resolve":
                resolution = await adapter.resolve(control.value, spec.kind)
                status.update(resolution.message or resolution.resolved)
            elif operation == "browse" and hasattr(adapter, "browse"):
                listing = await adapter.browse(control.value, spec.kind)
                control.value = listing.path
                status.update(listing.path)
            elif operation == "create" and hasattr(adapter, "create"):
                resolution = await adapter.create(control.value, spec.kind)
                status.update(resolution.message or resolution.resolved)

    async def on_input_changed(self, event: Input.Changed) -> None:
        name = event.input.name or ""
        if not name.startswith("state:"):
            return
        component_id = name.removeprefix("state:")
        value: Any = event.value
        if event.input.type == "number" and event.value:
            try:
                value = float(event.value)
            except ValueError:
                return
        await self.ui_state.dispatch(
            UIEvent(
                event_id=f"tui-{self.ui_state.revision}-{component_id}",
                component_id=component_id,
                kind="value_changed",
                state_key=self.inputs[component_id],
                value=value,
                revision=self.ui_state.revision,
            ),
            self.registry,
        )

    async def on_mount(self) -> None:
        for task_id, spec in self.tasks.items():
            adapter = self.registry.tasks.get(spec.adapter_id)
            if adapter is None:
                continue
            await self._update_task(task_id, await adapter.get_snapshot())
            if hasattr(adapter, "subscribe"):
                self.run_worker(self._follow_task(task_id, adapter), group=f"task:{task_id}", exclusive=True)

    async def _follow_task(self, task_id: str, adapter: Any) -> None:
        async for update in adapter.subscribe():
            await self._update_task(task_id, update)

    async def _update_task(self, task_id: str, snapshot: TaskSnapshot) -> None:
        await self.ui_state.dispatch(
            UIEvent(
                event_id=f"tui-{self.ui_state.revision}-{task_id}-update",
                component_id=task_id,
                kind="value_changed",
                state_key=task_id,
                value=snapshot.model_dump(mode="json"),
                revision=self.ui_state.revision,
            ),
            self.registry,
        )
        self.query_one(f'Label[name="task-label:{task_id}"]', Label).update(snapshot.label)
        self.query_one(f'ProgressBar[name="task-progress:{task_id}"]', ProgressBar).update(
            progress=snapshot.progress or 0
        )
        self.query_one(f'Static[name="task-log:{task_id}"]', Static).update(snapshot.log or "")


class LocalOpsDialogScreen(ModalScreen[Any]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, spec: DialogSpec, state: Mapping[str, Any]) -> None:
        super().__init__()
        self.spec = spec
        self.state = state

    def compose(self) -> ComposeResult:
        controls: list[Any] = [Label(self.spec.title)]
        if self.spec.description:
            controls.append(Static(self.spec.description))
        if self.spec.kind == "prompt":
            controls.append(
                Input(value=str(self.state.get(self.spec.default_value_key or "", "")), name="dialog-value")
            )
        if self.spec.kind != "alert":
            controls.append(Button("Cancel", name="dialog-cancel"))
        controls.append(Button("OK", name="dialog-ok", variant="error" if self.spec.destructive else "primary"))
        yield Vertical(*controls, classes="localops-panel")

    def on_mount(self) -> None:
        prompt = self.query_one("Input", Input) if self.spec.kind == "prompt" else None
        (prompt or self.query_one('Button[name="dialog-ok"]', Button)).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.name == "dialog-cancel":
            self.dismiss(None if self.spec.kind == "prompt" else False)
        elif event.button.name == "dialog-ok":
            value = self.query_one("Input", Input).value if self.spec.kind == "prompt" else True
            self.dismiss(value)

    def action_cancel(self) -> None:
        self.dismiss(None if self.spec.kind == "prompt" else False)


def textual_app(snapshot: UISnapshot, registry: AdapterRegistry | None = None) -> LocalOpsTextualApp:
    return LocalOpsTextualApp(snapshot, registry)
