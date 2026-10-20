"""Backend capability validation and layout compilation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import DisclosureSpec, GridSpec, NodeSpec, PanelSpec, RowSpec, StackSpec, TabsSpec, UISpec


class Backend(StrEnum):
    WEB = "web"
    TEXTUAL = "textual"
    RICH = "rich"


class Support(StrEnum):
    NATIVE = "native"
    FALLBACK = "fallback"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class Capability:
    component_type: str
    support: Support
    note: str | None = None


@dataclass(frozen=True, slots=True)
class RenderNode:
    component_id: str
    component_type: str
    children: tuple[RenderNode, ...] = ()


@dataclass(frozen=True, slots=True)
class RenderPlan:
    backend: Backend
    roots: tuple[RenderNode, ...]
    capabilities: tuple[Capability, ...]


class UnsupportedCapabilityError(ValueError):
    pass


_WEB_NATIVE = {
    "text",
    "status_badge",
    "state_view",
    "button",
    "copy_control",
    "number_field",
    "slider_field",
    "dialog",
    "path_field",
    "data_table",
    "task_monitor",
    "chart",
    "tabs",
    "disclosure",
    "stack",
    "row",
    "grid",
    "panel",
}
_TEXTUAL_NATIVE = _WEB_NATIVE - {"copy_control", "slider_field", "chart", "tabs"}
_RICH_NATIVE = {
    "text",
    "status_badge",
    "state_view",
    "button",
    "dialog",
    "number_field",
    "path_field",
    "data_table",
    "task_monitor",
    "stack",
    "panel",
}


def capability(backend: Backend, component_type: str) -> Capability:
    native = {Backend.WEB: _WEB_NATIVE, Backend.TEXTUAL: _TEXTUAL_NATIVE, Backend.RICH: _RICH_NATIVE}[backend]
    if component_type in native:
        return Capability(component_type, Support.NATIVE)
    if backend is Backend.TEXTUAL and component_type in {"copy_control", "slider_field", "chart", "tabs"}:
        return Capability(
            component_type,
            Support.FALLBACK,
            "Rendered with a terminal-native semantic fallback",
        )
    if backend is Backend.RICH and component_type in {
        "copy_control",
        "slider_field",
        "chart",
        "tabs",
        "disclosure",
        "row",
        "grid",
    }:
        return Capability(component_type, Support.FALLBACK, "Rendered as a sequential terminal representation")
    return Capability(component_type, Support.UNSUPPORTED)


class LayoutCompiler:
    def compile(self, spec: UISpec, backend: Backend) -> RenderPlan:
        capabilities: dict[str, Capability] = {}
        roots = []
        for page in spec.pages:
            root = self._node(page.body, backend, capabilities)
            roots.append(root)
        unsupported = [item for item in capabilities.values() if item.support is Support.UNSUPPORTED]
        if unsupported:
            names = ", ".join(sorted(item.component_type for item in unsupported))
            raise UnsupportedCapabilityError(f"{backend} cannot render: {names}")
        return RenderPlan(backend, tuple(roots), tuple(capabilities.values()))

    def _node(self, node: NodeSpec, backend: Backend, capabilities: dict[str, Capability]) -> RenderNode:
        current = capability(backend, node.type)
        capabilities[node.type] = current
        children: list[RenderNode] = []
        if isinstance(node, (StackSpec, RowSpec, GridSpec, PanelSpec, DisclosureSpec)):
            children.extend(self._node(child, backend, capabilities) for child in node.children)
        elif isinstance(node, TabsSpec):
            for tab in node.tabs:
                children.extend(self._node(child, backend, capabilities) for child in tab.children)
        return RenderNode(node.id, node.type, tuple(children))
