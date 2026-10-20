"""Closed direct-editor interchange contracts; consumers own draft and newline policy."""

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .models import Identifier, PublicModel

SafeInteger = Annotated[int, Field(ge=0, le=9007199254740991)]


def editor_text(value: str) -> str:
    if "\r" in value or len(value.encode("utf-8")) > 1048576 or value.count("\n") + 1 > 20000:
        raise ValueError("editor requires LF text within 1 MiB / 20000 lines")
    return value


class EditorDocument(PublicModel):
    id: Identifier
    revision: SafeInteger
    text: str
    readOnly: bool

    _text = field_validator("text")(editor_text)


class EditorSelection(PublicModel):
    start: SafeInteger
    end: SafeInteger
    direction: Literal["none", "forward", "backward"] = "none"

    @model_validator(mode="after")
    def ordered(self) -> "EditorSelection":
        if self.end < self.start:
            raise ValueError("selection must be ordered")
        return self


def validate_selection(text: str, selection: EditorSelection) -> None:
    encoded = text.encode("utf-16-le")
    units = [int.from_bytes(encoded[i : i + 2], "little") for i in range(0, len(encoded), 2)]
    for offset in (selection.start, selection.end):
        if offset > len(units) or (
            0 < offset < len(units) and 0xD800 <= units[offset - 1] <= 0xDBFF and 0xDC00 <= units[offset] <= 0xDFFF
        ):
            raise ValueError("invalid UTF-16 selection boundary")


class EditorDraft(PublicModel):
    documentId: Identifier
    revision: SafeInteger
    text: str
    selection: EditorSelection

    _text = field_validator("text")(editor_text)

    @model_validator(mode="after")
    def selection_bounds(self) -> "EditorDraft":
        validate_selection(self.text, self.selection)
        return self


class EditorState(PublicModel):
    kind: Literal["ready", "loading", "unavailable", "error"]
    message: str | None = None


class EditorHistory(PublicModel):
    undo: Annotated[int, Field(ge=0, le=100)]
    redo: Annotated[int, Field(ge=0, le=100)]
    bytes: Annotated[int, Field(ge=0, le=8388608)]
    discardedTransactions: SafeInteger

    @model_validator(mode="after")
    def bounded(self) -> "EditorHistory":
        if self.undo + self.redo > 100:
            raise ValueError("history exceeds 100 transactions")
        return self


class EditorSnapshot(PublicModel):
    documentId: Identifier
    revision: SafeInteger
    text: str
    selection: EditorSelection
    dirty: bool
    readOnly: bool
    state: EditorState
    history: EditorHistory

    _text = field_validator("text")(editor_text)

    @model_validator(mode="after")
    def selection_bounds(self) -> "EditorSnapshot":
        validate_selection(self.text, self.selection)
        return self


class EditorLineRange(PublicModel):
    startLine: Annotated[int, Field(ge=1, le=20000)]
    endLine: Annotated[int, Field(ge=1, le=20000)]

    @model_validator(mode="after")
    def ordered(self) -> "EditorLineRange":
        if self.endLine < self.startLine:
            raise ValueError("line range must be ordered")
        return self
