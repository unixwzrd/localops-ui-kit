"""Strict direct-component presentation contracts; independent of the manifest schema."""

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .models import Identifier, PublicModel

Revision = Annotated[int, Field(ge=0, le=9007199254740991)]


def _title(value: str) -> str:
    if not value.strip():
        raise ValueError("title must be nonempty")
    return value


class ReaderResult(PublicModel):
    id: Identifier
    title: str
    excerpt: str

    _named = field_validator("title")(_title)


class ReaderBlock(PublicModel):
    id: Identifier
    text: str


class UnselectedReader(PublicModel):
    kind: Literal["unselected"] = "unselected"


class LoadingReader(PublicModel):
    kind: Literal["loading"] = "loading"
    resultId: Identifier
    message: str


class FailedReader(PublicModel):
    kind: Literal["error", "unavailable"]
    resultId: Identifier
    message: str
    retryAvailable: bool


class ReadyReader(PublicModel):
    kind: Literal["ready"] = "ready"
    resultId: Identifier
    id: Identifier
    contentRevision: Revision
    title: str
    blocks: tuple[ReaderBlock, ...]
    activeBlockId: Identifier | None = None

    _named = field_validator("title")(_title)

    @model_validator(mode="after")
    def validate_blocks(self) -> "ReadyReader":
        ids = [block.id for block in self.blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate block identity")
        if self.activeBlockId is not None and self.activeBlockId not in ids:
            raise ValueError("active block is missing")
        return self


class ResultReaderSnapshot(PublicModel):
    revision: Revision
    results: tuple[ReaderResult, ...]
    selectedResultId: Identifier | None
    reader: Annotated[UnselectedReader | LoadingReader | FailedReader | ReadyReader, Field(discriminator="kind")]

    @model_validator(mode="after")
    def validate_selection(self) -> "ResultReaderSnapshot":
        ids = [result.id for result in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate result identity")
        if self.selectedResultId is not None and self.selectedResultId not in ids:
            raise ValueError("selected result is missing")
        if isinstance(self.reader, UnselectedReader):
            if self.selectedResultId is not None:
                raise ValueError("selected result needs an owned reader state")
        elif self.reader.resultId != self.selectedResultId:
            raise ValueError("reader does not own the selected result")
        return self


class ReaderReveal(PublicModel):
    documentId: Identifier
    contentRevision: Revision
    blockId: Identifier
