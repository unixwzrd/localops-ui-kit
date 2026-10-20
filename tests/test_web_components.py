import json
from pathlib import Path

import pytest


def test_public_module_exports_match_manifest(page, repository_url: str) -> None:
    manifest = json.loads(Path("packages/web/assets.json").read_text(encoding="utf-8"))
    page.goto(f"{repository_url}/examples/component-gallery/")
    exports = page.evaluate(
        """async (url) => Object.keys(await import(url)).sort()""",
        f"{repository_url}/packages/web/static/index.js",
    )
    assert exports == sorted(manifest["exports"])


def test_dom_format_primitives_forms_and_chart_states(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    result = page.evaluate(
        """
        async (url) => {
          const ui = await import(url);
          const details = ui.element("details", { open: false }, "content");
          let copied = "";
          const copy = ui.copyControl({ text: () => "value", write: async (value) => { copied = value; } });
          document.body.append(copy);
          copy.click();
          await Promise.resolve();

          const number = ui.numberField({ label: "Count", value: 2, min: 1, max: 4 });
          number.input.value = "9";
          number.input.dispatchEvent(new Event("change"));
          const slider = ui.sliderField({ label: "Ratio", value: 0.5, min: 0, max: 1, step: 0.1 });
          slider.slider.value = "0.8";
          slider.slider.dispatchEvent(new Event("input"));

          const invalid = ui.chartContainer({
            dataset: { title: "Invalid", points: [{ label: "bad", value: Number.NaN }] },
          });
          const empty = ui.chartContainer({ dataset: { title: "Empty", points: [] } });
          return {
            copied,
            falseAttributeOmitted: !details.hasAttribute("open"),
            duration: ui.formatDuration(45200),
            invalidNumber: ui.formatNumber(Number.NaN),
            clampedNumber: number.value(),
            synchronizedSlider: number.input.value !== slider.input.value && slider.input.value,
            invalidChart: invalid.textContent,
            emptyChart: empty.textContent,
            iconName: ui.iconButton({ label: "Settings", icon: "*" }).getAttribute("aria-label"),
            errorRole: ui.stateView({ kind: "error", title: "Failed" }).getAttribute("role"),
          };
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert result == {
        "copied": "value",
        "falseAttributeOmitted": True,
        "duration": "45.2s (45200 ms)",
        "invalidNumber": "n/a",
        "clampedNumber": 4,
        "synchronizedSlider": "0.8",
        "invalidChart": "Invalid chart dataThe supplied dataset contains a non-finite value or invalid label.",
        "emptyChart": "No dataEmpty has no points.",
        "iconName": "Settings",
        "errorRole": "alert",
    }


def test_path_adapter_callbacks_and_validation(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    result = page.evaluate(
        """
        async (url) => {
          const { pathField } = await import(url);
          const calls = [];
          const field = pathField({
            label: "Path",
            kind: "directory",
            value: "start",
            adapter: {
              resolve: async (path, kind) => {
                calls.push(["resolve", path, kind]);
                return { input: path, resolved: `/resolved/${path}`, exists: true, valid: true, kind };
              },
              browse: async (path, kind) => {
                calls.push(["browse", path, kind]);
                return { path: "browsed", entries: [] };
              },
              create: async (path, kind) => {
                calls.push(["create", path, kind]);
                return { input: path, resolved: path, exists: true, valid: true, kind };
              },
            },
          });
          document.body.append(field.root);
          await field.resolve();
          [...field.root.querySelectorAll("button")].find((node) => node.textContent === "Browse").click();
          await new Promise((resolve) => setTimeout(resolve, 0));
          [...field.root.querySelectorAll("button")].find((node) => node.textContent === "Create").click();
          await new Promise((resolve) => setTimeout(resolve, 0));
          let validationError = "";
          try { pathField({ label: "Bad", adapter: {} }); } catch (error) { validationError = error.message; }
          return { calls, value: field.input.value, validationError };
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert result["calls"] == [
        ["resolve", "start", "directory"],
        ["browse", "start", "directory"],
        ["resolve", "browsed", "directory"],
        ["create", "browsed", "directory"],
    ]
    assert result["value"] == "browsed"
    assert result["validationError"] == "PathAdapter.resolve must be a function"


def test_data_table_behavior_and_task_log_preservation(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    result = page.evaluate(
        """
        async (url) => {
          const { DataTable, TaskMonitor } = await import(url);
          const saves = [];
          const table = new DataTable({
            caption: "Records",
            rowKey: (row) => row.id,
            rows: [{ id: "a", value: 20 }, { id: "b", value: 3 }],
            clientSort: true,
            sortLocale: "en",
            columns: [
              { id: "id", label: "Identity", value: (row) => row.id, sortable: true },
              { id: "value", label: "Value", value: (row) => row.value, sortable: true },
            ],
            preferenceKey: "records",
            preferenceStore: { load: () => undefined, save: (_key, value) => saves.push(value) },
          });
          document.body.append(table.root);
          await new Promise((resolve) => setTimeout(resolve, 0));
          table.root.querySelectorAll(".lui-data-table__sort")[1].click();
          const firstRow = table.root.querySelector("tbody tr").dataset.rowKey;
          const identityToggle = table.root.querySelector('.lui-data-table__columns input[type="checkbox"]');
          identityToggle.checked = false;
          identityToggle.dispatchEvent(new Event("change"));
          table.root.querySelector('[aria-label="Resize Value"]').dispatchEvent(
            new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
          );
          table.root.querySelector('[title="Move Value left"]').click();

          let cancelled = 0;
          let snapshot = {
            id: "task", phase: "running", label: "Generic task", progress: 25,
            log: Array.from({ length: 200 }, (_, index) => `line ${index}`).join("\\n"),
          };
          const monitor = new TaskMonitor({
            adapter: {
              getSnapshot: async () => snapshot,
              cancel: async () => { cancelled += 1; snapshot = { ...snapshot, phase: "cancelled" }; },
            },
          });
          document.body.append(monitor.root);
          const log = monitor.root.querySelector(".lui-task__log");
          log.style.height = "80px";
          log.style.overflow = "auto";
          await monitor.start();
          log.scrollTop = 30;
          const before = log.scrollTop;
          monitor.update({ ...snapshot, log: `${snapshot.log}\\nnew line` });
          const after = log.scrollTop;
          monitor.root.querySelector(".lui-task__actions button").click();
          await new Promise((resolve) => setTimeout(resolve, 0));
          monitor.stop();
          return {
            firstRow,
            layout: table.getLayout(),
            saveCount: saves.length,
            progress: monitor.root.querySelector("progress").value,
            cancelled,
            scrollPreserved: before === after,
          };
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert result["firstRow"] == "b"
    assert result["layout"]["order"] == ["value", "id"]
    assert result["layout"]["visible"] == ["value"]
    assert result["layout"]["widths"]["value"] >= 80
    assert result["saveCount"] >= 3
    assert result["progress"] == 25
    assert result["cancelled"] == 1
    assert result["scrollPreserved"] is True


def test_data_table_rejects_bad_rows_and_recovers_from_bad_preferences(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    result = page.evaluate(
        """
        async (url) => {
          const { DataTable } = await import(url);
          const table = new DataTable({
            caption: "Safe records", rowKey: (row) => row.id,
            columns: [{ id: "id", label: "ID", value: (row) => row.id }],
            rows: [{ id: "one" }], preferenceKey: "bad",
            preferenceStore: { load: async () => ({ order: "wrong" }), save: async () => {} },
          });
          document.body.append(table.root);
          await new Promise((resolve) => setTimeout(resolve, 0));
          const preferenceStatus = table.root.querySelector(".lui-data-table__status").textContent;
          const usableRows = table.root.querySelectorAll("tbody tr").length;
          table.setRows([{ id: "same" }, { id: "same" }]);
          return {
            preferenceStatus, usableRows,
            rowStatus: table.root.querySelector(".lui-data-table__status").textContent,
            role: table.root.querySelector(".lui-data-table__status").getAttribute("role"),
          };
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert "invalid" in result["preferenceStatus"].lower()
    assert result["usableRows"] == 1
    assert "row keys" in result["rowStatus"]
    assert result["role"] == "alert"


def test_data_table_all_retired_preferences_restore_default_columns(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    result = page.evaluate(
        """
        async (url) => {
          const { DataTable } = await import(url);
          const table = new DataTable({
            caption: "Current records", rowKey: (row) => row.id,
            columns: [
              { id: "id", label: "ID", value: (row) => row.id },
              { id: "value", label: "Value", value: (row) => row.value },
            ],
            rows: [{ id: "one", value: 1 }], preferenceKey: "stale",
            preferenceStore: {
              load: async () => ({ order: ["retired"], visible: ["retired"], widths: { retired: 120 } }),
              save: async () => {},
            },
          });
          document.body.append(table.root);
          await new Promise((resolve) => setTimeout(resolve, 0));
          return {
            headers: [...table.root.querySelectorAll("thead th")].map((node) => node.textContent),
            cells: [...table.root.querySelectorAll("tbody td")].map((node) => node.textContent),
            status: table.root.querySelector(".lui-data-table__status").textContent,
          };
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert result["headers"] == ["ID", "Value"]
    assert result["cells"] == ["one", "1"]
    assert "invalid" in result["status"].lower()


def test_data_table_external_sort_does_not_reinterpret_rows(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    result = page.evaluate(
        """
        async (url) => {
          const { DataTable } = await import(url);
          const sorts = [];
          const table = new DataTable({
            caption: "Backend sorted", rowKey: (row) => row.id,
            rows: [{ id: "z" }, { id: "a" }],
            columns: [{ id: "id", label: "ID", value: (row) => row.id, sortable: true }],
            onSort: (sort) => sorts.push(sort),
          });
          document.body.append(table.root);
          await new Promise((resolve) => setTimeout(resolve, 0));
          table.root.querySelector(".lui-data-table__sort").click();
          await Promise.resolve();
          return { sorts, first: table.root.querySelector("tbody tr").dataset.rowKey };
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert result == {"sorts": [{"columnId": "id", "direction": "ascending"}], "first": "z"}


def test_manifest_events_and_stale_patch_rejection(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/manifest.html")
    page.get_by_role("spinbutton", name="Workers").fill("6")
    page.get_by_role("spinbutton", name="Workers").blur()
    page.get_by_role("button", name="Confirm operation").click()
    page.get_by_role("dialog").get_by_role("button", name="OK").click()
    page.get_by_role("tab", name="Chart").click()
    assert page.get_by_text("Manifest values").is_visible()

    stale_error = page.evaluate(
        """
        async (url) => {
          const { ManifestRuntime } = await import(url);
          const root = document.createElement("div");
          const snapshot = {
            schema_version: "1", revision: 0,
            spec: { schema_version: "1", id: "test", initial_page_id: "main", pages: [
              { id: "main", title: "Test", body: { type: "stack", id: "root", children: [] } },
            ] },
            state: {},
          };
          const runtime = new ManifestRuntime(root, { load: async () => snapshot, send: async () => ({
            schema_version: "1", result: null,
            update: { schema_version: "1", base_revision: 0, revision: 1, changes: {} },
          }) });
          await runtime.start();
          try {
            runtime.apply({ schema_version: "1", base_revision: 9, revision: 10, changes: {} });
          } catch (error) {
            return error.message;
          }
          return "";
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert stale_error == "stale or out-of-order state patch"


def test_manifest_contract_rejects_wrong_versions_and_raw_results(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    errors = page.evaluate(
        """
        async (url) => {
          const { ManifestRuntime } = await import(url);
          const root = document.createElement("div");
          const base = { schema_version: "1", revision: 0, spec: { schema_version: "1", id: "ui", pages: [
            { id: "page", title: "Page", body: { type: "button", id: "go", label: "Go", command_id: "go" } },
          ] }, state: {} };
          const messages = [];
          try {
            await new ManifestRuntime(root, {
              load: async () => ({ ...base, schema_version: "2" }), send: async () => null,
            }).start();
          }
          catch (error) { messages.push(error.message); }
          const runtime = new ManifestRuntime(root, { load: async () => base, send: async () => ({ raw: true }) });
          await runtime.start();
          try { await runtime.event("go", "command", undefined, "go"); }
          catch (error) { messages.push(error.message); }
          return messages;
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert errors == ["UISnapshot.schema_version must equal 1", "UITransportResponse.raw is not allowed"]


def test_adapter_validators_reject_incomplete_objects(page, repository_url: str) -> None:
    page.goto(f"{repository_url}/examples/component-gallery/")
    errors = page.evaluate(
        """
        async (url) => {
          const ui = await import(url);
          const cases = [
            [ui.assertTaskAdapter, {}, "TaskAdapter.getSnapshot must be a function"],
            [ui.assertPreferenceStore, { load() {} }, "PreferenceStore.save must be a function"],
            [ui.assertArtifactProvider, { list() {} }, "ArtifactProvider.open must be a function"],
            [ui.assertManifestTransport, { load() {} }, "ManifestTransport.send must be a function"],
          ];
          return cases.map(([validate, value, expected]) => {
            try { validate(value); return ""; } catch (error) { return [error.message, expected]; }
          });
        }
        """,
        f"{repository_url}/packages/web/static/index.js",
    )
    assert all(actual == expected for actual, expected in errors)


@pytest.mark.parametrize("dialog_name", ["Alert", "Prompt"])
def test_additional_dialog_kinds_open_accessible_modals(page, gallery_url: str, dialog_name: str) -> None:
    page.goto(gallery_url)
    page.get_by_role("button", name=dialog_name, exact=True).click()
    dialog = page.get_by_role("dialog")
    assert dialog.get_attribute("aria-modal") == "true"
    assert dialog.get_attribute("aria-labelledby")
    page.keyboard.press("Escape")
    assert dialog.is_hidden()
