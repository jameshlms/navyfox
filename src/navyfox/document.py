from __future__ import annotations

import contextlib
import os
import tempfile
import threading
import weakref
from collections.abc import Iterable
from typing import IO, TYPE_CHECKING, Any, ClassVar, Self, overload

import navyfox._native.handle as _handle_mod
from navyfox._block import BlockContainerMixin, _BlockViewProperty
from navyfox._collection import CollectionMixin
from navyfox._native.handle import Handle
from navyfox._proxy.base import Element
from navyfox.errors import DocumentClosedError
from navyfox.paragraph import Paragraph
from navyfox.table import Table

if TYPE_CHECKING:
    from navyfox._collection import DocumentView
    from navyfox.formats import PageMargins
    from navyfox.section import Section
    from navyfox.styles import StyleCollection

_PathArg = str | os.PathLike[str] | IO[bytes]

_active_count = 0
_active_count_lock = threading.Lock()


def _resolve_open_path(path: _PathArg) -> tuple[str, str | None]:
    """Return (str_path, tmp_path). tmp_path is set for IO inputs and must be deleted after use."""
    if isinstance(path, (str, os.PathLike)):
        return os.fspath(path), None
    data = path.read()
    fd, tmp_path = tempfile.mkstemp(suffix=".docx")
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return tmp_path, tmp_path


class _DocMetaProperty:
    """Document-level metadata descriptor backed by the native layer. readonly=True blocks set."""

    def __init__(self, key: str, *, readonly: bool = False) -> None:
        self._key = key
        self._readonly = readonly

    @overload
    def __get__(self, obj: None, objtype: type) -> _DocMetaProperty: ...
    @overload
    def __get__(self, obj: Document, objtype: type) -> str: ...

    def __get__(self, obj: Document | None, objtype: type | None = None) -> str | _DocMetaProperty:
        if obj is None:
            return self
        return obj._lib.get_str(obj._require_open(), self._key) or ""

    def __set__(self, obj: Document, value: str) -> None:
        if self._readonly:
            raise AttributeError(f"{self._key!r} is read-only")
        obj._lib.set_str(obj._require_open(), self._key, value)


def _section_type() -> type[Section]:
    from navyfox.section import Section

    return Section


def _type_name_map() -> dict[type, str]:
    from navyfox.section import Section

    return {
        Paragraph: "paragraphs",
        Table: "tables",
        Section: "sections",
    }


def _collection_for_type(t: type) -> str:
    return _type_name_map().get(t, "body")


class Document(BlockContainerMixin, CollectionMixin[Element]):
    """A DOCX document backed by the NavyFox native library.

    The document is the body collection — iterate it, append to it, and access
    typed filtered views via ``.paragraphs``, ``.tables``, ``.sections``, etc.

    All document data lives in the C# native layer. Python proxies (Paragraph, Run,
    Table, …) hold only integer handles. Every property access crosses the FFI boundary.

    Prefer the context manager for deterministic cleanup:

    .. code-block:: python

        with Document.open("report.docx") as doc:
            doc.paragraphs[0].text = "Updated"
            doc.save()

    Without a context manager, call ``.close()`` explicitly:

    .. code-block:: python

        doc = Document()
        doc.add_paragraph("Hello")
        doc.save("output.docx")
        doc.close()

    Closing an already-closed document is safe (idempotent). Forgetting to close
    triggers a ``ResourceWarning`` when the object is garbage-collected.
    """

    _lib: Handle
    _handle: int
    _path: str | None
    _edit_path: str | None
    _tmp_path: str | None
    _io_edit: IO[bytes] | None
    _open: bool
    _finalizer: weakref.finalize[[Handle, int, str | None], Any]
    _collection_name = "body"

    @staticmethod
    def _dispose(lib: Handle, handle: int, tmp_path: str | None) -> None:
        with contextlib.suppress(Exception):
            lib.dispose(handle)
        if tmp_path:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)

    def __init__(self) -> None:
        lib = _handle_mod.get_handle()
        handle = lib.create_document()
        self._lib = lib
        self._handle = handle
        self._path = None
        self._edit_path = None
        self._tmp_path = None
        self._io_edit = None
        self._open = True
        self._finalizer = weakref.finalize(self, Document._dispose, lib, handle, None)

    @classmethod
    def _from_path(cls, path: _PathArg, *, edit: bool) -> Document:
        str_path, tmp_path = _resolve_open_path(path)
        lib = _handle_mod.get_handle()
        handle = lib.open_document(str_path)
        doc = cls.__new__(cls)
        doc._lib = lib
        doc._handle = handle
        doc._path = None if tmp_path else str_path
        doc._edit_path = str_path if edit else None
        doc._tmp_path = tmp_path
        doc._io_edit = path if (edit and not isinstance(path, (str, os.PathLike))) else None
        doc._open = True
        doc._finalizer = weakref.finalize(doc, Document._dispose, lib, handle, tmp_path)
        return doc

    @classmethod
    def open(cls, path: _PathArg) -> Document:
        """Open an existing ``.docx`` file for reading or writing.

        Args:
            path: Filesystem path (``str`` or :class:`pathlib.Path`) or a
                binary file-like object (``IO[bytes]``).  When an ``IO``
                object is given its current contents are read immediately;
                ``doc.path`` will be ``None``.

        Returns:
            A live ``Document`` backed by the given source.

        Example:
            .. code-block:: python

                with Document.open("report.docx") as doc:
                    for para in doc.paragraphs:
                        print(para.text)

                # from a byte stream
                with open("report.docx", "rb") as f:
                    with Document.open(f) as doc:
                        print(doc.paragraphs[0].text)
        """
        return cls._from_path(path, edit=False)

    @classmethod
    def edit(cls, path: _PathArg) -> Document:
        """Open a document for in-place editing.

        Identical to ``open()`` except that the context manager automatically
        saves back to *path* on ``__exit__``.  When *path* is an ``IO``
        object the modified bytes are written back to it on exit.

        Args:
            path: Filesystem path (``str`` or :class:`pathlib.Path`) or a
                binary file-like object (``IO[bytes]``).

        Example:
            .. code-block:: python

                with Document.edit("report.docx") as doc:
                    doc.paragraphs[0].text = "New heading"
                # saved automatically

                # round-trip through a buffer
                buf = io.BytesIO(pathlib.Path("report.docx").read_bytes())
                with Document.edit(buf) as doc:
                    doc.paragraphs[0].text = "New heading"
                buf.seek(0)
                pathlib.Path("report.docx").write_bytes(buf.read())
        """
        return cls._from_path(path, edit=True)

    @property
    def _parent_handle(self) -> int:
        return self._require_open()

    @property
    def _document(self) -> Document:
        return self

    _elem_types: ClassVar[tuple[type[Paragraph], type[Table]]] = (Paragraph, Table)

    def _block_context(self) -> tuple[int, Any, Any]:
        return (self._require_open(), self._lib, self)

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def path(self) -> str | None:
        return self._path

    def close(self) -> None:
        """Release the native document handle. Idempotent."""
        if self._open:
            self._open = False
            self._finalizer()

    def __enter__(self) -> Self:
        global _active_count
        with _active_count_lock:
            _active_count += 1
        return self

    def __exit__(self, *_: object) -> None:
        global _active_count
        if self._open:
            if self._io_edit is not None:
                self.save(self._io_edit)
            elif self._edit_path:
                self.save(self._edit_path)
        self.close()
        with _active_count_lock:
            _active_count -= 1

    def _require_open(self) -> int:
        if not self._open:
            raise DocumentClosedError(
                "Document is closed. "
                "Call .copy() inside the context manager to use data outside it."
            )
        return self._handle

    def save(self, path: _PathArg | None = None) -> None:
        """Save the document.

        Args:
            path: Destination as a ``str``, :class:`pathlib.Path`, or binary
                ``IO[bytes]`` object.  If omitted, saves back to the path the
                document was opened from or last saved to.  An ``IO`` target
                never updates ``doc.path``.

        Raises:
            ValueError: If *path* is ``None`` and no associated path exists.
        """
        target: _PathArg | None = path if path is not None else self._path
        if target is None:
            raise ValueError(
                "No path provided and document has no associated path. Pass a path to save()."
            )
        lib: Handle = self._lib
        if isinstance(target, (str, os.PathLike)):
            str_target = os.fspath(target)
            lib.save_document(self._require_open(), str_target)
            self._path = str_target
        else:
            fd, tmp = tempfile.mkstemp(suffix=".docx")
            os.close(fd)
            try:
                lib.save_document(self._require_open(), tmp)
                with open(tmp, "rb") as f:
                    target.write(f.read())
            finally:
                with contextlib.suppress(OSError):
                    os.unlink(tmp)

    @property
    def styles(self) -> StyleCollection:
        from navyfox.styles import StyleCollection

        return StyleCollection(self._require_open(), self)

    @property
    def default_style(self) -> object:
        return self.styles.default

    author = _DocMetaProperty("author")
    title = _DocMetaProperty("title")
    # The native C# API only exposes write access for author and title.
    subject = _DocMetaProperty("subject", readonly=True)
    description = _DocMetaProperty("description", readonly=True)
    language = _DocMetaProperty("language", readonly=True)

    sections: _BlockViewProperty[Section] = _BlockViewProperty(_section_type)

    @property
    def margins(self) -> PageMargins:
        """Page margins for the document.

        On get: returns the shared :class:`~navyfox.formats.PageMargins` when all
        sections have identical margins, or the defaults if no sections exist.
        Raises :exc:`ValueError` if sections have differing margins — use
        ``doc.sections[i].margin_*`` to read per-section values instead.

        On set: applies the given margins to **all** sections. Accepts:

        - A :class:`~navyfox.formats.PageMargins` instance.
        - A single ``float`` — sets top, bottom, left, and right uniformly.
        - A 2-tuple ``(vertical, horizontal)`` — CSS-style shorthand.
        - A 4-tuple ``(top, bottom, left, right)``.

        Example:
            .. code-block:: python

                doc.margins = 0.75                    # tight, all sides
                doc.margins = (0.75, 1.0)             # 0.75 top/bottom, 1.0 left/right
                doc.margins = PageMargins(left=0.5, right=0.5)
        """
        from navyfox.formats import PageMargins

        secs = self.sections
        if len(secs) == 0:
            return PageMargins()
        first = PageMargins(
            top=secs[0].margin_top,
            bottom=secs[0].margin_bottom,
            left=secs[0].margin_left,
            right=secs[0].margin_right,
            header=secs[0].margin_header,
            footer=secs[0].margin_footer,
        )
        mismatch = any(
            PageMargins(
                top=s.margin_top,
                bottom=s.margin_bottom,
                left=s.margin_left,
                right=s.margin_right,
                header=s.margin_header,
                footer=s.margin_footer,
            )
            != first
            for s in secs[1:]
        )

        if mismatch:
            raise ValueError(
                "Sections have differing margins; cannot return a single value. Read margins from individual sections instead."
            )

        return first

    @margins.setter
    def margins(
        self,
        value: PageMargins | float | tuple[float, float] | tuple[float, float, float, float],
    ) -> None:
        from navyfox.formats import PageMargins

        match value:
            case PageMargins():
                pm = value

            case float() | int():
                v = float(value)
                pm = PageMargins(top=v, bottom=v, left=v, right=v)

            case (float() | int(), float() | int()):
                v, h = float(value[0]), float(value[1])
                pm = PageMargins(top=v, bottom=v, left=h, right=h)

            case (float() | int(), float() | int(), float() | int(), float() | int()):
                pm = PageMargins(
                    top=float(value[0]),
                    bottom=float(value[1]),
                    left=float(value[2]),
                    right=float(value[3]),
                )
            case tuple():
                raise ValueError(
                    f"margins tuple must have 2 or 4 elements, got {len(value)}"
                )
            case _:
                raise TypeError(
                    f"margins must be a PageMargins, float, or tuple; got {type(value).__name__!r}"
                )

        for section in self.sections:
            section.margin_top = pm.top
            section.margin_bottom = pm.bottom
            section.margin_left = pm.left
            section.margin_right = pm.right
            section.margin_header = pm.header
            section.margin_footer = pm.footer

    def group[T: Element](self, types: list[type[T]]) -> DocumentView[T]:
        """Return a live view over the body containing only the given element types.

        Args:
            types: A list of proxy types to include (e.g. ``[Paragraph, Table]``).

        Returns:
            A :class:`~navyfox.collection.DocumentView` that yields only elements
            whose type is in *types*.

        Example:
            .. code-block:: python

                from navyfox import Paragraph, Table
                for elem in doc.group([Paragraph, Table]):
                    print(type(elem).__name__, repr(elem))
        """
        from navyfox._collection import DocumentView

        return DocumentView(
            self._require_open(),
            self,  # type: ignore[arg-type]  # Self@Document IS Document; Pyright can't resolve the circular stub
            self._lib,
            tuple(types),
            "body",
        )

    def __bool__(self) -> bool:
        return self._open

    def __contains__(self, element: object) -> bool:
        from navyfox._proxy.base import Element

        if not isinstance(element, Element):
            return False
        native = element._native  # type: ignore[union-attr]
        if native is None:
            return False
        doc = element._document  # type: ignore[union-attr]
        return doc is self

    @overload
    def __getitem__(self, key: int) -> Element: ...
    @overload
    def __getitem__(self, key: slice) -> DocumentView[Element]: ...
    @overload
    def __getitem__[T: Element](self, key: type[T]) -> DocumentView[T]: ...

    def __getitem__(self, key: int | slice | type) -> Element | DocumentView[Any]:
        if isinstance(key, type):
            return self._block_view(key, _collection_for_type(key))
        return super().__getitem__(key)  # type: ignore[return-value]

    def __iadd__(self, elements: Iterable[Element]) -> Self:  # type: ignore[override]
        self.extend(elements)
        return self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return NotImplemented
        return self._handle == other._handle

    def __hash__(self) -> int:
        return hash(self._handle)

    def __repr__(self) -> str:
        try:
            n = len(self) if self._open else "?"
        except Exception:
            n = "?"
        return f"<Document path={self._path!r} elements={n} open={self._open}>"
