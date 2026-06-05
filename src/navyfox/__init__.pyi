from navyfox._collection import DocumentView as DocumentView
from navyfox._proxy.base import Element as Element
from navyfox.document import Document as Document
from navyfox.errors import (
    DocumentClosedError as DocumentClosedError,
)
from navyfox.errors import (
    NativeRuntimeError as NativeRuntimeError,
)
from navyfox.errors import (
    NavyFoxError as NavyFoxError,
)
from navyfox.errors import (
    OwnershipError as OwnershipError,
)
from navyfox.errors import (
    StaleProxyError as StaleProxyError,
)
from navyfox.formats import (
    Border as Border,
)
from navyfox.formats import (
    CellBorders as CellBorders,
)
from navyfox.formats import (
    CellMargin as CellMargin,
)
from navyfox.formats import (
    ColumnFormat as ColumnFormat,
)
from navyfox.formats import (
    IndentFormat as IndentFormat,
)
from navyfox.formats import (
    ListFormat as ListFormat,
)
from navyfox.formats import (
    PageMargins as PageMargins,
)
from navyfox.formats import (
    ParagraphBorders as ParagraphBorders,
)
from navyfox.formats import (
    RGBColor as RGBColor,
)
from navyfox.formats import (
    Shading as Shading,
)
from navyfox.formats import (
    SpacingFormat as SpacingFormat,
)
from navyfox.formats import (
    TableBorders as TableBorders,
)
from navyfox.hyperlink import Hyperlink as Hyperlink
from navyfox.image import Image as Image
from navyfox.paragraph import HorizontalRule as HorizontalRule
from navyfox.paragraph import Paragraph as Paragraph
from navyfox.run import Run as Run
from navyfox.section import Section as Section
from navyfox.styles import Style as Style
from navyfox.styles import StyleCollection as StyleCollection
from navyfox.table import Cell as Cell
from navyfox.table import Row as Row
from navyfox.table import Table as Table
from navyfox.units import Centimeters as Centimeters
from navyfox.units import Color as Color
from navyfox.units import Inches as Inches
from navyfox.units import Length as Length
from navyfox.units import Millimeters as Millimeters
from navyfox.units import Points as Points
from navyfox.units import Twips as Twips

__version__: str

def snapshot[T: Element](elem: T) -> T: ...
