from typing import Any, Literal, Self

from navyfox._proxy.base import Element as _Element
from navyfox.units import Color as Color

class Run(_Element):
    text: str
    style: str
    bold: bool
    italic: bool
    strikethrough: bool
    all_caps: bool
    small_caps: bool
    superscript: bool
    subscript: bool
    hidden: bool
    emboss: bool
    imprint: bool
    outline: bool
    shadow: bool
    no_spell_check: bool
    no_grammar_check: bool

    @property
    def underline(self) -> Literal["single", "double", "dotted", "dashed", "wave"] | None: ...
    @underline.setter
    def underline(
        self,
        value: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None,
    ) -> None: ...
    @property
    def color(self) -> str | None: ...
    @color.setter
    def color(self, value: str | Color | None) -> None: ...

    highlight: (
        Literal[
            "yellow",
            "green",
            "cyan",
            "magenta",
            "blue",
            "red",
            "dark_blue",
            "dark_cyan",
            "dark_green",
            "dark_magenta",
            "dark_red",
            "dark_yellow",
            "dark_gray",
            "light_gray",
            "black",
            "white",
        ]
        | None
    )

    font_name: str
    font_name_eastasia: str
    font_name_complex: str
    font_size: float
    font_scale: float
    character_spacing: float
    kerning: float
    baseline: float
    language: str

    def __init__(
        self,
        text: str = "",
        *,
        style: str = "",
        bold: bool = False,
        italic: bool = False,
        strikethrough: bool = False,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] = False,
        all_caps: bool = False,
        small_caps: bool = False,
        superscript: bool = False,
        subscript: bool = False,
        hidden: bool = False,
        emboss: bool = False,
        imprint: bool = False,
        outline: bool = False,
        shadow: bool = False,
        color: str | Color | None = None,
        highlight: str | None = None,
        font_name: str = "",
        font_size: float = 0.0,
        language: str = "",
    ) -> None: ...
    def set_bold(self, value: bool = True) -> Self: ...
    def set_italic(self, value: bool = True) -> Self: ...
    def set_strikethrough(self, value: bool = True) -> Self: ...
    def set_underline(
        self,
        value: bool | Literal["single", "double", "dotted", "dashed", "wave"] = True,
    ) -> Self: ...
    def set_all_caps(self, value: bool = True) -> Self: ...
    def set_small_caps(self, value: bool = True) -> Self: ...
    def set_superscript(self, value: bool = True) -> Self: ...
    def set_subscript(self, value: bool = True) -> Self: ...
    def set_hidden(self, value: bool = True) -> Self: ...
    def set_color(self, value: str | Color) -> Self: ...
    def set_highlight(self, value: str) -> Self: ...
    def set_font(self, name: str, size: float | None = None) -> Self: ...
    def set_language(self, tag: str) -> Self: ...
    def format(
        self,
        *,
        style: str = ...,
        text: str = ...,
        bold: bool = ...,
        italic: bool = ...,
        strikethrough: bool = ...,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] = ...,
        all_caps: bool = ...,
        small_caps: bool = ...,
        superscript: bool = ...,
        subscript: bool = ...,
        hidden: bool = ...,
        emboss: bool = ...,
        imprint: bool = ...,
        outline: bool = ...,
        shadow: bool = ...,
        color: str | Color | None = ...,
        highlight: str | None = ...,
        font_name: str = ...,
        font_size: float = ...,
        language: str = ...,
    ) -> Self: ...
    def _copy_data(self) -> dict[str, Any]: ...
    def split(self, index: int) -> tuple[Run, Run]: ...
    def copy(self) -> Run: ...
    def __add__(self, other: Run) -> Run: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __bool__(self) -> bool: ...
    def __len__(self) -> int: ...
