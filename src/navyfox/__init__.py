"""NavyFox — Pythonic ``.docx`` manipulation backed by a C# Native AOT library.

All document data lives in the C# layer; Python holds lightweight proxy objects
(handles). The central types are:

- :class:`Document` — open, create, and save ``.docx`` files
- :class:`Paragraph` / :class:`Run` — block text and character-level spans
- :class:`Table` / :class:`Row` / :class:`Cell` — tabular content
- :class:`Section` — page-layout containers
- :class:`Style` / :class:`StyleCollection` — style definitions

Use :func:`snapshot` to capture a document-independent copy of any proxy element
so it can be used after the document is closed.
"""

from navyfox._collection import DocumentView
from navyfox._proxy.base import Definition, Element, NativeProxy
from navyfox.document import Document
from navyfox.errors import (
    DocumentClosedError,
    NativeRuntimeError,
    NavyFoxError,
    OwnershipError,
    StaleProxyError,
)
from navyfox.formats import (
    Border,
    CellBorders,
    CellMargin,
    ColumnFormat,
    IndentFormat,
    ListFormat,
    PageMargins,
    ParagraphBorders,
    RGBColor,
    Shading,
    SpacingFormat,
    TableBorders,
)
from navyfox.hyperlink import Hyperlink
from navyfox.image import Image
from navyfox.paragraph import HorizontalRule, Paragraph
from navyfox.run import Run
from navyfox.section import Section
from navyfox.styles import (
    AnyStyle,
    CharacterStyle,
    NumberingStyle,
    ParagraphStyle,
    Style,
    StyleCollection,
    TableStyle,
)
from navyfox.table import Cell, Row, Table
from navyfox.units import (
    Centimeters,
    Color,
    Inches,
    Length,
    Millimeters,
    Points,
    Twips,
)


def snapshot[T: NativeProxy](elem: T) -> T:
    """Return a document-independent copy of *elem*.

    The snapshot has no native handle and can be safely used after the source
    document is closed. For content elements (:class:`Paragraph`, :class:`Run`,
    :class:`Table`, etc.) the copy can also be appended to a different document.

    Args:
        elem: Any live proxy — content element or definition
            (:class:`Paragraph`, :class:`Run`, :class:`Table`, :class:`Style`, etc.).

    Returns:
        A new snapshot object of the same type with all properties copied from *elem*.

    Example:
        .. code-block:: python

            with Document.open("report.docx") as doc:
                para = doc.paragraphs[0]
                snap = snapshot(para)   # copy data before close

            # doc is closed — snap is still valid
            print(snap.text)
    """
    return elem.__copydocelem__()


__all__ = [
    # Core
    "snapshot",
    "NativeProxy",
    "Element",
    "Definition",
    "Document",
    "DocumentView",
    "Paragraph",
    "HorizontalRule",
    "Run",
    "Image",
    "Hyperlink",
    "Table",
    "Row",
    "Cell",
    "Section",
    # Styles
    "AnyStyle",
    "Style",
    "ParagraphStyle",
    "CharacterStyle",
    "TableStyle",
    "NumberingStyle",
    "StyleCollection",
    # Format types
    "RGBColor",
    "Color",
    "Inches",
    "Centimeters",
    "Millimeters",
    "Twips",
    "Points",
    "Length",
    "Border",
    "ParagraphBorders",
    "TableBorders",
    "CellBorders",
    "Shading",
    "IndentFormat",
    "SpacingFormat",
    "ListFormat",
    "PageMargins",
    "CellMargin",
    "ColumnFormat",
    # Errors
    "NavyFoxError",
    "NativeRuntimeError",
    "DocumentClosedError",
    "StaleProxyError",
    "OwnershipError",
]

__version__ = "0.1.0"
