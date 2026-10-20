# Native JavaScript migration baseline

This inventory freezes the provisional browser implementation immediately before the native JavaScript migration. Generated ES2022 modules and the copied Python static directory were byte-identical. The native modules preserve that runtime behavior while `packages/web/static/` becomes the sole authored source.

## Source and export mapping

| Provisional source | Canonical module | Public runtime API |
| --- | --- | --- |
| `chart.ts` | `chart.js` | `chartContainer` |
| `contracts.ts` | `contracts.js` | Adapter JSDoc plus runtime adapter validators |
| `data-table.ts` | `data-table.js` | `DataTable` |
| `dialogs.ts` | `dialogs.js` | `alertDialog`, `confirmDialog`, `promptDialog` |
| `dom.ts` | `dom.js` | `element`, `uniqueId`, `replace` |
| `format.ts` | `format.js` | `formatDuration`, `formatNumber` |
| `forms.ts` | `forms.js` | `numberField`, `sliderField`, `pathField` |
| `manifest.ts` | `manifest.js` | `ManifestRuntime` |
| `navigation.ts` | `navigation.js` | `tabs`, `disclosure` |
| `primitives.ts` | `primitives.js` | `button`, `iconButton`, `copyControl`, `statusBadge`, `stateView` |
| `shell.ts` | `shell.js` | `operatorShell` |
| `task-monitor.ts` | `task-monitor.js` | `TaskMonitor` |
| `index.ts` | `index.js` | Re-exports the public browser API |
| `styles.css` | `styles.css` | Tokens, shell, primitives, forms, navigation, dialogs, tables, task monitor, chart, and responsive behavior |

The authoritative expected file and export list is `packages/web/assets.json`.

## Test replacement mapping

| Provisional test | Python replacement responsibility |
| --- | --- |
| `tests/unit/components.test.ts` | DOM boolean attributes, formatters, tabs, and dialog focus restoration in a real browser |
| `tests/unit/data-table.test.ts` | Sorting, visibility, resize persistence, ordering, task progress, cancel delegation, and log scroll preservation |
| `tests/unit/manifest.test.ts` | Python-shaped manifest events and stale-patch rejection |
| `tests/playwright/gallery.spec.ts` | Gallery reachability, desktop/tablet/mobile layout, keyboard tabs, modal accessibility, themes, manifest interaction, and negative control |

## Gallery states and accessibility baseline

The gallery covers primitive buttons and status views, synchronized numeric controls, injected path callbacks, tabs and disclosure, all three dialog kinds, configurable tables, task monitoring, and valid chart data. The manifest gallery covers Python-authored form, dialog, tabs, table, and chart definitions. Required accessibility behavior includes labelled modal dialogs, focus trapping and restoration, Escape handling, tab relationships and managed focus, keyboard table resizing, accessible control names, and visible focus styles.
