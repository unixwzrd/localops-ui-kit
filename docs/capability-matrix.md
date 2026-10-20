# Backend capability matrix

`native` means the backend has a direct interactive representation. `fallback` preserves meaning and commands using a backend-appropriate sequential representation.

| Component               | WebUI  | Textual                  | Rich CLI                       |
| ----------------------- | ------ | ------------------------ | ------------------------------ |
| Text, status, state     | native | native                   | native                         |
| Button and command      | native | native                   | native or injected interaction |
| Copy control            | native | selectable-text fallback | printable-text fallback        |
| Number field            | native | native                   | prompt or rendered value       |
| Slider plus number      | native | numeric-input fallback   | numeric-prompt fallback        |
| Path field              | native | native                   | validated-prompt fallback      |
| Data table              | native | native                   | sequential table fallback      |
| Task monitor and log    | native | native                   | progress/log fallback          |
| Derived chart dataset   | native | textual dataset fallback | table fallback                 |
| Tabs and disclosure     | native | native                   | ordered-section fallback       |
| Stack, row, grid, panel | native | native                   | sequential layout fallback     |

Renderers must not infer domain meaning while applying a fallback.

`ContentPanel` (0.1.4) is a direct native WebUI modal panel for supplied DOM/text, with expansion and focus recovery. A dedicated manifest/Textual/Rich modal panel is unsupported. Sequential terminal document sections with consumer-owned navigation are a composition fallback, not new qualified terminal functionality.

`CodeEditor` (0.1.3) is a direct WebUI component with textarea editing, line reveal, literal replacement and bounded history. Dedicated manifest/Textual/Rich editor support is unsupported in this slice; no terminal editing parity is claimed. Copy/export callbacks belong to consumers.

The 0.1.2 shell's explicit `closeNavigation` operation is native WebUI behavior. A browser drawer close operation is unsupported/not applicable in Textual and Rich; consumers use their existing terminal view-navigation operations. No new terminal parity is claimed.

`ResultReader` (0.1.1) is a direct native browser controller, outside the manifest schema. Dedicated ResultReader nodes/controllers are unsupported in Textual and Rich. Consumers can compose existing terminal text, state, list/table and command presentations with their own operations; that is a recipe, not validated interactive parity. Static CLI output cannot supply independent scrolling or browser text selection.
