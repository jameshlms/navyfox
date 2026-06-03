"""Descriptor types for proxy property declarations.

Adding a new property is one line:

    class Run(ProxyBase):
        bold = BoolProperty("bold")

Each descriptor handles both live (FFI) and spec (_data) mode transparently.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, overload

from navyfox.units import Color as _Color

if TYPE_CHECKING:
    from navyfox._proxy.base import ProxyBase


# ---------------------------------------------------------------------------
# NullableStringProperty
# ---------------------------------------------------------------------------


class NullableStringProperty:
    """String property that maps empty string → None on get; accepts None on set (stores as '')."""

    def __init__(self, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, obj: None, objtype: type) -> NullableStringProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> str | None: ...

    def __get__(
        self, obj: ProxyBase | None, objtype: type | None = None
    ) -> str | None | NullableStringProperty:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            val = obj._get_lib().get_str(object.__getattribute__(obj, "_native"), self._name)
            return val or None
        data: dict[str, Any] = object.__getattribute__(obj, "_data")
        return data.get(self._name) or None

    def __set__(self, obj: ProxyBase, value: str | None) -> None:
        normalized = value or ""
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            obj._get_lib().set_str(native, self._name, normalized)
        else:
            object.__getattribute__(obj, "_data")[self._name] = normalized


# ---------------------------------------------------------------------------
# BoolProperty
# ---------------------------------------------------------------------------


class BoolProperty:
    """Boolean property stored as int (0/1) on the C# side. Default False."""

    def __init__(self, name: str, *, default: bool = False) -> None:
        self._name = name
        self._default = default

    @overload
    def __get__(self, obj: None, objtype: type) -> BoolProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> bool: ...

    def __get__(self, obj: ProxyBase | None, objtype: type | None = None) -> bool | BoolProperty:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            rc = obj._get_lib().get_int(object.__getattribute__(obj, "_native"), self._name)
            return bool(rc) if rc >= 0 else self._default
        data: dict[str, Any] = object.__getattribute__(obj, "_data")
        return bool(data.get(self._name, self._default))

    def __set__(self, obj: ProxyBase, value: bool) -> None:
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            obj._get_lib().set_int(native, self._name, int(bool(value)))
        else:
            object.__getattribute__(obj, "_data")[self._name] = bool(value)


# ---------------------------------------------------------------------------
# StringProperty
# ---------------------------------------------------------------------------


class StringProperty:
    """String property with an optional default. Normalises None → default."""

    def __init__(self, name: str, *, default: str = "") -> None:
        self._name = name
        self._default = default

    @overload
    def __get__(self, obj: None, objtype: type) -> StringProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> str: ...

    def __get__(self, obj: ProxyBase | None, objtype: type | None = None) -> str | StringProperty:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            val = obj._get_lib().get_str(object.__getattribute__(obj, "_native"), self._name)
            return val if val else self._default
        data: dict[str, Any] = object.__getattribute__(obj, "_data")
        return str(data.get(self._name, self._default))

    def __set__(self, obj: ProxyBase, value: str | None) -> None:
        normalized = value if value is not None else self._default
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            obj._get_lib().set_str(native, self._name, normalized)
        else:
            object.__getattribute__(obj, "_data")[self._name] = normalized


# ---------------------------------------------------------------------------
# FloatProperty
# ---------------------------------------------------------------------------


class FloatProperty:
    """Float property with an optional default."""

    def __init__(self, name: str, *, default: float = 0.0) -> None:
        self._name = name
        self._default = default

    @overload
    def __get__(self, obj: None, objtype: type) -> FloatProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> float: ...

    def __get__(self, obj: ProxyBase | None, objtype: type | None = None) -> float | FloatProperty:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            try:
                return obj._get_lib().get_float(object.__getattribute__(obj, "_native"), self._name)
            except Exception:
                return self._default
        data: dict[str, Any] = object.__getattribute__(obj, "_data")
        return float(data.get(self._name, self._default))

    def __set__(self, obj: ProxyBase, value: float) -> None:
        v = float(value)
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            obj._get_lib().set_float(native, self._name, v)
        else:
            object.__getattribute__(obj, "_data")[self._name] = v


# ---------------------------------------------------------------------------
# IntProperty
# ---------------------------------------------------------------------------


class IntProperty:
    """Integer property. Default 0. Treats negative native return as 'not set'."""

    def __init__(self, name: str, *, default: int = 0) -> None:
        self._name = name
        self._default = default

    @overload
    def __get__(self, obj: None, objtype: type) -> IntProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> int: ...

    def __get__(self, obj: ProxyBase | None, objtype: type | None = None) -> int | IntProperty:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            rc = obj._get_lib().get_int(object.__getattribute__(obj, "_native"), self._name)
            return rc if rc >= 0 else self._default
        data: dict[str, Any] = object.__getattribute__(obj, "_data")
        return int(data.get(self._name, self._default))

    def __set__(self, obj: ProxyBase, value: int) -> None:
        v = int(value)
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            obj._get_lib().set_int(native, self._name, v)
        else:
            object.__getattribute__(obj, "_data")[self._name] = v


# ---------------------------------------------------------------------------
# ChoiceProperty
# ---------------------------------------------------------------------------


class ChoiceProperty[L: str]:
    """String restricted to a tuple of Literal values.

    Set allow_bool=True so True maps to choices[0] and False maps to None.
    """

    def __init__(
        self,
        name: str,
        choices: tuple[str, ...],
        *,
        allow_bool: bool = False,
        default: str | None = None,
    ) -> None:
        self._name = name
        self._choices = choices
        self._allow_bool = allow_bool
        self._default = default

    @overload
    def __get__(self, obj: None, objtype: type) -> ChoiceProperty[L]: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> L | None: ...

    def __get__(
        self, obj: ProxyBase | None, objtype: type | None = None
    ) -> L | None | ChoiceProperty[L]:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            val = obj._get_lib().get_str(object.__getattribute__(obj, "_native"), self._name)
            return cast(L, val or self._default)
        data: dict[str, Any] = object.__getattribute__(obj, "_data")
        return cast(L | None, data.get(self._name, self._default))

    def __set__(self, obj: ProxyBase, value: bool | str | None) -> None:
        if self._allow_bool:
            if value is True:
                value = self._choices[0]
            elif value is False:
                value = None
        if value is not None and value not in self._choices:
            raise ValueError(f"{self._name!r} must be one of {self._choices!r}, got {value!r}")
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            obj._get_lib().set_str(native, self._name, value or "")
        else:
            object.__getattribute__(obj, "_data")[self._name] = value


# ---------------------------------------------------------------------------
# ColorProperty
# ---------------------------------------------------------------------------


class ColorProperty:
    """Accepts "#RRGGBB", "RRGGBB", RGBColor, or "auto". Normalises to bare hex."""

    def __init__(self, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, obj: None, objtype: type) -> ColorProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> str | None: ...

    def __get__(
        self, obj: ProxyBase | None, objtype: type | None = None
    ) -> str | None | ColorProperty:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            val = obj._get_lib().get_str(object.__getattribute__(obj, "_native"), self._name)
            if not val:
                return None
            return f"#{val}" if val != "auto" else "auto"
        raw: str | None = object.__getattribute__(obj, "_data").get(self._name, None)
        if raw and raw != "auto":
            return f"#{raw}"
        return raw

    def __set__(self, obj: ProxyBase, value: Any) -> None:

        normalized = _Color.normalize(value)
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            obj._get_lib().set_str(native, self._name, normalized or "")
        else:
            object.__getattribute__(obj, "_data")[self._name] = normalized


# ---------------------------------------------------------------------------
# ObjectProperty
# ---------------------------------------------------------------------------


class ObjectProperty:
    """Nested proxy sub-object (Font, Shading, etc.).

    On read: wraps a C# sub-object handle in the appropriate proxy type.
    On write: validates type before setting.
    """

    def __init__(self, name: str, proxy_type: type[ProxyBase]) -> None:
        self._name = name
        self._proxy_type = proxy_type

    @overload
    def __get__(self, obj: None, objtype: type) -> ObjectProperty: ...
    @overload
    def __get__(self, obj: ProxyBase, objtype: type) -> Any: ...

    def __get__(self, obj: ProxyBase | None, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        if object.__getattribute__(obj, "_native") is not None:
            obj._check_valid()
            sub_handle = obj._get_lib().get_int(object.__getattribute__(obj, "_native"), self._name)
            if sub_handle <= 0:
                return None
            doc = object.__getattribute__(obj, "_document")
            return self._proxy_type._from_native(sub_handle, doc)
        return object.__getattribute__(obj, "_data").get(self._name, None)

    def __set__(self, obj: ProxyBase, value: Any) -> None:
        if value is not None and not isinstance(value, self._proxy_type):
            raise TypeError(
                f"{self._name!r} expects {self._proxy_type.__name__}, got {type(value).__name__}"
            )
        native = object.__getattribute__(obj, "_native")
        if native is not None:
            obj._check_valid()
            # Sub-object writes are applied via the sub-object's own properties
            raise NotImplementedError(
                f"Writing {self._name!r} on a live proxy is not yet supported. "
                "Modify the sub-object's properties directly."
            )
        object.__getattribute__(obj, "_data")[self._name] = value
