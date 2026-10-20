"""Revisioned UI state and command dispatch."""

from __future__ import annotations

import inspect
from copy import deepcopy
from dataclasses import dataclass, field

from pydantic import TypeAdapter

from .adapters import AdapterRegistry
from .models import JsonValue, StatePatch, UIEvent, UISnapshot, UISpec, UITransportResponse, mutable_json

_JSON_VALUE = TypeAdapter(JsonValue, config={"strict": True})


class StaleRevisionError(ValueError):
    pass


@dataclass(slots=True)
class UIState:
    spec: UISpec
    values: dict[str, JsonValue] = field(default_factory=dict)
    revision: int = 0

    def __post_init__(self) -> None:
        self.values = {key: mutable_json(value) for key, value in self.values.items()}

    def snapshot(self) -> UISnapshot:
        return UISnapshot(revision=self.revision, spec=self.spec, state=deepcopy(self.values))

    def apply(self, patch: StatePatch) -> None:
        if patch.base_revision != self.revision:
            raise StaleRevisionError(f"expected base revision {self.revision}, received {patch.base_revision}")
        self.values.update({key: mutable_json(value) for key, value in patch.changes.items()})
        for key in patch.removed:
            self.values.pop(key, None)
        self.revision = patch.revision

    async def dispatch(self, event: UIEvent, registry: AdapterRegistry) -> UITransportResponse:
        if event.revision != self.revision:
            raise StaleRevisionError(f"event revision {event.revision} does not match {self.revision}")
        base_revision = self.revision
        before = deepcopy(self.values)
        try:
            state_event = event.kind in {"value_changed", "selection_changed", "layout_changed", "dialog_result"}
            state_updated = False
            result: JsonValue = event.value
            if state_event:
                if event.state_key:
                    self.values[event.state_key] = mutable_json(event.value)
                    self.revision += 1
                    state_updated = True
                if not event.command_id:
                    if not state_updated:
                        self.revision += 1
                    return self._response(base_revision, before, result)
            if event.command_id:
                if event.command_id not in registry.commands:
                    raise KeyError(f"unknown command ID: {event.command_id}")
                command_result = registry.commands[event.command_id](event)
                if inspect.isawaitable(command_result):
                    command_result = await command_result
                result = _JSON_VALUE.validate_python(command_result)
                if not state_updated:
                    self.revision += 1
            else:
                raise KeyError("command event requires command_id")
            return self._response(base_revision, before, result)
        except Exception:
            self.values = before
            self.revision = base_revision
            raise

    def _response(self, base_revision: int, before: dict[str, JsonValue], result: JsonValue) -> UITransportResponse:
        changes = {
            key: deepcopy(value) for key, value in self.values.items() if key not in before or before[key] != value
        }
        removed = tuple(key for key in before if key not in self.values)
        patch = StatePatch(
            base_revision=base_revision,
            revision=self.revision,
            changes=changes,
            removed=removed,
        )
        return UITransportResponse(result=deepcopy(result), update=patch)
