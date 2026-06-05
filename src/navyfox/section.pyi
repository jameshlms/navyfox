from pathlib import Path
from typing import Any, Literal

from navyfox._collection import DocumentView as DocumentView
from navyfox._proxy.base import Element as _Element
from navyfox.image import Image
from navyfox.paragraph import HorizontalRule, LineStyleArg, Paragraph
from navyfox.table import Table

class Section(_Element):
    orientation: Literal["portrait", "landscape"]
    page_width: float
    page_height: float
    margin_top: float
    margin_bottom: float
    margin_left: float
    margin_right: float
    margin_header: float
    margin_footer: float
    start_type: Literal["continuous", "newPage", "evenPage", "oddPage"]
    different_first_page: bool

    def __init__(self) -> None: ...
    def format(
        self,
        *,
        orientation: Literal["portrait", "landscape"] = ...,
        page_width: float = ...,
        page_height: float = ...,
        margin_top: float = ...,
        margin_bottom: float = ...,
        margin_left: float = ...,
        margin_right: float = ...,
        margin_header: float = ...,
        margin_footer: float = ...,
        start_type: Literal["continuous", "newPage", "evenPage", "oddPage"] = ...,
        different_first_page: bool = ...,
    ) -> Section: ...
    @property
    def paragraphs(self) -> DocumentView[Paragraph]: ...
    @property
    def tables(self) -> DocumentView[Table]: ...
    def add_paragraph(self, text: str = ..., style: str = ...) -> Paragraph: ...
    def add_heading(self, text: str = ..., level: int = ...) -> Paragraph: ...
    def add_table(self, rows: int, cols: int, style: str = ...) -> Table: ...
    def add_horizontal_rule(
        self,
        *,
        line_style: LineStyleArg = ...,
        line_width: float = ...,
        line_color: str = ...,
    ) -> HorizontalRule: ...
    def add_bullet(self, text: str = ..., level: int = ...) -> Paragraph: ...
    def add_numbered(self, text: str = ..., level: int = ...) -> Paragraph: ...
    def add_image(
        self,
        src: str | Path | None = ...,
        *,
        data: bytes | None = ...,
        content_type: str | None = ...,
        width: float = ...,
        height: float = ...,
        alt_text: str = ...,
    ) -> Image: ...
    def _copy_data(self) -> dict[str, Any]: ...
    def copy(self) -> Section: ...
    def __repr__(self) -> str: ...
