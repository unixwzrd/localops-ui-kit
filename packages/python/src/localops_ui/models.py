"""Versioned, backend-neutral public UI models."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

Tone = Literal["neutral", "info", "success", "warning", "danger"]
Identifier = Annotated[
    str,
    Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9._:-]*[A-Za-z0-9])?$"),
]
NonEmptyString = Annotated[str, Field(min_length=1)]


class FrozenJsonDict(dict[str, JsonValue]):
    """JSON object that preserves normal serialization while rejecting mutation."""

    def _immutable(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("public JSON state is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable

    def __deepcopy__(self, _memo: dict[int, object]) -> FrozenJsonDict:
        return self


def _freeze_json(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return FrozenJsonDict({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)  # type: ignore[return-value]
    return value


def mutable_json(value: JsonValue) -> JsonValue:
    """Return an internal mutable copy of a validated public JSON value."""
    if isinstance(value, dict):
        return {key: mutable_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [mutable_json(item) for item in value]  # type: ignore[arg-type]
    return value


class PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ContentPanelState(PublicModel):
    """Presentation-only snapshot for the direct native content panel."""

    open: bool
    expanded: bool


class TextSpec(PublicModel):
    type: Literal["text"] = "text"
    id: Identifier
    text: str
    style: Literal["body", "heading", "muted", "code"] = "body"


class StatusBadgeSpec(PublicModel):
    type: Literal["status_badge"] = "status_badge"
    id: Identifier
    label: NonEmptyString
    tone: Tone = "neutral"


class StateViewSpec(PublicModel):
    type: Literal["state_view"] = "state_view"
    id: Identifier
    kind: Literal["empty", "loading", "warning", "error"]
    title: NonEmptyString
    message: str | None = None
    action_id: str | None = None
    action_label: str | None = None


class ButtonSpec(PublicModel):
    type: Literal["button"] = "button"
    id: Identifier
    label: NonEmptyString
    command_id: Identifier
    variant: Literal["default", "primary", "danger", "quiet"] = "default"
    disabled: bool = False
    icon: str | None = None


class DialogSpec(PublicModel):
    type: Literal["dialog"] = "dialog"
    id: Identifier
    kind: Literal["alert", "confirm", "prompt"]
    trigger_label: NonEmptyString
    title: NonEmptyString
    description: str | None = None
    command_id: Identifier | None = None
    result_key: Identifier | None = None
    default_value_key: Identifier | None = None
    destructive: bool = False


class CopyControlSpec(PublicModel):
    type: Literal["copy_control"] = "copy_control"
    id: Identifier
    label: NonEmptyString = "Copy"
    value_key: Identifier


class NumberFieldSpec(PublicModel):
    type: Literal["number_field"] = "number_field"
    id: Identifier
    label: NonEmptyString
    value_key: Identifier
    minimum: float | None = None
    maximum: float | None = None
    step: float = Field(default=1, gt=0)
    suffix: str | None = None

    @model_validator(mode="after")
    def valid_range(self) -> NumberFieldSpec:
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class SliderFieldSpec(NumberFieldSpec):
    type: Literal["slider_field"] = "slider_field"
    minimum: float
    maximum: float


class PathFieldSpec(PublicModel):
    type: Literal["path_field"] = "path_field"
    id: Identifier
    label: NonEmptyString
    value_key: Identifier
    adapter_id: Identifier
    kind: Literal["file", "directory", "any"] = "any"
    allow_browse: bool = True
    allow_create: bool = False


class DataColumnSpec(PublicModel):
    id: Identifier
    label: NonEmptyString
    value_key: Identifier
    sortable: bool = False
    visible: bool = True
    width: int | None = Field(default=None, ge=80)
    align: Literal["start", "center", "end"] = "start"


class DataTableSpec(PublicModel):
    type: Literal["data_table"] = "data_table"
    id: Identifier
    caption: NonEmptyString
    columns: tuple[DataColumnSpec, ...]
    rows_key: Identifier
    row_key: Identifier
    preference_key: Identifier | None = None
    sort_command_id: Identifier | None = None
    client_sort: bool = False
    sort_locale: NonEmptyString | None = None
    empty_message: str = "No rows"

    @model_validator(mode="after")
    def unique_columns(self) -> DataTableSpec:
        ids = [column.id for column in self.columns]
        if len(ids) != len(set(ids)):
            raise ValueError("column IDs must be unique")
        if self.client_sort and self.sort_locale is None:
            raise ValueError("client_sort requires an explicit sort_locale")
        if self.client_sort and self.sort_command_id is not None:
            raise ValueError("client_sort and sort_command_id are mutually exclusive")
        return self


class TaskMonitorSpec(PublicModel):
    type: Literal["task_monitor"] = "task_monitor"
    id: Identifier
    adapter_id: Identifier
    cancel_command_id: Identifier | None = None
    retry_command_id: Identifier | None = None
    poll_interval_ms: int = Field(default=2000, ge=100)


class ChartPoint(PublicModel):
    label: str
    value: float | None


class ChartDataset(PublicModel):
    title: str
    points: tuple[ChartPoint, ...]
    unit: str | None = None


class ChartSpec(PublicModel):
    type: Literal["chart"] = "chart"
    id: Identifier
    dataset_key: Identifier
    description: str | None = None


class TabSpec(PublicModel):
    id: Identifier
    label: NonEmptyString
    children: tuple[NodeSpec, ...]


class TabsSpec(PublicModel):
    type: Literal["tabs"] = "tabs"
    id: Identifier
    tabs: tuple[TabSpec, ...]
    selected_key: Identifier | None = None
    aria_label: NonEmptyString = "Sections"

    @model_validator(mode="after")
    def valid_tabs(self) -> TabsSpec:
        ids = [tab.id for tab in self.tabs]
        if not ids:
            raise ValueError("tabs requires at least one tab")
        if len(ids) != len(set(ids)):
            raise ValueError("tab IDs must be unique")
        return self


class DisclosureSpec(PublicModel):
    type: Literal["disclosure"] = "disclosure"
    id: Identifier
    title: NonEmptyString
    children: tuple[NodeSpec, ...]
    open_key: Identifier | None = None
    initially_open: bool = False


class StackSpec(PublicModel):
    type: Literal["stack"] = "stack"
    id: Identifier
    children: tuple[NodeSpec, ...]
    gap: Literal["none", "small", "medium", "large"] = "medium"


class RowSpec(PublicModel):
    type: Literal["row"] = "row"
    id: Identifier
    children: tuple[NodeSpec, ...]
    wrap: bool = True
    gap: Literal["none", "small", "medium", "large"] = "medium"


class GridSpec(PublicModel):
    type: Literal["grid"] = "grid"
    id: Identifier
    children: tuple[NodeSpec, ...]
    columns: int = Field(default=2, ge=1, le=12)
    gap: Literal["none", "small", "medium", "large"] = "medium"


class PanelSpec(PublicModel):
    type: Literal["panel"] = "panel"
    id: Identifier
    title: str | None = None
    children: tuple[NodeSpec, ...]


NodeSpec = Annotated[
    TextSpec
    | StatusBadgeSpec
    | StateViewSpec
    | ButtonSpec
    | DialogSpec
    | CopyControlSpec
    | NumberFieldSpec
    | SliderFieldSpec
    | PathFieldSpec
    | DataTableSpec
    | TaskMonitorSpec
    | ChartSpec
    | TabsSpec
    | DisclosureSpec
    | StackSpec
    | RowSpec
    | GridSpec
    | PanelSpec,
    Field(discriminator="type"),
]


class NavigationItemSpec(PublicModel):
    id: Identifier
    label: NonEmptyString
    command_id: Identifier | None = None


class PageSpec(PublicModel):
    id: Identifier
    title: NonEmptyString
    body: NodeSpec
    navigation: tuple[NavigationItemSpec, ...] = ()


class UISpec(PublicModel):
    schema_version: Literal["1"] = "1"
    id: Identifier
    pages: tuple[PageSpec, ...]
    initial_page_id: Identifier | None = None

    @model_validator(mode="after")
    def valid_pages_and_ids(self) -> UISpec:
        page_ids = [page.id for page in self.pages]
        if not page_ids:
            raise ValueError("UI requires at least one page")
        if len(page_ids) != len(set(page_ids)):
            raise ValueError("page IDs must be unique")
        if self.initial_page_id is not None and self.initial_page_id not in page_ids:
            raise ValueError("initial_page_id must reference a page")
        seen: set[str] = set(page_ids)
        for page in self.pages:
            for item in page.navigation:
                if item.id in seen:
                    raise ValueError(f"duplicate public ID: {item.id}")
                seen.add(item.id)
            for component_id in _component_ids(page.body):
                if component_id in seen:
                    raise ValueError(f"duplicate public ID: {component_id}")
                seen.add(component_id)
        return self


def _component_ids(node: NodeSpec) -> list[str]:
    result = [node.id]
    if isinstance(node, (StackSpec, RowSpec, GridSpec, PanelSpec, DisclosureSpec)):
        for child in node.children:
            result.extend(_component_ids(child))
    elif isinstance(node, TabsSpec):
        for tab in node.tabs:
            result.append(tab.id)
            for child in tab.children:
                result.extend(_component_ids(child))
    return result


class UISnapshot(PublicModel):
    schema_version: Literal["1"] = "1"
    revision: int = Field(ge=0)
    spec: UISpec
    state: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator("state", mode="after")
    @classmethod
    def freeze_state(cls, state: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return FrozenJsonDict({key: _freeze_json(value) for key, value in state.items()})

    @model_validator(mode="after")
    def valid_state_keys(self) -> UISnapshot:
        for key in self.state:
            if not key or len(key) > 128:
                raise ValueError("state keys must be non-empty and no longer than 128 characters")
        return self


class StatePatch(PublicModel):
    schema_version: Literal["1"] = "1"
    base_revision: int = Field(ge=0)
    revision: int = Field(ge=0)
    changes: dict[str, JsonValue] = Field(default_factory=dict)
    removed: tuple[str, ...] = ()

    @field_validator("changes", mode="after")
    @classmethod
    def freeze_changes(cls, changes: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return FrozenJsonDict({key: _freeze_json(value) for key, value in changes.items()})

    @model_validator(mode="after")
    def revision_advances(self) -> StatePatch:
        if self.revision <= self.base_revision:
            raise ValueError("patch revision must advance")
        if len(self.removed) != len(set(self.removed)):
            raise ValueError("removed state keys must be unique")
        if set(self.changes) & set(self.removed):
            raise ValueError("a state key cannot be changed and removed in the same patch")
        return self


class UIEvent(PublicModel):
    schema_version: Literal["1"] = "1"
    event_id: Identifier
    component_id: Identifier
    kind: Literal["command", "value_changed", "selection_changed", "layout_changed", "dialog_result"]
    command_id: Identifier | None = None
    state_key: Identifier | None = None
    value: JsonValue = None
    revision: int = Field(ge=0)

    @field_validator("value", mode="after")
    @classmethod
    def freeze_value(cls, value: JsonValue) -> JsonValue:
        return _freeze_json(value)

    @model_validator(mode="after")
    def valid_command(self) -> UIEvent:
        if self.kind == "command" and self.command_id is None:
            raise ValueError("command events require command_id")
        return self


class UITransportResponse(PublicModel):
    """Closed event response carrying both command data and an advancing update."""

    schema_version: Literal["1"] = "1"
    result: JsonValue = None
    update: UISnapshot | StatePatch

    @field_validator("result", mode="after")
    @classmethod
    def freeze_result(cls, result: JsonValue) -> JsonValue:
        return _freeze_json(result)


class TaskSnapshot(PublicModel):
    id: Identifier
    phase: Literal["idle", "pending", "running", "succeeded", "failed", "cancelled"]
    label: str
    progress: float | None = Field(default=None, ge=0, le=100)
    message: str | None = None
    log: str | None = None
    updated_at: str | None = None


class PathResolution(PublicModel):
    input: str
    resolved: str
    exists: bool
    valid: bool
    kind: Literal["file", "directory", "any"] | None = None
    message: str | None = None


class PathEntry(PublicModel):
    name: str
    path: str
    kind: Literal["file", "directory"]


class PathListing(PublicModel):
    path: str
    parent: str | None = None
    entries: tuple[PathEntry, ...] = ()


class ArtifactDescriptor(PublicModel):
    id: Identifier
    label: str
    media_type: str | None = None
    size: int | None = Field(default=None, ge=0)
