"""Hyperlink proxy — an inline hyperlink element within a paragraph.

In OpenXML a hyperlink is stored as ``<w:hyperlink>`` containing one or more
``<w:r>`` runs, making it a direct child of ``<w:p>`` (sibling of runs).
"""

from __future__ import annotations

from typing import Any, override

from navyfox._proxy.base import ElementState, Element
from navyfox._proxy.descriptors import StringProperty

__all__ = ["Hyperlink"]


class Hyperlink(Element):
    """An inline hyperlink element within a paragraph.

    **Live proxy** (the only supported path — hyperlinks require a live paragraph):

    .. code-block:: python

        para = doc.add_paragraph("Visit ")
        link = para.add_hyperlink("our website", "https://example.com")
        link.url = "https://example.com/updated"

    Properties:
        text: Display text of the hyperlink.
        url:  Target URL.
    """

    __slots__ = ()
    _child_type_name = "hyperlink"

    text = StringProperty("text", default="")
    url = StringProperty("url", default="")

    def __init__(self, text: str = "", url: str = "") -> None:
        super().__init__()
        d: dict[str, Any] = {}
        if text:
            d["text"] = text
        if url:
            d["url"] = url
        self._data = d

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    @override
    def _copy_data(self) -> dict[str, Any]:
        if not self._is_live:
            return dict(self._data)
        lib = self._get_lib()
        native = self._require_native
        return {
            "text": lib.get_str(native, "text"),
            "url": lib.get_str(native, "url"),
        }

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------

    @override
    def __repr__(self) -> str:
        if self.state is ElementState.STALE:
            return "Hyperlink(<stale>)"
        native = self._native
        if native is None:
            return f"Hyperlink(text={self._data.get('text', '')!r}, url={self._data.get('url', '')!r})"
        try:
            return f"Hyperlink(text={self.text!r}, url={self.url!r}, handle={native!r})"
        except Exception:
            return f"Hyperlink(handle={native!r})"

    def __str__(self) -> str:
        return self.text

    def __bool__(self) -> bool:
        return bool(self.text) or bool(self.url)
