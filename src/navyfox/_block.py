"""BlockContainerMixin — paragraph and table collections for body-like containers.

Both ``Document`` and ``Cell`` use this mixin. Concrete classes must implement
``_block_context()`` which returns the ``(handle, lib, document)`` triple needed to
build live ``DocumentView`` objects, or ``None`` when the container is not yet live.
"""

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

    def __init__(self, type_factory: Callable[[], type[T]], collection: str) -> None:
        self._factory = type_factory
        self._collection = collection
        self._type: type[T] | None = None

    @overload
    def __get__(self, obj: None, objtype: type) -> _BlockViewProperty[T]: ...
    @overload
    def __get__(self, obj: BlockContainerMixin, objtype: type) -> DocumentView[T]: ...

    def __get__(
        self, obj: BlockContainerMixin | None, objtype: type | None = None
    ) -> DocumentView[T] | _BlockViewProperty[T]:
        if obj is None:
            return self
        if self._type is None:
            self._type = self._factory()
        return obj._block_view(self._type, self._collection)

    def __set__(self, obj: BlockContainerMixin, _: object) -> None:
        pass  # absorbs __iadd__ re-assignment


def _paragraph_type() -> type[Paragraph]:
    from navyfox.paragraph import Paragraph

    return Paragraph


def _table_type() -> type[Table]:
    from navyfox.table import Table

    return Table


class BlockContainerMixin:
    """Mixin that adds ``paragraphs``, ``tables``, and ``add_*`` convenience helpers.

    Applied to :class:`~navyfox.document.Document` and :class:`~navyfox.table.Cell`.
    Concrete classes implement :meth:`_block_context`; everything else is derived
    from that single hook.

    Provides:

    - ``paragraphs`` -- live :class:`~navyfox.collection.DocumentView` of paragraphs
    - ``tables`` -- live :class:`~navyfox.collection.DocumentView` of tables
    - :meth:`add_paragraph` -- create and append a paragraph in one call
    - :meth:`add_heading` -- create and append a heading paragraph in one call
    - :meth:`add_table` -- create and append a table in one call
    - :meth:`add_horizontal_rule` -- create and append a horizontal rule in one call
    """

    __slots__ = ()

    def _block_context(self) -> BlockCtx | None:
        """Return ``(handle, lib, document)`` for collection access, or ``None`` when not live."""
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

    # ------------------------------------------------------------------
    # Filtered views
    # ------------------------------------------------------------------

    paragraphs: _BlockViewProperty[Paragraph] = _BlockViewProperty(_paragraph_type, "paragraphs")
    tables: _BlockViewProperty[Table] = _BlockViewProperty(_table_type, "tables")

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def add_paragraph(self, text: str = "", style: str = "Normal") -> Paragraph:
        """Append a new paragraph and return the live proxy.

        Args:
            text: Initial text content. Defaults to an empty paragraph.
            style: Paragraph style name. Defaults to ``"Normal"``.

        Returns:
            A live :class:`~navyfox.paragraph.Paragraph` proxy.
        """
        from navyfox.paragraph import Paragraph

        return self._block_append(Paragraph(text, style=style))

    def add_heading(self, text: str = "", level: int = 1) -> Paragraph:
        """Append a heading paragraph and return the live proxy.

        This is a shorthand for ``add_paragraph(text, style="Heading<level>")``.

        Args:
            text: Heading text.
            level: Heading level (1–9). Defaults to ``1``.

        Returns:
            A live :class:`~navyfox.paragraph.Paragraph` proxy styled as a heading.
        """
        from navyfox.paragraph import Paragraph

        return self._block_append(Paragraph(text, style=f"Heading{level}"))

    def add_table(self, rows: int, cols: int, style: str = "TableGrid") -> Table:
        """Append a new table and return the live proxy.

        Args:
            rows: Number of rows.
            cols: Number of columns.
            style: Table style name. Defaults to ``"TableGrid"``.

        Returns:
            A live :class:`~navyfox.table.Table` proxy.
        """
        from navyfox.table import Table

        return self._block_append(Table(rows, cols, style=style))

    def add_horizontal_rule(
        self,
        *,
        line_style: LineStyleArg = "single",
        line_width: float = 6.0,
        line_color: str = "auto",
    ) -> HorizontalRule:
        """Append a horizontal rule and return the live proxy.

        Args:
            line_style: Border style — ``"single"`` (default), ``"double"``,
                ``"dotted"``, ``"dashed"``, or ``"wave"``.
            line_width: Rule thickness in points. Defaults to ``6.0``.
            line_color: Rule colour as ``"#RRGGBB"`` or ``"auto"``. Defaults to ``"auto"``.

        Returns:
            A live :class:`~navyfox.paragraph.HorizontalRule` proxy.
        """
        from navyfox.paragraph import HorizontalRule

        return self._block_append(
            HorizontalRule(line_style=line_style, line_width=line_width, line_color=line_color)
        )

    def add_bullet(self, text: str = "", level: int = 0) -> Paragraph:
        """Append a bullet list item and return the live proxy.

        Args:
            text: Item text.
            level: Nesting level (0–8). Defaults to ``0``.
        """
        from navyfox.paragraph import Paragraph

        return self._block_append(Paragraph(text, list_style="bullet", list_level=level))

    def add_numbered(self, text: str = "", level: int = 0) -> Paragraph:
        """Append a numbered list item and return the live proxy.

        Args:
            text: Item text.
            level: Nesting level (0–8). Defaults to ``0``.
        """
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
        """Append a standalone paragraph containing a single inline image.

        Creates a new blank paragraph, appends the image to it, and returns
        the live :class:`~navyfox.image.Image` proxy — the same pattern as
        ``python-docx``'s ``add_picture()``.

        Args:
            src: Path to an image file. Content type is inferred from the
                extension unless *content_type* is also given.
            data: Raw image bytes (alternative to *src*).
            content_type: MIME type, e.g. ``"image/png"``.
            width: Display width in inches. ``0.0`` uses the image's natural size.
            height: Display height in inches. ``0.0`` uses the image's natural size.
            alt_text: Accessibility description for screen readers.

        Returns:
            A live :class:`~navyfox.image.Image` proxy for the inserted image.
        """
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
