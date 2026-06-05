"""Table, Row, and Cell proxy types."""

from __future__ import annotations

from collections.abc import Generator, Iterator
from typing import Any, Literal, overload, override

from navyfox._block import BlockContainerMixin
from navyfox._block import BlockCtx as _BlockCtx
from navyfox._collection import DocumentView
from navyfox._proxy.base import ElementState, Element
from navyfox._proxy.descriptors import BoolProperty, ChoiceProperty, FloatProperty, StringProperty
from navyfox.paragraph import Paragraph


class Cell(BlockContainerMixin, Element):
    """A single table cell.

    Cells are live proxies — always accessed through a :class:`Row`:

    .. code-block:: python

        cell = table.rows[0].cells[0]
        cell.text = "Header"
        cell.vertical_alignment = "center"

    Or via the shorthand ``table[row, col]`` and ``table.cell(row, col)``:

    .. code-block:: python

        table[0, 0].text = "Header"

    Cells are block containers — they support the same ``add_paragraph``,
    ``add_table``, ``paragraphs``, and ``tables`` API as a document body.
    Iterating a cell yields block elements (paragraphs and tables) in
    document order.
    """

    __slots__ = ()
    _child_type_name = "cell"

    text = StringProperty("text", default="")
    width = FloatProperty("width", default=0.0)  # inches
    vertical_alignment: ChoiceProperty[Literal["top", "center", "bottom"]] = ChoiceProperty(
        "vertical_alignment", ("top", "center", "bottom"), default="top"
    )
    merge_up = StringProperty("merge_up", default="")  # "restart" | "continue" | ""
    merge_left = StringProperty("merge_left", default="")

    def __init__(self) -> None:
        super().__init__()

    @override
    def _block_context(self) -> _BlockCtx | None:
        if not self._is_live:
            return None
        self._check_valid()
        handle, doc = self._require_live()
        return handle, self._get_lib(), doc

    def merge(self, other: Cell) -> None:
        raise NotImplementedError("Cell.merge() is not yet implemented in v1.")

    @override
    def _copy_data(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "width": self.width,
            "vertical_alignment": self.vertical_alignment,
        }

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Cell(<stale>)"
        native = self._native
        if native is None:
            return "Cell(spec)"
        try:
            return f"Cell(text={self.text!r}, handle={native!r})"
        except Exception:
            return f"Cell(handle={native!r})"

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text)

    def __len__(self) -> int:
        if not self._is_live:
            return 0
        self._check_valid()
        try:
            return self._get_lib().get_count(self._require_native, "body")
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Paragraph | Table]:
        if not self._is_live:
            return iter([])
        self._check_valid()
        handle, doc = self._require_live()
        return iter(DocumentView(handle, doc, self._get_lib(), (Paragraph, Table), "body"))


class Row(Element):
    """A table row — a live proxy that provides access to its :attr:`cells`.

    Rows are accessed through :attr:`Table.rows`:

    .. code-block:: python

        row = table.rows[0]
        for cell in row:
            print(cell.text)

    Or via index shorthand on the table:

    .. code-block:: python

        row = table[0]    # same as table.rows[0]
    """

    __slots__ = ()
    _child_type_name = "row"

    height = FloatProperty("height", default=0.0)  # points, 0 = auto
    height_rule: ChoiceProperty[Literal["auto", "exact", "atLeast"]] = ChoiceProperty(
        "height_rule", ("auto", "exact", "atLeast"), default="auto"
    )
    is_header = BoolProperty("is_header")
    cant_split = BoolProperty("cant_split")

    def __init__(self) -> None:
        super().__init__()

    @property
    def cells(self) -> DocumentView[Cell]:
        if not self._is_live:
            return DocumentView.empty(Cell, "cells")
        self._check_valid()
        handle, doc = self._require_live()
        return DocumentView(handle, doc, self._get_lib(), Cell, "cells")

    @override
    def _copy_data(self) -> dict[str, Any]:
        return {
            "height": self.height,
            "height_rule": self.height_rule,
        }

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Row(<stale>)"
        native = self._native
        if native is None:
            return "Row(spec)"
        return f"Row(handle={native!r})"

    def __bool__(self) -> bool:
        try:
            return len(self.cells) > 0
        except Exception:
            return False

    def __len__(self) -> int:
        if self._is_live:
            self._check_valid()
        try:
            return len(self.cells)
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Cell]:
        return iter(self.cells)

    def __getitem__(self, index: int) -> Cell:
        return self.cells[index]


class Table(Element):
    """A table element — either a live proxy or a construction object.

    **Construction**::

        table = Table(rows=3, cols=4, style="TableGrid")
        doc.tables.append(table)

    **Live proxy** (from doc.tables[i])::

        table = doc.tables[0]
        table.cell(0, 0).text = "Header"
    """

    __slots__ = ()
    _child_type_name = "table"

    style = StringProperty("style", default="TableGrid")
    alignment: ChoiceProperty[Literal["left", "center", "right"]] = ChoiceProperty(
        "alignment", ("left", "center", "right")
    )
    width = FloatProperty("width", default=0.0)  # inches
    indent = FloatProperty("indent", default=0.0)  # left indent, inches
    cell_spacing = FloatProperty("cell_spacing", default=0.0)  # points

    def __init__(
        self,
        rows: int,
        cols: int,
        *,
        style: str = "TableGrid",
    ) -> None:
        super().__init__()
        data: dict[str, Any] = {"rows": rows, "cols": cols}
        if style != "TableGrid":
            data["style"] = style
        self._data = data

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    @property
    def rows(self) -> DocumentView[Row]:
        if not self._is_live:
            return DocumentView.empty(Row, "rows")
        self._check_valid()
        handle, doc = self._require_live()
        return DocumentView(handle, doc, self._get_lib(), Row, "rows")

    @property
    def columns(self) -> DocumentView[Row]:
        raise NotImplementedError("Table.columns is not yet implemented in v1.")

    @property
    def cells(self) -> DocumentView[Cell]:
        if not self._is_live:
            return DocumentView.empty(Cell, "cells")
        self._check_valid()
        handle, doc = self._require_live()
        return DocumentView(handle, doc, self._get_lib(), Cell, "cells")

    @property
    def data(self) -> Generator[list[str], None, None]:
        """Plain text grid — plug directly into a DataFrame constructor."""
        if not self._is_live:
            yield []
            return

        for row in self.rows:
            yield [cell.text for cell in row.cells]

    def cell(self, row: int, col: int) -> Cell:
        """Return the cell at (row, col)."""
        if not self._is_live:
            raise ValueError("Cannot access cell on a construction-object Table.")
        self._check_valid()
        return self.rows[row].cells[col]

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    @override
    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._data)
        return dict(
            style=self.style,
            alignment=self.alignment,
        )

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Table(<stale>)"
        native = self._native
        if native is None:
            d = self._data
            return f"Table(rows={d.get('rows')}, cols={d.get('cols')})"
        try:
            return f"Table(rows={len(self.rows)}, handle={native!r})"
        except Exception:
            return f"Table(handle={native!r})"

    def __bool__(self) -> bool:
        try:
            return len(self.rows) > 0
        except Exception:
            return False

    def __len__(self) -> int:
        if self._is_live:
            self._check_valid()
        try:
            return len(self.rows)
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Row]:
        return iter(self.rows)

    def __contains__(self, row: object) -> bool:
        return row in self.rows

    @overload
    def __getitem__(self, index: int) -> Row: ...
    @overload
    def __getitem__(self, index: tuple[int, int]) -> Cell: ...

    def __getitem__(self, index: int | tuple[int, int]) -> Row | Cell:
        if isinstance(index, tuple):
            row, col = index
            return self.cell(row, col)
        return self.rows[index]
