# LocalOps UI Kit Agent Instructions

## Mission

LocalOps UI Kit is a reusable, domain-neutral UI toolkit for local-first operational applications. It owns semantic UI contracts, native browser components, Textual and Rich renderers, accessibility behavior, and rendered-layout verification. Consumers own transport, authorization, routes, domain interpretation, persisted domain state, and operational commands.

Preserve that boundary. Do not turn this repository into an MLXForge-specific library or an application framework.

## Read Before Changing Code

Read the smallest relevant set before substantive work:

- `README.md`
- `docs/architecture.md`
- `docs/native-javascript-migration-plan.md`
- `docs/adoption-guide.md`
- `docs/capability-matrix.md`
- `compatibility/consumer-impact.json`
- the matching local document under `docs/consumer-handoffs/`, when available (private and intentionally absent from public checkouts)

Treat current architecture and compatibility documents as authority. Planning material is not proof that a feature ships.

## Core Architecture

- Python is authoritative for semantic UI specifications, state contracts, packaging, and browser-test orchestration.
- Public and persisted Python contracts use strict Pydantic v2 models with `extra="forbid"`. Reject bool-as-int and malformed identities where exact integers are required.
- Internal immutable renderer plans and observations should use frozen dataclasses when they do not cross a serialization boundary.
- Do not pass unconstrained `dict[str, Any]` structures across public, persisted, adapter, renderer, or package boundaries. Convert external mappings once at the owning boundary.
- Browser source is standards-based JavaScript ES modules and CSS under `packages/web/static/`.
- `packages/web/static/` is the only authored browser-asset tree. The wheel installs identical bytes under `localops_ui/static/`.
- Do not add Node, npm, TypeScript, transpilers, bundlers, generated `dist/` assets, source maps, or a second checked-in browser build.
- Keep the browser implementation framework-free. Use platform APIs and focused JSDoc for public option and adapter shapes.
- Use `importlib.resources` through the existing resource helpers rather than assuming wheel assets have ordinary filesystem paths.
- Keep one semantic engine across WebUI, Textual, and Rich. Renderers may differ in capability, but they must not invent independent domain meaning.

## Consumer Boundaries

- LocalOps UI Kit must remain URL-free and transport-neutral. It must not embed consumer routes, ports, credentials, authorization logic, or backend clients.
- `PathAdapter`, `TaskAdapter`, `PreferenceStore`, `ArtifactProvider`, `ManifestTransport`, and related interfaces describe capabilities, not application policy.
- Consumers own lifecycle actions, metric meaning, severity, validity, acceptance, model state, filesystem policy, and error interpretation.
- Never import consumer code or copy consumer-specific behavior into this repository.
- Do not edit MLXForge, Code Analysis Suite, or another consumer without explicit maintainer authorization.
- Do not claim that a consumer has adopted or validated a toolkit revision. Update compatibility and handoff records, then let the consumer qualify adoption independently.
- Preserve clean-room and licensing provenance when adapting ideas from another project.

## Browser And Component Rules

- Prefer small composable modules and explicit controller objects over hidden lifecycle machinery.
- Keep state transitions revisioned and deterministic. Stale `UISnapshot` or `StatePatch` updates must fail rather than overwrite newer state.
- Runtime-validate public JSON and adapter boundaries when malformed data would otherwise create ambiguous behavior.
- Components must remain usable with keyboard navigation and visible focus.
- Dialogs must enforce a modal focus boundary, provide initial focus, handle Escape, and restore focus.
- Tabs must preserve stable relationships, managed `tabindex`, and Arrow/Home/End keyboard behavior.
- Fixed-format controls must have stable responsive dimensions. Text, labels, controls, and modal content must not overlap or clip at governed viewports.
- Responsive browser layouts are one web implementation, not separate desktop and mobile applications.
- Keep domain-specific visible text and business rules in consumers. Toolkit examples and gallery states should remain neutral.
- Use established toolkit primitives before adding another component with overlapping behavior.

## Python And JavaScript Style

- Require Python 3.12 or newer.
- Use type hints on new and substantially modified Python functions.
- Use concise module, class, and function docstrings where purpose, side effects, ownership, or contract behavior is not obvious.
- Prefer keyword-only arguments for nontrivial Python APIs.
- Prefer explicit data flow, stable IDs, direct imports, and mechanically understandable code.
- Avoid hidden global state, monkey patches, silent retries, unbounded queues, service locators, speculative plugin systems, and unnecessary wrapper layers.
- Keep JavaScript imports relative and explicit. Public browser exports belong in `packages/web/static/index.js`.
- Do not duplicate contract interpretation between JavaScript and Python. Browser validation protects the browser boundary; Python models remain authoritative for serialized specifications.
- Preserve deterministic ordering and serialization where output is compared, packaged, or persisted.

## Scope And Refactoring

- Keep each change bounded to one component, contract, renderer, packaging concern, or test surface.
- Do not mix behavior changes, schema migrations, browser redesign, broad formatting, and package restructuring in one pass unless the maintainer approved a coordinated migration.
- Line count and complexity are indicators, not proof of a required refactor. Require an ownership, duplication, coupling, state, or validation reason.
- Prefer extraction by responsibility over generic helper accumulation.
- Do not create compatibility shims or duplicate old and new implementations indefinitely. If compatibility is required, document its owner and removal condition.
- Preserve public behavior first unless changing it is the task. Add migration notes for intentional compatibility changes.

## Testing And Validation

Use the Python-authoritative workflow with a Python 3.12+ interpreter from your chosen environment. If the command harness sterilizes `PATH`, use its absolute executable path; do not hardcode another developer's environment:

```bash
PY=python3.12
$PY -VV
$PY -c 'import sys; print(sys.executable)'
```

Do not install or upgrade global or Conda packages implicitly. Do not install Playwright browsers without explicit authorization.

Run the narrowest relevant checks first, then expand as risk warrants. The complete repository validation surface is:

```bash
ruff format --check packages/python packages/python-testkit tests scripts
ruff check packages/python packages/python-testkit tests scripts
$PY scripts/validate_assets.py
$PY -m pytest packages/python/tests packages/python-testkit/tests tests
$PY -m build
$PY -m build packages/python-testkit
```

For browser or component changes:

- Use real Chromium through Python Playwright.
- Cover desktop, tablet, and mobile viewports in light and dark modes when layout or tokens change.
- Verify keyboard behavior, dialogs, focus restoration, overflow, clipping, occlusion, hit testing, and reachability.
- Preserve an intentional negative control for the layout oracle.
- Import every public browser module in a real browser.
- Verify wheel-installed browser assets are byte-identical to `packages/web/static/`.
- Verify clean-copy sdist-to-wheel packaging and loopback serving without Node tooling.

Do not report a browser suite as passed if its loader, terminal summary, artifact manifest, or expected membership is incomplete.

## Evidence And Compatibility

- Separate observations, implementation status, review readiness, consumer adoption, and release approval.
- A passing local suite does not self-approve UX quality or consumer adoption.
- Preserve failed-run evidence and describe the first governing failure accurately. Do not relabel historical failures after fixing a later candidate.
- Portable artifacts must not contain developer home paths, volume paths, temporary roots, credentials, or consumer-private data.
- When public contracts, assets, behavior, or packaging change, update `compatibility/consumer-impact.json`, the matching consumer handoff, and relevant architecture/adoption documentation.
- Keep schema and asset versioning explicit and additive when compatibility permits. Fail closed on unsupported or malformed versions.

## Git, Documentation, And Release Discipline

- Work with existing user or agent changes. Never reset, discard, or overwrite changes you did not make.
- Do not use destructive Git or filesystem commands without explicit approval and verified targets.
- Do not commit, push, tag, publish packages, or announce adoption unless explicitly authorized.
- Keep commits focused and reviewable. Avoid unrelated metadata or formatting churn.
- Update `README.md` and architecture/compatibility documentation when public behavior materially changes.
- Use current ISO-8601 dates. Preserve original creation dates and never future-date documents.
- Do not describe planned behavior as shipped behavior.

## Required Completion Report

For implementation work, report:

1. Files changed.
2. Contracts or behavior changed.
3. Tests and packaging checks run, with exact failures or skips.
4. Browser viewports and accessibility/layout evidence when relevant.
5. Compatibility and consumer-impact updates.
6. Deferred findings and hard-stop conditions.
