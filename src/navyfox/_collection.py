"""DocumentView[T] — the live generic collection type for all proxy elements.

A DocumentView is never a copy. It holds a reference to the parent object and
the collection name, and reflects the current document state on every access.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any, Self, overload

from navyfox._proxy.base import Element
from navyfox.errors import NativeRuntimeError, OwnershipError

type ElemTypesArg[T: Element] = type[T] | tuple[type[T], ...]


def _to_elem_tuple[T: Element](arg: ElemTypesArg[T]) -> tuple[type[T], ...]:
    return (arg,) if isinstance(arg, type) else arg


if TYPE_CHECKING:
    from navyfox._native.handle import Handle
    from navyfox.document import Document


class CollectionMixin[T: Element]:
    """Shared live-collection behaviour for :class:`Document` and :class:`DocumentView`.

    Provides list-like access (``__len__``, ``__iter__``, ``__getitem__``,
    ``__contains__``) plus mutation helpers (``append``, ``extend``, ``remove``,
    ``pop``, ``clear``).

    Every method queries the native layer — there is no Python-side cache.
    Indices and lengths reflect the document state at the time of the call.

    Concrete subclasses must expose: ``_lib``, ``_document``, ``_elem_types``,
    ``_collection_name``, and ``_parent_handle`` (property or int).
    """

    _lib: Handle
    _document: Document
    _elem_types: tuple[type[T], ...]
    _collection_name: str
    _parent_handle: int

    # ------------------------------------------------------------------
    # Core internal helpers
    # ------------------------------------------------------------------

    def _count(self) -> int:
        return self._lib.get_count(
            self._parent_handle,
            self._collection_name,
        )

    def _handle_at(self, index: int) -> int:
        return self._lib.get_child_handle(
            self._parent_handle,
            self._collection_name,
            index,
        )

    def _make_proxy(self, child_handle: int) -> T:
        if len(self._elem_types) == 1:
            return self._elem_types[0]._from_native(  # type: ignore[reportPrivateUsage]
                child_handle,
                self._document,
            )
        type_name = self._lib.get_element_type(child_handle)
        for proxy_type in self._elem_types:
            if proxy_type._child_type_name == type_name:  # type: ignore[reportPrivateUsage]
                return proxy_type._from_native(  # type: ignore[reportPrivateUsage]
                    child_handle,
                    self._document,
                )
        raise NativeRuntimeError(f"Unknown element type {type_name!r} returned by native library")

    def _validate_element(self, element: Any) -> None:
        if not isinstance(element, tuple(self._elem_types)):
            names = " | ".join(t.__name__ for t in self._elem_types)
            raise TypeError(
                f"{type(self).__name__}[{names}] only accepts {names} elements, "
                f"got {type(element).__name__}. "
                "Use doc.append() or doc[ParaType | TableType] instead."
            )

    _EMU_PER_INCH = 914400

    def _resolve_style(self, data: dict[str, Any]) -> dict[str, Any]:
        """Replace ``"style"`` value with its style ID if a display name was given."""
        if "style" not in data:
            return data
        name_or_id = str(data["style"])
        resolved = self._document.styles._id_for(name_or_id)
        if resolved is None or resolved == name_or_id:
            return data
        return {**data, "style": resolved}

    def _append_one(self, element: T) -> T:
        from navyfox.image import Image
        from navyfox.table import Table

        self._validate_element(element)
        native = object.__getattribute__(element, "_native")
        if native is not None:
            doc = object.__getattribute__(element, "_document")
            if doc is not self._document:
                raise OwnershipError(
                    f"This {type(element).__name__} belongs to a different document. "
                    "Call snapshot() to get a document-independent copy."
                )
            raise ValueError(f"This {type(element).__name__} is already in a document.")

        data: dict[str, Any] = object.__getattribute__(element, "_data")

        if isinstance(element, Table):
            rows = int(data.get("rows", 1))
            cols = int(data.get("cols", 1))
            child_handle = self._lib.add_table(self._parent_handle, rows, cols)
            filtered = {k: v for k, v in data.items() if k not in ("rows", "cols")}
            filtered = self._resolve_style(filtered)
            if filtered:
                self._lib.set_many(child_handle, filtered)
        elif isinstance(element, Image):
            image_data: bytes = data.get("_image_data") or b""
            content_type: str = data.get("_content_type") or "image/png"
            width_emu = int(float(data.get("width", 0.0)) * self._EMU_PER_INCH)
            height_emu = int(float(data.get("height", 0.0)) * self._EMU_PER_INCH)
            child_handle = self._lib.add_image(
                self._parent_handle, image_data, content_type, width_emu, height_emu
            )
            alt_text: str = data.get("alt_text", "")
            if alt_text:
                self._lib.set_str(child_handle, "alt_text", alt_text)
        else:
            child_handle = self._lib.append_child(
                self._parent_handle,
                type(element)._child_type_name,  # type: ignore[reportPrivateUsage]
            )
            runs_data: list[Any] | None = data.get("runs")
            plain_data = {k: v for k, v in data.items() if k != "runs"}
            plain_data = self._resolve_style(plain_data)
            if plain_data:
                self._lib.set_many(child_handle, plain_data)
            if runs_data:
                for run in runs_data:
                    run_data: dict[str, Any] = object.__getattribute__(run, "_data")
                    run_handle = self._lib.append_child(child_handle, "run")
                    if run_data:
                        self._lib.set_many(run_handle, run_data)
                    run._attach(run_handle, self._document)  # type: ignore[reportPrivateUsage]

        element._attach(child_handle, self._document)  # type: ignore[reportPrivateUsage]
        return element

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def first(self) -> T | None:
        """Returns the first element of the collection

        Raises:
            NativeRuntimeError: If the native library returns an error when trying to access the first element

        Returns:
            T | None: The first element of the collection. Defaults to None if the collection is empty.
        """
        if self._count() == 0:
            return None
        try:
            return self._make_proxy(self._handle_at(0))
        except NativeRuntimeError:
            return None

    @property
    def last(self) -> T | None:
        """Returns the last element of the collection

        Raises:
            NativeRuntimeError: If the native library returns an error when trying to access the last element

        Returns:
            T | None: The last element of the collection. Defaults to None if the collection is empty.
        """
        n = self._count()
        if n == 0:
            return None
        return self._make_proxy(self._handle_at(n - 1))

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def append(self, element: T) -> None:
        """Append the provided element to the collection of elements

        Args:
            element (T): The element to append, being of the same type that is supported by the collection.
        Raises:
            OwnershipError: Occurs if the element provided belongs to another document instead of being passed as a snapshot by calling snapshot(element).
            ValueError: Occurs if the element already exists in the collection.
            TypeError: Occurs if the element being appened is not of the same type specified by the collection.
        """
        self._append_one(element)

    def extend(self, elements: Iterable[T]) -> None:
        """Append each element in *elements* to the collection in order.

        Args:
            elements: An iterable of construction-state proxy objects of the
                collection's element type.

        Raises:
            OwnershipError: If any element belongs to a different document.
            ValueError: If any element is already live in this document.
            TypeError: If any element is the wrong type for this collection.
        """
        for elem in elements:
            self._append_one(elem)

    def insert(self, index: int, element: T) -> None:
        """Append *element* to the collection (positional insert is not yet supported).

        .. warning::
            In v1 ``insert()`` always appends to the end, regardless of *index*,
            and emits a :class:`FutureWarning`. Positional insertion will be
            supported in a future release, at which point this behaviour will change.

        Args:
            index: Intended insertion position (currently ignored).
            element: The element to append.
        """
        if index != len(self):
            warnings.warn(
                f"insert() ignores positional index {index!r} in v1 and always appends. "
                "Positional insertion will be supported in a future release.",
                FutureWarning,
                stacklevel=2,
            )
        self._append_one(element)

    def remove(self, element: T) -> None:
        """Remove *element* from the collection and mark it stale.

        After removal, any attempt to access *element*'s properties raises
        :exc:`~navyfox.errors.StaleProxyError`. Call ``snapshot()`` before
        removing if you need to keep the data.

        Args:
            element: A live proxy that currently belongs to this collection.

        Raises:
            TypeError: If *element* is the wrong type for this collection.
            ValueError: If *element* is not currently in a document.
        """
        self._validate_element(element)
        native = object.__getattribute__(element, "_native")
        if native is None:
            raise ValueError(f"Cannot remove a {type(element).__name__} that is not in a document.")
        self._lib.remove_child(native)
        # call via object.__getattribute__ to avoid direct protected-member access
        object.__getattribute__(element, "_mark_stale")()

    def pop(self, index: int | None = None) -> T:
        """Remove an element in a collection at a specified index.

        Args:
            index (int | None, optional): The index to delete an element at. Defaults to None.

        Raises:
            IndexError: Occurs if a provided index is outside of range of indexes of the collections.

        Returns:
            T: The element at the specified index.
        """
        index = -1 if index is None else index
        n = self._count()
        if index < 0:
            index = n + index
        if not (0 <= index < n):
            raise IndexError(f"index {index} out of range for collection of length {n}")
        item = self._make_proxy(self._handle_at(index))
        snap = item.copy()
        self.remove(item)
        return snap

    def clear(self) -> None:
        """Empties the elements of the collection."""
        while self._count() > 0:
            self.remove(self._make_proxy(self._handle_at(0)))

    def index(self, element: T) -> int:
        """Returns the index of the provided element inside of the collection.

        Args:
            element (T): The element to find the index of.

        Raises:
            ValueError: Occurs if the element provided does not exist in the collection.

        Returns:
            int: The index of the element in the collection.
        """
        for i, item in enumerate(self):
            if item == element:
                return i
        raise ValueError(f"{element!r} is not in this collection")

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._count()

    def __iter__(self) -> Iterator[T]:
        for i in range(len(self)):
            yield self._make_proxy(self._handle_at(i))

    def __reversed__(self) -> Iterator[T]:
        for i in range(len(self) - 1, -1, -1):
            yield self._make_proxy(self._handle_at(i))

    def __contains__(self, element: object) -> bool:
        if not isinstance(element, tuple(self._elem_types)):
            return False
        native = object.__getattribute__(element, "_native")
        if native is None:
            return False
        return any(object.__getattribute__(item, "_native") == native for item in self)

    def __iadd__(self, elements: Iterable[T]) -> Self:
        self.extend(elements)
        return self

    def __getitem__(self, index: int | slice) -> T | DocumentView[T]:
        if isinstance(index, slice):
            indices = range(*index.indices(self._count()))
            items = [self._make_proxy(self._handle_at(i)) for i in indices]
            return _SliceView(
                items, self._document, self._lib, self._elem_types, self._collection_name
            )
        n = self._count()
        if index < 0:
            index = n + index
        if not (0 <= index < n):
            raise IndexError(f"index {index} out of range for collection of length {n}")
        return self._make_proxy(self._handle_at(index))


class DocumentView[T: Element](CollectionMixin[T]):
    """Live view over a typed subset of a document element's children.

    A ``DocumentView`` holds a reference to the parent handle and a collection
    name. All reads and mutations go directly to the native layer — nothing is
    cached in Python.

    Obtained via collection properties on :class:`~navyfox.document.Document`,
    :class:`~navyfox.paragraph.Paragraph`, :class:`~navyfox.table.Table`, etc.:

    .. code-block:: python

        paras = doc.paragraphs          # DocumentView[Paragraph]
        runs  = para.runs               # DocumentView[Run]
        cells = table.rows[0].cells     # DocumentView[Cell]

    Supports the full list protocol: iteration, indexing, slicing, ``len()``,
    ``in``, ``+=``, ``append()``, ``extend()``, ``remove()``, ``pop()``,
    ``clear()``, ``index()``, plus ``.first`` and ``.last`` shortcuts.

    Two ``DocumentView`` objects over the same parent can be merged with ``|``:

    .. code-block:: python

        mixed = doc.paragraphs | doc.tables  # DocumentView[Paragraph | Table]
    """

    def __init__(
        self,
        parent_handle: int,
        document: Document,
        lib: Handle,
        elem_types: ElemTypesArg[T],
        collection_name: str,
    ) -> None:
        self._parent_handle = parent_handle
        self._document = document
        self._lib = lib
        self._elem_types = _to_elem_tuple(elem_types)
        self._collection_name = collection_name

    @staticmethod
    def empty[VT: Element](
        elem_types: ElemTypesArg[VT], collection_name: str
    ) -> DocumentView[VT]:
        """Return an empty, inert DocumentView with no native handle."""
        return _SliceView([], None, None, _to_elem_tuple(elem_types), collection_name)

    def __bool__(self) -> bool:
        return self._count() > 0

    def __or__[U: Element](self, other: DocumentView[U]) -> DocumentView[T | U]:
        return _UnionView(
            self._parent_handle,
            self._document,
            self._lib,
            self._elem_types + other._elem_types,
            "body",
        )

    def __repr__(self) -> str:
        names = " | ".join(t.__name__ for t in self._elem_types)
        try:
            return f"DocumentView[{names}](len={len(self)})"
        except Exception:
            return f"DocumentView[{names}](<error>)"


class _SliceView[T: Element](DocumentView[T]):
    """A fixed-size view over a slice of a parent collection (snapshot of handles)."""

    def __init__(
        self,
        items: list[T],
        document: Document | None,
        lib: Handle | None,
        elem_types: ElemTypesArg[T],
        collection_name: str,
    ) -> None:
        self._items = items
        self._document = document
        self._lib = lib
        self._elem_types = _to_elem_tuple(elem_types)
        self._collection_name = collection_name

    def _count(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> DocumentView[T]: ...
    def __getitem__(self, index: int | slice) -> T | DocumentView[T]:
        if isinstance(index, slice):
            return _SliceView(
                self._items[index],
                self._document,
                self._lib,
                self._elem_types,
                self._collection_name,
            )
        return self._items[index]


class _UnionView[T: Element](DocumentView[T]):
    """A view over the full body, returning all matching element types."""

    pass
