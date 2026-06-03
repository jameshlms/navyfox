using Xunit;
using static NavyFox.Native.Tests.TestHelper;

namespace NavyFox.Native.Tests;

/// <summary>
/// Tests for the generic property/collection API — GetInt, SetInt, GetFloat, SetFloat,
/// GetStr, SetStr, GetCount, GetChildHandle, AppendChild, GetElementType, RemoveChild.
/// These are the internal APIs the Python FFI layer calls for every property access.
/// </summary>
public sealed class GenericApiTests
{
    // ------------------------------------------------------------------
    // GetCount
    // ------------------------------------------------------------------

    [Fact]
    public void GetCount_Paragraphs_EmptyDocument_ReturnsZero()
    {
        var doc = DocumentBuilder.CreateDocument();
        Assert.Equal(0, Count(doc, "paragraphs"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetCount_Paragraphs_AfterAppend_ReturnsOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        Append(doc, "paragraph");
        Assert.Equal(1, Count(doc, "paragraphs"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetCount_Body_IncludesParagraphsAndTables()
    {
        var doc = DocumentBuilder.CreateDocument();
        Append(doc, "paragraph");
        DocumentBuilder.AddTable(doc, 2, 2);
        Assert.Equal(2, Count(doc, "body"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetCount_Runs_AfterAppendingTwo_ReturnsTwo()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Append(para, "run");
        Append(para, "run");
        Assert.Equal(2, Count(para, "runs"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetCount_Rows_AfterAddTable_ReturnsRowCount()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 3, 2);
        Assert.Equal(3, Count(tbl, "rows"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetCount_Cells_AfterAddTable_ReturnsRowsTimesCols()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 3, 4);
        Assert.Equal(12, Count(tbl, "cells"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetCount_InvalidHandle_ReturnsMinusOne()
    {
        Assert.Equal(-1, Count(9999, "paragraphs"));
    }

    // ------------------------------------------------------------------
    // GetChildHandle
    // ------------------------------------------------------------------

    [Fact]
    public void GetChildHandle_Paragraph_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        Append(doc, "paragraph");
        Assert.NotEqual(0, ChildAt(doc, "paragraphs", 0));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetChildHandle_Run_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Append(para, "run");
        Assert.NotEqual(0, ChildAt(para, "runs", 0));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetChildHandle_Row_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        Assert.NotEqual(0, ChildAt(tbl, "rows", 0));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetChildHandle_Cell_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        var row = ChildAt(tbl, "rows", 0);
        Assert.NotEqual(0, ChildAt(row, "cells", 0));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetChildHandle_OutOfRange_ReturnsZero()
    {
        var doc = DocumentBuilder.CreateDocument();
        Append(doc, "paragraph");
        Assert.Equal(0, ChildAt(doc, "paragraphs", 5));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetChildHandle_NegativeIndex_ReturnsLastElement()
    {
        var doc = DocumentBuilder.CreateDocument();
        Append(doc, "paragraph");
        var first = ChildAt(doc, "paragraphs", 0);
        var last = ChildAt(doc, "paragraphs", -1);
        Assert.Equal(first, last);
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetChildHandle_SameCallTwice_ReturnsSameHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        Append(doc, "paragraph");
        Assert.Equal(ChildAt(doc, "paragraphs", 0), ChildAt(doc, "paragraphs", 0));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetChildHandle_InvalidHandle_ReturnsZero()
    {
        Assert.Equal(0, ChildAt(9999, "paragraphs", 0));
    }

    // ------------------------------------------------------------------
    // AppendChild
    // ------------------------------------------------------------------

    [Fact]
    public void AppendChild_Paragraph_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        Assert.NotEqual(0, Append(doc, "paragraph"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AppendChild_Run_ToParagraph_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Assert.NotEqual(0, Append(para, "run"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AppendChild_UnknownType_ReturnsZero()
    {
        var doc = DocumentBuilder.CreateDocument();
        Assert.Equal(0, Append(doc, "bogustype"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AppendChild_InvalidHandle_ReturnsZero()
    {
        Assert.Equal(0, Append(9999, "paragraph"));
    }

    // ------------------------------------------------------------------
    // GetElementType
    // ------------------------------------------------------------------

    [Fact]
    public void GetElementType_Document_ReturnsDocument()
    {
        var doc = DocumentBuilder.CreateDocument();
        Assert.Equal("document", ReadType(doc));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetElementType_Paragraph_ReturnsParagraph()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Assert.Equal("paragraph", ReadType(para));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetElementType_Run_ReturnsRun()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal("run", ReadType(run));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetElementType_Table_ReturnsTable()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        Assert.Equal("table", ReadType(tbl));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetElementType_Row_ReturnsRow()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        var row = ChildAt(tbl, "rows", 0);
        Assert.Equal("row", ReadType(row));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetElementType_Cell_ReturnsCell()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        var row = ChildAt(tbl, "rows", 0);
        var cell = ChildAt(row, "cells", 0);
        Assert.Equal("cell", ReadType(cell));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public unsafe void GetElementType_InvalidHandle_ReturnsMinusOne()
    {
        var buf = new byte[64];
        int required = 0;
        fixed (byte* pBuf = buf)
            Assert.Equal(-1, DocumentBuilder.GetElementType(9999, pBuf, buf.Length, &required));
    }

    // ------------------------------------------------------------------
    // GetInt / SetInt
    // ------------------------------------------------------------------

    [Fact]
    public void SetInt_Bold_ThenGetInt_ReturnsOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal(0, SetInt(run, "bold", 1));
        Assert.Equal(1, GetInt(run, "bold"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetInt_BoldExplicitFalse_ThenGetInt_ReturnsZero()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        SetInt(run, "bold", 1);
        SetInt(run, "bold", 0);
        Assert.Equal(0, GetInt(run, "bold"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetInt_Italic_ThenGetInt_ReturnsOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal(0, SetInt(run, "italic", 1));
        Assert.Equal(1, GetInt(run, "italic"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetInt_UnsetBoolProperty_ReturnsMinusOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal(-1, GetInt(run, "bold"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetInt_KeepTogether_ThenGetInt_ReturnsOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Assert.Equal(0, SetInt(para, "keep_together", 1));
        Assert.Equal(1, GetInt(para, "keep_together"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetInt_AllRunBoolProperties_RoundTrip()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        foreach (var prop in new[] { "bold", "italic", "strikethrough", "all_caps", "small_caps",
                                     "hidden", "emboss", "imprint", "outline", "shadow", "no_spell_check" })
        {
            Assert.Equal(0, SetInt(run, prop, 1));
            Assert.Equal(1, GetInt(run, prop));
        }
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetInt_InvalidHandle_ReturnsMinusOne()
    {
        Assert.Equal(-1, SetInt(9999, "bold", 1));
    }

    [Fact]
    public void GetInt_InvalidHandle_ReturnsMinusTwo()
    {
        Assert.Equal(-2, GetInt(9999, "bold"));
    }

    [Fact]
    public void SetInt_UnknownProperty_ReturnsMinusOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal(-1, SetInt(run, "no_such_prop", 1));
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // GetFloat / SetFloat
    // ------------------------------------------------------------------

    [Fact]
    public void SetFloat_FontSize_ThenGetFloat_ReturnsCorrectValue()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal(0, SetFloat(run, "font_size", 12.0));
        Assert.Equal(12.0, GetFloat(run, "font_size"), precision: 3);
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetFloat_FontSize_HalfPoint_RoundTrips()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        SetFloat(run, "font_size", 10.5);
        Assert.Equal(10.5, GetFloat(run, "font_size"), precision: 3);
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetFloat_UnsetFontSize_ReturnsZero()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal(0.0, GetFloat(run, "font_size"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetFloat_InvalidHandle_ReturnsNaN()
    {
        Assert.True(double.IsNaN(GetFloat(9999, "font_size")));
    }

    // ------------------------------------------------------------------
    // GetStr / SetStr — paragraph
    // ------------------------------------------------------------------

    [Fact]
    public void SetStr_ParagraphText_ThenGetStr_ReturnsText()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Assert.Equal(0, SetStr(para, "text", "Hello Native"));
        Assert.Equal("Hello Native", ReadStr(para, "text"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_ParagraphStyle_ThenGetStr_ReturnsStyle()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "style", "Heading1");
        Assert.Equal("Heading1", ReadStr(para, "style"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_ParagraphAlignment_Center_RoundTrips()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "alignment", "center");
        Assert.Equal("center", ReadStr(para, "alignment"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_ParagraphAlignment_Right_RoundTrips()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "alignment", "right");
        Assert.Equal("right", ReadStr(para, "alignment"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_ParagraphAlignment_Justify_RoundTrips()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "alignment", "justify");
        Assert.Equal("justify", ReadStr(para, "alignment"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_ParagraphText_OverwritesPreviousText()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "text", "first");
        SetStr(para, "text", "second");
        Assert.Equal("second", ReadStr(para, "text"));
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // GetStr / SetStr — run
    // ------------------------------------------------------------------

    [Fact]
    public void SetStr_RunText_ThenGetStr_ReturnsText()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.Equal(0, SetStr(run, "text", "run content"));
        Assert.Equal("run content", ReadStr(run, "text"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_FontName_ThenGetStr_ReturnsName()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        SetStr(run, "font_name", "Arial");
        Assert.Equal("Arial", ReadStr(run, "font_name"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_Color_ThenGetStr_ReturnsColor()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        SetStr(run, "color", "FF0000");
        Assert.Equal("FF0000", ReadStr(run, "color"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_Underline_Single_RoundTrips()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        SetStr(run, "underline", "single");
        Assert.Equal("single", ReadStr(run, "underline"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_Underline_AllValues_RoundTrip()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        foreach (var uv in new[] { "single", "double", "dotted", "dashed", "wave" })
        {
            SetStr(run, "underline", uv);
            Assert.Equal(uv, ReadStr(run, "underline"));
        }
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // GetStr / SetStr — cell
    // ------------------------------------------------------------------

    [Fact]
    public void SetStr_CellText_ThenGetStr_ReturnsText()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        var row = ChildAt(tbl, "rows", 0);
        var cell = ChildAt(row, "cells", 0);
        Assert.Equal(0, SetStr(cell, "text", "Cell Content"));
        Assert.Equal("Cell Content", ReadStr(cell, "text"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_MultipleCells_EachHoldsOwnText()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 1, 3);
        var row = ChildAt(tbl, "rows", 0);
        var c0 = ChildAt(row, "cells", 0);
        var c1 = ChildAt(row, "cells", 1);
        var c2 = ChildAt(row, "cells", 2);
        SetStr(c0, "text", "A");
        SetStr(c1, "text", "B");
        SetStr(c2, "text", "C");
        Assert.Equal("A", ReadStr(c0, "text"));
        Assert.Equal("B", ReadStr(c1, "text"));
        Assert.Equal("C", ReadStr(c2, "text"));
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // GetStr / SetStr — document metadata
    // ------------------------------------------------------------------

    [Fact]
    public void SetStr_DocAuthor_ThenGetStr_ReturnsAuthor()
    {
        var doc = DocumentBuilder.CreateDocument();
        SetStr(doc, "author", "Test Author");
        Assert.Equal("Test Author", ReadStr(doc, "author"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void SetStr_DocTitle_ThenGetStr_ReturnsTitle()
    {
        var doc = DocumentBuilder.CreateDocument();
        SetStr(doc, "title", "My Document");
        Assert.Equal("My Document", ReadStr(doc, "title"));
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // RemoveChild
    // ------------------------------------------------------------------

    [Fact]
    public void RemoveChild_Run_DecreasesRunCount()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Append(para, "run");
        Assert.Equal(2, Count(para, "runs"));
        Assert.Equal(0, DocumentBuilder.RemoveChild(run));
        Assert.Equal(1, Count(para, "runs"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void RemoveChild_Paragraph_DecreasesCount()
    {
        var doc = DocumentBuilder.CreateDocument();
        var p1 = Append(doc, "paragraph");
        Append(doc, "paragraph");
        Assert.Equal(0, DocumentBuilder.RemoveChild(p1));
        Assert.Equal(1, Count(doc, "paragraphs"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void RemoveChild_Paragraph_AlsoRemovesItsRuns()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        DocumentBuilder.RemoveChild(para);
        // run's handle should be gone too
        Assert.Equal(-1, DocumentBuilder.RemoveChild(run));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void RemoveChild_InvalidHandle_ReturnsMinusOne()
    {
        Assert.Equal(-1, DocumentBuilder.RemoveChild(9999));
    }

    [Fact]
    public void RemoveChild_CalledTwice_SecondCallReturnsMinusOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Assert.Equal(0, DocumentBuilder.RemoveChild(para));
        Assert.Equal(-1, DocumentBuilder.RemoveChild(para));
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // Dispose — child handle cleanup
    // ------------------------------------------------------------------

    [Fact]
    public void Dispose_RemovesChildHandlesFromRegistry()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        DocumentBuilder.Dispose(doc);
        Assert.Equal(-1, DocumentBuilder.RemoveChild(para));
        Assert.Equal(-1, DocumentBuilder.RemoveChild(run));
    }

    [Fact]
    public void Dispose_RemovesTableChildHandles()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        var row = ChildAt(tbl, "rows", 0);
        var cell = ChildAt(row, "cells", 0);
        DocumentBuilder.Dispose(doc);
        Assert.Equal(-1, DocumentBuilder.RemoveChild(row));
        Assert.Equal(-1, DocumentBuilder.RemoveChild(cell));
    }
}
