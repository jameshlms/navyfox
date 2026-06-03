"""Plain Python data types for formatting properties.

These are pure Python dataclasses — no C# handles, no FFI. They are used as
property values on proxy objects and are returned by ``snapshot()`` / ``copy()``.
All instances are mutable unless otherwise noted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from navyfox.units import Color

# Backward-compatible alias — prefer Color directly.
RGBColor = Color


# ---------------------------------------------------------------------------
# Paragraph format types
# ---------------------------------------------------------------------------


@dataclass
class IndentFormat:
    """Paragraph indentation values, all in **inches**."""

    #: Left indent from the margin.
    left: float = 0.0
    #: Right indent from the margin.
    right: float = 0.0
    #: First-line indent (positive) or hanging indent (negative).
    first_line: float = 0.0


@dataclass
class SpacingFormat:
    """Paragraph spacing values."""

    #: Space before the paragraph in **points**.
    before: float = 0.0
    #: Space after the paragraph in **points**.
    after: float = 0.0
    #: Line-spacing multiplier (``1.0`` = single, ``1.5`` = 1.5×, ``2.0`` = double).
    #: Ignored when *line_rule* is ``"exact"`` or ``"atLeast"``.
    line: float = 0.0
    #: How *line* is interpreted — ``"auto"`` (multiplier), ``"exact"`` (fixed points),
    #: or ``"atLeast"`` (minimum points).
    line_rule: Literal["auto", "exact", "atLeast"] = "auto"


@dataclass
class ListFormat:
    """Raw list/numbering identifiers (v1 exposes only the IDs, not full list formatting)."""

    #: Numbering definition ID from the document's ``numbering.xml``.
    num_id: int = 0
    #: Zero-based list level (0 = outermost).
    level: int = 0


# ---------------------------------------------------------------------------
# Border / Shading
# ---------------------------------------------------------------------------


@dataclass
class Border:
    """A single border line on a paragraph, table, or cell."""

    #: Line style — one of ``"single"``, ``"double"``, ``"dotted"``,
    #: ``"dashed"``, ``"wave"``, ``"none"``.
    style: Literal["single", "double", "dotted", "dashed", "wave", "none"] = "none"
    #: Line thickness in **points**.
    width: float = 0.0
    #: Line colour as ``"#RRGGBB"`` / ``"RRGGBB"`` or ``"auto"``.
    color: str = "auto"
    #: Distance from the nearest text edge in **points**.
    spacing: float = 0.0
    #: Whether a drop-shadow is applied to the border.
    shadow: bool = False


@dataclass
class ParagraphBorders:
    """All four border sides of a paragraph."""

    top: Border = field(default_factory=Border)
    bottom: Border = field(default_factory=Border)
    left: Border = field(default_factory=Border)
    right: Border = field(default_factory=Border)


@dataclass
class TableBorders:
    """Outer and inner border lines of a table."""

    #: Top outer edge.
    top: Border = field(default_factory=Border)
    #: Bottom outer edge.
    bottom: Border = field(default_factory=Border)
    #: Left outer edge.
    left: Border = field(default_factory=Border)
    #: Right outer edge.
    right: Border = field(default_factory=Border)
    #: Horizontal rules between rows.
    inside_h: Border = field(default_factory=Border)
    #: Vertical rules between columns.
    inside_v: Border = field(default_factory=Border)


@dataclass
class CellBorders:
    """Four border sides of a table cell."""

    top: Border = field(default_factory=Border)
    bottom: Border = field(default_factory=Border)
    left: Border = field(default_factory=Border)
    right: Border = field(default_factory=Border)


@dataclass
class Shading:
    """Background shading applied to a paragraph or cell."""

    #: Background fill colour as ``"#RRGGBB"`` / ``"RRGGBB"`` or ``"auto"``.
    fill: str = "auto"
    #: Pattern foreground colour (used with non-``"clear"`` patterns).
    color: str = "auto"
    #: Shading pattern — ``"clear"`` (no shading), ``"solid"``, or a
    #: percentage string such as ``"10"`` (10 % dot shading).
    pattern: str = "clear"


# ---------------------------------------------------------------------------
# Section format types
# ---------------------------------------------------------------------------


class PageMargins:
    """Page margins for a document section, all in **inches**.

    A single positional argument sets all four page margins uniformly::

        PageMargins(0.5)          # 0.5 in on all sides
        PageMargins.uniform(0.5)  # equivalent classmethod form
        PageMargins(top=1.0, left=0.75, right=0.75)  # explicit per-side
    """

    def __init__(
        self,
        all_sides: float | None = None,
        *,
        top: float = 1.0,
        bottom: float = 1.0,
        left: float = 1.25,
        right: float = 1.25,
        header: float = 0.5,
        footer: float = 0.5,
    ) -> None:
        if all_sides is not None:
            self.top = float(all_sides)
            self.bottom = float(all_sides)
            self.left = float(all_sides)
            self.right = float(all_sides)
        else:
            self.top = float(top)
            self.bottom = float(bottom)
            self.left = float(left)
            self.right = float(right)
        self.header = float(header)
        self.footer = float(footer)

    @classmethod
    def uniform(cls, value: float, *, header: float = 0.5, footer: float = 0.5) -> PageMargins:
        """Return a :class:`PageMargins` with *value* on all four sides."""
        return cls(float(value), header=header, footer=footer)

    def __repr__(self) -> str:
        return (
            f"PageMargins(top={self.top}, bottom={self.bottom}, "
            f"left={self.left}, right={self.right}, "
            f"header={self.header}, footer={self.footer})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PageMargins):
            return NotImplemented
        return (
            self.top == other.top
            and self.bottom == other.bottom
            and self.left == other.left
            and self.right == other.right
            and self.header == other.header
            and self.footer == other.footer
        )

    def __hash__(self) -> int:
        return hash((self.top, self.bottom, self.left, self.right, self.header, self.footer))


@dataclass
class ColumnFormat:
    """Multi-column section layout."""

    #: Number of text columns. Default ``1`` (single-column).
    count: int = 1
    #: Space between columns in **inches**. Default ``0.5``.
    spacing: float = 0.5
    #: If ``True``, all columns share equal width. Default ``True``.
    equal_width: bool = True


# ---------------------------------------------------------------------------
# Table/cell format types
# ---------------------------------------------------------------------------


@dataclass
class CellMargin:
    """Internal padding for a table cell, all in **points**."""

    #: Space above the cell content.
    top: float = 0.0
    #: Space below the cell content.
    bottom: float = 0.0
    #: Space to the left of the cell content.
    left: float = 0.0
    #: Space to the right of the cell content.
    right: float = 0.0
