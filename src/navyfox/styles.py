"""Style and StyleCollection."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Literal, cast, override

from navyfox._proxy.base import ElementState, ProxyBase
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


class Style(ProxyBase):
    """A document style definition — always live, backed by a native handle.

    Obtained from :class:`StyleCollection` via ``doc.styles["Heading1"]`` or
    by iterating ``doc.styles``, or created via ``doc.styles.register("My Style")``.

    Metadata properties (read/write):

    - ``name`` — display name (e.g. ``"Heading 1"``)
    - ``type`` — ``"paragraph"``, ``"character"``, ``"table"``, or ``"numbering"``
    - ``based_on`` — parent style name/id, or ``None``
    - ``next_style`` — style for the following paragraph, or ``None``
    - ``is_default`` — ``True`` if this is the document's default paragraph style

    Character formatting (read/write, stored in the style's ``<w:rPr>``):

    - ``bold``, ``italic``, ``underline``, ``color``, ``font_name``, ``font_size``

    Paragraph formatting (read/write, stored in the style's ``<w:pPr>``):

    - ``alignment``, ``space_before``, ``space_after``, ``line_spacing``
    - ``indent_left``, ``indent_right``, ``indent_hanging``
    """

    __slots__ = ()
    _child_type_name = "style"

    # Metadata
    style_id = StringProperty("style_id", default="")
    name = StringProperty("style_name", default="")
    type: ChoiceProperty[Literal["paragraph", "character", "table", "numbering"]] = ChoiceProperty(
        "style_type", ("paragraph", "character", "table", "numbering"), default="paragraph"
    )
    based_on = NullableStringProperty("based_on")
    next_style = NullableStringProperty("next_style")
    is_default = BoolProperty("is_default")

    # Character formatting
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

    # Paragraph formatting
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
    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._data)
        return {
            "style_name": self.name,
            "style_type": self.type,
            "based_on": self.based_on,
            "next_style": self.next_style,
            "is_default": self.is_default,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "color": self.color,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "alignment": self.alignment,
            "space_before": self.space_before,
            "space_after": self.space_after,
            "line_spacing": self.line_spacing,
            "indent_left": self.indent_left,
            "indent_right": self.indent_right,
            "indent_hanging": self.indent_hanging,
        }

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Style(<stale>)"
        native = self._native
        if native is None:
            return "Style(spec)"
        try:
            return f"Style({self.name!r})"
        except Exception:
            return "Style(<error>)"


class StyleCollection:
    """Live view over all styles defined in a document.

    Obtained via :attr:`~navyfox.document.Document.styles`:

    .. code-block:: python

        styles = doc.styles
        heading = styles["Heading1"]
        for style in styles:
            print(style.name, style.type)

    Supports ``len()``, iteration, ``in`` (by style name/id), dict-style
    lookup by name/id, and :meth:`add` for creating new styles.

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

    @property
    def default(self) -> Style | None:
        try:
            h = self._get_lib().get_child_handle(self._handle, "default_style", 0)
            return Style._from_native(h, self._doc)
        except Exception:
            return None

    def __getitem__(self, name: str) -> Style:
        try:
            h = self._get_lib().get_child_handle(self._handle, f"style:{name}", 0)
            if not h:
                raise KeyError(name)
            return Style._from_native(h, self._doc)
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

    def __iter__(self) -> Iterator[Style]:
        try:
            n = self._get_lib().get_count(self._handle, "styles")
        except Exception:
            return
        for i in range(n):
            try:
                h = self._get_lib().get_child_handle(self._handle, "styles", i)
                yield Style._from_native(h, self._doc)
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
    ) -> Style:
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
                ``"center"``, or ``"justify"``.
            space_before: Space before paragraph in points.
            space_after: Space after paragraph in points.
            line_spacing: Line spacing multiplier (e.g. ``1.5``).
            indent_left: Left indent in inches.
            indent_right: Right indent in inches.
            indent_hanging: Hanging indent in inches.

        Returns:
            The newly created :class:`Style` object.
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

        style = Style._from_native(h, self._doc)

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
            changes["font_size"] = font_size
        if alignment is not None:
            changes["alignment"] = alignment
        if space_before:
            changes["space_before"] = space_before
        if space_after:
            changes["space_after"] = space_after
        if line_spacing:
            changes["line_spacing"] = line_spacing
        if indent_left:
            changes["indent_left"] = indent_left
        if indent_right:
            changes["indent_right"] = indent_right
        if indent_hanging:
            changes["indent_hanging"] = indent_hanging
        if changes:
            style._apply_changes(changes)

        self._invalidate_cache()
        return style

    def __repr__(self) -> str:
        try:
            return f"StyleCollection(len={len(self)})"
        except Exception:
            return "StyleCollection(<error>)"
