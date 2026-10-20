"""Application-supplied behavior contracts."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Protocol

from .models import ArtifactDescriptor, JsonValue, PathListing, PathResolution, TaskSnapshot, UIEvent


class PathAdapter(Protocol):
    async def resolve(self, path: str, kind: str) -> PathResolution: ...

    async def browse(self, path: str, kind: str) -> PathListing: ...

    async def create(self, path: str, kind: str) -> PathResolution: ...


class TaskAdapter(Protocol):
    async def get_snapshot(self) -> TaskSnapshot: ...


class TaskSubscriptionAdapter(TaskAdapter, Protocol):
    def subscribe(self) -> AsyncIterator[TaskSnapshot]: ...


class TaskCancelAdapter(TaskAdapter, Protocol):
    async def cancel(self) -> None: ...


class TaskRetryAdapter(TaskAdapter, Protocol):
    async def retry(self) -> None: ...


class PreferenceStore(Protocol):
    async def load(self, key: str) -> JsonValue: ...

    async def save(self, key: str, value: JsonValue) -> None: ...


class ArtifactProvider(Protocol):
    async def list(self) -> tuple[ArtifactDescriptor, ...]: ...

    async def open(self, artifact_id: str) -> bytes | str: ...


class DataProvider(Protocol):
    async def load(self, key: str) -> JsonValue: ...


CommandHandler = Callable[[UIEvent], Awaitable[JsonValue] | JsonValue]


class AdapterRegistry:
    """Explicit, instance-local registry; no import-time global state."""

    def __init__(self) -> None:
        self.paths: dict[str, PathAdapter] = {}
        self.tasks: dict[str, TaskAdapter] = {}
        self.preferences: dict[str, PreferenceStore] = {}
        self.artifacts: dict[str, ArtifactProvider] = {}
        self.data: dict[str, DataProvider] = {}
        self.commands: dict[str, CommandHandler] = {}

    def register(self, category: str, adapter_id: str, adapter: Any) -> None:
        target = getattr(self, category, None)
        if not isinstance(target, dict):
            raise ValueError(f"unknown adapter category: {category}")
        if adapter_id in target:
            raise ValueError(f"duplicate {category} adapter ID: {adapter_id}")
        target[adapter_id] = adapter
