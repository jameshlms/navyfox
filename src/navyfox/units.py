from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import ClassVar

AUTO = "auto"


@dataclass(frozen=True)
class Color:
    """An immutable RGB colour value (each component 0-255).

    `str(color)` returns bare `RRGGBB` hex for the native layer.
    `color.to_hex()` returns `#RRGGBB` for human-facing output.
    """

    r: int
    g: int
    b: int

    BLACK: ClassVar[Color]
    WHITE: ClassVar[Color]
    RED: ClassVar[Color]
    GREEN: ClassVar[Color]
    BLUE: ClassVar[Color]
    YELLOW: ClassVar[Color]
    CYAN: ClassVar[Color]
    MAGENTA: ClassVar[Color]

    def __post_init__(self) -> None:
        for name, v in zip("rgb", (self.r, self.g, self.b), strict=False):
            if not (0 <= v <= 255):
                raise ValueError(f"Color.{name} must be an integer 0-255, got {v!r}")

    @classmethod
    def from_hex(cls, value: str) -> Color:
        """Parse `'#RRGGBB'` or `'RRGGBB'`."""
        s = value.lstrip("#")
        if len(s) != 6:
            raise ValueError(f"Invalid hex color {value!r}: expected 6 hex digits")
        try:
            return cls(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except ValueError:
            raise ValueError(f"Invalid hex color {value!r}") from None

    def to_hex(self) -> str:
        """Return `'#RRGGBB'`."""
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def to_tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def __str__(self) -> str:
        """Bare `'RRGGBB'` — used by the native layer."""
        return f"{self.r:02X}{self.g:02X}{self.b:02X}"

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b})"

    def __iter__(self) -> Iterator[int]:
        """Yield r, g, b — enables `r, g, b = color` unpacking."""
        yield self.r
        yield self.g
        yield self.b

    @property
    def luminance(self) -> float:
        """Relative luminance (0.0 = black, 1.0 = white), per WCAG 2.x."""

        def _lin(c: int) -> float:
            s = c / 255.0
            return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

        return 0.2126 * _lin(self.r) + 0.7152 * _lin(self.g) + 0.0722 * _lin(self.b)

    @property
    def is_dark(self) -> bool:
        """True when luminance < 0.5."""
        return self.luminance < 0.5

    @property
    def is_light(self) -> bool:
        """True when luminance >= 0.5."""
        return not self.is_dark

    def blend(self, other: Color, t: float = 0.5) -> Color:
        """Linearly interpolate toward *other* (t=0 → self, t=1 → other)."""
        t = max(0.0, min(1.0, t))
        return Color(
            round(self.r + (other.r - self.r) * t),
            round(self.g + (other.g - self.g) * t),
            round(self.b + (other.b - self.b) * t),
        )

    def lighten(self, amount: float = 0.1) -> Color:
        """Return a lighter version by blending toward white."""
        return self.blend(Color(255, 255, 255), amount)

    def darken(self, amount: float = 0.1) -> Color:
        """Return a darker version by blending toward black."""
        return self.blend(Color(0, 0, 0), amount)

    @classmethod
    def normalize(cls, value: Color | str | None) -> str | None:
        """Normalize a color value to the bare ``RRGGBB`` string used by the native layer.

        Accepts any of the formats accepted throughout the navyfox API and
        converts them to the canonical internal representation:

        - ``None`` — returned as-is; clears the color when passed to a setter.
        - ``'auto'`` — returned as-is; tells Word to pick the theme color.
        - :class:`Color` instance — converted via ``str(color)`` (bare ``RRGGBB``).
        - ``'#RRGGBB'`` or ``'RRGGBB'`` — ``#`` stripped, validated, uppercased.

        Raises :exc:`ValueError` for any other input.

        Example::

            Color.normalize(Color(255, 0, 0))   # → 'FF0000'
            Color.normalize('#cc0000')           # → 'CC0000'
            Color.normalize('auto')             # → 'auto'
            Color.normalize(None)               # → None
        """
        if value is None:
            return None
        if value == AUTO:
            return AUTO
        if isinstance(value, cls):
            return str(value)
        if isinstance(value, str):
            s = value.lstrip("#")
            if len(s) == 6:
                try:
                    int(s, 16)
                    return s.upper()
                except ValueError:
                    pass
        raise ValueError(
            f"Invalid color {value!r}. Use '#RRGGBB', 'RRGGBB', Color(r, g, b), or 'auto'."
        )


Color.BLACK = Color(0, 0, 0)
Color.WHITE = Color(255, 255, 255)
Color.RED = Color(255, 0, 0)
Color.GREEN = Color(0, 128, 0)
Color.BLUE = Color(0, 0, 255)
Color.YELLOW = Color(255, 255, 0)
Color.CYAN = Color(0, 255, 255)
Color.MAGENTA = Color(255, 0, 255)


def _positive_float(name: str, value: float) -> float:
    if value < 0:
        raise ValueError(f"{name} value cannot be negative, got {value}")
    return float(value)


@dataclass(frozen=True)
class _Length:
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _positive_float(
                name=type(self).__name__,
                value=self.value,
            ),
        )

    @property
    def points(self) -> float:
        raise NotImplementedError

    @property
    def twips(self) -> int:
        return round(self.points * 20)

    @property
    def emu(self) -> int:
        return round(self.points * 12700)


@dataclass(frozen=True)
class Inches(_Length):
    """Represents a length in inches."""

    @property
    def points(self) -> float:
        return self.value * 72.0


@dataclass(frozen=True)
class Centimeters(_Length):
    """Represents a length in centimeters."""

    @property
    def points(self) -> float:
        return self.value * 28.3464567


@dataclass(frozen=True)
class Millimeters(_Length):
    """Represents a length in millimeters."""

    @property
    def points(self) -> float:
        return self.value * 2.83464567


@dataclass(frozen=True)
class Twips(_Length):
    """Represents a length in twips (1/20 of a point)."""

    @property
    def points(self) -> float:
        return self.value * 0.05

    @property
    def twips(self) -> int:
        return round(self.value)


@dataclass(frozen=True)
class Points(_Length):
    """Represents a length in points."""

    @property
    def points(self) -> float:
        return self.value


Length = Inches | Centimeters | Millimeters | Twips | Points
