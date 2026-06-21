from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, overload

from navyfox._proxy.base import Element

if TYPE_CHECKING:
    from pathlib import Path

    from navyfox._collection import DocumentView
    from navyfox._native.handle import Handle
    from navyfox.document import Document
    from navyfox.image import Image
    from navyfox.paragraph import HorizontalRule, LineStyleArg, Paragraph
    from navyfox.table import Table


type BlockCtx = tuple[int, Handle, Document]


class _BlockViewProperty[T: Element]:
    """Collection view descriptor that silently absorbs ``__iadd__`` re-assignment.

    Accepts a zero-argument callable that returns the element type, called once and
    cached, so circular imports at module load time are not an issue.
    """

    def __init__(self, type_factory: Callable[[], type[T]]) -> None:
        self._factory = type_factory
        self._type: type[T] | None = None

    def _resolve(self) -> tuple[type[T], str]:
        if self._type is None:
            self._type = self._factory()
        return self._type, self._type._collection_name

    @overload
    def __get__(self, obj: None, objtype: type) -> _BlockViewProperty[T]: ...
    @overload
    def __get__(self, obj: BlockContainerMixin, objtype: type) -> DocumentView[T]: ...

    def __get__(
        self, obj: BlockContainerMixin | None, objtype: type | None = None
    ) -> DocumentView[T] | _BlockViewProperty[T]:
        if obj is None:
            return self
        elem_type, collection = self._resolve()
        return obj._block_view(elem_type, collection)

    def __set__(self, obj: BlockContainerMixin, _: object) -> None:
        pass  # absorbs __iadd__ re-assignment


def _paragraph_type() -> type[Paragraph]:
    from navyfox.paragraph import Paragraph

    return Paragraph


def _table_type() -> type[Table]:
    from navyfox.table import Table

    return Table


class BlockContainerMixin:
    """Mixin for ``Document`` and ``Cell`` that adds paragraph/table collections and ``add_*`` helpers."""

    __slots__ = ()

    def _block_context(self) -> BlockCtx | None:
        raise NotImplementedError(f"{type(self).__name__} must implement _block_context()")

    def _block_view[T: Element](
        self,
        elem_type: type[T],
        collection: str,
    ) -> DocumentView[T]:
        from navyfox._collection import DocumentView

        ctx = self._block_context()
        if ctx is None:
            return DocumentView.empty(elem_type, collection)
        handle, lib, document = ctx
        return DocumentView(handle, document, lib, elem_type, collection)

    def _block_append[T: Element](self, element: T) -> T:
        ctx = self._block_context()
        if ctx is None:
            raise ValueError(f"Cannot add content to a {type(self).__name__} that is not live.")
        handle, lib, document = ctx
        from navyfox._collection import DocumentView

        view = DocumentView(handle, document, lib, type(element), "body")
        return view._append_one(element)

    paragraphs: _BlockViewProperty[Paragraph] = _BlockViewProperty(_paragraph_type)
    tables: _BlockViewProperty[Table] = _BlockViewProperty(_table_type)

    def add_paragraph(self, text: str = "", style: str = "Normal") -> Paragraph:
        from navyfox.paragraph import Paragraph

        return self._block_append(Paragraph(text, style=style))

    def add_heading(self, text: str = "", level: int = 1) -> Paragraph:
        from navyfox.paragraph import Paragraph

        return self._block_append(Paragraph(text, style=f"Heading{level}"))

    def add_table(self, rows: int, cols: int, style: str = "TableGrid") -> Table:
        from navyfox.table import Table

        return self._block_append(Table(rows, cols, style=style))

    def add_horizontal_rule(
        self,
        *,
        line_style: LineStyleArg = "single",
        line_width: float = 6.0,
        line_color: str = "auto",
    ) -> HorizontalRule:
        from navyfox.paragraph import HorizontalRule

        return self._block_append(
            HorizontalRule(line_style=line_style, line_width=line_width, line_color=line_color)
        )

    def add_bullet(self, text: str = "", level: int = 0) -> Paragraph:
        from navyfox.paragraph import Paragraph

        return self._block_append(Paragraph(text, list_style="bullet", list_level=level))

    def add_numbered(self, text: str = "", level: int = 0) -> Paragraph:
        from navyfox.paragraph import Paragraph

        return self._block_append(Paragraph(text, list_style="number", list_level=level))

    def add_image(
        self,
        src: str | Path | None = None,
        *,
        data: bytes | None = None,
        content_type: str | None = None,
        width: float = 0.0,
        height: float = 0.0,
        alt_text: str = "",
    ) -> Image:
        from navyfox.paragraph import Paragraph

        para = self._block_append(Paragraph())
        return para.add_image(
            src,
            data=data,
            content_type=content_type,
            width=width,
            height=height,
            alt_text=alt_text,
        )
