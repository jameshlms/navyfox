"""NativeProxy, Element, and Definition — the native-handle proxy hierarchy.

NativeProxy
  Base for all objects backed by a C# native handle. Provides the state
  machine, FFI dispatch, descriptor protocol, and snapshot machinery.
  Never instantiated directly — use _from_native or subclass via Element.

Element (NativeProxy)
  Document content objects: Paragraph, Run, Table, Row, Cell, Section, etc.
  Adds CONSTRUCTION state so objects can be built in Python then attached to
  a document. Carries _child_type_name / _collection_name ClassVars.

Definition (NativeProxy)
  Document definition objects: Style, etc. Always created via _from_native;
  direct construction raises TypeError.

States (ElementState):
  LIVE         — _native is an int handle; every property access crosses FFI.
  CONSTRUCTION — _native is None; data lives in _data dict; no handle yet.
                 Valid only for Element subclasses.
  SNAPSHOT     — _native is None; _data populated by copy(); safe outside ctx manager.
  STALE        — removed from document; all access raises StaleProxyError.
"""

from __future__ import annotations

import contextlib
import enum
from abc import abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar, Self, cast

from navyfox.errors import DocumentClosedError, StaleProxyError
from navyfox.units import Color as _Color


class ElementState(enum.Enum):
    """The lifecycle state of a proxy object."""

    CONSTRUCTION = "construction"
    LIVE = "live"
    SNAPSHOT = "snapshot"
    STALE = "stale"


if TYPE_CHECKING:
    from navyfox._native.handle import Handle
    from navyfox.document import Document


class NativeProxy:
    """Base for all C#-backed proxy objects.

    Provides the shared state machine, FFI helpers, descriptor routing,
    batch-write context manager, and snapshot protocol. All instance state
    lives in __slots__; subclasses must also declare ``__slots__ = ()``.
    """

    __slots__ = ("_native", "_data", "_document", "_state")

    _native: int | None
    _data: dict[str, Any]
    _document: Document | None
    _state: ElementState

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def _from_native(cls, native_handle: int, document: Document) -> Self:
        instance = cls.__new__(cls)
        instance._native = native_handle
        instance._document = document
        instance._state = ElementState.LIVE
        instance._data = {}
        return instance

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def state(self) -> ElementState:
        """The current lifecycle state of this proxy."""
        return self._state

    @property
    def is_live(self) -> bool:
        """True when backed by a native handle in an open document."""
        return self._state is ElementState.LIVE

    @property
    def is_snapshot(self) -> bool:
        """True when this is a document-independent copy made by ``copy()``."""
        return self._state is ElementState.SNAPSHOT

    @property
    def is_stale(self) -> bool:
        """True when the element has been removed from its document."""
        return self._state is ElementState.STALE

    @property
    def _is_live(self) -> bool:
        return self.is_live

    def _check_valid(self) -> None:
        if self._state is ElementState.STALE:
            raise StaleProxyError(
                f"This {type(self).__name__} was removed from the document. "
                "Call copy() before removing to retain data."
            )
        doc = self._document
        if doc is not None and not doc.is_open:
            raise DocumentClosedError(
                f"{type(self).__name__} cannot be accessed after its document has been "
                "closed. Call copy() inside the context manager to retain data."
            )

    def _mark_stale(self) -> None:
        self._state = ElementState.STALE

    def _attach(self, native_handle: int, document: Document) -> None:
        self._native = native_handle
        self._document = document
        self._state = ElementState.LIVE

    def _get_lib(self) -> Handle:
        doc = self._document
        if doc is None:
            raise ValueError(f"{type(self).__name__} has no associated document.")
        return cast("Handle", object.__getattribute__(doc, "_lib"))

    @property
    def _require_native(self) -> int:
        """The native handle; only valid in an open, non-stale LIVE state."""
        if self._native is None:
            raise RuntimeError(f"{type(self).__name__}._require_native accessed outside LIVE state")
        self._check_valid()
        return self._native

    def _require_live(self) -> tuple[int, Document]:
        """Return ``(native_handle, document)``; raises if not in a valid LIVE state."""
        if self._native is None or self._document is None:
            raise RuntimeError(f"{type(self).__name__} is not in LIVE state")
        self._check_valid()
        return self._native, self._document

    # ------------------------------------------------------------------
    # Batch write
    # ------------------------------------------------------------------

    def _apply_changes(self, changes: dict[str, Any]) -> None:
        """Apply *changes* in one FFI call, or a dict update when not live."""
        if not changes:
            return
        if not self._is_live:
            self._data.update(changes)
        else:
            self._check_valid()
            pending = {k: int(v) if isinstance(v, bool) else v for k, v in changes.items()}
            self._get_lib().set_many(cast(int, self._native), pending)

    @contextlib.contextmanager
    def edit(self) -> Iterator[Self]:
        """Context manager that batches property writes into a single FFI call.

        Prefer the class-specific ``format()`` for straightforward updates.
        Use ``edit()`` when the batch requires conditional logic:

        .. code-block:: python

            with para.edit() as p:
                if urgent:
                    p.space_before = 0.0
                p.alignment = "left"

        On a non-live proxy ``edit()`` is a no-op — writes already go
        directly to the local data dict.
        """
        if not self._is_live:
            yield self
            return
        self._check_valid()
        pending: dict[str, Any] = {}
        yield cast(Self, _EditProxy(self, pending))
        if pending:
            self._get_lib().set_many(cast(int, self._native), pending)

    # ------------------------------------------------------------------
    # Attribute routing
    # ------------------------------------------------------------------

    def _get_data(self) -> dict[str, Any]:
        if self._is_live:
            self._check_valid()
        return self._data

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        for klass in type(self).__mro__:
            if name in klass.__dict__:
                desc = klass.__dict__[name]
                if hasattr(desc, "__set__"):
                    desc.__set__(self, value)
                    return
                break
        state = object.__getattribute__(self, "_state")
        if state is ElementState.LIVE or state is ElementState.STALE:
            self._check_valid()
            raise AttributeError(f"{type(self).__name__!r} has no settable attribute {name!r}")
        object.__getattribute__(self, "_data")[name] = value

    def __getattr__(self, name: str) -> Any:
        try:
            state = object.__getattribute__(self, "_state")
            data = object.__getattribute__(self, "_data")
        except AttributeError:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}") from None
        if state is ElementState.LIVE or state is ElementState.STALE:
            self._check_valid()
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")
        try:
            return data[name]
        except KeyError:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}") from None

    # ------------------------------------------------------------------
    # Snapshot / copy
    # ------------------------------------------------------------------

    def __copydocelem__(self) -> Self:
        """Return a mutable snapshot with no native handle.

        Safe to use outside the document context manager.
        Modifying the snapshot does not affect the document.
        Called by the module-level ``snapshot()`` function.
        """
        if self._is_live:
            self._check_valid()
        data = self._copy_data()
        instance: Self = type(self).__new__(type(self))
        instance._native = None
        instance._document = None
        instance._state = ElementState.SNAPSHOT
        instance._data = data
        return instance

    def copy(self) -> Self:
        """Return a document-independent snapshot of this proxy.

        Equivalent to the module-level ``snapshot()`` function.
        """
        return self.__copydocelem__()

    @abstractmethod
    def _copy_data(self) -> dict[str, Any]: ...

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        if self._native is None and other._native is None:
            return self._data == other._data
        return self._native is not None and self._native == other._native

    def __hash__(self) -> int:
        return hash(self._native) if self._native is not None else id(self)

    def __repr__(self) -> str:
        state = self._state
        if state is ElementState.STALE:
            return f"{type(self).__name__}(<stale>)"
        if self._native is None:
            return f"{type(self).__name__}(spec)"
        return f"{type(self).__name__}(handle={self._native!r})"


class Element(NativeProxy):
    """Root class for document content objects backed by a C# native handle.

    Subclasses (Paragraph, Run, Table, Row, Cell, Section …) may exist in any
    of the four ElementState values, including CONSTRUCTION — where an object is
    built in Python and later attached to a document via an ``append`` call.
    """

    __slots__ = ()

    _child_type_name: ClassVar[str]
    _collection_name: ClassVar[str]

    def __init__(self) -> None:
        self._native = None
        self._document = None
        self._state = ElementState.CONSTRUCTION
        self._data = {}

    @property
    def is_construction(self) -> bool:
        """True when this is a manually constructed spec not yet appended to a document."""
        return self._state is ElementState.CONSTRUCTION


class Definition(NativeProxy):
    """Root class for document definition objects backed by a C# native handle.

    Subclasses (Style …) are always created via ``_from_native``; they have no
    meaningful construction state and cannot be instantiated directly.
    """

    __slots__ = ()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            f"{type(self).__name__} cannot be constructed directly. "
            "Use the appropriate document collection method instead "
            "(e.g. doc.styles.register(...))."
        )


class _EditProxy:
    """Accumulates property writes inside an ``edit()`` block; flushed as one ``set_many`` call."""

    __slots__ = ("_proxy", "_pending")

    def __init__(self, proxy: NativeProxy, pending: dict[str, Any]) -> None:
        object.__setattr__(self, "_proxy", proxy)
        object.__setattr__(self, "_pending", pending)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        pending: dict[str, Any] = object.__getattribute__(self, "_pending")
        match value:
            case bool():
                pending[name] = int(value)
            case _Color():
                pending[name] = str(value)
            case str() | float() | int():
                pending[name] = value
            case _:
                raise TypeError(f"Cannot batch-write {name!r}={value!r}")

    def __getattr__(self, name: str) -> Any:
        proxy: NativeProxy = object.__getattribute__(self, "_proxy")
        return getattr(proxy, name)
