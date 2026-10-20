import json

import pytest
from localops_ui.result_reader import ResultReaderSnapshot
from pydantic import ValidationError


def snapshot():
    return {
        "revision": 1,
        "results": [{"id": "result-a", "title": "Title", "excerpt": "Text"}],
        "selectedResultId": "result-a",
        "reader": {
            "kind": "ready",
            "resultId": "result-a",
            "id": "document-a",
            "contentRevision": 1,
            "title": "Title",
            "blocks": [{"id": "block-a", "text": "<script>literal</script>"}],
            "activeBlockId": "block-a",
        },
    }


def test_reader_json_is_strict_immutable_and_text_preserving():
    model = ResultReaderSnapshot.model_validate_json(json.dumps(snapshot()))
    assert json.loads(model.model_dump_json(exclude_none=True)) == snapshot()
    assert isinstance(model.results, tuple)
    with pytest.raises(ValidationError):
        model.revision = 2


@pytest.mark.parametrize("mutation", ["bool", "duplicate", "ownership", "block", "extra"])
def test_reader_rejects_invalid_boundary(mutation):
    value = snapshot()
    if mutation == "bool":
        value["revision"] = True
    elif mutation == "duplicate":
        value["results"] *= 2
    elif mutation == "ownership":
        value["reader"]["resultId"] = "other"
    elif mutation == "block":
        value["reader"]["activeBlockId"] = "missing"
    else:
        value["url"] = "unexpected"
    with pytest.raises(ValidationError):
        ResultReaderSnapshot.model_validate_json(json.dumps(value))
