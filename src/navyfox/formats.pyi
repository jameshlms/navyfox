from typing import Literal

class RGBColor:
    r: int
    g: int
    b: int
    def __init__(self, r: int, g: int, b: int) -> None: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...

class IndentFormat:
    left: float
    right: float
    first_line: float
    def __init__(
        self,
        left: float = ...,
        right: float = ...,
        first_line: float = ...,
    ) -> None: ...

class SpacingFormat:
    before: float
    after: float
    line: float
    line_rule: Literal["auto", "exact", "atLeast"]
    def __init__(
        self,
        before: float = ...,
        after: float = ...,
        line: float = ...,
        line_rule: Literal["auto", "exact", "atLeast"] = ...,
    ) -> None: ...

class ListFormat:
    num_id: int
    level: int
    def __init__(self, num_id: int = ..., level: int = ...) -> None: ...

class Border:
    style: Literal["single", "double", "dotted", "dashed", "wave", "none"]
    width: float
    color: str
    spacing: float
    shadow: bool
    def __init__(
        self,
        style: Literal["single", "double", "dotted", "dashed", "wave", "none"] = ...,
        width: float = ...,
        color: str = ...,
        spacing: float = ...,
        shadow: bool = ...,
    ) -> None: ...

class ParagraphBorders:
    top: Border
    bottom: Border
    left: Border
    right: Border
    def __init__(
        self,
        top: Border = ...,
        bottom: Border = ...,
        left: Border = ...,
        right: Border = ...,
    ) -> None: ...

class TableBorders:
    top: Border
    bottom: Border
    left: Border
    right: Border
    inside_h: Border
    inside_v: Border
    def __init__(
        self,
        top: Border = ...,
        bottom: Border = ...,
        left: Border = ...,
        right: Border = ...,
        inside_h: Border = ...,
        inside_v: Border = ...,
    ) -> None: ...

class CellBorders:
    top: Border
    bottom: Border
    left: Border
    right: Border
    def __init__(
        self,
        top: Border = ...,
        bottom: Border = ...,
        left: Border = ...,
        right: Border = ...,
    ) -> None: ...

class Shading:
    fill: str
    color: str
    pattern: str
    def __init__(
        self,
        fill: str = ...,
        color: str = ...,
        pattern: str = ...,
    ) -> None: ...

class PageMargins:
    top: float
    bottom: float
    left: float
    right: float
    header: float
    footer: float
    def __init__(
        self,
        all_sides: float | None = ...,
        *,
        top: float = ...,
        bottom: float = ...,
        left: float = ...,
        right: float = ...,
        header: float = ...,
        footer: float = ...,
    ) -> None: ...
    @classmethod
    def uniform(
        cls, value: float, *, header: float = ..., footer: float = ...
    ) -> PageMargins: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...

class ColumnFormat:
    count: int
    spacing: float
    equal_width: bool
    def __init__(
        self,
        count: int = ...,
        spacing: float = ...,
        equal_width: bool = ...,
    ) -> None: ...

class CellMargin:
    top: float
    bottom: float
    left: float
    right: float
    def __init__(
        self,
        top: float = ...,
        bottom: float = ...,
        left: float = ...,
        right: float = ...,
    ) -> None: ...
