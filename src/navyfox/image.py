"""Image proxy — a run-level inline image element.

In OpenXML an image is stored as ``<w:drawing>`` inside a ``<w:r>`` run, so
:class:`Image` is a sibling of :class:`~navyfox.run.Run` within
``para.runs``.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from navyfox._proxy.base import Element, ElementState
from navyfox._proxy.descriptors import FloatProperty, StringProperty

if TYPE_CHECKING:
    from navyfox._native.handle import Handle
    from navyfox.document import Document

__all__ = ["Image"]

_CONTENT_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".emf": "image/x-emf",
    ".wmf": "image/x-wmf",
}


def _guess_content_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in _CONTENT_TYPES:
        return _CONTENT_TYPES[ext]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "image/png"


class Image(Element):
    """A run-level inline image element.

    **Construction** (before appending to a paragraph):

    .. code-block:: python

        # From a file path — content type is inferred from the extension
        img = Image("photo.png", width=3.0, height=2.0)
        para.runs.append(img)

        # From raw bytes
        img = Image(data=png_bytes, content_type="image/png", width=3.0, height=2.0)
        para.runs.append(img)

    **Live proxy** (from ``para.runs[i]`` when the element is an image):

    .. code-block:: python

        img = para.images[0]
        print(img.width, img.height)
        img.alt_text = "Company logo"

    Both ``width`` and ``height`` are in **inches**.
    """

    __slots__ = ()
    _child_type_name = "image"

    alt_text = StringProperty("alt_text", default="")
    content_type = StringProperty("content_type", default="")
    width = FloatProperty("width", default=0.0)  # inches
    height = FloatProperty("height", default=0.0)  # inches

    def __init__(
        self,
        src: str | Path | None = None,
        *,
        data: bytes | None = None,
        content_type: str | None = None,
        width: float = 0.0,
        height: float = 0.0,
        alt_text: str = "",
    ) -> None:
        """
        Args:
            src: Path to an image file. Content type is inferred from the
                extension unless *content_type* is also given.
            data: Raw image bytes. Must be given if *src* is omitted.
            content_type: MIME type, e.g. ``"image/png"``. Required when
                *data* is used; optional when *src* is used.
            width: Display width in inches. ``0.0`` lets the C# side use the
                image's natural size.
            height: Display height in inches. ``0.0`` lets the C# side use the
                image's natural size.
            alt_text: Accessibility description for screen readers.

        Raises:
            ValueError: If both *src* and *data* are given, or if neither is given.
        """
        if src is not None and data is not None:
            raise ValueError("Provide either src (file path) or data (bytes), not both.")
        if src is None and data is None:
            raise ValueError("Provide either src (file path) or data (bytes).")

        super().__init__()
        d: dict[str, Any] = {}

        if src is not None:
            src_path = Path(src)
            with open(src_path, "rb") as fh:
                d["_image_data"] = fh.read()
            d["_content_type"] = content_type or _guess_content_type(src_path)
        else:
            d["_image_data"] = data
            d["_content_type"] = content_type or "image/png"

        if width:
            d["width"] = width
        if height:
            d["height"] = height
        if alt_text:
            d["alt_text"] = alt_text

        self._data = d

    _EMU_PER_INCH = 914400

    @override
    def _build_native(
        self,
        parent_handle: int,
        lib: Handle,
        data: dict[str, Any],
        document: Document,
    ) -> int:
        image_data: bytes = data.get("_image_data") or b""
        content_type: str = data.get("_content_type") or "image/png"
        width_emu = int(float(data.get("width", 0.0)) * self._EMU_PER_INCH)
        height_emu = int(float(data.get("height", 0.0)) * self._EMU_PER_INCH)
        child_handle = lib.add_image(parent_handle, image_data, content_type, width_emu, height_emu)
        alt_text: str = data.get("alt_text", "")
        if alt_text:
            lib.set_str(child_handle, "alt_text", alt_text)
        return child_handle

    @override
    def _copy_data(self) -> dict[str, Any]:
        if not self.is_live:
            return dict(self._data)
        lib = self._get_lib()
        native = self._require_native
        return {
            "_image_data": lib.get_image_data(native),
            "_content_type": lib.get_str(native, "content_type") or "image/png",
            "width": lib.get_float(native, "width"),
            "height": lib.get_float(native, "height"),
            "alt_text": lib.get_str(native, "alt_text"),
        }

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Image(<stale>)"
        native = self._native
        if native is None:
            ct = self._data.get("_content_type", "")
            w = self._data.get("width", 0.0)
            h = self._data.get("height", 0.0)
            return f"Image(content_type={ct!r}, width={w}, height={h})"
        try:
            return f"Image(width={self.width}, height={self.height}, handle={native!r})"
        except Exception:
            return f"Image(handle={native!r})"
