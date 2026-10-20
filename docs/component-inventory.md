# Component inventory and extraction decisions

Version 0.1.4 adds original `ContentPanel` for CAS-UX-001, using native dialog mechanics and existing DOM/button/token primitives. Existing message dialogs, literal-block ResultReader and disclosures do not provide this arbitrary trusted-DOM/expansion contract. No consumer source or document renderer was copied; parsing, safe links and document semantics remain consumer-owned.

Version 0.1.3 adds original `CodeEditor` native assets and Python interchange models for CAS-001. Implementation uses platform textarea input/composition/selection and existing tokens/buttons, with a synchronized measured line gutter and bounded toolkit history. No source repository implementation, editor framework or consumer runtime behavior is copied. The direct controller remains outside the manifest and terminal renderer surfaces.

Version 0.1.2 adds an explicit `closeNavigation({focusTarget?})` operation to the shell's existing DOM root in response to RB-005. Original implementation, no consumer code copied: idempotent drawer closure, synchronized ARIA expansion and mobile focus relocation. It preserves existing mounting/callback behavior and adds no route or terminal drawer abstraction.

## Additive results/reader component

Version 0.1.1 adds an original, domain-neutral `ResultReader` native component and strict Python presentation models in response to RB-001. It reuses the existing shell, DOM helper, buttons and state displays. No consumer source or private content is copied. The direct component provides responsive labelled panes, text-only blocks, stable result/block identity, passive-update preservation and explicit block reveal. It does not add a manifest node or dedicated terminal renderer; those capabilities remain unsupported.

## Provenance and licensing decision

The MLXForge reference was inspected at commit `c3b083fe9d18f7edb2edefd783cf628a3c283099`. Code Analysis Suite was inspected from the provided directory, which was not a Git worktree. Its governing reuse requirement is `docs/REQUIREMENTS.md` section 11.2.

Neither reference root contained a `LICENSE`, `COPYING`, or `NOTICE` file granting permission to copy its project source. MLXForge's `docs/LICENSE_COMPLIANCE.md` describes dependency licenses but does not license MLXForge source itself. Therefore this repository does not copy or adapt reference source or the complete `app.css`. It uses a clean-room implementation from the work order and documented generic behavior. New code in this repository is licensed under MIT.

Source references remain read-only and are not package dependencies.

ConnectomeAI UI2 was also inspected as an owned architectural reference. Its Pydantic specifications, named bindings, and backend-factory approach informed the Python-first design. No NiceGUI or Quasar implementation, properties, lifecycle behavior, or dependency was copied into this toolkit.

## Native JavaScript decision

MLXForge demonstrates the required deployment property: ordinary static JavaScript and CSS can be served by a local Python process without a frontend package manager. LocalOps UI Kit therefore retains ES modules but removes TypeScript as an authored source format and npm as a build/test requirement. This is an architectural alignment decision, not a new extraction from MLXForge; the clean-room and licensing boundaries above remain unchanged.

Python remains authoritative for shared semantic UI definitions, public JSON validation, wheel construction, and Playwright/layout-oracle testing. WebUI components remain JavaScript-first at the browser boundary so existing applications can adopt them incrementally without adopting the Python schema renderer.

## Candidate classification

| Reference source                                        | Observed responsibility                                                                                 | Decision                                    | Toolkit result                                                                                                       |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `src/forge/ui/static/lib/dom.js`                        | DOM creation, copy, tables, chart rendering, sorting, scroll helpers, plus Forge error-envelope parsing | Reusable after domain decoupling            | Original `element`, copy control, data table, chart container, and task log behavior; request/error client excluded  |
| `src/forge/ui/static/lib/form-controls.js`              | Number field and synchronized range/number control                                                      | Reusable substantially unchanged in concept | Original typed number and slider fields with accessible labels                                                       |
| `src/forge/ui/static/lib/page-tabs.js`                  | In-page selection                                                                                       | Useful pattern but requires redesign        | ARIA tablist/tab/tabpanel relationships, stable IDs, managed focus, arrow/Home/End navigation                        |
| `src/forge/ui/static/lib/window-shade.js`               | Native details/summary disclosure                                                                       | Reusable substantially unchanged in concept | Native accessible disclosure primitive                                                                               |
| `src/forge/ui/static/lib/message-dialog.js`             | Alert, confirm, and prompt overlays                                                                     | Useful pattern but requires redesign        | Modal dialog semantics, labelled relationships, initial focus, trap, Escape, restoration                             |
| `src/forge/ui/static/lib/path-common.js`                | Debounce, path string manipulation, Forge status labels                                                 | Useful pattern but requires redesign        | Neutral status presentation; path policy and status interpretation move behind `PathAdapter`                         |
| `src/forge/ui/static/lib/path-field.js`                 | Resolve/create/browse field tied to UI endpoints                                                        | Reusable after domain decoupling            | Typed injected `PathAdapter`; no URL, path semantics, or status-envelope assumptions                                 |
| `src/forge/ui/static/lib/path-dialog.js`                | Route-bound defaults, recents, listing, create, select dialog                                           | Useful pattern but requires redesign        | Adapter surface supports a future browser dialog; route calls, preferences shape, and path policy remain in MLXForge |
| `src/forge/ui/static/lib/stats-table.js`                | Metrics catalog, formatting, sorting, visibility, sizing, ordering, persistence                         | Reusable after domain decoupling            | Generic `DataTable<Row>` and injected `PreferenceStore`; catalog and all metric interpretation remain in MLXForge    |
| `src/forge/ui/static/lib/format-duration.js`            | Human duration formatting                                                                               | Reusable substantially unchanged in concept | Original `formatDuration` plus neutral `formatNumber`                                                                |
| `src/forge/ui/static/lib/mlx-pipeline-job.js`           | Conversion/quantization job lifecycle, route polling/SSE, log scroll behavior                           | MLXForge-specific and must remain there     | Generic `TaskMonitor` reuses only the scroll-preservation pattern through a neutral `TaskAdapter`                    |
| `src/forge/ui/static/app.css`                           | Tokens, shell, responsive rules, and extensive MLXForge page/domain styling                             | Useful pattern but requires redesign        | Original token system and component-scoped responsive CSS; complete stylesheet and domain selectors excluded         |
| `tests/support/operator_ui_layout.py`                   | Rendered geometry, occlusion, hit-testing, clipping, reachability, modal reporting                      | Reusable after domain decoupling            | Original Python 3.12 oracle with neutral selectors and closed Pydantic reports                                       |
| `tests/integration/test_ui_layout_oracle_playwright.py` | Desktop/mobile routes, state fixtures, scroll sweeps, modal and negative cases                          | Useful pattern but requires redesign        | Gallery-based desktop/tablet/mobile tests and a standalone intentional failure page                                  |

## Explicit exclusions

- `fetchJson`/`api` error-envelope interpretation
- Forge routes and preferences schemas
- MLX path status labels and socket/model path rules
- the stats column catalog and metric formatting
- conversion, quantization, promotion, serving, or daemon terms
- pipeline strings, convert monitoring, and lifecycle fingerprints
- domain selectors or visual rules from the complete MLXForge stylesheet

These items remain consumer responsibilities.
