from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Literal, Self

from navyfox._collection import DocumentView as DocumentView
from navyfox._proxy.base import ProxyBase as _ProxyBase
from navyfox.hyperlink import Hyperlink as Hyperlink
from navyfox.image import Image as Image
from navyfox.run import Run as Run

class Paragraph(_ProxyBase):
    _child_type_name: ClassVar[str]
    @property
    def text(self) -> str: ...
    @text.setter
    def text(self, value: str) -> None: ...
    style: str
    @property
    def alignment(self) -> Literal["left", "right", "center", "justify"] | None: ...
    @alignment.setter
    def alignment(self, value: Literal["left", "right", "center", "justify"] | None) -> None: ...
    keep_together: bool
    keep_with_next: bool
    page_break_before: bool
    space_before: float
    space_after: float
    line_spacing: float
    indent_left: float
    indent_right: float
    indent_hanging: float
    @property
    def list_style(self) -> Literal["bullet", "number"] | None: ...
    @list_style.setter
    def list_style(self, value: Literal["bullet", "number"] | None) -> None: ...
    list_level: int
    def __init__(
        self,
        text: str | Run | list[str | Run] | None = None,
        *,
        style: str = "Normal",
        alignment: Literal["left", "right", "center", "justify"] | None = None,
        keep_together: bool = False,
        keep_with_next: bool = False,
        page_break_before: bool = False,
        space_before: float = ...,
        space_after: float = ...,
        line_spacing: float = ...,
        indent_left: float = ...,
        indent_right: float = ...,
        indent_hanging: float = ...,
        list_style: Literal["bullet", "number"] | None = None,
        list_level: int = 0,
    ) -> None: ...
    @property
    def runs(self) -> DocumentView[Run]: ...
    @property
    def images(self) -> DocumentView[Image]: ...
    @property
    def hyperlinks(self) -> DocumentView[Hyperlink]: ...
    def add_run(self, text: str = "") -> Run: ...
    def add_image(
        self,
        src: str | Path | None = None,
        *,
        data: bytes | None = None,
        content_type: str | None = None,
        width: float = 0.0,
        height: float = 0.0,
        alt_text: str = "",
    ) -> Image: ...
    def add_hyperlink(self, text: str, url: str) -> Hyperlink: ...
    def format(
        self,
        *,
        style: str = ...,
        alignment: Literal["left", "right", "center", "justify"] = ...,
        keep_together: bool = ...,
        keep_with_next: bool = ...,
        page_break_before: bool = ...,
        space_before: float = ...,
        space_after: float = ...,
        line_spacing: float = ...,
        indent_left: float = ...,
        indent_right: float = ...,
        indent_hanging: float = ...,
        list_style: Literal["bullet", "number"] = ...,
        list_level: int = ...,
    ) -> Self: ...
    def add_break(self) -> Self: ...
    def align(self, alignment: Literal["left", "right", "center", "justify"]) -> Self: ...
    def set_style(self, style: str) -> Self: ...
    def copy(self) -> Paragraph: ...
    def _copy_data(self) -> dict[str, Any]: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __bool__(self) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Run]: ...
    def __contains__(self, run: object) -> bool: ...

class HorizontalRule(Paragraph):
    @property
    def line_style(self) -> Literal["single", "double", "dotted", "dashed", "wave"] | None: ...
    @line_style.setter
    def line_style(self, value: Literal["single", "double", "dotted", "dashed", "wave"] | None) -> None: ...
    line_width: float
    line_color: str | None
    def __init__(
        self,
        *,
        line_style: LineStyleArg = "single",
        line_width: float = 1.0,
        line_color: str = "auto",
    ) -> None: ...
    def copy(self) -> HorizontalRule: ...
    def _copy_data(self) -> dict[str, Any]: ...
    def __repr__(self) -> str: ...

class LineStyle(StrEnum):
    """Border style for a horizontal rule."""

    SINGLE = "single"
    DOUBLE = "double"
    DOTTED = "dotted"
    DASHED = "dashed"
    WAVE = "wave"

LineStyleArg = LineStyle | Literal["single", "double", "dotted", "dashed", "wave"]
