"""Domain-neutral cross-renderer gallery fixture."""

from .models import (
    ButtonSpec,
    ChartSpec,
    DataColumnSpec,
    DataTableSpec,
    DialogSpec,
    DisclosureSpec,
    GridSpec,
    NumberFieldSpec,
    PageSpec,
    PanelSpec,
    PathFieldSpec,
    SliderFieldSpec,
    StackSpec,
    StatusBadgeSpec,
    TabSpec,
    TabsSpec,
    TaskMonitorSpec,
    UISnapshot,
    UISpec,
)


def operator_workspace_snapshot() -> UISnapshot:
    spec = UISpec(
        id="component-gallery",
        initial_page_id="workspace",
        pages=(
            PageSpec(
                id="workspace",
                title="LocalOps Component Gallery",
                body=StackSpec(
                    id="workspace-stack",
                    children=(
                        StatusBadgeSpec(id="workspace-status", label="Ready", tone="success"),
                        PanelSpec(
                            id="input-panel",
                            title="Inputs",
                            children=(
                                GridSpec(
                                    id="input-grid",
                                    columns=2,
                                    children=(
                                        NumberFieldSpec(
                                            id="worker-count",
                                            label="Workers",
                                            value_key="workers",
                                            minimum=1,
                                            maximum=16,
                                        ),
                                        SliderFieldSpec(
                                            id="retention-slider",
                                            label="Retention",
                                            value_key="retention",
                                            minimum=0,
                                            maximum=100,
                                            suffix="%",
                                        ),
                                        PathFieldSpec(
                                            id="workspace-path",
                                            label="Workspace path",
                                            value_key="workspace_path",
                                            adapter_id="paths",
                                            kind="directory",
                                            allow_create=True,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        TabsSpec(
                            id="workspace-tabs",
                            selected_key="selected_tab",
                            tabs=(
                                TabSpec(
                                    id="records",
                                    label="Records",
                                    children=(
                                        DataTableSpec(
                                            id="records-table",
                                            caption="Example records",
                                            rows_key="records",
                                            row_key="id",
                                            preference_key="gallery.records.layout",
                                            columns=(
                                                DataColumnSpec(id="name", label="Name", value_key="name"),
                                                DataColumnSpec(id="status", label="Status", value_key="status"),
                                                DataColumnSpec(
                                                    id="value", label="Value", value_key="value", align="end"
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                TabSpec(
                                    id="activity",
                                    label="Activity",
                                    children=(
                                        TaskMonitorSpec(
                                            id="gallery-task",
                                            adapter_id="tasks",
                                            cancel_command_id="task.cancel",
                                            retry_command_id="task.retry",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        DisclosureSpec(
                            id="chart-details",
                            title="Derived dataset",
                            initially_open=True,
                            children=(ChartSpec(id="gallery-chart", dataset_key="chart"),),
                        ),
                        DialogSpec(
                            id="confirm-run",
                            kind="confirm",
                            trigger_label="Confirm run",
                            title="Run this operation?",
                            description="This gallery command has no domain behavior.",
                            command_id="run.confirmed",
                            result_key="run_confirmed",
                        ),
                        ButtonSpec(id="run-action", label="Run", command_id="run", variant="primary"),
                    ),
                ),
                navigation=(
                    # Navigation is intentionally presentation-only in the gallery.
                ),
            ),
        ),
    )
    return UISnapshot(
        revision=0,
        spec=spec,
        state={
            "workers": 4,
            "retention": 75,
            "workspace_path": "/example/workspace",
            "selected_tab": "records",
            "records": [
                {"id": "one", "name": "First", "status": "ready", "value": 12},
                {"id": "two", "name": "Second", "status": "waiting", "value": 7},
            ],
            "gallery-task": {
                "id": "gallery-task",
                "phase": "running",
                "label": "Example task",
                "progress": 45,
                "log": "Started\nProcessing",
            },
            "chart": {
                "title": "Example values",
                "points": [{"label": "First", "value": 12}, {"label": "Second", "value": 7}],
            },
        },
    )
