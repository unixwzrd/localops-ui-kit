# Adoption guide

## Consume static assets

Copy `packages/web/static/` into the application's static asset tree, serve that directory directly during development, or use `localops_ui.web_assets()` with `importlib.resources.as_file()` to mount the installed wheel resources. No compilation, bundling, JavaScript package installation, or JavaScript server runtime is required. Load the application integration code with a standard module script:

```html
<link rel="stylesheet" href="/static/localops-ui/styles.css" />
<script type="module" src="/static/application-ui.js"></script>
```

The browser executes native ES modules and the Python process serves static bytes. `packages/web/static/` is the stable authored asset root and `localops_ui/static/` is its installed-wheel location.

## Content panel (0.1.4)

Import `ContentPanel` from native `index.js`. Construct with `{id,title,content,description?,closeLabel?,expandLabel?,restoreLabel?,fallbackFocus?,onOpenChange?,onExpandedChange?}`. Options are closed and validated; IDs use toolkit identifier rules and labels must be nonempty. Content is a DOM Element/Text/DocumentFragment or a literal string. Nodes are moved, not cloned; fragments are consumed. DOM must be consumer-trusted/compiled and safe for insertion. This API is not a sanitizer: the consumer owns parsing, safe links, lookup, guide history, authorization and document meaning. Strings become text nodes; no HTML or Markdown interpretation occurs.

`open({opener?,initialFocus?})` opens a native modal dialog, appending `.root` to the body if needed. It returns true only for a new opening. Default initial focus is the accessible title; an optional focus target must be a visible programmatically focusable descendant. Pass the triggering control explicitly as `opener` for deterministic pointer focus restoration. The default opener is the active element. `close()` is idempotent and restores focus to the still-valid opener, then configured fallback, then a visible main pane or document body. Escape closes. Native modal inertness and an explicit Tab/Shift-Tab boundary keep background controls inoperable. Repeated open/close retains content nodes, inputs and expansion state.

`setExpanded(boolean)` switches between a desktop side panel (up to 42rem) and full width, with no child rebuild. Both modes naturally fill mobile width. It returns whether state changed, updates the expansion button's `aria-pressed`, and emits `onExpandedChange(boolean)` once. `onOpenChange(boolean)` reports open/close transitions once. `getState()` returns a frozen `{open,expanded}` matching strict Python `ContentPanelState` from `localops_ui.models`. No manifest node or domain state is introduced.

Since 0.1.5, an unmodified, non-composing Escape is owned by the innermost native panel: a capture listener prevents native control defaults and closes once, retaining a populated search input's value and restoring focus. Version 0.1.4 relied only on dialog cancellation; Chromium's native search input consumes Escape when populated, clearing the query instead of dismissing the dialog. The panel does not intercept Ctrl/Alt/Meta/Shift+Escape, composing key events, or legacy composition key code 229; those remain control/browser-owned. Tracked active composition also suppresses native dialog cancellation until composition ends. This is not a guarantee about browser/OS modified shortcuts. Synthetic composition regression tests pass; hardware IME acceptance remains pending. No component API change is required.

`setContent(Node|string)` explicitly replaces supplied content, including consumer loading/error views. If replacement removes the focused child while open, focus goes to the panel title; otherwise focus is retained. Close and expansion never replace content. `destroy()` closes/restores focus, removes listeners and the root, and makes subsequent operations fail. The component owns only its own surface; no underlying draft or source state is changed. Dedicated Textual/Rich modal panels are unsupported; consumers can present documents sequentially using existing terminal text/sections and their own navigation. No new terminal implementation or parity is claimed.

Nested `ContentPanel` dialogs are supported in last-opened-first-closed order: the child restores focus inside its still-open parent, and the parent later restores the original opener. Close inner panels before closing/destroying outer ones. Existing `alertDialog`/`confirmDialog`/`promptDialog` use a custom overlay rather than the native dialog top layer; they are not supported above an open native panel. Close the panel first before using those legacy message overlays. No implicit modal manager or cross-component auto-closing is added.

## Supply domain behavior

```js
import { pathField, TaskMonitor } from "/static/localops-ui/index.js";

const paths = pathField({
  label: "Destination",
  kind: "directory",
  adapter: {
    resolve: (path, kind) => applicationClient.resolvePath({ path, kind }),
    browse: (path, kind) => applicationClient.listPath({ path, kind }),
    create: (path, kind) => applicationClient.createPath({ path, kind }),
  },
});

const monitor = new TaskMonitor({ adapter: applicationTaskAdapter });
document.querySelector("main").append(paths.root, monitor.root);
await monitor.start();
```

The application client owns URLs, authentication, error mapping, authorization, and domain data transformation. Convert backend responses into toolkit interfaces before passing them to components.

## Explicit shell navigation closing (0.1.2)

`operatorShell(options)` still returns an HTMLElement for existing DOM mounting. That same element now exposes `shell.closeNavigation({focusTarget?})`; call it after the application's navigation has been accepted and the destination is rendered. It returns true when an expanded state was closed and false for an already-closed state. It removes the overlay state and synchronizes the toggle's `aria-expanded` without invoking routes or navigation callbacks.

On narrow screens, an optional visible, enabled, programmatically focusable HTMLElement within the shell content pane receives focus. Without a target, focus in the hidden sidebar moves to the existing main pane; focus outside navigation stays where it is. Desktop sidebar visibility and focus remain unchanged. Repeated calls do not move focus. Invalid targets throw before mutation. Nothing closes automatically on passive data updates. Consumer code can replace DOM-query/toggle-click workarounds with this operation; no new import or controller wrapper is needed. Textual/Rich have no browser drawer operation and keep their existing view-navigation semantics.

## Code editor (0.1.3)

Import `CodeEditor` from the canonical `index.js`. Construct with `{id, label, onChange?, onSelection?, onCopy?, onExport?, historyLimit?}` and mount `.root` in a constrained-height host, as in the synthetic `examples/component-gallery/code-editor.html` harness. Callbacks receive detached `EditorSnapshot` objects. The editor does not fetch, save, download, analyze or execute documents; copy/export buttons emit intents only. No callbacks means those intent buttons are disabled.

`setDocument({id, revision, text, readOnly}, {discardChanges?})` supplies a closed document. Text must be well-formed Unicode, normalized LF, at most 1 MiB UTF-8 and 20,000 logical lines. CR/CRLF input is rejected; the consumer preserves original newline metadata and reconstructs its own explicit exports. Same-document revisions must strictly advance. Unchanged supplied baselines preserve dirty text, selection, history and focus. Replacing a dirty baseline or switching documents fails unless the consumer explicitly supplies `discardChanges:true`; this operation makes no decision or confirmation on the consumer's behalf. Completed document switches reset history. `setState({kind, message?})` accepts ready/loading/unavailable/error, preserves draft text and disables editing outside ready state. `readOnly` is a separate supplied document property.

`getSnapshot()` returns `{documentId, revision, text, selection:{start,end,direction}, dirty, readOnly, state:{kind,message?}, history:{undo,redo,bytes,discardedTransactions}}`, detached from internal state. Python matching models live in `localops_ui.code_editor`: `EditorDocument`, `EditorSelection`, `EditorState`, `EditorHistory`, `EditorSnapshot`, `EditorLineRange`. Serialize optional fields with `exclude_none=True`.

Selections use zero-based UTF-16 offsets with exclusive end, reject positions splitting a surrogate pair, and accept direction none/forward/backward. `setSelection({start,end,direction?})` changes selection without deliberate focus. `revealLines({startLine,endLine}, {focus?})` uses one-based inclusive logical lines including the empty final line after a trailing LF. It scrolls to the first line; optional focus also selects the supplied range. Passive reveal does not change focus or selection. The consumer binds delayed navigation to its current document identity; no source/report semantics are inferred.

Editing operations: `undo()`, `redo()`, `revert()`, `indent(unit="  ", outdent=false)`, `find(query)`, `replaceSelection(query,replacement)`, and `replaceAll(query,replacement)`. Search is literal, case-sensitive and wraps once. Replace-selection replaces only an exact selected match; otherwise it finds the next match. Replacement strings are literal, including `$` characters. Indentation applies to intersected logical lines; a selection ending just after LF excludes the following line. Revert is explicit and undoable. Tab always moves focus. Ctrl/Cmd-Z and Shift-Z or Ctrl/Cmd-Y use toolkit history, including programmatic operations.

History defaults to 100 transactions and 8 MiB of UTF-8 before/after text payload per document, excluding runtime object overhead. `historyLimit` may lower these limits via `{transactions,bytes}`. Oldest transactions are discarded until both bounds hold; redo-branch replacement is also disclosed. A single oversized transaction retains the new draft but clears history, increments `discardedTransactions`, and announces the loss in the status area. No silent draft eviction occurs. Completed IME composition is one transaction; intermediate updates do not emit change callbacks. Document/state/selection/reveal changes are rejected during composition. The automated tests use synthetic composition events; hardware IME interaction remains a consumer usability check.

`destroy()` disconnects resize observation, removes listeners, makes the textarea read-only and causes subsequent documented operations to fail. Dedicated manifest, Textual and Rich CodeEditor rendering is unsupported in this slice. Syntax highlighting, regex search, completion, LSP, diagnostics, collaboration, persistent drafts and source saves are deferred.

## Define a shared Python UI

To reopen a consumer-cached session draft, first supply its original baseline with `setDocument`, then explicitly call `setDraft({documentId,revision,text,selection})`. Identity and revision must match that current baseline. This undoable edit preserves the original text used to calculate dirty state; it does not persist the draft or transfer previous undo stacks. Matching strict model: `EditorDraft` in `localops_ui.code_editor`. All draft text/selection is validated before mutation.

Use the Pydantic models in `localops_ui.models` as the source of truth. Serve `UISnapshot.model_dump_json()` to the browser manifest transport, pass the snapshot to `textual_app()`, or render it with `run_cli()`/`run_cli_sync()`.

The browser transport is application-owned: it loads a validated `UISnapshot`, sends `UIEvent` objects, and returns a closed `UITransportResponse` with `schema_version`, an optional JSON `result`, and a required advancing `update` (`UISnapshot` or revision-checked `StatePatch`). Subscription callbacks carry the same validated update types. The transport may use HTTP, WebSocket, an embedded bridge, or a test fake; LocalOps UI Kit defines no routes.

Before adopting a toolkit revision, inspect `compatibility/consumer-impact.json` and the public changelog. Private consumer coordination is deliberately excluded from public checkouts; maintainers may provide an exact-artifact handoff separately. Adoption remains incremental and consumer-owned even though the toolkit's native JavaScript acceptance gates pass.

## Results and document reading (0.1.1)

Import `ResultReader` from the native `index.js` alongside `operatorShell`. The runnable synthetic harness is `examples/component-gallery/result-reader.html`; its sibling JavaScript supplies required labels and demonstrates loading, selection and obsolete-load cancellation. Mount `controller.root` in a height-constrained host; the shell content pane provides this constraint. Pane navigation responds to component width, with sequential views below 700 CSS pixels.

Construction requires `id`, `resultsLabel`, `readerLabel`, `openLabel`, `returnLabel`, `emptyLabel`, `unselectedLabel`, `loadingLabel`, `errorLabel`, `unavailableLabel`, `retryLabel`, and `onSelect(resultId)`. Optional callbacks are `onViewChange(view)` and `onRetry(resultId)`. Callbacks request consumer operations; they do not supply automatic updates or retrieval.

`setSnapshot({revision, results, selectedResultId, reader})` accepts exact shapes. Results contain `{id, title, excerpt}`. Reader state is `{kind: "unselected"}` with null selection; `{kind: "loading", resultId, message}`; `{kind: "error" | "unavailable", resultId, message, retryAvailable}`; or `{kind: "ready", resultId, id, contentRevision, title, blocks: [{id, text}], activeBlockId?}`. IDs follow toolkit identifier rules. Revisions are nonnegative safe integers; snapshot revisions strictly advance. Ready content must belong to the selected result. A changed title/blocks requires a changed content revision. Every block renders as text.

Python applications import `ResultReaderSnapshot` and constituent value models from `localops_ui.result_reader`. Serialize with `model_dump_json(exclude_none=True)`; arrays become immutable tuples at the strict Python boundary. These models do not change the manifest schema.

For RB-001-Q1, after supplying the current ready snapshot, call `revealBlock({documentId, contentRevision, blockId}, {focus: false})` to deliberately reveal another match in unchanged content. The default is no focus change. Hidden readers retain the reveal until opened. `openReader()` deliberately focuses the reader heading; `{focus: true}` on reveal also opens/focuses it. `returnToResults()` restores selected-result focus or the results heading and retained list position. Passive snapshots preserve unchanged reader nodes, text selection and scroll. Activating a result opens/focuses the reader on narrow screens and keeps result focus on wide screens. `destroy()` disconnects observation and prevents subsequent controller operations.

The consumer invalidates obsolete requests even if a late response could receive a new presentation revision. The harness demonstrates this with a generation token. Component ownership checks supplement cancellation. Dedicated manifest, Textual and Rich ResultReader support is currently unsupported; use existing terminal presentations through consumer-owned operations.

## Use the layout oracle

```python
from localops_ui_testkit import assert_layout, measure_layout

page.set_viewport_size({"width": 820, "height": 1024})
page.goto(application_url)
report = measure_layout(page, mode="reachability")
assert_layout(report, label="tablet-main-view")
```

Mark independently governed panes with `data-layout-pane`. Add `data-layout-label` to non-`label` text whose permanent clipping must fail validation.

## Recommended adoption sequence

### MLXForge

1. Vendor or install a reviewed build artifact without changing routes or domain models.
2. Adopt tokens and the responsive shell behind visual regression tests.
3. Replace low-risk primitives and format helpers.
4. Adapt tabs and dialogs, validating keyboard behavior before removing existing implementations.
5. Map path operations to `PathAdapter` without moving path policy into the toolkit.
6. Map the current metrics table catalog into generic `DataColumn` definitions and its preference persistence into `PreferenceStore`; use backend `onSort` handling unless an explicit client locale and display-value ordering are appropriate.
7. Implement a `TaskAdapter` around the current monitor transport; retain conversion/quantization semantics in MLXForge.
8. Run the new oracle alongside the existing oracle before considering replacement.

### Code Analysis Suite

1. Define report/query and operation adapters from its backend authority.
2. Adopt tokens, shell, tabs, dialogs, and state views without importing MLXForge.
3. Configure generic tables from backend-supplied finding/report display fields; keep severity and validity interpretation server-side.
4. Add artifact and task adapters only after those backend contracts are stable.
5. Use the gallery viewport matrix as a baseline, then add Code Analysis-specific pages to the neutral oracle.

Each consumer should adopt incrementally and retain its own tests. This repository does not claim either consumer has adopted the toolkit.
