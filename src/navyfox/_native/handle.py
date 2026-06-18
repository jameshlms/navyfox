"""FFI transport layer — delegates all calls to the _navyfox Rust extension."""
from __future__ import annotations

from typing import Any

import _navyfox as _nx

from navyfox.errors import NativeRuntimeError

_cached: Handle | None = None


def _call(fn, *args):
    """Invoke a _navyfox function, re-raising RuntimeError as NativeRuntimeError."""
    try:
        return fn(*args)
    except RuntimeError as exc:
        raise NativeRuntimeError(str(exc)) from exc


class Handle:
    """Thin adapter over the _navyfox Rust extension.

    Presents the same interface as the old ctypes Handle so all proxy and
    descriptor code above this layer is unchanged.
    """

    # ── Document lifecycle ────────────────────────────────────────────────

    def create_document(self) -> int:
        return _call(_nx.create_document)

    def open_document(self, path: str) -> int:
        return _call(_nx.open_document, path)

    def edit_document(self, path: str) -> int:
        return _call(_nx.edit_document, path)

    def save_document(self, handle: int, path: str) -> None:
        _call(_nx.save_document, handle, path)

    def dispose(self, handle: int) -> None:
        _nx.dispose(handle)

    # ── Generic property access ───────────────────────────────────────────

    def get_int(self, handle: int, name: str) -> int:
        return int(_nx.get_int(handle, name))

    def set_int(self, handle: int, name: str, value: int) -> None:
        _call(_nx.set_int, handle, name, value)

    def get_float(self, handle: int, name: str) -> float:
        return _call(_nx.get_float, handle, name)

    def set_float(self, handle: int, name: str, value: float) -> None:
        _call(_nx.set_float, handle, name, value)

    def get_str(self, handle: int, name: str) -> str:
        return _call(_nx.get_str, handle, name)

    def set_str(self, handle: int, name: str, value: str) -> None:
        _call(_nx.set_str, handle, name, value)

    # ── Collection operations ─────────────────────────────────────────────

    def get_count(self, handle: int, collection: str) -> int:
        return _call(_nx.get_count, handle, collection)

    def get_child_handle(self, handle: int, collection: str, index: int) -> int:
        return _call(_nx.get_child_handle, handle, collection, index)

    def append_child(self, handle: int, child_type: str) -> int:
        return _call(_nx.append_child, handle, child_type)

    def remove_child(self, handle: int) -> None:
        _call(_nx.remove_child, handle)

    def get_element_type(self, handle: int) -> str:
        return _nx.get_element_type(handle)

    # ── Special-case constructors ─────────────────────────────────────────

    def add_table(self, doc_handle: int, rows: int, cols: int) -> int:
        return _call(_nx.add_table, doc_handle, rows, cols)

    def add_image(
        self,
        parent_handle: int,
        data: bytes,
        content_type: str,
        width_emu: int,
        height_emu: int,
    ) -> int:
        return _call(_nx.add_image, parent_handle, data, content_type, width_emu, height_emu)

    def get_image_data(self, handle: int) -> bytes:
        return _call(_nx.get_image_data, handle)

    # ── Batch write ───────────────────────────────────────────────────────

    def set_many(self, handle: int, data: dict[str, Any]) -> None:
        for name, value in data.items():
            if value is None:
                continue
            match value:
                case bool():
                    self.set_int(handle, name, int(value))
                case int():
                    self.set_int(handle, name, value)
                case float() if value != 0.0:
                    self.set_float(handle, name, value)
                case str() if value:
                    self.set_str(handle, name, value)
                case _:
                    raise ValueError(
                        f"Unsupported value type for {name!r}: {type(value).__name__}"
                    )


def get_handle() -> Handle:
    """Return the lazily-created Handle singleton."""
    global _cached
    if _cached is None:
        _cached = Handle()
    return _cached
