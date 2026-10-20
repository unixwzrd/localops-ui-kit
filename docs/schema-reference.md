# Python UI schema

The Python API is authoritative. Its strict Pydantic models serialize to versioned JSON for browser transport, persistence, fixtures, and external tooling.

## Envelope

`UISpec` contains pages and a schema version. `UISnapshot` combines a specification, revision, and recursively immutable JSON state. `StatePatch` advances one known revision and replaces or removes state keys. `UIEvent` carries a stable component ID, optional state or command ID, event kind, value, and originating revision. `UITransportResponse` closes the event round trip with a required advancing update and an optional JSON command result.

Unknown fields, coercive scalar inputs, empty or colliding public IDs, invalid page references, invalid numeric ranges, duplicate table columns, empty tab sets, malformed state rows/preferences, and stale or non-advancing revisions fail explicitly.

## Bindings

- `value_key` binds a component to JSON state.
- `command_id` resolves through an instance-local command registry.
- `adapter_id` identifies a consumer-supplied path or task adapter.
- `rows_key` and `dataset_key` reference already-derived data in state.
- `sort_command_id` delegates ordering to the application; `client_sort` requires an explicit `sort_locale` and is never enabled by default.
- Python callables, URLs, CSS classes, NiceGUI properties, and domain interpretation are not serialized.

## Layout

Applications compose explicit `StackSpec`, `RowSpec`, `GridSpec`, `PanelSpec`, `TabsSpec`, and `DisclosureSpec` trees. The internal layout compiler validates the tree against WebUI, Textual, or Rich capabilities; there is no mutable public pack stack.
