from __future__ import annotations

import ctypes
import math
import os
import platform
from pathlib import Path
from typing import Any

from navyfox.errors import NativeRuntimeError

_PLATFORM_MAP: dict[tuple[str, str], tuple[str, str]] = {
    ("Linux", "x86_64"):  ("linux-x64",  "NavyFox.Native.so"),
    ("Linux", "aarch64"): ("linux-arm64", "NavyFox.Native.so"),
    ("Windows", "AMD64"): ("win-x64",    "NavyFox.Native.dll"),
    ("Windows", "ARM64"): ("win-arm64",  "NavyFox.Native.dll"),
    ("Darwin", "arm64"):  ("osx-arm64",  "NavyFox.Native.dylib"),
    ("Darwin", "x86_64"): ("osx-x64",   "NavyFox.Native.dylib"),
}

_BUF_INIT = 256

_nf: ctypes.CDLL | None = None
_cached: Handle | None = None


def _load_native() -> ctypes.CDLL:
    key = (platform.system(), platform.machine())
    entry = _PLATFORM_MAP.get(key)
    if entry is None:
        raise RuntimeError(
            f"navyfox: unsupported platform {key[0]!r}/{key[1]!r}. "
            f"Supported: {list(_PLATFORM_MAP)}"
        )
    rid, lib_name = entry
    lib_path = Path(__file__).parent.parent / "_libs" / rid / lib_name
    if not lib_path.exists():
        raise RuntimeError(
            f"navyfox: native binary not found at {lib_path}.\n"
            f"Install navyfox from a binary wheel or build the native library:\n"
            f"  dotnet publish native/NavyFox.Native -r {rid} -c Release"
        )
    if platform.system() == "Windows":
        # Add the lib dir and the delvewheel-managed .libs dir to the DLL
        # search path so bundled CRT dependencies are found by the loader.
        os.add_dll_directory(str(lib_path.parent))  # type: ignore[attr-defined]
        libs_dir = lib_path.parent.parent.parent / ".libs"
        if libs_dir.exists():
            os.add_dll_directory(str(libs_dir))  # type: ignore[attr-defined]
    lib = ctypes.CDLL(str(lib_path))
    _configure(lib)
    return lib


def _configure(lib: ctypes.CDLL) -> None:
    ss = ctypes.c_ssize_t
    ci = ctypes.c_int32
    cd = ctypes.c_double
    cp = ctypes.c_char_p
    pi = ctypes.POINTER(ctypes.c_int32)

    lib.create_document.restype = ss
    lib.create_document.argtypes = []

    lib.open_document.restype = ss
    lib.open_document.argtypes = [cp, ci]

    lib.edit_document.restype = ss
    lib.edit_document.argtypes = [cp, ci]

    lib.save_document.restype = ci
    lib.save_document.argtypes = [ss, cp, ci]

    lib.dispose.restype = None
    lib.dispose.argtypes = [ss]

    lib.get_int.restype = ci
    lib.get_int.argtypes = [ss, cp, ci]

    lib.set_int.restype = ci
    lib.set_int.argtypes = [ss, cp, ci, ci]

    lib.get_float.restype = cd
    lib.get_float.argtypes = [ss, cp, ci]

    lib.set_float.restype = ci
    lib.set_float.argtypes = [ss, cp, ci, cd]

    lib.get_str.restype = ci
    lib.get_str.argtypes = [ss, cp, ci, cp, ci, pi]

    lib.set_str.restype = ci
    lib.set_str.argtypes = [ss, cp, ci, cp, ci]

    lib.get_count.restype = ci
    lib.get_count.argtypes = [ss, cp, ci]

    lib.get_child_handle.restype = ss
    lib.get_child_handle.argtypes = [ss, cp, ci, ci]

    lib.append_child.restype = ss
    lib.append_child.argtypes = [ss, cp, ci]

    lib.remove_child.restype = ci
    lib.remove_child.argtypes = [ss]

    lib.get_element_type.restype = ci
    lib.get_element_type.argtypes = [ss, cp, ci, pi]

    lib.add_table.restype = ss
    lib.add_table.argtypes = [ss, ci, ci]

    lib.add_image.restype = ss
    lib.add_image.argtypes = [ss, cp, ci, cp, ci, ci, ci]

    lib.get_image_data.restype = ci
    lib.get_image_data.argtypes = [ss, cp, ci, pi]


def _get_lib() -> ctypes.CDLL:
    global _nf
    if _nf is None:
        _nf = _load_native()
    return _nf


class Handle:
    def create_document(self) -> int:
        h = _get_lib().create_document()
        if h == 0:
            raise NativeRuntimeError("create_document returned null handle")
        return int(h)

    def open_document(self, path: str) -> int:
        enc = path.encode()
        h = _get_lib().open_document(enc, len(enc))
        if h == 0:
            raise NativeRuntimeError(f"open_document failed for {path!r}")
        return int(h)

    def edit_document(self, path: str) -> int:
        enc = path.encode()
        h = _get_lib().edit_document(enc, len(enc))
        if h == 0:
            raise NativeRuntimeError(f"edit_document failed for {path!r}")
        return int(h)

    def save_document(self, handle: int, path: str) -> None:
        enc = path.encode()
        rc = _get_lib().save_document(handle, enc, len(enc))
        if rc != 0:
            raise NativeRuntimeError(f"save_document failed for {path!r}")

    def dispose(self, handle: int) -> None:
        _get_lib().dispose(handle)

    def get_int(self, handle: int, name: str) -> int:
        enc = name.encode()
        return int(_get_lib().get_int(handle, enc, len(enc)))

    def set_int(self, handle: int, name: str, value: int) -> None:
        enc = name.encode()
        rc = _get_lib().set_int(handle, enc, len(enc), value)
        if rc != 0:
            raise NativeRuntimeError(f"set_int({name!r}={value}) failed")

    def get_float(self, handle: int, name: str) -> float:
        enc = name.encode()
        val: float = _get_lib().get_float(handle, enc, len(enc))
        if math.isnan(val):
            raise NativeRuntimeError(f"get_float({name!r}) failed")
        return val

    def set_float(self, handle: int, name: str, value: float) -> None:
        enc = name.encode()
        rc = _get_lib().set_float(handle, enc, len(enc), value)
        if rc != 0:
            raise NativeRuntimeError(f"set_float({name!r}={value}) failed")

    def get_str(self, handle: int, name: str) -> str:
        enc = name.encode()
        buf_size = _BUF_INIT
        lib = _get_lib()
        while True:
            buf = ctypes.create_string_buffer(buf_size)
            required = ctypes.c_int32(0)
            n = lib.get_str(handle, enc, len(enc), buf, buf_size, ctypes.byref(required))
            if n < 0:
                raise NativeRuntimeError(f"get_str({name!r}) failed (rc={n})")
            if n == 0:
                if required.value == 0:
                    return ""
                buf_size = required.value + 1
                continue
            return buf.raw[:n].decode("utf-8")

    def set_str(self, handle: int, name: str, value: str) -> None:
        enc_name = name.encode()
        enc_val = value.encode()
        rc = _get_lib().set_str(handle, enc_name, len(enc_name), enc_val, len(enc_val))
        if rc != 0:
            raise NativeRuntimeError(f"set_str({name!r}) failed")

    def get_count(self, handle: int, collection: str) -> int:
        enc = collection.encode()
        n = _get_lib().get_count(handle, enc, len(enc))
        if n < 0:
            raise NativeRuntimeError(f"get_count({collection!r}) failed (rc={n})")
        return int(n)

    def get_child_handle(self, handle: int, collection: str, index: int) -> int:
        enc = collection.encode()
        h = _get_lib().get_child_handle(handle, enc, len(enc), index)
        if h == 0:
            raise NativeRuntimeError(f"get_child_handle({collection!r}, {index}) failed")
        return int(h)

    def append_child(self, handle: int, child_type: str) -> int:
        enc = child_type.encode()
        h = _get_lib().append_child(handle, enc, len(enc))
        if h == 0:
            raise NativeRuntimeError(f"append_child({child_type!r}) failed")
        return int(h)

    def remove_child(self, handle: int) -> None:
        rc = _get_lib().remove_child(handle)
        if rc != 0:
            raise NativeRuntimeError("remove_child failed")

    def get_element_type(self, handle: int) -> str:
        buf_size = _BUF_INIT
        lib = _get_lib()
        while True:
            buf = ctypes.create_string_buffer(buf_size)
            required = ctypes.c_int32(0)
            n = lib.get_element_type(handle, buf, buf_size, ctypes.byref(required))
            if n <= 0:
                if required.value > buf_size:
                    buf_size = required.value + 1
                    continue
                return "unknown"
            return buf.raw[:n].decode("utf-8")

    def add_table(self, doc_handle: int, rows: int, cols: int) -> int:
        h = _get_lib().add_table(doc_handle, rows, cols)
        if h == 0:
            raise NativeRuntimeError("add_table failed")
        return int(h)

    def add_image(
        self,
        parent_handle: int,
        data: bytes,
        content_type: str,
        width_emu: int,
        height_emu: int,
    ) -> int:
        enc_ct = content_type.encode()
        h = _get_lib().add_image(
            parent_handle, data, len(data), enc_ct, len(enc_ct), width_emu, height_emu
        )
        if h == 0:
            raise NativeRuntimeError("add_image failed")
        return int(h)

    def get_image_data(self, handle: int) -> bytes:
        buf_size = 4096
        lib = _get_lib()
        while True:
            buf = ctypes.create_string_buffer(buf_size)
            required = ctypes.c_int32(0)
            n = lib.get_image_data(handle, buf, buf_size, ctypes.byref(required))
            if n < 0:
                raise NativeRuntimeError("get_image_data failed")
            if n == 0:
                if required.value == 0:
                    return b""
                buf_size = required.value + 1
                continue
            return buf.raw[:n]

    def set_many(self, handle: int, data: dict[str, Any]) -> None:
        for name, value in data.items():
            if value is None:
                continue
            match value:
                case int() | bool():
                    self.set_int(handle, name, int(value))
                case float():
                    self.set_float(handle, name, value)
                case str() if value:
                    self.set_str(handle, name, value)
                case _:
                    raise ValueError(
                        f"Unsupported value type for {name!r}: {type(value).__name__}"
                    )


def get_handle() -> Handle:
    global _cached
    if _cached is None:
        _get_lib()  # ensure lib loads and fails fast before creating Handle
        _cached = Handle()
    return _cached
