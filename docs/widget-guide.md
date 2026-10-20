# Widget and control guide

LocalOps UI Kit 0.2.0 is a Python-first presentation toolkit. WebUI is primary; Textual and Rich render the shared semantic specification where their [declared capabilities](capability-matrix.md) allow it. Direct browser widgets also work independently of Python models. No widget executes commands, chooses backend URLs or interprets application findings or metrics.

Try the [local showcase](../examples/showcase/index.html) through HTTP(S), or assemble a standalone site using the [public-demo instructions](public-release.md#static-demonstration). The galleries use synthetic data only. They are working development/demo harnesses, not application templates or production clients.

## Quick start

Serve the repository with a loopback HTTP server during development, then open `/examples/showcase/`. For production, serve only the canonical modules, stylesheet and your application-owned integration code; never expose the checkout or local journals.

```html
<link rel="stylesheet" href="./localops-ui/styles.css">
<main id="app"></main>
<script type="module">
  import {button, numberField, element} from './localops-ui/index.js';
  const count = numberField({label: 'Copies', value: 1, min: 1, max: 10});
  const result = element('p', {role: 'status', text: 'No selection yet'});
  const apply = button({label: 'Preview', onClick: () => {
    result.textContent = `Selected ${count.value()} copies`;
  }});
  document.querySelector('#app').append(count.root, apply, result);
</script>
```

All APIs below are exported from `packages/web/static/index.js`. The installed Python wheel exposes the same unchanged files via `localops_ui.web_assets()`. Functions returning an element can be appended directly; controllers expose `.root`. Keep controllers when updates or cleanup are needed. User-visible labels are consumer supplied. Do not call undocumented implementation methods simply because JavaScript exposes them.

## Layout and navigation

### Design tokens

Load `styles.css`. Override `--lui-color-*`, `--lui-font-*`, `--lui-space-*`, `--lui-radius-*`, `--lui-border` and `--lui-focus` in your own stylesheet. Set `document.documentElement.dataset.theme` to `light` or `dark`. Keep contrast and visible focus when changing tokens. Browser tokens do not configure terminal palettes automatically.

### operatorShell

`operatorShell({title, navigation, content, topBarActions?, navigationLabel?}) → HTMLElement`. Navigation entries are `{id,label,href?,onSelect?}`; actions and content are supplied DOM. It provides a top bar, sidebar and independently scrolling primary pane, with an overlay navigation drawer on small viewports. Mount once; route selection remains the application's job.

The returned element has `closeNavigation({focusTarget?}) → boolean`. Call after an accepted view change; it is idempotent. A supplied focus target must be visible and focusable inside the content pane. This operation does not fetch data, change routes or auto-close after every link callback.

### tabs

`tabs({tabs:[{id,label,content}], ariaLabel?, initialId?, onChange?}) → {root,select,selectedId}`. Content is a Node or a factory returning one. Supply a nonempty list with distinct stable IDs. `select(id)` changes the active panel; `selectedId()` reads it. Left/Right and Home/End move selection/focus, and generated tab/panel IDs provide ARIA relationships and managed tabindex. All panels are built on construction; this is not a router or lazy backend loader.

### disclosure

`disclosure({title,content,open?}) → HTMLDetailsElement`. A native summary/details control for optional inline content. The browser handles keyboard activation. Read or set `.open` on the returned element. Use ContentPanel instead when you need a modal surface and focus return.

## Actions, status and state

### button

`button({label,variant?,disabled?,title?,onClick?}) → HTMLButtonElement`. Variants include `default`, `primary`, `danger` and `quiet`. Native button semantics, a text accessible name and visible focus are retained. The callback is consumer-owned; long-running command state and errors must be supplied by the application.

### iconButton

`iconButton({label,icon,...buttonOptions}) → HTMLButtonElement`. `icon` is a string or Node. The required label becomes its accessible name even when no text is visible. Supply trusted decorative DOM, not untrusted HTML.

### copyControl

`copyControl({text,write?,label?,copiedLabel?}) → HTMLButtonElement`. `text()` returns the current string; optional `write(value)` replaces the default `navigator.clipboard.writeText`. The temporary copied label appears after the writer resolves. Clipboard access needs a secure context and browser permission. A consumer writer should own permission/error handling; this is not a file export control.

### statusBadge

`statusBadge(label,tone='neutral') → HTMLElement`. Tones include `neutral`, `info`, `success`, `warning` and `danger`. Text conveys status without relying on color alone. The toolkit never assigns finding severity or business validity: supply both the label and tone.

### stateView

`stateView({kind,title,message?,action?}) → HTMLElement`. Use `empty`, `loading`, `warning` or `error` and optional action DOM. Error views use role `alert`; other states use role `status`. It renders supplied text, not exception envelopes, automatic retries or domain interpretation.

## Form controls

### numberField

`numberField({label,value?,min?,max?,step?,suffix?,onChange?}) → {root,input,value,setValue}`. Read `value()` or update `setValue(number)`. Change/blur normalizes/clamps the value and calls `onChange(number)`; consumers should tolerate repeated notifications for unchanged values. Programmatic `setValue` does not invoke the callback. Browser step handling is not a substitute for backend validation.

### sliderField

`sliderField({label,min,max,value?,step?,suffix?,onChange?}) → {root,input,slider,value,setValue}`. Combines a labelled numeric input with an accessible range input. User input synchronizes the controls; programmatic `setValue` is the inherited numeric-field setter and does not move the slider or emit callbacks, so set `.slider.value` too when updating both programmatically. This limitation is explicit rather than a separate hidden state model.

### pathField

`pathField({label,adapter,value?,kind?,onChange?}) → {root,input,resolve}`. `kind` is `file`, `directory` or `any`. Call `await resolve()` for initial resolution. The injected PathAdapter owns resolve/browse/create policy and all URLs; the widget does not touch a filesystem. It shows resolution results and suppresses obsolete resolve replies. The current Browse action accepts the adapter's returned `listing.path`; it is not a full directory-picker dialog. Create is offered only when supplied and kind is not `any`.

```js
const field = pathField({label: 'Location', kind: 'directory', adapter: {
  resolve: async (input, kind) => ({input, resolved: input, kind, exists: false, valid: true}),
  browse: async input => ({path: input, entries: []}),
}});
document.querySelector('#app').append(field.root);
await field.resolve(); // Synthetic example; no I/O.
```

## Dialogs and content

### alertDialog

`await alertDialog({title,description?,confirmLabel?,closeOnEscape?}) → boolean`. Resolves when dismissed; confirmation returns true and Escape returns false. The title/description label the modal. Initial focus, Tab wrapping, Escape and focus restoration are implemented. No browser `window.alert` is used.

### confirmDialog

`await confirmDialog({title,description?,confirmLabel?,cancelLabel?,destructive?,closeOnEscape?}) → boolean`. Confirmation returns true; cancel/Escape returns false. The caller decides whether to execute anything after confirmation. Destructive styling does not grant authorization.

### promptDialog

`await promptDialog({title,description?,defaultValue?,confirmLabel?,cancelLabel?,closeOnEscape?}) → string|null`. The input receives initial focus. Confirmation returns its string, cancellation returns null. Validate the returned string in the application.

These three message dialogs use a custom overlay, not the browser's native dialog top layer. Do not open them above an open ContentPanel; close the native panel first. No general nested-overlay stack or automatic cross-component closure is promised.

### ContentPanel

`new ContentPanel({id,title,content,description?,closeLabel?,expandLabel?,restoreLabel?,fallbackFocus?,onOpenChange?,onExpandedChange?})`. A native modal side panel for consumer-trusted Element/Text/DocumentFragment or a literal string. Nodes are moved, not cloned; strings never become HTML. The consumer owns parsing, safe links and document history. See the [complete contract](adoption-guide.md#content-panel-014) and [live panel harness](../examples/component-gallery/content-panel.html).

Use `.root`, `open({opener?,initialFocus?})`, `close()`, `setExpanded(boolean)`, `setContent(Node|string)`, `getState()` and `destroy()`. Expansion/reopening retains supplied child identity and state. Plain non-composing Escape closes the innermost native panel without clearing populated search text. Modified shortcuts and composition remain control/browser-owned. Close child panels before parents; focus recovers to opener, configured fallback or primary content. `ContentPanelState` is a strict Python presentation model; no dedicated manifest/TUI/CLI panel exists.

### ResultReader

`new ResultReader(options)` displays labelled results and literal document blocks in responsive panes. Construction requires stable `id`, all labels and `onSelect(resultId)`; optional `onRetry` and `onViewChange` report consumer intents. The [full option and state contract](adoption-guide.md#results-and-document-reading-011) and [runnable reader](../examples/component-gallery/result-reader.html) show all required labels.

Mount `.root` in a height-constrained host. Use `setSnapshot`, `revealBlock`, `openReader`, `returnToResults` and `destroy`. Snapshots have strictly advancing revisions and explicit unselected/loading/error/unavailable/ready states. Same-document passive updates preserve DOM and scroll; `revealBlock` is explicit identity-checked navigation. The consumer cancels obsolete loads. Strict Python models live in `localops_ui.result_reader`. No HTML rendering, document retrieval, metric interpretation or dedicated terminal/manifest reader is included.

### CodeEditor

`new CodeEditor({id,label,...callbacksAndOptions})` is a native textarea draft editor with line numbers. Mount `.root` and supply normalized LF text through `setDocument({id,revision,text,readOnly})`. See the [complete contract](adoption-guide.md#code-editor-013) and [runnable editor](../examples/component-gallery/code-editor.html) for callback, selection, history and dirty-replacement decisions.

Public operations include `getSnapshot`, `setState`, `setDocument`, `setDraft`, `setSelection`, `revealLines`, `find`, `replaceSelection`, `replaceAll`, `indent`, `undo`, `redo`, `revert` and `destroy`. Text offsets use UTF-16 boundaries; same-document revisions advance. Default history is bounded to 100 transactions/8 MiB of text payload, with disclosed eviction. Copy/export callbacks request consumer action, not filesystem writes. Python contracts live in `localops_ui.code_editor`. No syntax highlighting, LSP, execution, save service or dedicated terminal editor is supplied. Hardware IME and large-document performance need application qualification.

## Data presentation and monitoring

### DataTable

`new DataTable({caption,columns,rowKey,rows?,onSort?,clientSort?,sortLocale?,preferenceStore?,preferenceKey?})`. Each column has `id,label,value(row)` and optional `width,visible,align,sortable`. IDs must be distinct; `rowKey` must produce stable unique nonempty row identities. Cell values are display text. Mount `.root`; call `setRows(rows)` for supplied data and `getLayout()` for a detached layout snapshot.

Sorting is disabled by default. Supply `onSort({columnId,direction})` to request backend sorting, then return new rows; alternatively explicitly enable `clientSort:true` and `sortLocale`. Do not enable both. The Columns disclosure offers visibility/order controls, headers support pointer/keyboard resizing and drag ordering, and the table owns a horizontal scroll pane. Optional PreferenceStore persists a closed `{order,visible,widths}` layout. Invalid preferences produce an explicit status while defaults remain usable. Persistence failures remain consumer-owned. Try these controls in the [gallery](../examples/component-gallery/index.html).

### TaskMonitor

`new TaskMonitor({adapter,pollIntervalMs?,labels?})`. Mount `.root`, then `await start()`; call `stop()` before unmounting to release timers/subscriptions. `refresh()` reads the adapter once; `update(snapshot)` applies supplied state. Call start once per active mounting. The adapter supplies `getSnapshot()` and optionally `subscribe(onUpdate,onError)`, `cancel()` and `retry()`.

Snapshots are `{id,phase,label,progress?,message?,log?,updatedAt?}` with phases `idle`, `pending`, `running`, `succeeded`, `failed`, `cancelled`; progress is 0–100 or absent/indeterminate. No lifecycle outcome is inferred. The log preserves reading position when away from the tail, avoids forced following during selection and offers explicit Top/Follow tail controls. Cancel/retry callbacks are application commands, not shell execution. The gallery adapter only changes in-memory values.

### chartContainer

`chartContainer({dataset?,description?}) → HTMLElement`. Dataset shape is `{title,unit?,points:[{label,value}]}` where values are finite numbers or null. Missing/empty/all-null data yields an explicit no-data state; invalid labels/nonfinite values yield an error state. The current SVG bar container scales supplied magnitudes and styles negatives distinctly; it is not a full signed-axis plotting library. It performs no metric aggregation or interpretation. Replace the element to display another dataset. Accessible description/title remains consumer supplied.

## DOM and formatting helpers

### element

`element(tag,attributes={},...children) → HTMLElement`. `className`, `text`, `dataset` and `on*` callbacks have convenience handling; other properties/attributes use platform semantics. Child strings become text nodes. Omitted/null/false children are skipped. This is not an HTML sanitizer or safe-URL policy: validate attributes and supplied DOM in the consumer.

### replace

`replace(host,child)` calls `host.replaceChildren(child)`. It performs no controller cleanup or focus recovery; call component lifecycle methods before discarding managed views.

### uniqueId

`uniqueId(prefix='localops') → string` uses `crypto.randomUUID()` for DOM relationship IDs. It requires a modern secure browser context. Generated IDs are not stable persisted component identities: use application-supplied stable IDs for snapshots and events.

### formatDuration

`formatDuration(milliseconds,{includeMilliseconds?}={}) → string`. Returns human seconds/minutes/hours, by default followed by rounded milliseconds. Set `includeMilliseconds:false` for only the human part. Invalid or negative inputs yield `n/a`. This is display formatting, not a monotonic timer.

### formatNumber

`formatNumber(value,intlOptions={}) → string`. Finite numeric values are formatted with the browser's default locale and supplied Intl.NumberFormat options; other inputs return `n/a`. Locale-dependent output is not a serialized numeric contract or a domain-specific formatter.

## Python manifest bridge and adapters

### ManifestRuntime

`new ManifestRuntime(root,transport)`. `await start()` loads/render a supplied snapshot and attaches any subscription. `stop()` releases the subscription and task monitors; `apply(update)` accepts validated advancing snapshots or matching-base patches. Python UISpec/UISnapshot are the authoring authority. Transport `send(event)` must return a closed UITransportResponse with an advancing update and optional JSON result. No protocol or route is prescribed. Full manifest rendering replaces the shell; use direct controllers where continuous editor/reader DOM identity is required. See [schema reference](schema-reference.md) and `examples/component-gallery/manifest.html` (development harness, not deployed by the public showcase).

### assertPathAdapter

`assertPathAdapter(value)` checks required `resolve` and optional `browse/create` function presence and returns the adapter. Resolution/listing field contracts are documented in `contracts.js`; a shape assertion is not path authorization or validation of every callback result.

### assertTaskAdapter

`assertTaskAdapter(value)` checks required `getSnapshot` and optional `subscribe/cancel/retry` callback presence. Applications validate their supplied snapshots and retain lifecycle/error policy.

### assertPreferenceStore

`assertPreferenceStore(value)` checks `load(key)` and `save(key,value)`. Storage medium, error handling and authorization are application-owned. The table validates its preference payload; do not store arbitrary domain data as a table layout.

### assertArtifactProvider

`assertArtifactProvider(value)` checks `list()` and `open(id)`. Descriptors carry `id,label,mediaType?,size?`; `open` returns a Blob or string. This is an adapter contract, not a standalone artifact-picker widget, file handler or permission grant.

### assertManifestTransport

`assertManifestTransport(value)` checks required `load/send` and optional `subscribe`. ManifestRuntime validates interchange payloads and revision ordering separately. Application code owns connections, cancellation and credentials.

## Testing and choosing a renderer

The Python `localops-ui-testkit` package supplies `measure_layout` and `assert_layout`: mark independent scroll panes with `data-layout-pane`, and labels with `data-layout-label` when needed. It detects overflow, occlusion, failed hit-testing, clipping and reachability issues in real rendered pages. The negative-control harness is deliberately broken and is excluded from public-site assembly. It proves the oracle rejects bad geometry; it is not a normal demo.

Use strict Python UI specifications for shared semantic screens and check the [capability matrix](capability-matrix.md) before rendering. Textual can offer terminal interaction; Rich favors deterministic sequential output and injected prompts. Neither should imitate independent browser scrolling, arbitrary DOM, native modal layering or editor behavior by claiming unsupported parity. Components present data; the application always owns actions.
