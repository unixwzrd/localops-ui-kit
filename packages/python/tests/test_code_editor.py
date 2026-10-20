import json

import pytest
from localops_ui.code_editor import EditorDocument, EditorSnapshot
from pydantic import ValidationError


def test_document_bounds_and_strict_identity():
    for text in ("x\r\ny", "x" * 1048577, "\n" * 20000, "\ud800"):
        with pytest.raises(ValidationError):
            EditorDocument(id="doc", revision=1, text=text, readOnly=False)
    with pytest.raises(ValidationError):
        EditorDocument(id="doc", revision=True, text="", readOnly=False)


def test_snapshot_unicode_selection_and_closed_shape():
    value = {
        "documentId": "doc",
        "revision": 1,
        "text": "😀 text",
        "selection": {"start": 0, "end": 2, "direction": "none"},
        "dirty": True,
        "readOnly": False,
        "state": {"kind": "ready"},
        "history": {"undo": 1, "redo": 0, "bytes": 8, "discardedTransactions": 0},
    }
    model = EditorSnapshot.model_validate_json(json.dumps(value))
    assert json.loads(model.model_dump_json(exclude_none=True)) == value
    value["selection"]["start"] = 1
    with pytest.raises(ValidationError):
        EditorSnapshot.model_validate_json(json.dumps(value))
    value["selection"]["start"] = 0
    value["path"] = "unexpected"
    with pytest.raises(ValidationError):
        EditorSnapshot.model_validate_json(json.dumps(value))
