"""Regression tests for the P0–P3 refactor.

Each test targets a specific bug or behavioral guarantee introduced or fixed
during the June 2026 refactor. Test names are intentionally verbose so a
failure message tells you exactly what regressed.
"""
from __future__ import annotations

import warnings
from unittest.mock import patch

import pytest

from tests.unit.mock_handle import MockHandle


def _make_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    with patch("navyfox._native.handle.get_handle", return_value=mock):
        from navyfox.document import Document
        doc = Document()
    return doc, mock


# ---------------------------------------------------------------------------
# P0 — pop(0) regression: should return first element, not last
# ---------------------------------------------------------------------------

class TestPopIndexBug:
    def test_pop_zero_returns_first_element(self):
        """pop(0) must return the first element — not the last (falsy-index bug)."""
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("first"))
        doc.paragraphs.append(Paragraph("second"))
        doc.paragraphs.append(Paragraph("third"))
        popped = doc.paragraphs.pop(0)
        assert popped.text == "first", (
            "pop(0) returned last element — the '0 or -1' falsy-index bug is back"
        )

    def test_pop_zero_leaves_remaining_in_correct_order(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        for label in ["A", "B", "C"]:
            doc.paragraphs.append(Paragraph(label))
        doc.paragraphs.pop(0)
        remaining = [p.text for p in doc.paragraphs]
        assert remaining == ["B", "C"]

    def test_pop_no_arg_returns_last_element(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("first"))
        doc.paragraphs.append(Paragraph("last"))
        popped = doc.paragraphs.pop()
        assert popped.text == "last"

    def test_pop_no_arg_leaves_preceding_elements(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        for label in ["A", "B", "C"]:
            doc.paragraphs.append(Paragraph(label))
        doc.paragraphs.pop()
        assert len(doc.paragraphs) == 2
        assert doc.paragraphs[0].text == "A"
        assert doc.paragraphs[1].text == "B"

    def test_pop_middle_index(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        for label in ["X", "Y", "Z"]:
            doc.paragraphs.append(Paragraph(label))
        popped = doc.paragraphs.pop(1)
        assert popped.text == "Y"
        assert len(doc.paragraphs) == 2

    def test_pop_negative_index(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        for label in ["A", "B", "C"]:
            doc.paragraphs.append(Paragraph(label))
        popped = doc.paragraphs.pop(-2)
        assert popped.text == "B"

    def test_pop_returns_snapshot_not_live_proxy(self):
        """pop() returns a frozen snapshot, not a live proxy."""
        from navyfox._proxy.base import ElementState
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("gone"))
        snap = doc.paragraphs.pop(0)
        assert snap.state is ElementState.SNAPSHOT
        assert snap.text == "gone"


# ---------------------------------------------------------------------------
# P0 — Color storage consistency
# ---------------------------------------------------------------------------

class TestColorStorageConsistency:
    def test_construction_state_color_returns_hash_prefix(self):
        """Run(color='#FF0000').color must return '#FF0000', not bare 'FF0000'."""
        from navyfox.run import Run
        run = Run("x", color="#FF0000")
        assert run.color == "#FF0000", (
            f"Construction-state color returned {run.color!r} — missing '#' prefix"
        )

    def test_construction_color_auto_returns_auto(self):
        from navyfox.run import Run
        run = Run("x", color="auto")
        assert run.color == "auto"

    def test_construction_color_none_when_unset(self):
        from navyfox.run import Run
        run = Run("x")
        assert run.color is None

    def test_construction_state_color_object_returns_hash_prefix(self):
        from navyfox.run import Run
        from navyfox.units import Color
        run = Run("x", color=Color(0, 128, 255))
        assert run.color is not None
        assert run.color.startswith("#"), f"Expected '#RRGGBB', got {run.color!r}"
        assert run.color.upper() == "#0080FF"

    def test_live_color_matches_construction_format(self):
        """Reading color from live proxy must use same '#RRGGBB' format as construction."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run("x", color="#CC0000"))
        run = para.runs[0]
        # The live path returns '#CC0000' (ColorProperty.__get__ adds '#')
        assert run.color is not None
        assert run.color.startswith("#"), f"Live color missing '#': {run.color!r}"

    def test_color_assignment_and_read_roundtrip_live(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run("x"))
        run = para.runs[0]
        run.color = "#AABBCC"
        color = run.color
        assert color is not None
        assert color.upper() == "#AABBCC"

    def test_construction_and_live_color_produce_same_format(self):
        """Construction-state and live reads must return the same '#RRGGBB' format."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        # Construction
        spec = Run("x", color="#123456")
        construction_color = spec.color

        # Append to doc → becomes live
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        doc.paragraphs[0].runs.append(spec)
        live_color = spec.color

        # Both should start with '#'
        assert construction_color is not None and construction_color.startswith("#"), (
            f"Construction color: {construction_color!r}"
        )
        assert live_color is not None and live_color.startswith("#"), (
            f"Live color: {live_color!r}"
        )


# ---------------------------------------------------------------------------
# P2 — _EditProxy supports Color values
# ---------------------------------------------------------------------------

class TestEditProxyColorSupport:
    def test_edit_block_with_color_object_does_not_raise(self):
        """with run.edit() as r: r.color = Color(...) must not raise TypeError."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        from navyfox.units import Color
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run("x"))
        run = para.runs[0]
        with run.edit() as r:
            r.color = Color(255, 0, 0)  # must not raise

    def test_edit_block_with_color_updates_value(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        from navyfox.units import Color
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run("x"))
        run = para.runs[0]
        with run.edit() as r:
            r.bold = True
            r.color = Color(0, 255, 0)
        assert run.bold is True

    def test_edit_block_with_string_color_works(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run("x"))
        run = para.runs[0]
        with run.edit() as r:
            r.color = "#FF0000"
        assert run.color is not None


# ---------------------------------------------------------------------------
# P0 — Table.data in construction state
# ---------------------------------------------------------------------------

class TestTableDataConstructionState:
    def test_data_yields_exactly_one_empty_list_in_construction(self):
        """Table.data in construction state must yield exactly one empty list and stop."""
        from navyfox.table import Table
        tbl = Table(rows=2, cols=3)
        result = list(tbl.data)
        assert result == [[]], (
            f"Expected [[]]; got {result!r} — missing 'return' after 'yield []'"
        )

    def test_data_does_not_fall_through_to_live_loop(self):
        from navyfox.table import Table
        tbl = Table(rows=5, cols=5)
        result = list(tbl.data)
        assert len(result) == 1  # only the sentinel empty list, not 5 rows

    def test_data_generator_is_exhausted_after_first_iteration(self):
        from navyfox.table import Table
        tbl = Table(rows=2, cols=2)
        gen = tbl.data
        first = next(gen)
        assert first == []
        with pytest.raises(StopIteration):
            next(gen)


# ---------------------------------------------------------------------------
# P1 — Row.is_header and Row.cant_split are bool, not str
# ---------------------------------------------------------------------------

class TestRowBoolProperties:
    def _make_table(self):
        from navyfox.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=2, cols=2))
        return doc.tables[0], mock

    def test_is_header_default_is_false_bool(self):
        """row.is_header must return False (bool), not '' (str)."""
        table, _ = self._make_table()
        row = table.rows[0]
        assert row.is_header is False, (
            f"is_header returned {row.is_header!r} — StringProperty regression"
        )
        assert isinstance(row.is_header, bool), (
            f"is_header type is {type(row.is_header).__name__}, expected bool"
        )

    def test_cant_split_default_is_false_bool(self):
        """row.cant_split must return False (bool), not '' (str)."""
        table, _ = self._make_table()
        row = table.rows[0]
        assert row.cant_split is False, (
            f"cant_split returned {row.cant_split!r} — StringProperty regression"
        )
        assert isinstance(row.cant_split, bool), (
            f"cant_split type is {type(row.cant_split).__name__}, expected bool"
        )

    def test_is_header_roundtrip_true(self):
        table, _ = self._make_table()
        row = table.rows[0]
        row.is_header = True
        assert row.is_header is True

    def test_cant_split_roundtrip_true(self):
        table, _ = self._make_table()
        row = table.rows[0]
        row.cant_split = True
        assert row.cant_split is True

    def test_is_header_truthiness_false_by_default(self):
        """is_header must be falsy when unset — '' (str) would also be falsy, but this guards the type."""
        table, _ = self._make_table()
        row = table.rows[0]
        if row.is_header:
            pytest.fail("is_header should be falsy by default")

    def test_cant_split_truthiness_false_by_default(self):
        table, _ = self._make_table()
        row = table.rows[0]
        if row.cant_split:
            pytest.fail("cant_split should be falsy by default")


# ---------------------------------------------------------------------------
# P1 — PageMargins hashability and uniform() factory
# ---------------------------------------------------------------------------

class TestPageMarginsHashAndFactory:
    def test_page_margins_is_hashable(self):
        """PageMargins must be hashable — it defines __eq__ so __hash__ must be explicit."""
        from navyfox.formats import PageMargins
        pm = PageMargins()
        h = hash(pm)  # must not raise
        assert isinstance(h, int)

    def test_equal_page_margins_have_same_hash(self):
        from navyfox.formats import PageMargins
        a = PageMargins(top=1.0, bottom=1.0, left=1.25, right=1.25)
        b = PageMargins(top=1.0, bottom=1.0, left=1.25, right=1.25)
        assert a == b
        assert hash(a) == hash(b)

    def test_page_margins_usable_as_dict_key(self):
        from navyfox.formats import PageMargins
        d: dict[object, str] = {}
        pm = PageMargins()
        d[pm] = "ok"
        assert d[pm] == "ok"

    def test_page_margins_usable_in_set(self):
        from navyfox.formats import PageMargins
        s = {PageMargins(), PageMargins()}
        assert len(s) == 1  # equal objects deduplicate

    def test_uniform_factory_sets_all_sides(self):
        from navyfox.formats import PageMargins
        pm = PageMargins.uniform(0.5)
        assert pm.top == 0.5
        assert pm.bottom == 0.5
        assert pm.left == 0.5
        assert pm.right == 0.5

    def test_uniform_factory_preserves_header_footer_defaults(self):
        from navyfox.formats import PageMargins
        pm = PageMargins.uniform(1.0)
        # header and footer should use their defaults, not 1.0
        assert pm.header == 0.5
        assert pm.footer == 0.5

    def test_uniform_factory_custom_header_footer(self):
        from navyfox.formats import PageMargins
        pm = PageMargins.uniform(1.0, header=0.25, footer=0.25)
        assert pm.header == 0.25
        assert pm.footer == 0.25

    def test_uniform_factory_returns_page_margins_instance(self):
        from navyfox.formats import PageMargins
        pm = PageMargins.uniform(0.75)
        assert isinstance(pm, PageMargins)


# ---------------------------------------------------------------------------
# P2 — _ConstructionRunsView: pop, clear, index
# ---------------------------------------------------------------------------

class TestConstructionRunsViewMethods:
    def test_pop_no_arg_returns_last_run(self):
        """_ConstructionRunsView.pop() must return the last run."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        r1 = Run("first")
        r2 = Run("last")
        para.runs.append(r1)
        para.runs.append(r2)
        popped = para.runs.pop()
        assert popped is r2
        assert len(para.runs) == 1

    def test_pop_zero_returns_first_run(self):
        """_ConstructionRunsView.pop(0) must return the first run."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        r1 = Run("first")
        r2 = Run("second")
        r3 = Run("third")
        para.runs.append(r1)
        para.runs.append(r2)
        para.runs.append(r3)
        popped = para.runs.pop(0)
        assert popped is r1
        remaining_texts = [r.text for r in para.runs]
        assert remaining_texts == ["second", "third"]

    def test_pop_removes_run_from_list(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("a"))
        para.runs.append(Run("b"))
        para.runs.pop()
        assert len(para.runs) == 1
        assert para.runs[0].text == "a"

    def test_clear_empties_runs(self):
        """_ConstructionRunsView.clear() must remove all runs."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("a"))
        para.runs.append(Run("b"))
        para.runs.append(Run("c"))
        para.runs.clear()
        assert len(para.runs) == 0

    def test_clear_on_empty_runs_is_safe(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        para.runs.clear()  # must not raise
        assert len(para.runs) == 0

    def test_index_returns_correct_position(self):
        """_ConstructionRunsView.index() must return the zero-based position."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        r1 = Run("a")
        r2 = Run("b")
        r3 = Run("c")
        para.runs.append(r1)
        para.runs.append(r2)
        para.runs.append(r3)
        assert para.runs.index(r1) == 0
        assert para.runs.index(r2) == 1
        assert para.runs.index(r3) == 2

    def test_index_raises_for_absent_run(self):
        """_ConstructionRunsView.index() must raise ValueError for a run not in this paragraph."""
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("a"))
        other = Run("other")
        with pytest.raises(ValueError):
            para.runs.index(other)

    def test_pop_then_text_updates(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("hello "))
        para.runs.append(Run("world"))
        para.runs.pop(0)
        assert para.text == "world"


# ---------------------------------------------------------------------------
# P1 — insert() warning fires BEFORE mutation
# ---------------------------------------------------------------------------

class TestInsertWarningOrder:
    def test_insert_at_end_emits_no_warning(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            doc.paragraphs.insert(1, Paragraph("B"))  # index == len, no warning

    def test_insert_at_non_end_emits_future_warning(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        with pytest.warns(FutureWarning, match="insert()"):
            doc.paragraphs.insert(0, Paragraph("B"))

    def test_insert_warning_fires_before_append(self):
        """Warning must be emitted before _append_one executes — fire-before-mutate."""
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        # Use a single stable view reference — doc.paragraphs creates a new object each call
        view = doc.paragraphs
        view.append(Paragraph("A"))
        events: list[str] = []

        real_warn = warnings.warn

        def tracking_warn(*args, **kwargs):
            events.append("warn")
            real_warn(*args, **kwargs)

        real_append = view._append_one

        def tracking_append(elem):
            events.append("append")
            return real_append(elem)

        with (
            patch("warnings.warn", side_effect=tracking_warn),
            patch.object(view, "_append_one", side_effect=tracking_append),
        ):
            view.insert(0, Paragraph("B"))

        assert events == ["warn", "append"], (
            f"Expected ['warn', 'append']; got {events!r} — warning fired after mutation"
        )

    def test_insert_still_appends_element(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            doc.paragraphs.insert(0, Paragraph("X"))
        assert len(doc.paragraphs) == 1

    def test_insert_warning_message_contains_index(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        with pytest.warns(FutureWarning, match="0"):
            doc.paragraphs.insert(0, Paragraph("B"))


# ---------------------------------------------------------------------------
# P1 — Unit type exports from navyfox top-level
# ---------------------------------------------------------------------------

class TestUnitTypeExports:
    def test_inches_importable_from_navyfox(self):
        from navyfox import Inches
        assert Inches is not None

    def test_centimeters_importable_from_navyfox(self):
        from navyfox import Centimeters
        assert Centimeters is not None

    def test_millimeters_importable_from_navyfox(self):
        from navyfox import Millimeters
        assert Millimeters is not None

    def test_twips_importable_from_navyfox(self):
        from navyfox import Twips
        assert Twips is not None

    def test_points_importable_from_navyfox(self):
        from navyfox import Points
        assert Points is not None

    def test_length_importable_from_navyfox(self):
        from navyfox import Length
        assert Length is not None

    def test_unit_types_have_correct_point_values(self):
        from navyfox import Centimeters, Inches, Millimeters, Points, Twips
        # 1 inch = 72 points
        assert abs(Inches(1.0).points - 72.0) < 1e-9
        # 2.54 cm ≈ 1 inch = 72 points
        assert abs(Centimeters(2.54).points - 72.0) < 1e-4
        # 25.4 mm ≈ 1 inch = 72 points
        assert abs(Millimeters(25.4).points - 72.0) < 1e-4
        # 72 pt = 72 points
        assert abs(Points(72.0).points - 72.0) < 1e-9
        # 1440 twips = 1 inch = 72 points
        assert abs(Twips(1440).points - 72.0) < 1e-6

    def test_unit_types_store_raw_value(self):
        from navyfox import Centimeters, Inches, Millimeters, Points, Twips
        assert Inches(1.5).value == 1.5
        assert Centimeters(3.0).value == 3.0
        assert Millimeters(10.0).value == 10.0
        assert Points(12.0).value == 12.0
        assert Twips(720).value == 720


# ---------------------------------------------------------------------------
# P3 — StyleCollection name→id cache
# ---------------------------------------------------------------------------

class TestStyleCollectionCache:
    def _make_doc_with_styles(self):
        mock = MockHandle()
        with patch("navyfox._native.handle.get_handle", return_value=mock):
            from navyfox.document import Document
            doc = Document()

        # Manually inject a style into the mock
        style_h = mock._alloc("style")
        mock._handles[style_h]["style_id"] = "Heading1"
        mock._handles[style_h]["style_name"] = "Heading 1"  # Style.name reads "style_name"
        mock._handles[style_h]["style_type"] = "paragraph"  # Style.type reads "style_type"
        mock._children.setdefault(doc._handle, []).append(style_h)
        mock._parent[style_h] = doc._handle
        return doc, mock

    def test_id_for_resolves_by_style_id(self):
        """_id_for(style_id) must return the style_id directly (fast path)."""
        doc, mock = self._make_doc_with_styles()
        sc = doc.styles
        result = sc._id_for("Heading1")
        assert result == "Heading1"

    def test_id_for_resolves_by_display_name(self):
        """_id_for(display_name) must return the style_id via the name→id cache."""
        doc, mock = self._make_doc_with_styles()
        sc = doc.styles
        result = sc._id_for("Heading 1")
        assert result == "Heading1"

    def test_id_for_returns_none_for_unknown(self):
        """_id_for(unknown) must return None when neither ID nor display name matches."""
        doc, mock = self._make_doc_with_styles()
        sc = doc.styles
        assert sc._id_for("NonExistentStyle") is None

    def test_cache_is_none_before_first_access(self):
        """_name_to_id cache starts as None — populated lazily."""
        doc, mock = self._make_doc_with_styles()
        sc = doc.styles
        assert sc._name_to_id is None

    def test_cache_is_populated_after_name_lookup(self):
        """Accessing _id_for by display name must warm the cache."""
        doc, mock = self._make_doc_with_styles()
        sc = doc.styles
        sc._id_for("Heading 1")
        assert sc._name_to_id is not None
        assert "Heading 1" in sc._name_to_id

    def test_cache_is_invalidated_after_invalidate_call(self):
        """_invalidate_cache() must reset _name_to_id to None."""
        doc, mock = self._make_doc_with_styles()
        sc = doc.styles
        sc._get_name_to_id()  # explicitly warm the cache
        assert sc._name_to_id is not None
        sc._invalidate_cache()
        assert sc._name_to_id is None

    def test_cache_repopulates_after_invalidation(self):
        """After invalidation, a second lookup must rebuild the cache with new styles."""
        doc, mock = self._make_doc_with_styles()
        sc = doc.styles
        sc._get_name_to_id()  # warm cache

        # Inject a second style directly into the mock
        style_h2 = mock._alloc("style")
        mock._handles[style_h2]["style_id"] = "CustomStyle"
        mock._handles[style_h2]["style_name"] = "My Custom Style"
        mock._handles[style_h2]["style_type"] = "paragraph"
        mock._children[doc._handle].append(style_h2)
        mock._parent[style_h2] = doc._handle
        sc._invalidate_cache()

        result = sc._id_for("My Custom Style")
        assert result == "CustomStyle"
