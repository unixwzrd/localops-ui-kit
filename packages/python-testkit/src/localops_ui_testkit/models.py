from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class Viewport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    width: int = Field(ge=1)
    height: int = Field(ge=1)


class ModalState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    open: bool
    roots: tuple[str, ...] = ()


class LayoutIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: Literal[
        "document-overflow",
        "pane-overflow",
        "overlay-occlusion",
        "hit-test",
        "clipped-label",
        "permanent-clipping",
        "unreachable-control",
        "modal-background-operable",
    ]
    target: str
    detail: dict[str, JsonValue] = Field(default_factory=dict)


class LayoutReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    viewport: Viewport
    mode: Literal["static", "reachability"]
    modal: ModalState
    issues: tuple[LayoutIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.issues
