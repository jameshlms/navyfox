from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal, Self, TypedDict, Unpack, override

from navyfox._collection import DocumentView
from navyfox._proxy.base import Element, ElementState
from navyfox._proxy.descriptors import (
    BoolProperty,
    ChoiceProperty,
    ColorProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from navyfox.formats import Border, ParagraphBorder, coerce_border_group

if TYPE_CHECKING:
    from navyfox.hyperlink import Hyperlink
    from navyfox.image import Image
    from navyfox.run import Run


class _ParagraphFormat(TypedDict, total=False):
    style: str
    alignment: Literal["left", "right", "center", "justify"]
    keep_together: bool
    keep_with_next: bool
    page_break_before: bool
    space_before: float
    space_after: float
    line_spacing: float
    indent_left: float
    indent_right: float
    indent_hanging: float
    list_style: Literal["bullet", "number"]
    list_level: int
    border: ParagraphBorder


class Paragraph(Element):

    __slots__ = ()
    _child_type_name = "paragraph"
    _collection_name = "paragraphs"

    style = StringProperty("style", default="Normal")
    alignment: ChoiceProperty[Literal["left", "right", "center", "justify"]] = ChoiceProperty(
        "alignment", ("left", "right", "center", "justify")
    )
    keep_together = BoolProperty("keep_together")
    keep_with_next = BoolProperty("keep_with_next")
    page_break_before = BoolProperty("page_break_before")
    space_before = FloatProperty("space_before", default=0.0)  # points
    space_after = FloatProperty("space_after", default=0.0)  # points
    line_spacing = FloatProperty("line_spacing", default=1.0)  # multiplier (1.0 = single)
    indent_left = FloatProperty("indent_left", default=0.0)  # inches
    indent_right = FloatProperty("indent_right", default=0.0)  # inches
    indent_hanging = FloatProperty(
        "indent_hanging", default=0.0
    )  # inches (first-line negative indent)
    list_style: ChoiceProperty[Literal["bullet", "number"]] = ChoiceProperty(
        "list_style", ("bullet", "number")
    )
    list_level = IntProperty("list_level", default=0)  # 0–8
    is_horizontal_rule = BoolProperty("_horizontal_line")

    @property
    def border(self) -> ParagraphBorder:
        if not self.is_live:
            return self._get_data().setdefault("border", ParagraphBorder())
        self._check_valid()
        borders = ParagraphBorder(
            **{
                side: Border(
                    style=self._get_lib().get_str(self._require_native, f"border_{side}_style")
                    or "none",
                    width=self._get_lib().get_float(self._require_native, f"border_{side}_width"),
                    color=self._get_lib().get_str(self._require_native, f"border_{side}_color")
                    or "auto",
                    spacing=self._get_lib().get_float(self._require_native, f"border_{side}_spacing"),
                    shadow=bool(self._get_lib().get_int(self._require_native, f"border_{side}_shadow")),
                )
                for side in ("top", "bottom", "left", "right")
            }
        )
        self._bind_borders(borders)
        return borders

    @border.setter
    def border(self, value: ParagraphBorder | dict[str, Border | dict[str, object]]) -> None:
        value = coerce_border_group(value, ParagraphBorder)
        self._bind_borders(value)
        if self.is_live:
            self._check_valid()
            pending: dict[str, Any] = {}
            for side in ("top", "bottom", "left", "right"):
                border = getattr(value, side)
                pending.update(self._border_changes(side, border))
            self._get_lib().set_many(self._require_native, pending)
        else:
            self._get_data()["border"] = value

    @property
    def borders(self) -> ParagraphBorder:
        """Deprecated alias for :attr:`border`."""
        return self.border

    @borders.setter
    def borders(self, value: ParagraphBorder) -> None:
        self.border = value

    def _border_changes(self, side: str, border: Border) -> dict[str, Any]:
        return {
            f"border_{side}_style": border.style,
            f"border_{side}_width": border.width,
            f"border_{side}_color": border.color,
            f"border_{side}_spacing": border.spacing,
            f"border_{side}_shadow": int(border.shadow),
        }

    def _bind_borders(self, borders: ParagraphBorder) -> None:
        for side in ("top", "bottom", "left", "right"):
            border = getattr(borders, side)
            border._on_change = lambda name, value, side=side: self._border_changed(
                side, name, value
            )

    def _border_changed(self, side: str, name: str, value: object) -> None:
        if name == "_on_change":
            return
        if not self.is_live:
            return
        self._check_valid()
        property_name = f"border_{side}_{name}"
        if name == "shadow":
            value = int(bool(value))
        self._get_lib().set_many(self._require_native, {property_name: value})

    @property
    def text(self) -> str:
        if self.is_live:
            self._check_valid()
            return self._get_lib().get_str(self._require_native, "text") or ""
        self._check_valid()
        return "".join(r.text for r in self._get_data().get("runs", []))

    @text.setter
    def text(self, value: str) -> None:
        if self.is_live:
            self._check_valid()
            self._get_lib().set_str(self._require_native, "text", value)
            return
        from navyfox.run import Run

        self._get_data()["runs"] = [Run(value)] if value else []

    def __init__(
        self,
        text: str | Run | list[str | Run] | None = None,
        *,
        style: str = "Normal",
        alignment: Literal["left", "right", "center", "justify"] | None = None,
        keep_together: bool = False,
        keep_with_next: bool = False,
        page_break_before: bool = False,
        space_before: float = 0.0,
        space_after: float = 0.0,
        line_spacing: float = 1.0,
        indent_left: float = 0.0,
        indent_right: float = 0.0,
        indent_hanging: float = 0.0,
        list_style: Literal["bullet", "number"] | None = None,
        list_level: int = 0,
        border: ParagraphBorder | dict[str, Border | dict[str, object]] | None = None,
        borders: ParagraphBorder | dict[str, Border | dict[str, object]] | None = None,
    ) -> None:
        from navyfox.run import Run

        super().__init__()
        data: dict[str, Any] = {}
        if isinstance(text, str):
            if text:
                data["runs"] = [Run(text)]
        elif isinstance(text, Run):
            data["runs"] = [text]
        else:
            if text:
                data["runs"] = [Run(t) if isinstance(t, str) else t for t in text]
        if style and style != "Normal":
            data["style"] = style
        if alignment is not None:
            data["alignment"] = alignment
        if keep_together:
            data["keep_together"] = True
        if keep_with_next:
            data["keep_with_next"] = True
        if page_break_before:
            data["page_break_before"] = True
        if space_before:
            data["space_before"] = float(space_before)
        if space_after:
            data["space_after"] = float(space_after)
        if line_spacing != 1.0:
            data["line_spacing"] = float(line_spacing)
        if indent_left:
            data["indent_left"] = float(indent_left)
        if indent_right:
            data["indent_right"] = float(indent_right)
        if indent_hanging:
            data["indent_hanging"] = float(indent_hanging)
        if list_style is not None:
            data["list_style"] = list_style
        if list_level:
            data["list_level"] = int(list_level)
        if border is None:
            border = borders
        if border is not None:
            border = coerce_border_group(border, ParagraphBorder)
            data["border"] = border
            self._bind_borders(border)
        self._data = data

    @property
    def runs(self) -> DocumentView[Run]:
        from navyfox.run import Run

        if not self.is_live:
            runs_list: list[Any] = self._get_data().setdefault("runs", [])
            return _ConstructionRunsView(runs_list)  # type: ignore[return-value]
        self._check_valid()
        handle, doc = self._require_live()
        return DocumentView(handle, doc, self._get_lib(), Run, "runs")

    @property
    def images(self) -> DocumentView[Image]:
        from navyfox.image import Image

        if not self.is_live:
            return DocumentView.empty(Image, "images")
        self._check_valid()
        handle, doc = self._require_live()
        return DocumentView(handle, doc, self._get_lib(), Image, "images")

    def add_run(self, text: str = "") -> Run:
        from navyfox.run import Run

        if not self.is_live:
            run = Run(text)
            self._get_data().setdefault("runs", []).append(run)
            return run
        from navyfox._collection import DocumentView

        handle, doc = self._require_live()
        view = DocumentView(handle, doc, self._get_lib(), Run, "runs")
        return view._append_one(Run(text))

    def add_image(
        self,
        src: str | None = None,
        *,
        data: bytes | None = None,
        content_type: str | None = None,
        width: float = 0.0,
        height: float = 0.0,
        alt_text: str = "",
    ) -> Image:
        from navyfox.image import Image

        if not self.is_live:
            raise ValueError("Cannot add_image to a paragraph that is not yet in a document.")
        return self.images._append_one(
            Image(
                src,
                data=data,
                content_type=content_type,
                width=width,
                height=height,
                alt_text=alt_text,
            )
        )

    @property
    def hyperlinks(self) -> DocumentView[Hyperlink]:
        from navyfox.hyperlink import Hyperlink

        if not self.is_live:
            return DocumentView.empty(Hyperlink, "hyperlinks")
        self._check_valid()
        handle, doc = self._require_live()
        return DocumentView(handle, doc, self._get_lib(), Hyperlink, "hyperlinks")

    def add_hyperlink(self, text: str, url: str) -> Hyperlink:
        from navyfox.hyperlink import Hyperlink

        if not self.is_live:
            raise ValueError("Cannot add_hyperlink to a paragraph that is not yet in a document.")
        return self.hyperlinks._append_one(Hyperlink(text, url))

    def add_break(self) -> Self:
        """Append a soft line break within the paragraph and return self."""
        if not self.is_live:
            raise ValueError("Cannot add_break to a paragraph that is not yet in a document.")
        self._check_valid()
        self._get_lib().append_child(self._require_native, "break")
        return self

    def align(self, alignment: Literal["left", "right", "center", "justify"]) -> Self:
        self.alignment = alignment
        return self

    def set_style(self, style: str) -> Self:
        self.style = style
        return self

    def format(self, **kwargs: Unpack[_ParagraphFormat]) -> Self:
        """Set multiple paragraph properties in a single FFI call and return self."""
        changes = dict(kwargs)
        border = changes.pop("border", None)
        self._apply_changes(changes)
        if border is not None:
            self.border = border
        return self

    @override
    def _copy_data(self) -> dict[str, Any]:
        if not self.is_live:
            data = dict(self._data)
            if "runs" in data:
                data["runs"] = [r.copy() for r in data["runs"]]
            if "border" in data:
                borders = data["border"]
                data["border"] = ParagraphBorder(
                    **{
                        side: Border(
                            style=getattr(borders, side).style,
                            width=getattr(borders, side).width,
                            color=getattr(borders, side).color,
                            spacing=getattr(borders, side).spacing,
                            shadow=getattr(borders, side).shadow,
                        )
                        for side in ("top", "bottom", "left", "right")
                    }
                )
            return data
        return {
            "style": self.style,
            "alignment": self.alignment,
            "keep_together": self.keep_together,
            "keep_with_next": self.keep_with_next,
            "page_break_before": self.page_break_before,
            "space_before": self.space_before,
            "space_after": self.space_after,
            "line_spacing": self.line_spacing,
            "indent_left": self.indent_left,
            "indent_right": self.indent_right,
            "indent_hanging": self.indent_hanging,
            "list_style": self.list_style,
            "list_level": self.list_level,
            "border": ParagraphBorder(
                **{
                    side: Border(
                        style=getattr(self.border, side).style,
                        width=getattr(self.border, side).width,
                        color=getattr(self.border, side).color,
                        spacing=getattr(self.border, side).spacing,
                        shadow=getattr(self.border, side).shadow,
                    )
                    for side in ("top", "bottom", "left", "right")
                }
            ),
            "runs": [r.copy() for r in self.runs],
        }

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Paragraph(<stale>)"
        native = self._native
        if native is None:
            return f"Paragraph({self.text!r})"
        try:
            return f"Paragraph(text={self.text!r}, handle={native!r})"
        except Exception:
            return f"Paragraph(handle={native!r})"

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text)

    def __len__(self) -> int:
        if not self.is_live:
            data = self._get_data()
            return len(data.get("runs", []))
        try:
            return len(self.runs)
        except Exception:
            return 0

    def __iter__(self) -> Iterator[Run]:
        return iter(self.runs)

    def __contains__(self, run: object) -> bool:
        return run in self.runs


class _ConstructionRunsView:
    """Mutable run list for construction-state paragraphs. Mirrors the DocumentView[Run] interface."""

    _collection_name = "runs"

    def __init__(self, runs: list[Any]) -> None:
        self._runs = runs

    def _validate_element(self, element: Any) -> None:
        from navyfox.run import Run

        if not isinstance(element, Run):
            raise TypeError(f"runs only accepts Run elements, got {type(element).__name__}")

    def append(self, element: Any) -> None:
        self._validate_element(element)
        if object.__getattribute__(element, "_native") is not None:
            raise ValueError("Cannot add a live Run to a construction-state paragraph.")
        self._runs.append(element)

    def extend(self, elements: Iterable[Any]) -> None:
        for e in elements:
            self.append(e)

    def remove(self, element: Any) -> None:
        self._validate_element(element)
        try:
            self._runs.remove(element)
        except ValueError:
            raise ValueError("Run is not in this paragraph.") from None

    @property
    def first(self) -> Any | None:
        return self._runs[0] if self._runs else None

    @property
    def last(self) -> Any | None:
        return self._runs[-1] if self._runs else None

    def __len__(self) -> int:
        return len(self._runs)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._runs)

    def __reversed__(self) -> Iterator[Any]:
        return reversed(self._runs)

    def __getitem__(self, index: int | slice) -> Any:
        return self._runs[index]

    def __contains__(self, element: object) -> bool:
        return element in self._runs

    def __bool__(self) -> bool:
        return bool(self._runs)

    def pop(self, index: int | None = None) -> Any:
        i = -1 if index is None else index
        run = self._runs[i]
        del self._runs[i]
        return run

    def clear(self) -> None:
        self._runs.clear()

    def index(self, element: Any) -> int:
        try:
            return self._runs.index(element)
        except ValueError:
            raise ValueError("Run is not in this paragraph.") from None

    def __iadd__(self, elements: Iterable[Any]) -> _ConstructionRunsView:
        self.extend(elements)
        return self

    def __repr__(self) -> str:
        return f"DocumentView[Run](len={len(self._runs)}, construction)"


class LineStyle(StrEnum):
    SINGLE = "single"
    DOUBLE = "double"
    DOTTED = "dotted"
    DASHED = "dashed"
    WAVE = "wave"


LineStyleArg = LineStyle | Literal["single", "double", "dotted", "dashed", "wave"]


class HorizontalRule(Paragraph):

    __slots__ = ()

    line_style: ChoiceProperty[LineStyle] = ChoiceProperty(
        "hr_style",
        ("single", "double", "dotted", "dashed", "wave"),
        default="single",
    )
    line_width = FloatProperty("hr_width", default=1.0)
    line_color = ColorProperty("hr_color")

    def __init__(
        self,
        *,
        line_style: LineStyleArg = "single",
        line_width: float = 1.0,
        line_color: str = "auto",
    ) -> None:
        super().__init__()
        data: dict[str, Any] = self._data
        data["_horizontal_line"] = True
        data["hr_style"] = line_style
        data["hr_width"] = line_width
        data["hr_color"] = line_color

    @override
    def _copy_data(self) -> dict[str, Any]:
        if not self.is_live:
            return dict(self._data)
        data = super()._copy_data()
        data["_horizontal_line"] = True
        data["hr_style"] = self.line_style
        data["hr_width"] = self.line_width
        data["hr_color"] = self.line_color
        return data

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "HorizontalRule(<stale>)"
        native = self._native
        style: LineStyle | Literal["single"] = (
            self._data.get("hr_style", "single")
            if native is None
            else (self.line_style or "single")
        )
        if native is None:
            return f"HorizontalRule(line_style={style!r})"
        try:
            return f"HorizontalRule(line_style={style!r}, handle={native!r})"
        except Exception:
            return f"HorizontalRule(handle={native!r})"
