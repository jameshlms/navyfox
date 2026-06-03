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
from navyfox._proxy.base import ProxyBase as _ProxyBase
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
from navyfox.styles import Style, StyleCollection
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


def snapshot[T: _ProxyBase](elem: T) -> T:
    """Return a document-independent copy of *elem*.

    The returned object is in *construction state* — it has no native handle and
    can be safely used after the source document is closed. It can also be
    appended to a different document.

    Args:
        elem: Any live or construction-state proxy
            (:class:`Paragraph`, :class:`Run`, :class:`Table`, etc.).

    Returns:
        A new construction-state object of the same type with all properties
        copied from *elem*.

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
    "Style",
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
