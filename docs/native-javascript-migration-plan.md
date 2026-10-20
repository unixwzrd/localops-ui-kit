# Native JavaScript migration plan

Status: complete in the LocalOps UI Kit repository; consumer adoption remains pending.

## Decision

LocalOps UI Kit is Python-first across WebUI, Textual, and Rich. The WebUI implementation is authored as standards-based JavaScript ES modules and CSS. A Python application can build a wheel, install it, and serve the browser assets without a JavaScript toolchain. The same canonical browser files are usable directly from a simple loopback server.

This plan replaces the provisional TypeScript/npm packaging direction. It does not change the framework-free component model, Python semantic UI contracts, adapter boundaries, accessibility requirements, or consumer ownership of domain behavior.

## Target repository layout

```text
packages/
  web/
    static/
      index.js
      *.js
      styles.css
  python/
    src/localops_ui/
      ...
  python-testkit/
examples/component-gallery/
tests/
  browser/
```

`packages/web/static/` is the only authored copy of browser assets. The Hatch wheel build uses `force-include` to place that directory at `localops_ui/static/` in the wheel. It must not run a prebuild hook, invoke npm, or maintain a second checked-in copy.

## Public contract policy

- Preserve the current browser export names and runtime behavior unless a separate compatibility decision documents a change.
- Express JavaScript option and adapter shapes with focused JSDoc and documentation examples. Do not recreate a TypeScript build through another transpiler.
- Validate Python-authored and persisted JSON at the Pydantic boundary. Validate externally supplied JavaScript adapter objects at runtime only where failure would otherwise be unclear.
- Keep `PathAdapter`, `TaskAdapter`, `PreferenceStore`, `ArtifactProvider`, and `ManifestTransport` domain-neutral and URL-free.
- Keep WebUI available independently of the Python manifest renderer so MLXForge can adopt individual components without rewriting its UI definition layer.

## Implementation phases

### 1. Freeze and map behavior

Record the current exports, interaction tests, accessibility behavior, gallery states, and wheel contents. Add a migration checklist mapping every TypeScript source and test to its JavaScript or Python replacement. This is the comparison baseline; generated `dist/` files are not a new source of truth.

Acceptance gate: the export inventory, test inventory, and expected static file manifest are checked into the repository.

### 2. Port browser source to native modules

Move each implementation from `packages/web/src/*.ts` to `packages/web/static/*.js`, removing type-only syntax while preserving module boundaries and public exports. Move the canonical stylesheet into the same static directory. Add JSDoc only where it clarifies public options, callbacks, adapter results, or controller return values.

Acceptance gate: the component gallery loads modules directly from `packages/web/static/` in Chromium with no generated intermediary, and all existing interaction and accessibility behavior is preserved.

### 3. Move browser validation to Python

Port Playwright interaction, keyboard, light/dark, responsive, and negative-control tests to Python 3.12 using `pytest-playwright`. Keep `localops-ui-testkit` as the rendered-geometry authority. Replace Vitest/jsdom assertions with focused real-browser tests or pure Python contract tests according to what each test is proving.

Add a small Python static-asset validation command that checks the declared asset manifest, relative module imports, forbidden domain/runtime imports, and absolute developer paths. JavaScript syntax and resolution are validated by importing every public module in the browser.

Acceptance gate: desktop, tablet, and mobile browser suites pass from a Python environment; keyboard navigation, dialogs, light/dark mode, and the intentional sticky-overlay or clipped-control negative page are covered; the negative page is demonstrably rejected by the oracle.

### 4. Package canonical assets in the wheel

Configure Hatch `force-include` from `packages/web/static/` to `localops_ui/static/`. Expose a small Python resource helper for locating or traversing installed assets through `importlib.resources` without assuming a filesystem installation. Build both wheel and sdist from a clean checkout using Python build tooling only.

Acceptance gate: wheel and sdist build with JavaScript tooling absent; installed wheel assets are byte-for-byte identical to `packages/web/static/`; a temporary Python loopback server serves the installed gallery successfully.

### 5. Remove the provisional toolchain

Delete TypeScript sources and generated declarations only after their native replacements pass the preceding gates. Remove `package.json`, `package-lock.json`, TypeScript configuration, ESLint/Prettier/Vitest configuration, Node Playwright configuration, `node_modules` assumptions, `packages/web/dist/`, and any CI steps that install or invoke npm.

Acceptance gate: a clean repository search finds no required npm, Node, TypeScript, `dist/`, or source-map build path; documentation and CI contain only the Python-authoritative workflow.

### 6. Notify consumers for review

Update `compatibility/consumer-impact.json`, the consumer handoff, and the adoption guide with the final static paths and version. Notify the MLXForge and Code Analysis Suite build agents that the browser packaging contract is ready for review. Do not edit either consumer repository, claim adoption, or request broad migration before their own tests pass.

Acceptance gate: both notifications contain the reviewed version, changed imports/asset paths, recommended incremental adoption order, and explicit read-only/no-adoption language.

## Target validation commands

The authoritative validation commands are:

```bash
python -m pip install -e '.[all,test]'
python -m pip install -e 'packages/python-testkit[test]'
ruff format --check packages/python packages/python-testkit tests
ruff check packages/python packages/python-testkit tests
pytest packages/python/tests packages/python-testkit/tests tests
python -m build
python -m build packages/python-testkit
python scripts/verify_distribution.py
```

No command in the final clean-checkout build or test path may invoke npm, Node, a TypeScript compiler, or a JavaScript bundler.

## Completion criteria

- Browser source is ordinary `.js` ES modules and CSS under `packages/web/static/`.
- Direct static serving and installed-wheel serving exercise the same authored files.
- WebUI, Textual, and Rich render the shared Python semantic specification within their documented capability levels.
- Component and adapter APIs remain domain-neutral and contain no consumer URLs or interpretation.
- Accessibility requirements and layout-oracle coverage remain green at desktop, tablet, and mobile viewports.
- The negative-control page fails for the expected geometry violation.
- Wheel and sdist build from a clean checkout with no JavaScript toolchain installed.
- Generated artifacts contain no absolute developer paths and no import or dependency from `forge`.
- Consumer agents have been informed of the reviewed packaging change, but neither consumer is represented as having adopted it.
