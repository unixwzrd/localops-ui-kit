import {
  DataTable,
  TaskMonitor,
  alertDialog,
  button,
  chartContainer,
  confirmDialog,
  copyControl,
  disclosure,
  element,
  formatDuration,
  formatNumber,
  iconButton,
  numberField,
  operatorShell,
  pathField,
  promptDialog,
  sliderField,
  stateView,
  statusBadge,
  tabs,
} from "../../packages/web/static/index.js";

const section = (title, ...children) =>
  element(
    "section",
    { id: title.toLowerCase().replaceAll(" ", "-"), className: "gallery-section", "data-layout-pane": "" },
    element("h2", { text: title, "data-layout-label": "" }),
    ...children,
  );
const rows = [
  { id: "a", name: "Alpha", state: "Ready", count: 1200 },
  {
    id: "b",
    name: "Beta with a long operator-visible label",
    state: "Waiting",
    count: 42,
  },
  { id: "c", name: "Gamma", state: "Failed", count: 7 },
];
const preferences = new Map();
const table = new DataTable({
  caption: "Example records",
  rowKey: (row) => row.id,
  rows,
  clientSort: true,
  sortLocale: "en",
  preferenceKey: "gallery.table",
  preferenceStore: {
    load: (key) => preferences.get(key),
    save: (key, value) => preferences.set(key, value),
  },
  columns: [
    { id: "name", label: "Name", value: (row) => row.name, width: 260, sortable: true },
    { id: "state", label: "State", value: (row) => row.state, sortable: true },
    { id: "count", label: "Count", value: (row) => row.count, align: "end", sortable: true },
  ],
});
table.root.classList.add("gallery-table");

const path = pathField({
  label: "Output path",
  kind: "directory",
  value: "./output",
  adapter: {
    resolve: async (input, kind) => ({
      input,
      resolved: `/example/${input.replace(/^\.\//, "")}`,
      exists: true,
      valid: true,
      kind,
    }),
    browse: async (input) => ({ path: input || ".", entries: [] }),
    create: async (input) => ({
      input,
      resolved: input,
      exists: true,
      valid: true,
      kind: "directory",
    }),
  },
});

let taskSnapshot = {
  id: "example",
  phase: "running",
  label: "Example task",
  progress: 37,
  message: "Processing supplied data",
  log: Array.from({ length: 80 }, (_, index) => `line ${index + 1}`).join("\n"),
};
const monitor = new TaskMonitor({
  adapter: {
    getSnapshot: async () => taskSnapshot,
    cancel: async () => {
      taskSnapshot = {
        ...taskSnapshot,
        phase: "cancelled",
        message: "Cancelled by operator",
      };
    },
    retry: async () => {
      taskSnapshot = {
        ...taskSnapshot,
        phase: "running",
        message: "Retrying",
        progress: 0,
      };
    },
  },
});

const tabSet = tabs({
  ariaLabel: "Gallery views",
  tabs: [
    {
      id: "overview",
      label: "Overview",
      content: element("p", { text: "Keyboard-operable tab panel." }),
    },
    {
      id: "details",
      label: "Details",
      content: disclosure({
        title: "More information",
        content: element("p", { text: "A native details disclosure." }),
      }),
    },
    {
      id: "history",
      label: "History",
      content: element("p", { text: "No history is supplied." }),
    },
  ],
});

const content = element(
  "div",
  { className: "gallery-stack" },
  section(
    "Primitives",
    element(
      "div",
      { className: "gallery-row" },
      button({ label: "Default" }),
      button({ label: "Primary", variant: "primary" }),
      button({ label: "Danger", variant: "danger" }),
      iconButton({label: "Example settings", icon: "⚙"}),
      copyControl({ text: () => "local operator value" }),
      statusBadge("Healthy", "success"),
      statusBadge("Attention", "warning"),
    ),
    stateView({
      kind: "empty",
      title: "Nothing here",
      message: "The backend supplied an empty result.",
    }),
  ),
  section(
    "States",
    ...["empty", "loading", "warning", "error"].map(kind => stateView({
      kind, title: `Example ${kind}`, message: "Synthetic presentation state supplied by the demo.",
    })),
    element("p", {text: `Duration: ${formatDuration(45200)} · Number: ${formatNumber(12345.67)}`}),
  ),
  section(
    "Forms",
    numberField({ label: "Workers", value: 4, min: 1, max: 32 }),
    sliderField({ label: "Threshold", value: 0.5, min: 0, max: 1, step: 0.1 }),
    path.root,
  ),
  section("Navigation and disclosure", tabSet.root),
  section(
    "Dialogs",
    element(
      "div",
      { className: "gallery-row" },
      button({
        label: "Alert",
        onClick: () =>
          void alertDialog({
            title: "Information",
            description: "This dialog traps focus and restores it on close.",
          }),
      }),
      button({
        label: "Confirm",
        onClick: () =>
          void confirmDialog({
            title: "Confirm action",
            description: "Proceed with the generic operation?",
          }),
      }),
      button({
        label: "Prompt",
        onClick: () =>
          void promptDialog({
            title: "Name",
            description: "Enter a display name.",
          }),
      }),
    ),
  ),
  section("Data table", table.root),
  section("Task monitor", monitor.root),
  section(
    "Chart container",
    chartContainer({description: "No dataset supplied"}),
    chartContainer({dataset: {title: "Invalid example", points: [{label: "Invalid", value: Number.NaN}]}}),
    chartContainer({
      dataset: {
        title: "Backend-derived values",
        unit: "items",
        points: [
          { label: "A", value: 4 },
          { label: "B", value: 9 },
          { label: "C", value: null },
          { label: "D", value: 6 },
        ],
      },
    }),
  ),
);

const theme = button({
  label: "Toggle theme",
  onClick: () => {
    document.documentElement.dataset.theme =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  },
});
document.querySelector("#app").append(
  operatorShell({
    title: "LocalOps UI Kit",
    navigation: [
      { id: "showcase", label: "Showcase index", href: "../showcase/" },
      { id: "primitives", label: "Components" },
      { id: "states", label: "States" },
      { id: "navigation-and-disclosure", label: "Accessibility" },
    ],
    content,
    topBarActions: [theme],
  }),
);
void path.resolve();
void monitor.start();
