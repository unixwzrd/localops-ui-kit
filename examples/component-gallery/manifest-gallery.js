import { ManifestRuntime } from "../../packages/web/static/index.js";

const snapshot = {
  schema_version: "1",
  revision: 0,
  spec: {
    schema_version: "1",
    id: "manifest-gallery",
    initial_page_id: "workspace",
    pages: [
      {
        id: "workspace",
        title: "Python Manifest Gallery",
        body: {
          type: "stack",
          id: "manifest-root",
          children: [
            {
              type: "status_badge",
              id: "manifest-status",
              label: "Ready",
              tone: "success",
            },
            {
              type: "number_field",
              id: "manifest-workers",
              label: "Workers",
              value_key: "workers",
              minimum: 1,
              maximum: 16,
            },
            {
              type: "dialog",
              id: "manifest-confirm",
              kind: "confirm",
              trigger_label: "Confirm operation",
              title: "Continue?",
              description: "This is a domain-neutral manifest dialog.",
              result_key: "confirmed",
            },
            {
              type: "tabs",
              id: "manifest-tabs",
              selected_key: "selected_tab",
              tabs: [
                {
                  id: "records",
                  label: "Records",
                  children: [
                    {
                      type: "data_table",
                      id: "manifest-table",
                      caption: "Manifest records",
                      rows_key: "records",
                      row_key: "id",
                      columns: [
                        { id: "name", label: "Name", value_key: "name" },
                        {
                          id: "value",
                          label: "Value",
                          value_key: "value",
                          align: "end",
                        },
                      ],
                    },
                  ],
                },
                {
                  id: "chart",
                  label: "Chart",
                  children: [
                    {
                      type: "chart",
                      id: "manifest-chart",
                      dataset_key: "chart",
                    },
                  ],
                },
              ],
            },
          ],
        },
      },
    ],
  },
  state: {
    workers: 4,
    selected_tab: "records",
    confirmed: false,
    records: [
      { id: "one", name: "First", value: 12 },
      { id: "two", name: "Second", value: 7 },
    ],
    chart: {
      title: "Manifest values",
      points: [
        { label: "First", value: 12 },
        { label: "Second", value: 7 },
      ],
    },
  },
};

const transport = {
  async load() {
    return snapshot;
  },
  async send(event) {
    const nextRevision = snapshot.revision + 1;
    const patch = {
      schema_version: "1",
      base_revision: snapshot.revision,
      revision: nextRevision,
      changes: event.state_key ? { [event.state_key]: event.value } : {},
    };
    if (event.state_key) snapshot.state[event.state_key] = event.value;
    snapshot.revision = nextRevision;
    return { schema_version: "1", result: null, update: patch };
  },
};

const root = document.querySelector("#app");
const runtime = new ManifestRuntime(root, transport);
await runtime.start();
window.addEventListener("pagehide", () => runtime.stop(), { once: true });
