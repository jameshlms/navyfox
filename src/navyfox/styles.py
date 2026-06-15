"""Style and StyleCollection."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast, overload, override

from navyfox._proxy.base import Definition, ElementState
from navyfox._proxy.descriptors import (
    BoolProperty,
    ChoiceProperty,
    ColorProperty,
    FloatProperty,
    NullableStringProperty,
    StringProperty,
)

if TYPE_CHECKING:
    from navyfox._native.handle import Handle
    from navyfox.document import Document


class Style(Definition):
    """Base class for all document style definitions.

    Obtained from :class:`StyleCollection` via ``doc.styles["Heading1"]`` or
    by iterating ``doc.styles``.

    All style types share these properties:

    - ``name`` — display name (e.g. ``"Heading 1"``)
    - ``style_id`` — internal markup id (e.g. ``"Heading1"``)
    - ``based_on`` — parent style name/id, or ``None``
    - ``is_default`` — ``True`` if this is the document's default paragraph style
    - ``type`` — ``"paragraph"``, ``"character"``, ``"table"``, or ``"numbering"``

    Use :class:`ParagraphStyle`, :class:`CharacterStyle`, :class:`TableStyle`,
    or :class:`NumberingStyle` directly when you need type-specific properties.
    """

    __slots__ = ()

    type: ClassVar[str]

    style_id = StringProperty("style_id", default="")
    name = StringProperty("style_name", default="")
    based_on = NullableStringProperty("based_on")
    is_default = BoolProperty("is_default")

    @override
    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._data)
        return self._live_copy_data()

    def _live_copy_data(self) -> dict[str, Any]:
        return {
            "style_name": self.name,
            "based_on": self.based_on,
            "is_default": self.is_default,
        }

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return f"{type(self).__name__}(<stale>)"
        if self._native is None:
            return f"{type(self).__name__}(spec)"
        try:
            return f"{type(self).__name__}({self.name!r})"
        except Exception:
            return f"{type(self).__name__}(<error>)"


class CharacterStyle(Style):
    """A character style — applies run-level formatting only.

    Character formatting properties (read/write, stored in ``<w:rPr>``):

    - ``bold``, ``italic``, ``underline``, ``color``, ``font_name``, ``font_size``
    """

    __slots__ = ()
    type: ClassVar[Literal["character"]] = "character"

    bold = BoolProperty("bold")
    italic = BoolProperty("italic")
    underline: ChoiceProperty[Literal["single", "double", "dotted", "dashed", "wave"]] = (
        ChoiceProperty(
            "underline",
            ("single", "double", "dotted", "dashed", "wave"),
            allow_bool=True,
        )
    )
    color = ColorProperty("color")
    font_name = StringProperty("font_name", default="")
    font_size = FloatProperty("font_size", default=0.0)

    @override
    def _live_copy_data(self) -> dict[str, Any]:
        return {
            **super()._live_copy_data(),
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "color": self.color,
            "font_name": self.font_name,
            "font_size": self.font_size,
        }


class ParagraphStyle(CharacterStyle):
    """A paragraph style — applies both paragraph and character formatting.

    Paragraph formatting properties (read/write, stored in ``<w:pPr>``):

    - ``next_style`` — style applied to the following paragraph
    - ``alignment``, ``space_before``, ``space_after``, ``line_spacing``
    - ``indent_left``, ``indent_right``, ``indent_hanging``

    Inherits all :class:`CharacterStyle` properties.
    """

    __slots__ = ()
    type: ClassVar[Literal["paragraph"]] = "paragraph"

    next_style = NullableStringProperty("next_style")
    alignment: ChoiceProperty[Literal["left", "right", "center", "justify"]] = ChoiceProperty(
        "alignment", ("left", "right", "center", "justify")
    )
    space_before = FloatProperty("space_before", default=0.0)
    space_after = FloatProperty("space_after", default=0.0)
    line_spacing = FloatProperty("line_spacing", default=0.0)
    indent_left = FloatProperty("indent_left", default=0.0)
    indent_right = FloatProperty("indent_right", default=0.0)
    indent_hanging = FloatProperty("indent_hanging", default=0.0)

    @override
    def _live_copy_data(self) -> dict[str, Any]:
        return {
            **super()._live_copy_data(),
            "next_style": self.next_style,
            "alignment": self.alignment,
            "space_before": self.space_before,
            "space_after": self.space_after,
            "line_spacing": self.line_spacing,
            "indent_left": self.indent_left,
            "indent_right": self.indent_right,
            "indent_hanging": self.indent_hanging,
        }


class TableStyle(Style):
    """A table style — applies table-level formatting."""

    __slots__ = ()
    type: ClassVar[Literal["table"]] = "table"


class NumberingStyle(Style):
    """A numbering style — defines list numbering formats."""

    __slots__ = ()
    type: ClassVar[Literal["numbering"]] = "numbering"


type AnyStyle = ParagraphStyle | CharacterStyle | TableStyle | NumberingStyle

_STYLE_TYPE_MAP: dict[str, type[AnyStyle]] = {
    "paragraph": ParagraphStyle,
    "character": CharacterStyle,
    "table": TableStyle,
    "numbering": NumberingStyle,
}


class StyleCollection:
    """Live view over all styles defined in a document.

    Obtained via :attr:`~navyfox.document.Document.styles`:

    .. code-block:: python

        styles = doc.styles
        heading = styles["Heading1"]
        for style in styles:
            print(style.name, style.type)

    Supports ``len()``, iteration, ``in`` (by style name/id), dict-style
    lookup by name/id, and :meth:`register` for creating new styles.

    Raises:
        KeyError: When a style name is not found.
    """

    def __init__(self, handle: int, doc: Document) -> None:
        self._handle = handle
        self._doc = doc
        self._name_to_id: dict[str, str] | None = None

    def _invalidate_cache(self) -> None:
        self._name_to_id = None

    def _get_name_to_id(self) -> dict[str, str]:
        if self._name_to_id is None:
            self._name_to_id = {
                s.name: s.style_id for s in self if s.name and s.style_id
            }
        return self._name_to_id

    def _get_lib(self) -> Handle:
        return cast("Handle", object.__getattribute__(self._doc, "_lib"))

    def _style_from_handle(self, h: int) -> AnyStyle:
        type_str = self._get_lib().get_str(h, "style_type")
        cls: type[AnyStyle] = _STYLE_TYPE_MAP.get(type_str, ParagraphStyle)
        return cls._from_native(h, self._doc)

    @property
    def default(self) -> ParagraphStyle | None:
        try:
            h = self._get_lib().get_child_handle(self._handle, "default_style", 0)
            style = self._style_from_handle(h)
            return style if isinstance(style, ParagraphStyle) else None
        except Exception:
            return None

    def __getitem__(self, name: str) -> AnyStyle:
        try:
            h = self._get_lib().get_child_handle(self._handle, f"style:{name}", 0)
            if not h:
                raise KeyError(name)
            return self._style_from_handle(h)
        except KeyError:
            raise
        except Exception:
            raise KeyError(name) from None

    def __contains__(self, name: object) -> bool:
        try:
            self[str(name)]
            return True
        except KeyError:
            return False

    def __iter__(self) -> Iterator[AnyStyle]:
        try:
            n = self._get_lib().get_count(self._handle, "styles")
        except Exception:
            return
        for i in range(n):
            try:
                h = self._get_lib().get_child_handle(self._handle, "styles", i)
                yield self._style_from_handle(h)
            except Exception:
                pass

    def __len__(self) -> int:
        try:
            return self._get_lib().get_count(self._handle, "styles")
        except Exception:
            return 0

    def _id_for(self, name_or_id: str) -> str | None:
        """Return the style ID for *name_or_id*, trying ID lookup first then display name.

        Returns ``None`` if no matching style is found.
        """
        if name_or_id in self:
            return name_or_id
        return self._get_name_to_id().get(name_or_id)

    @overload
    def register(
        self,
        name: str,
        *,
        type: Literal["paragraph"] = ...,
        based_on: str | None = ...,
        next_style: str | None = ...,
        style_id: str | None = ...,
        bold: bool = ...,
        italic: bool = ...,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None = ...,
        color: str | None = ...,
        font_name: str = ...,
        font_size: float = ...,
        alignment: Literal["left", "right", "center", "justify"] | None = ...,
        space_before: float = ...,
        space_after: float = ...,
        line_spacing: float = ...,
        indent_left: float = ...,
        indent_right: float = ...,
        indent_hanging: float = ...,
    ) -> ParagraphStyle: ...
    @overload
    def register(
        self,
        name: str,
        *,
        type: Literal["character"],
        based_on: str | None = ...,
        style_id: str | None = ...,
        bold: bool = ...,
        italic: bool = ...,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None = ...,
        color: str | None = ...,
        font_name: str = ...,
        font_size: float = ...,
    ) -> CharacterStyle: ...
    @overload
    def register(
        self,
        name: str,
        *,
        type: Literal["table"],
        based_on: str | None = ...,
        style_id: str | None = ...,
    ) -> TableStyle: ...
    @overload
    def register(
        self,
        name: str,
        *,
        type: Literal["numbering"],
        based_on: str | None = ...,
        style_id: str | None = ...,
    ) -> NumberingStyle: ...
    def register(
        self,
        name: str,
        *,
        type: Literal["paragraph", "character", "table", "numbering"] = "paragraph",
        based_on: str | None = None,
        next_style: str | None = None,
        style_id: str | None = None,
        # Character formatting
        bold: bool = False,
        italic: bool = False,
        underline: bool | Literal["single", "double", "dotted", "dashed", "wave"] | None = None,
        color: str | None = None,
        font_name: str = "",
        font_size: float = 0.0,
        # Paragraph formatting
        alignment: Literal["left", "right", "center", "justify"] | None = None,
        space_before: float = 0.0,
        space_after: float = 0.0,
        line_spacing: float = 0.0,
        indent_left: float = 0.0,
        indent_right: float = 0.0,
        indent_hanging: float = 0.0,
    ) -> AnyStyle:
        """Create and register a new style in the document.

        Args:
            name: Display name for the style (e.g. ``"My Heading"``).
            type: Style type — ``"paragraph"`` (default), ``"character"``,
                ``"table"``, or ``"numbering"``.
            based_on: Style name or id to inherit from (e.g. ``"Normal"``).
            next_style: Style applied to the next paragraph when Enter is
                pressed (paragraph styles only).
            style_id: Internal id used in markup; defaults to *name* with
                spaces removed.
            bold: Bold weight.
            italic: Italic style.
            underline: ``True`` for single underline, or a named style
                (``"single"``, ``"double"``, ``"dotted"``, ``"dashed"``, ``"wave"``).
            color: Text colour as ``"#RRGGBB"`` or ``"auto"``.
            font_name: Font family name.
            font_size: Font size in points.
            alignment: Paragraph alignment — ``"left"``, ``"right"``,
                ``"center"``, or ``"justify"`` (paragraph styles only).
            space_before: Space before paragraph in points (paragraph styles only).
            space_after: Space after paragraph in points (paragraph styles only).
            line_spacing: Line spacing multiplier, e.g. ``1.5`` (paragraph styles only).
            indent_left: Left indent in inches (paragraph styles only).
            indent_right: Right indent in inches (paragraph styles only).
            indent_hanging: Hanging indent in inches (paragraph styles only).

        Returns:
            The newly created style object.
        """
        lib = self._get_lib()
        if style_id is None:
            style_id = name.replace(" ", "")

        try:
            existing = self[style_id]
            h = existing._require_native
        except KeyError:
            h = lib.append_child(self._handle, "style")
            lib.set_str(h, "style_id", style_id)
            lib.set_str(h, "style_name", name)
            lib.set_str(h, "style_type", type)

        cls = _STYLE_TYPE_MAP.get(type, ParagraphStyle)
        style = cls._from_native(h, self._doc)

        changes: dict[str, Any] = {}
        if based_on is not None:
            changes["based_on"] = based_on
        if next_style is not None:
            changes["next_style"] = next_style
        if bold:
            changes["bold"] = True
        if italic:
            changes["italic"] = True
        if underline is not None and underline is not False:
            changes["underline"] = "single" if underline is True else underline
        if color is not None:
            changes["color"] = color
        if font_name:
            changes["font_name"] = font_name
        if font_size:
            changes["font_size"] = float(font_size)
        if alignment is not None:
            changes["alignment"] = alignment
        if space_before:
            changes["space_before"] = float(space_before)
        if space_after:
            changes["space_after"] = float(space_after)
        if line_spacing:
            changes["line_spacing"] = float(line_spacing)
        if indent_left:
            changes["indent_left"] = float(indent_left)
        if indent_right:
            changes["indent_right"] = float(indent_right)
        if indent_hanging:
            changes["indent_hanging"] = float(indent_hanging)
        if changes:
            style._apply_changes(changes)

        self._invalidate_cache()
        return style

    def __repr__(self) -> str:
        try:
            return f"StyleCollection(len={len(self)})"
        except Exception:
            return "StyleCollection(<error>)"
