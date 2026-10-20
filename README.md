# LocalOps UI Kit

LocalOps UI Kit is a Python-first, framework-independent foundation for local-first operator interfaces. Define a strict semantic UI once and render it through the browser WebUI, Textual, or Rich. The WebUI is authored as standards-based JavaScript ES modules and CSS that a Python application can serve unchanged. No JavaScript package manager, compiler, transpiler, bundler, or frontend framework is required.

The toolkit contains no MLX, model lifecycle, code-analysis, route, error-envelope, daemon, or backend-framework semantics. Applications supply data and behavior through adapters and callbacks.

## Widgets, documentation and demo

Version **0.2.0** is a public-preview preparation release. Start with the [widget and control guide](docs/widget-guide.md), grouped by layout/navigation, actions/states, forms, dialogs/content, data/tasks and integration helpers. Every public browser export is documented, including its callbacks and limitations. See also the [adoption guide](docs/adoption-guide.md), [renderer capability matrix](docs/capability-matrix.md) and [changelog](CHANGELOG.md).

Try the complete browser-only showcase locally:

```bash
python scripts/build_showcase.py
python -m http.server 8765 --bind 127.0.0.1 --directory _site
```

Open `http://127.0.0.1:8765/`. The showcase links live controls, tables, tasks, dialogs, the draft editor, content panels and results reader. All examples use synthetic data and in-memory adapters; nothing executes shell commands or accesses your filesystem. The browser runs ordinary JavaScript modules. GitHub Pages, Jekyll or another static host can serve the same files with no Python service at runtime. Hosting is prepared but no public demo URL is claimed live yet; see [deployment and privacy gates](docs/public-release.md).

## Repository layout

Version 0.1.5 includes `ContentPanel`, a modal side panel for consumer-trusted DOM or literal text, with responsive expansion and focus recovery. It fixes single-Escape dismissal from populated native search inputs, preserving their value and composition handling. See [the panel contract](docs/adoption-guide.md#content-panel-014) and `examples/component-gallery/content-panel.html`.

Version 0.1.3 adds `CodeEditor`, a native textarea with line numbers, explicit draft operations and bounded undo/redo. It emits injected copy/export intents and has no source-write or execution authority. See [the editor contract](docs/adoption-guide.md#code-editor-013) and `examples/component-gallery/code-editor.html`.

Version 0.1.2 adds an explicit `closeNavigation({focusTarget?})` operation on the existing shell element, allowing consumers to close mobile navigation after an accepted view change. See [the adoption guide](docs/adoption-guide.md#explicit-shell-navigation-closing-012) for focus and compatibility behavior.

Version 0.1.1 adds a direct `ResultReader` browser controller for responsive results and plain-text reading, with strict Python snapshot models and explicit same-document block navigation. See [the adoption guide](docs/adoption-guide.md#results-and-document-reading-011) and the synthetic `examples/component-gallery/result-reader.html` harness. Dedicated manifest and terminal ResultReader support is not included.

- `packages/web/`: framework-free browser JavaScript and CSS
- `packages/python/`: `localops-ui` semantic models and WebUI, Textual, and Rich renderers
- `packages/python-testkit/`: `localops-ui-testkit` Python package
- `examples/component-gallery/`: development and visual-test harness
- `examples/showcase/`: public demo index, grouped by widget purpose
- `tests/`: browser and component tests
- `docs/`: architecture, provenance inventory, and adoption guidance

## Build and test

```bash
python -m pip install -e '.[all,test]'
python -m pip install -e 'packages/python-testkit[test]'
python -m playwright install chromium
ruff format --check packages/python packages/python-testkit tests scripts
ruff check packages/python packages/python-testkit tests scripts
python scripts/validate_assets.py
python scripts/check_publication.py
pytest packages/python/tests packages/python-testkit/tests tests
python -m build
python -m build --outdir packages/python-testkit/dist packages/python-testkit
python scripts/verify_distribution.py
```

Canonical JavaScript and CSS live in `packages/web/static/` and are included unchanged in the Python wheel. The separate wheel and sdist commands keep the external canonical asset path explicit. Neither package is published to npm or PyPI.

## Python-first UI definition

```python
from localops_ui.gallery import operator_workspace_snapshot
from localops_ui.renderers.rich import run_cli_sync

snapshot = operator_workspace_snapshot()
run_cli_sync(snapshot, interactive=False)
```

Install `localops-ui[cli]`, `localops-ui[tui]`, or `localops-ui[all]` according to the required backends. JSON is a versioned interchange format; typed Python models remain authoritative.

## Python loopback mounting

Ship the canonical files from `packages/web/static/` with the Python application or install them from the wheel's `localops_ui/static/` resources. A Python build copies those bytes into the wheel as package data; it does not execute JavaScript tooling. A production deployment needs only a static-file server and a browser.

For a minimal loopback development server:

```python
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import as_file

from localops_ui import web_assets

with as_file(web_assets()) as assets:
    handler = partial(SimpleHTTPRequestHandler, directory=assets)
    ThreadingHTTPServer(("127.0.0.1", 8765), handler).serve_forever()
```

Mount `index.js`, its JavaScript module siblings, and `styles.css` through the application's own static-file mechanism. Applications may construct adapters in JavaScript or provide a Python-authored `UISnapshot` through `ManifestRuntime`. The consumer owns transport and URLs in both cases; each event reply carries a closed `UITransportResponse` with an advancing snapshot or patch plus any command result.

See [the adoption guide](docs/adoption-guide.md) for an adapter example and consumer sequence.

## Release privacy

Local agent/consumer handoffs stay in the private development workspace and are excluded from public history, distributions and demo assembly. Reviewed source changes are promoted into a separate public Git history; private ancestry is never merged or mirror-pushed into it. See the [development-to-public workflow](docs/public-release.md#development-to-public-workflow). Export/build tools never commit, push, change visibility or publish packages themselves.

## Contributing

Issues and pull requests are welcome for:

- framework-independent components and adapters
- accessibility and keyboard interaction improvements
- responsive operator layouts
- browser-testing and layout-oracle coverage
- documentation and adoption examples

Before submitting a change, run the Python-authoritative checks documented in [Build and test](#build-and-test). Keep domain-specific interpretation, backend routes, and consumer lifecycle assumptions outside this repository.

## Support This Work

If LocalOps UI Kit saves you time or helps you build better local-first operator tools, consider supporting independent development:

- [Patreon](https://patreon.com/unixwzrd)
- [Ko-Fi](https://ko-fi.com/unixwzrd)
- [Buy Me a Coffee](https://buymeacoffee.com/unixwzrd)

Quite a bit of effort goes into designing, testing, documenting, and preparing reusable releases. One coffee means one more tool gets released into the wild.

Thank you for keeping solo development alive.

## License

Copyright 2026<br>
[info@unixwzrd.ai](mailto:info@unixwzrd.ai)

[MIT License](LICENSE)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
