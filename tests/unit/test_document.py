"""Unit tests for the navyfox proxy model, DocumentView, and Document.

The native binary is mocked at the Handle level — no compiled C# needed.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.unit.mock_handle import MockHandle

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_doc(mock: MockHandle | None = None):
    if mock is None:
        mock = MockHandle()
    with patch("navyfox._native.handle.get_handle", return_value=mock):
        from navyfox.document import Document
        doc = Document()
    return doc, mock


# ---------------------------------------------------------------------------
# Document construction
# ---------------------------------------------------------------------------

class TestDocumentConstruction:
    def test_creates_handle_on_init(self):
        mock = MockHandle()
        doc, _ = _make_doc(mock)
        assert doc._handle in mock._handles

    def test_is_open_after_creation(self):
        doc, _ = _make_doc()
        assert doc.is_open

    def test_close_marks_not_open(self):
        doc, _ = _make_doc()
        doc.close()
        assert not doc.is_open

    def test_double_close_is_safe(self):
        doc, mock = _make_doc()
        doc.close()
        doc.close()  # should not raise

    def test_context_manager_closes_on_exit(self):
        mock = MockHandle()
        with patch("navyfox._native.handle.get_handle", return_value=mock):
            from navyfox.document import Document
            with Document() as doc:
                pass
        assert doc.is_open is False

    def test_require_open_raises_after_close(self):
        from navyfox.errors import DocumentClosedError
        doc, _ = _make_doc()
        doc.close()
        with pytest.raises(DocumentClosedError):
            doc._require_open()

    def test_document_open_classmethod(self):
        mock = MockHandle()
        mock.open_document = lambda path: mock.create_document()
        with patch("navyfox._native.handle.get_handle", return_value=mock):
            from navyfox.document import Document
            doc = Document.open("test.docx")
        assert doc.is_open


# ---------------------------------------------------------------------------
# Document as collection
# ---------------------------------------------------------------------------

class TestDocumentAsCollection:
    def test_len_is_zero_initially(self):
        doc, _ = _make_doc()
        assert len(doc) == 0

    def test_append_paragraph(self):
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("Hello"))
        assert len(doc) == 1

    def test_append_sets_text(self):
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("Hello"))
        para = doc.paragraphs[0]
        assert para.text == "Hello"

    def test_iter_yields_paragraphs(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("First"))
        doc.paragraphs.append(Paragraph("Second"))
        texts = [str(p) for p in doc.paragraphs]
        assert texts == ["First", "Second"]

    def test_paragraphs_first_last(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("First"))
        doc.paragraphs.append(Paragraph("Last"))
        assert doc.paragraphs.first.text == "First"
        assert doc.paragraphs.last.text == "Last"

    def test_paragraphs_first_is_none_when_empty(self):
        doc, _ = _make_doc()
        assert doc.paragraphs.first is None

    def test_remove_marks_proxy_stale(self):
        from navyfox.errors import StaleProxyError
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("Temp"))
        para = doc.paragraphs[0]
        doc.paragraphs.remove(para)
        with pytest.raises(StaleProxyError, match=r"copy\(\)"):
            _ = para.text

    def test_pop_removes_and_returns(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        popped = doc.paragraphs.pop()
        assert popped.text == "B"
        assert len(doc.paragraphs) == 1

    def test_append_table(self):
        from navyfox.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=2, cols=3))
        assert len(doc.tables) == 1

    def test_type_error_on_wrong_type_in_filtered_view(self):
        from navyfox.table import Table
        doc, _ = _make_doc()
        with pytest.raises(TypeError, match="DocumentView"):
            doc.paragraphs.append(Table(rows=1, cols=1))  # type: ignore

    def test_getitem_by_type_returns_filtered_view(self):
        from navyfox import DocumentView
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        view = doc[Paragraph]
        assert isinstance(view, DocumentView)

    def test_group_two_types(self):
        from navyfox import DocumentView
        from navyfox.paragraph import Paragraph
        from navyfox.table import Table
        doc, _ = _make_doc()
        view = doc.group([Paragraph, Table])
        assert isinstance(view, DocumentView)


# ---------------------------------------------------------------------------
# Paragraph proxy
# ---------------------------------------------------------------------------

class TestParagraphProxy:
    def test_text_roundtrip_live(self):
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("hello"))
        para = doc.paragraphs[0]
        assert para.text == "hello"
        para.text = "world"
        assert para.text == "world"

    def test_style_roundtrip_live(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("hi", style="Heading1"))
        para = doc.paragraphs[0]
        assert para.style == "Heading1"
        para.style = "Normal"
        assert para.style == "Normal"

    def test_alignment_roundtrip_live(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("hi", alignment="center"))
        para = doc.paragraphs[0]
        assert para.alignment == "center"
        para.alignment = "right"
        assert para.alignment == "right"

    def test_alignment_rejects_invalid(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("hi"))
        para = doc.paragraphs[0]
        with pytest.raises(ValueError, match="alignment"):
            para.alignment = "diagonal"  # type: ignore

    def test_spec_reads_from_data(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph("spec text", style="Heading2")
        assert para.text == "spec text"
        assert para.style == "Heading2"
        assert not para._is_live

    def test_copy_returns_snapshot(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("snapshot me"))
        para = doc.paragraphs[0]
        snap = para.copy()
        assert isinstance(snap, Paragraph)
        assert not snap._is_live
        assert snap.text == "snapshot me"

    def test_document_closed_raises_on_access(self):
        from navyfox.errors import DocumentClosedError
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("bye"))
        para = doc.paragraphs[0]
        doc.close()
        with pytest.raises(DocumentClosedError, match=r"copy\(\)"):
            _ = para.text

    def test_stale_proxy_raises_on_access(self):
        from navyfox.errors import StaleProxyError
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("gone"))
        para = doc.paragraphs[0]
        doc.paragraphs.remove(para)
        with pytest.raises(StaleProxyError, match=r"copy\(\)"):
            _ = para.text

    def test_unknown_attribute_raises(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        para = doc.paragraphs[0]
        with pytest.raises(AttributeError):
            _ = para.no_such_attr


# ---------------------------------------------------------------------------
# Paragraph spacing
# ---------------------------------------------------------------------------

class TestParagraphSpacing:
    def test_defaults_in_construction(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        assert para.space_before == 0.0
        assert para.space_after == 0.0
        assert para.line_spacing == 1.0

    def test_constructor_kwargs(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph("x", space_before=6.0, space_after=3.0, line_spacing=1.5)
        assert para.space_before == 6.0
        assert para.space_after == 3.0
        assert para.line_spacing == 1.5

    def test_construction_writable(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        para.space_before = 12.0
        para.space_after = 6.0
        para.line_spacing = 2.0
        assert para.space_before == 12.0
        assert para.space_after == 6.0
        assert para.line_spacing == 2.0

    def test_round_trip_through_document(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("x", space_before=6.0, space_after=3.0, line_spacing=1.5)
        doc.paragraphs.append(para)
        assert abs(para.space_before - 6.0) < 1e-9
        assert abs(para.space_after - 3.0) < 1e-9
        assert abs(para.line_spacing - 1.5) < 1e-9

    def test_live_setters(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.space_before = 8.0
        para.space_after = 4.0
        para.line_spacing = 1.15
        assert abs(para.space_before - 8.0) < 1e-9
        assert abs(para.space_after - 4.0) < 1e-9
        assert abs(para.line_spacing - 1.15) < 1e-9

    def test_spacing_preserved_in_snapshot(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("y", space_before=6.0, space_after=3.0))
        snap = doc.paragraphs[0].copy()
        assert abs(snap.space_before - 6.0) < 1e-9
        assert abs(snap.space_after - 3.0) < 1e-9

    def test_spacing_in_copy_data_live(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("z", line_spacing=1.5))
        data = doc.paragraphs[0]._copy_data()
        assert abs(data["space_before"] - 0.0) < 1e-9
        assert abs(data["line_spacing"] - 1.5) < 1e-9


# ---------------------------------------------------------------------------
# Paragraph indentation
# ---------------------------------------------------------------------------

class TestParagraphIndentation:
    def test_defaults_in_construction(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        assert para.indent_left == 0.0
        assert para.indent_right == 0.0
        assert para.indent_hanging == 0.0

    def test_constructor_kwargs(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph("x", indent_left=0.5, indent_right=0.25, indent_hanging=0.25)
        assert para.indent_left == 0.5
        assert para.indent_right == 0.25
        assert para.indent_hanging == 0.25

    def test_construction_writable(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        para.indent_left = 1.0
        para.indent_right = 0.5
        para.indent_hanging = 0.5
        assert para.indent_left == 1.0
        assert para.indent_right == 0.5
        assert para.indent_hanging == 0.5

    def test_round_trip_through_document(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("x", indent_left=0.5, indent_right=0.25, indent_hanging=0.25)
        doc.paragraphs.append(para)
        assert abs(para.indent_left - 0.5) < 1e-9
        assert abs(para.indent_right - 0.25) < 1e-9
        assert abs(para.indent_hanging - 0.25) < 1e-9

    def test_live_setters(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.indent_left = 0.75
        para.indent_right = 0.5
        para.indent_hanging = 0.25
        assert abs(para.indent_left - 0.75) < 1e-9
        assert abs(para.indent_right - 0.5) < 1e-9
        assert abs(para.indent_hanging - 0.25) < 1e-9

    def test_indentation_preserved_in_snapshot(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("y", indent_left=0.5, indent_hanging=0.25))
        snap = doc.paragraphs[0].copy()
        assert abs(snap.indent_left - 0.5) < 1e-9
        assert abs(snap.indent_hanging - 0.25) < 1e-9

    def test_indentation_in_copy_data_live(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("z", indent_left=1.0))
        data = doc.paragraphs[0]._copy_data()
        assert abs(data["indent_left"] - 1.0) < 1e-9
        assert abs(data["indent_right"] - 0.0) < 1e-9
        assert abs(data["indent_hanging"] - 0.0) < 1e-9


# ---------------------------------------------------------------------------
# Construction-state runs — text derived from runs, mutable before append
# ---------------------------------------------------------------------------

class TestConstructionRuns:
    def test_text_derives_from_runs_in_construction(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph("hello")
        assert para.text == "hello"

    def test_empty_para_has_empty_text(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        assert para.text == ""

    def test_runs_not_empty_when_text_given(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph("hello")
        assert len(para.runs) == 1
        assert para.runs[0].text == "hello"

    def test_runs_empty_when_no_text(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        assert len(para.runs) == 0

    def test_append_run_in_construction(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("world", bold=True))
        assert len(para.runs) == 1
        assert para.runs[0].text == "world"
        assert para.runs[0].bold is True

    def test_text_concatenates_multiple_construction_runs(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("Hello "))
        para.runs.append(Run("world"))
        assert para.text == "Hello world"

    def test_add_run_works_in_construction(self):
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        run = para.add_run("hello")
        assert len(para.runs) == 1
        assert run.text == "hello"

    def test_text_setter_replaces_runs_in_construction(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("old"))
        para.text = "new"
        assert len(para.runs) == 1
        assert para.text == "new"

    def test_construction_runs_survive_round_trip_through_document(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        para = Paragraph()
        para.runs.append(Run("Hello ", bold=True))
        para.runs.append(Run("world"))
        doc.paragraphs.append(para)
        assert para.text == "Hello world"
        assert len(para.runs) == 2

    def test_construction_run_formatting_survives_materialisation(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        para = Paragraph()
        para.runs.append(Run("bold", bold=True))
        doc.paragraphs.append(para)
        assert para.runs[0].bold is True

    def test_construction_runs_reject_wrong_type(self):
        from navyfox.image import Image
        from navyfox.paragraph import Paragraph
        para = Paragraph()
        with pytest.raises(TypeError):
            para.runs.append(Image(data=b"\x89PNG\r\n\x1a\n" + b"\x00" * 56))  # type: ignore

    def test_stale_para_text_raises(self):
        from navyfox.errors import StaleProxyError
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("bye"))
        para = doc.paragraphs[0]
        doc.paragraphs.remove(para)
        with pytest.raises(StaleProxyError):
            _ = para.text

    def test_snapshot_preserves_construction_runs(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        para = Paragraph()
        para.runs.append(Run("A", bold=True))
        para.runs.append(Run("B"))
        snap = para.copy()
        assert snap.text == "AB"
        assert len(snap.runs) == 2

    def test_snapshot_can_be_appended_with_runs(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        para = Paragraph()
        para.runs.append(Run("snap", italic=True))
        snap = para.copy()
        doc.paragraphs.append(snap)
        assert snap.text == "snap"
        assert snap.runs[0].italic is True


# ---------------------------------------------------------------------------
# Run proxy
# ---------------------------------------------------------------------------

class TestRunProxy:
    def _para_with_run(self, text: str = "hello", **run_kwargs):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run(text, **run_kwargs))
        run = para.runs[0]
        return run, mock

    def test_text_roundtrip(self):
        run, _ = self._para_with_run("hello")
        assert run.text == "hello"
        run.text = "world"
        assert run.text == "world"

    def test_bold_roundtrip(self):
        run, _ = self._para_with_run(bold=True)
        assert run.bold is True
        run.bold = False
        assert run.bold is False

    def test_italic_roundtrip(self):
        run, _ = self._para_with_run(italic=True)
        assert run.italic is True

    def test_font_size_roundtrip(self):
        run, _ = self._para_with_run(font_size=12.0)
        assert run.font_size == 12.0

    def test_font_name_roundtrip(self):
        run, _ = self._para_with_run(font_name="Arial")
        assert run.font_name == "Arial"

    def test_color_roundtrip(self):
        from navyfox.run import Run
        doc, _ = _make_doc()
        from navyfox.paragraph import Paragraph
        doc.paragraphs.append(Paragraph())
        para = doc.paragraphs[0]
        para.runs.append(Run("x"))
        run = para.runs[0]
        run.color = "#FF0000"
        # mock stores bare hex (after # strip in ColorProperty)
        assert run.color in ("#FF0000", "FF0000")

    def test_mutex_all_caps_small_caps(self):
        from navyfox.run import Run
        with pytest.raises(ValueError, match="mutually exclusive"):
            Run("x", all_caps=True, small_caps=True)

    def test_mutex_superscript_subscript(self):
        from navyfox.run import Run
        with pytest.raises(ValueError, match="mutually exclusive"):
            Run("x", superscript=True, subscript=True)

    def test_copy_returns_snapshot(self):
        from navyfox.run import Run
        run, _ = self._para_with_run("copy me", bold=True)
        snap = run.copy()
        assert isinstance(snap, Run)
        assert not snap._is_live
        assert snap.text == "copy me"
        assert snap.bold is True

    def test_stale_run_raises(self):
        from navyfox._proxy.base import ElementState
        from navyfox.errors import StaleProxyError
        run, _ = self._para_with_run("temp")
        object.__setattr__(run, "_state", ElementState.STALE)
        with pytest.raises(StaleProxyError, match=r"copy\(\)"):
            _ = run.text

    def test_spec_run_has_correct_data(self):
        from navyfox.run import Run
        run = Run("spec", bold=True, italic=False)
        assert run.text == "spec"
        assert run.bold is True
        assert not run._is_live


# ---------------------------------------------------------------------------
# Table proxy
# ---------------------------------------------------------------------------

class TestTableProxy:
    def test_table_append_and_access(self):
        from navyfox.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=2, cols=3))
        assert len(doc.tables) == 1
        table = doc.tables[0]
        assert isinstance(table, Table)

    def test_table_rows_count(self):
        from navyfox.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=3, cols=2))
        table = doc.tables[0]
        assert len(table.rows) == 3

    def test_table_cell_access(self):
        from navyfox.table import Table
        doc, mock = _make_doc()
        doc.tables.append(Table(rows=2, cols=2))
        table = doc.tables[0]
        cell = table.cell(0, 0)
        cell.text = "R0C0"
        assert table.cell(0, 0).text == "R0C0"

    def test_table_getitem_tuple(self):
        from navyfox.table import Table
        doc, _ = _make_doc()
        doc.tables.append(Table(rows=2, cols=2))
        table = doc.tables[0]
        table[1, 0].text = "R1C0"
        assert table[1, 0].text == "R1C0"


# ---------------------------------------------------------------------------
# DocumentView
# ---------------------------------------------------------------------------

class TestDocumentView:
    def test_slice_returns_view(self):
        from navyfox import DocumentView
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        for i in range(4):
            doc.paragraphs.append(Paragraph(f"Para {i}"))
        sliced = doc.paragraphs[1:3]
        assert isinstance(sliced, DocumentView)
        assert len(sliced) == 2

    def test_bool_false_when_empty(self):
        doc, _ = _make_doc()
        assert not doc.paragraphs

    def test_bool_true_when_not_empty(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        assert doc.paragraphs

    def test_iadd_extends(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs += [Paragraph("A"), Paragraph("B")]
        assert len(doc.paragraphs) == 2

    def test_contains_true_for_live_element(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        para = doc.paragraphs[0]
        assert para in doc.paragraphs

    def test_contains_false_for_spec(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        assert Paragraph("x") not in doc.paragraphs

    def test_reversed_order(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        texts = [p.text for p in reversed(doc.paragraphs)]
        assert texts == ["B", "A"]


# ---------------------------------------------------------------------------
# Document.save
# ---------------------------------------------------------------------------

class TestDocumentSave:
    def test_save_stores_path(self):
        doc, mock = _make_doc()
        doc.save("/tmp/out.docx")
        assert doc.path == "/tmp/out.docx"

    def test_save_without_path_raises(self):
        doc, _ = _make_doc()
        with pytest.raises(ValueError, match="path"):
            doc.save()

    def test_save_after_close_raises(self):
        from navyfox.errors import DocumentClosedError
        doc, _ = _make_doc()
        doc.close()
        with pytest.raises(DocumentClosedError):
            doc.save("/tmp/out.docx")


# ---------------------------------------------------------------------------
# Proxy lifecycle — CONSTRUCTION → LIVE transition (_attach)
# ---------------------------------------------------------------------------

class TestProxyLifecycle:
    def test_proxy_is_construction_before_append(self):
        from navyfox._proxy.base import ElementState
        from navyfox.paragraph import Paragraph
        para = Paragraph("hello")
        assert para.state is ElementState.CONSTRUCTION

    def test_proxy_is_live_after_append(self):
        from navyfox._proxy.base import ElementState
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("hello")
        doc.paragraphs.append(para)
        assert para.state is ElementState.LIVE

    def test_append_returns_same_object(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("hello")
        returned = doc.paragraphs._append_one(para)
        assert returned is para

    def test_post_append_mutation_reflects_in_document(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("original")
        doc.paragraphs.append(para)
        para.text = "mutated"
        assert doc.paragraphs[0].text == "mutated"

    def test_double_append_raises(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("hello")
        doc.paragraphs.append(para)
        with pytest.raises(ValueError, match="already in a document"):
            doc.paragraphs.append(para)

    def test_append_live_proxy_to_different_doc_raises_ownership_error(self):
        from navyfox.errors import OwnershipError
        from navyfox.paragraph import Paragraph
        doc1, _ = _make_doc()
        doc2, _ = _make_doc()
        para = Paragraph("hello")
        doc1.paragraphs.append(para)
        with pytest.raises(OwnershipError):
            doc2.paragraphs.append(para)

    def test_extend_transitions_all_to_live(self):
        from navyfox._proxy.base import ElementState
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        p1, p2 = Paragraph("A"), Paragraph("B")
        doc.paragraphs.extend([p1, p2])
        assert p1.state is ElementState.LIVE
        assert p2.state is ElementState.LIVE

    def test_iadd_transitions_all_to_live(self):
        from navyfox._proxy.base import ElementState
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        p1, p2 = Paragraph("A"), Paragraph("B")
        doc.paragraphs += [p1, p2]
        assert p1.state is ElementState.LIVE
        assert p2.state is ElementState.LIVE

    def test_snapshot_can_be_appended_and_becomes_live(self):
        from navyfox._proxy.base import ElementState
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("original"))
        snap = doc.paragraphs[0].copy()
        assert snap.state is ElementState.SNAPSHOT
        doc2, _ = _make_doc()
        doc2.paragraphs.append(snap)
        assert snap.state is ElementState.LIVE

    def test_copy_of_spec_appended_independently(self):
        """copy() creates a fresh CONSTRUCTION proxy that can be appended separately."""
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        template = Paragraph("template")
        doc.paragraphs.append(template.copy())
        doc.paragraphs.append(template.copy())
        assert len(doc.paragraphs) == 2
        assert template.is_construction  # original spec untouched

    def test_table_transitions_to_live_after_append(self):
        from navyfox._proxy.base import ElementState
        from navyfox.table import Table
        doc, _ = _make_doc()
        tbl = Table(rows=2, cols=2)
        doc.tables.append(tbl)
        assert tbl.state is ElementState.LIVE

    def test_table_double_append_raises(self):
        from navyfox.table import Table
        doc, _ = _make_doc()
        tbl = Table(rows=2, cols=2)
        doc.tables.append(tbl)
        with pytest.raises(ValueError, match="already in a document"):
            doc.tables.append(tbl)

    def test_closed_doc_raises_document_closed_not_stale(self):
        """Accessing a LIVE proxy after its doc closes raises DocumentClosedError, not StaleProxyError."""
        from navyfox.errors import DocumentClosedError
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        para = Paragraph("bye")
        doc.paragraphs.append(para)
        doc.close()
        with pytest.raises(DocumentClosedError):
            _ = para.text
        # confirm it is NOT a stale error
        assert not para.is_stale

    def test_para_accessed_after_context_manager_raises_document_closed(self):
        """Paragraph appended inside a context manager; reference held outside raises DocumentClosedError."""
        from navyfox.errors import DocumentClosedError
        from navyfox.paragraph import Paragraph
        mock = MockHandle()
        with patch("navyfox._native.handle.get_handle", return_value=mock):
            from navyfox.document import Document
            para = Paragraph("inside")
            with Document() as doc:
                doc.paragraphs.append(para)
        with pytest.raises(DocumentClosedError):
            _ = para.text

    def test_run_transitions_to_live_after_append(self):
        from navyfox._proxy.base import ElementState
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        run = Run("hello", bold=True)
        doc.paragraphs[0].runs.append(run)
        assert run.state is ElementState.LIVE

    def test_post_append_run_mutation_reflects_in_document(self):
        from navyfox.paragraph import Paragraph
        from navyfox.run import Run
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph())
        run = Run("original")
        doc.paragraphs[0].runs.append(run)
        run.text = "mutated"
        assert doc.paragraphs[0].runs[0].text == "mutated"


# ---------------------------------------------------------------------------
# Collection edge cases
# ---------------------------------------------------------------------------

class TestCollectionEdgeCases:
    def test_getitem_negative_index(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        assert doc.paragraphs[-1].text == "B"
        assert doc.paragraphs[-2].text == "A"

    def test_getitem_out_of_range_raises(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        with pytest.raises(IndexError):
            _ = doc.paragraphs[5]

    def test_clear_empties_collection(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        doc.paragraphs.clear()
        assert len(doc.paragraphs) == 0

    def test_index_returns_correct_position(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        para = doc.paragraphs[1]
        assert doc.paragraphs.index(para) == 1

    def test_index_raises_for_unknown_element(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        other = doc.paragraphs[0].copy()
        with pytest.raises(ValueError):
            doc.paragraphs.index(other)  # type: ignore

    def test_pop_with_explicit_index(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        doc.paragraphs.append(Paragraph("B"))
        doc.paragraphs.append(Paragraph("C"))
        popped = doc.paragraphs.pop(1)
        assert popped.text == "B"
        assert len(doc.paragraphs) == 2

    def test_pop_out_of_range_raises(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("A"))
        with pytest.raises(IndexError):
            doc.paragraphs.pop(5)

    def test_remove_construction_proxy_raises(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        spec = Paragraph("never appended")
        with pytest.raises(ValueError, match="not in a document"):
            doc.paragraphs.remove(spec)  # type: ignore

    def test_contains_false_after_remove(self):
        from navyfox.paragraph import Paragraph
        doc, _ = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        para = doc.paragraphs[0]
        doc.paragraphs.remove(para)
        assert para not in doc.paragraphs


# ---------------------------------------------------------------------------
# NativeRuntimeError propagation (error injection via MockHandle)
# ---------------------------------------------------------------------------

class TestNativeRuntimeError:
    def test_create_document_failure_propagates(self):
        from navyfox.document import Document
        from navyfox.errors import NativeRuntimeError
        mock = MockHandle()
        mock.inject_error("create_document", NativeRuntimeError("create_document returned null handle"))
        with patch("navyfox._native.handle.get_handle", return_value=mock), pytest.raises(NativeRuntimeError, match="create_document"):
            Document()

    def test_save_failure_propagates(self):
        from navyfox.errors import NativeRuntimeError
        doc, mock = _make_doc()
        mock.inject_error("save_document", NativeRuntimeError("save_document failed"))
        with pytest.raises(NativeRuntimeError, match="save_document"):
            doc.save("/tmp/out.docx")

    def test_append_child_failure_propagates(self):
        from navyfox.errors import NativeRuntimeError
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        mock.inject_error("append_child", NativeRuntimeError("append_child failed"))
        with pytest.raises(NativeRuntimeError, match="append_child"):
            doc.paragraphs.append(Paragraph("x"))

    def test_remove_child_failure_propagates(self):
        from navyfox.errors import NativeRuntimeError
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("x"))
        para = doc.paragraphs[0]
        mock.inject_error("remove_child", NativeRuntimeError("remove_child failed"))
        with pytest.raises(NativeRuntimeError, match="remove_child"):
            doc.paragraphs.remove(para)

    def test_set_str_failure_propagates(self):
        from navyfox.errors import NativeRuntimeError
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("hello"))
        para = doc.paragraphs[0]
        mock.inject_error("set_str", NativeRuntimeError("set_str failed"))
        with pytest.raises(NativeRuntimeError, match="set_str"):
            para.text = "new text"

    def test_set_int_failure_propagates(self):
        from navyfox.errors import NativeRuntimeError
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("hello"))
        para = doc.paragraphs[0]
        mock.inject_error("set_int", NativeRuntimeError("set_int failed"))
        with pytest.raises(NativeRuntimeError, match="set_int"):
            para.keep_together = True

    def test_get_count_failure_propagates(self):
        from navyfox.errors import NativeRuntimeError
        from navyfox.paragraph import Paragraph
        doc, mock = _make_doc()
        doc.paragraphs.append(Paragraph("hello"))
        mock.inject_error("get_count", NativeRuntimeError("get_count failed"))
        with pytest.raises(NativeRuntimeError, match="get_count"):
            len(doc.paragraphs)

    def test_error_cleared_after_clear_error(self):
        from navyfox.errors import NativeRuntimeError
        doc, mock = _make_doc()
        mock.inject_error("save_document", NativeRuntimeError("save_document failed"))
        with pytest.raises(NativeRuntimeError):
            doc.save("/tmp/out.docx")
        mock.clear_error("save_document")
        doc.save("/tmp/out.docx")  # should not raise
