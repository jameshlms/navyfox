"""Run proxy."""

from __future__ import annotations

from typing import Any, Literal, Self, TypedDict, Unpack, override

from navyfox._proxy.base import ElementState, ProxyBase
from navyfox._proxy.descriptors import (
    BoolProperty,
    ChoiceProperty,
    ColorProperty,
    FloatProperty,
    StringProperty,
)
from navyfox.units import Color


class _RunFormat(TypedDict, total=False):
    style: str
    text: str
    bold: bool
    italic: bool
    strikethrough: bool
    underline: bool | Literal["single", "double", "dotted", "dashed", "wave"]
    all_caps: bool
    small_caps: bool
    superscript: bool
    subscript: bool
    hidden: bool
    emboss: bool
    imprint: bool
    outline: bool
    shadow: bool
    color: str | Color | None
    highlight: str | None
    font_name: str
    font_size: float
    language: str


class Run(ProxyBase):
    """A run element — a contiguous span of text with uniform character formatting.

    **Construction** (before appending to a paragraph):

    .. code-block:: python

        run = Run("Hello", bold=True, font_name="Arial", font_size=12)
        para.runs.append(run)

    **Live proxy** (from ``para.runs[i]`` or ``para.add_run()``):

    .. code-block:: python

        run = para.runs[0]
        run.bold = True
        run.color = "#FF0000"

    **Mutually exclusive pairs** — setting both raises ``ValueError``:

    - ``all_caps`` and ``small_caps``
    - ``superscript`` and ``subscript``
    - ``emboss`` and ``imprint``

    For bulk edits use the :meth:`edit` context manager to batch all writes
    into a single FFI call.
    """

    __slots__ = ()
    _child_type_name = "run"

    # Text
    text = StringProperty("text", default="")

    # Character style by name
    style = StringProperty("style", default="")

    # Formatting — boolean
    bold = BoolProperty("bold")
    italic = BoolProperty("italic")
    strikethrough = BoolProperty("strikethrough")
    all_caps = BoolProperty("all_caps")
    small_caps = BoolProperty("small_caps")
    superscript = BoolProperty("superscript")
    subscript = BoolProperty("subscript")
    hidden = BoolProperty("hidden")
    emboss = BoolProperty("emboss")
    imprint = BoolProperty("imprint")
    outline = BoolProperty("outline")
    shadow = BoolProperty("shadow")
    no_spell_check = BoolProperty("no_spell_check")
    no_grammar_check = BoolProperty("no_grammar_check")

    # Formatting — underline (bool or named style)
    underline: ChoiceProperty[Literal["single", "double", "dotted", "dashed", "wave"]] = (
        ChoiceProperty(
            "underline",
            ("single", "double", "dotted", "dashed", "wave"),
            allow_bool=True,
        )
    )

    # Formatting — colour and highlight
    color = ColorProperty("color")
    highlight: ChoiceProperty[
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
    ] = ChoiceProperty(
        "highlight",
        (
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
        ),
    )

    # Formatting — font
    font_name = StringProperty("font_name", default="")
    font_name_eastasia = StringProperty("font_name_eastasia", default="")
    font_name_complex = StringProperty("font_name_complex", default="")
    font_size = FloatProperty("font_size", default=0.0)  # points, 0 = inherit
    font_scale = FloatProperty("font_scale", default=100.0)  # percentage
    character_spacing = FloatProperty("character_spacing", default=0.0)  # points
    kerning = FloatProperty("kerning", default=0.0)  # threshold in points
    baseline = FloatProperty("baseline", default=0.0)  # points, positive = up

    # Miscellaneous
    language = StringProperty("language", default="")

    _MUTEX_PAIRS = (
        ("all_caps", "small_caps"),
        ("superscript", "subscript"),
        ("emboss", "imprint"),
    )

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
    ) -> None:
        _check_mutex(
            all_caps=all_caps,
            small_caps=small_caps,
            superscript=superscript,
            subscript=subscript,
            emboss=emboss,
            imprint=imprint,
        )
        super().__init__()
        data: dict[str, Any] = {}
        if text:
            data["text"] = text
        if style:
            data["style"] = style
        if bold:
            data["bold"] = True
        if italic:
            data["italic"] = True
        if strikethrough:
            data["strikethrough"] = True
        if underline:
            data["underline"] = "single" if underline is True else underline
        if all_caps:
            data["all_caps"] = True
        if small_caps:
            data["small_caps"] = True
        if superscript:
            data["superscript"] = True
        if subscript:
            data["subscript"] = True
        if hidden:
            data["hidden"] = True
        if emboss:
            data["emboss"] = True
        if imprint:
            data["imprint"] = True
        if outline:
            data["outline"] = True
        if shadow:
            data["shadow"] = True
        if color is not None:
            data["color"] = Color.normalize(color)
        if highlight:
            data["highlight"] = highlight
        if font_name:
            data["font_name"] = font_name
        if font_size:
            data["font_size"] = font_size
        if language:
            data["language"] = language
        self._data = data

    def set_bold(self, value: bool = True) -> Self:
        """Set bold and return *self* for chaining."""
        self.bold = value
        return self

    def set_italic(self, value: bool = True) -> Self:
        """Set italic and return *self* for chaining."""
        self.italic = value
        return self

    def set_strikethrough(self, value: bool = True) -> Self:
        """Set strikethrough and return *self* for chaining."""
        self.strikethrough = value
        return self

    def set_underline(self, value: bool | str = True) -> Self:
        """Set underline style and return *self* for chaining.

        Args:
            value: ``True`` for single underline, ``False`` to clear, or a named
                style: ``"single"``, ``"double"``, ``"dotted"``, ``"dashed"``, ``"wave"``.
        """
        self.underline = value  # type: ignore[assignment]
        return self

    def set_all_caps(self, value: bool = True) -> Self:
        """Set all-caps and return *self* for chaining. Mutually exclusive with ``small_caps``."""
        self.all_caps = value
        return self

    def set_small_caps(self, value: bool = True) -> Self:
        """Set small-caps and return *self* for chaining. Mutually exclusive with ``all_caps``."""
        self.small_caps = value
        return self

    def set_superscript(self, value: bool = True) -> Self:
        """Set superscript and return *self* for chaining. Mutually exclusive with ``subscript``."""
        self.superscript = value
        return self

    def set_subscript(self, value: bool = True) -> Self:
        """Set subscript and return *self* for chaining. Mutually exclusive with ``superscript``."""
        self.subscript = value
        return self

    def set_hidden(self, value: bool = True) -> Self:
        """Set hidden (non-printing) and return *self* for chaining."""
        self.hidden = value
        return self

    def set_color(self, value: str | Color) -> Self:
        """Set text colour and return *self* for chaining.

        Args:
            value: A :class:`~navyfox.units.Color` instance, ``"#RRGGBB"`` hex string,
                or ``"auto"``.
        """
        self.color = value
        return self

    def set_highlight(self, value: str) -> Self:
        """Set highlight colour and return *self* for chaining.

        Args:
            value: A named highlight colour such as ``"yellow"``, ``"cyan"``, ``"green"``, etc.
        """
        self.highlight = value  # type: ignore[assignment]
        return self

    def set_font(self, name: str, size: float | None = None) -> Self:
        """Set font name (and optionally size) and return *self* for chaining.

        Args:
            name: Font family name, e.g. ``"Arial"`` or ``"Times New Roman"``.
            size: Font size in points. Omit to leave the current size unchanged.
        """
        self.font_name = name
        if size is not None:
            self.font_size = size
        return self

    def set_language(self, tag: str) -> Self:
        """Set the language tag (BCP-47) and return *self* for chaining.

        Args:
            tag: Language tag, e.g. ``"en-US"`` or ``"fr-FR"``.
        """
        self.language = tag
        return self

    # ------------------------------------------------------------------
    # format() — batch writes into a single set_many call
    # ------------------------------------------------------------------

    def format(self, **kwargs: Unpack[_RunFormat]) -> Self:
        """Set multiple run properties in a single FFI call and return *self*.

        Only the keyword arguments you pass are changed; omitted properties are
        left untouched. Raises :exc:`ValueError` for mutually exclusive pairs
        (``all_caps``/``small_caps``, ``superscript``/``subscript``,
        ``emboss``/``imprint``) before any write is attempted.

        Args:
            text: Run text content.
            bold: Bold weight.
            italic: Italic style.
            strikethrough: Strikethrough decoration.
            underline: ``True`` for single underline, ``False`` to clear, or a
                named style: ``"single"``, ``"double"``, ``"dotted"``,
                ``"dashed"``, ``"wave"``.
            all_caps: All-caps transform. Mutually exclusive with ``small_caps``.
            small_caps: Small-caps transform. Mutually exclusive with ``all_caps``.
            superscript: Superscript baseline. Mutually exclusive with ``subscript``.
            subscript: Subscript baseline. Mutually exclusive with ``superscript``.
            hidden: Hidden (non-printing) text.
            emboss: Emboss effect. Mutually exclusive with ``imprint``.
            imprint: Imprint (engrave) effect. Mutually exclusive with ``emboss``.
            outline: Outline effect.
            shadow: Shadow effect.
            color: Text colour as ``"#RRGGBB"``, ``"auto"``, or a
                :class:`~navyfox.units.Color` instance.
            highlight: Named highlight colour, e.g. ``"yellow"``.
            font_name: Font family name.
            font_size: Font size in points.
            language: BCP-47 language tag, e.g. ``"en-US"``.

        Returns:
            *self*, allowing chaining.

        Example:
            .. code-block:: python

                run.format(bold=True, italic=True, color="#CC0000", font_size=14)
        """
        _check_mutex(
            all_caps=bool(kwargs.get("all_caps")),
            small_caps=bool(kwargs.get("small_caps")),
            superscript=bool(kwargs.get("superscript")),
            subscript=bool(kwargs.get("subscript")),
            emboss=bool(kwargs.get("emboss")),
            imprint=bool(kwargs.get("imprint")),
        )

        changes: dict[str, Any] = dict(kwargs)

        if "underline" in changes:
            underline = changes.pop("underline")
            if underline is True:
                changes["underline"] = "single"
            elif underline is False:
                changes["underline"] = ""
            else:
                changes["underline"] = underline

        if "color" in changes:
            changes["color"] = Color.normalize(changes.pop("color"))

        self._apply_changes(changes)
        return self

    # ------------------------------------------------------------------
    # split() and __add__
    # ------------------------------------------------------------------

    def split(self, index: int) -> tuple[Run, Run]:
        """Split the run at *index* and return two new construction-state runs.

        The two returned runs share all formatting of the original. The original
        run is left in an undefined state and should not be used afterwards.

        Args:
            index: Character position at which to split. Characters ``[:index]``
                go to the first run, ``[index:]`` to the second.

        Returns:
            A tuple ``(left, right)`` of new construction-state :class:`Run` objects.
        """
        text = self.text
        a = Run(text[:index])
        b = Run(text[index:])
        data = self._data
        for k, v in data.items():
            if k != "text":
                a._data[k] = v
                b._data[k] = v
        return a, b

    def __add__(self, other: Run) -> Run:
        if type(other) is not Run:
            return NotImplemented
        self_data = self._data
        other_data = other._data
        # Check formatting compatibility (excluding text)
        self_fmt = {k: v for k, v in self_data.items() if k != "text"}
        other_fmt = {k: v for k, v in other_data.items() if k != "text"}
        if self_fmt != other_fmt:
            raise ValueError(
                "Cannot concatenate Runs with different formatting. "
                "Use str concatenation on .text instead."
            )
        return Run(self.text + other.text, **self_fmt)

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    @override
    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._data)
        lib = self._get_lib()
        native = self._require_native

        def get_bool(name: str) -> bool:
            return lib.get_int(native, name) > 0

        def get_str(name: str) -> str:
            try:
                return lib.get_str(native, name) or ""
            except Exception:
                return ""

        def get_str_or_none(name: str) -> str | None:
            try:
                v = lib.get_str(native, name)
                return v or None
            except Exception:
                return None

        def get_float(name: str, default: float = 0.0) -> float:
            try:
                return lib.get_float(native, name)
            except Exception:
                return default

        return dict(
            text=get_str("text"),
            style=get_str("style"),
            bold=get_bool("bold"),
            italic=get_bool("italic"),
            strikethrough=get_bool("strikethrough"),
            underline=get_str_or_none("underline"),
            all_caps=get_bool("all_caps"),
            small_caps=get_bool("small_caps"),
            superscript=get_bool("superscript"),
            subscript=get_bool("subscript"),
            hidden=get_bool("hidden"),
            emboss=get_bool("emboss"),
            imprint=get_bool("imprint"),
            outline=get_bool("outline"),
            shadow=get_bool("shadow"),
            no_spell_check=get_bool("no_spell_check"),
            no_grammar_check=get_bool("no_grammar_check"),
            color=get_str_or_none("color"),
            highlight=get_str_or_none("highlight"),
            font_name=get_str("font_name"),
            font_name_eastasia=get_str("font_name_eastasia"),
            font_name_complex=get_str("font_name_complex"),
            font_size=get_float("font_size"),
            font_scale=get_float("font_scale", 100.0),
            character_spacing=get_float("character_spacing"),
            kerning=get_float("kerning"),
            baseline=get_float("baseline"),
            language=get_str("language"),
        )

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Run(<stale>)"
        native = self._native
        if native is None:
            text = self._data.get("text", "")
            return f"Run({text!r})"
        try:
            return f"Run(text={self.text!r}, handle={native!r})"
        except Exception:
            return f"Run(handle={native!r})"

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text)

    def __len__(self) -> int:
        return len(self.text)


def _check_mutex(**kwargs: bool) -> None:
    pairs = (
        ("all_caps", "small_caps"),
        ("superscript", "subscript"),
        ("emboss", "imprint"),
    )
    for a, b in pairs:
        if kwargs.get(a) and kwargs.get(b):
            raise ValueError(f"{a!r} and {b!r} are mutually exclusive — set only one at a time.")
