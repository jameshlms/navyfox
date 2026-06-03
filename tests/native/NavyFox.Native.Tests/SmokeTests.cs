using System.Text;
using Xunit;
using static NavyFox.Native.Tests.TestHelper;

namespace NavyFox.Native.Tests;

/// <summary>
/// Smoke tests for DocumentBuilder core logic via the generic property/collection API.
/// No FFI / unmanaged pointers at the call site — helpers handle fixed() internally.
/// </summary>
public sealed class SmokeTests
{
    // ------------------------------------------------------------------
    // Document lifecycle
    // ------------------------------------------------------------------

    [Fact]
    public void CreateDocument_ReturnsNonZeroHandle()
    {
        var h = DocumentBuilder.CreateDocument();
        Assert.NotEqual(0, h);
        DocumentBuilder.Dispose(h);
    }

    [Fact]
    public void Dispose_WithInvalidHandle_DoesNotThrow()
    {
        DocumentBuilder.Dispose(9999);
    }

    [Fact]
    public void Dispose_CalledTwice_DoesNotThrow()
    {
        var h = DocumentBuilder.CreateDocument();
        DocumentBuilder.Dispose(h);
        DocumentBuilder.Dispose(h);
    }

    // ------------------------------------------------------------------
    // AppendChild — basic paragraph and run creation
    // ------------------------------------------------------------------

    [Fact]
    public void AppendChild_Paragraph_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        Assert.NotEqual(0, Append(doc, "paragraph"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AppendChild_ParagraphWithStyle_ReturnsNonZeroAndStylePersists()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Assert.NotEqual(0, para);
        SetStr(para, "style", "Normal");
        Assert.Equal("Normal", ReadStr(para, "style"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AppendChild_Run_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        var run = Append(para, "run");
        Assert.NotEqual(0, run);
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AppendChild_HeadingStyle_Persists()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "text", "My Heading");
        SetStr(para, "style", "Heading1");
        Assert.Equal("Heading1", ReadStr(para, "style"));
        Assert.Equal("My Heading", ReadStr(para, "text"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AppendChild_InvalidHandle_ReturnsZero()
    {
        Assert.Equal(0, Append(9999, "paragraph"));
    }

    // ------------------------------------------------------------------
    // AddTable
    // ------------------------------------------------------------------

    [Fact]
    public void AddTable_ReturnsNonZeroHandle()
    {
        var doc = DocumentBuilder.CreateDocument();
        Assert.NotEqual(0, DocumentBuilder.AddTable(doc, 2, 2));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void AddTable_SetCellText_Succeeds()
    {
        var doc = DocumentBuilder.CreateDocument();
        var tbl = DocumentBuilder.AddTable(doc, 2, 2);
        var row = ChildAt(tbl, "rows", 1);
        var cell = ChildAt(row, "cells", 0);
        Assert.Equal(0, SetStr(cell, "text", "North"));
        Assert.Equal("North", ReadStr(cell, "text"));
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // SaveDocument
    // ------------------------------------------------------------------

    [Fact]
    public unsafe void SaveDocument_WritesFile()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "text", "Test Doc");
        SetStr(para, "style", "Heading1");

        var path = SaveToTempFile(doc);
        try
        {
            Assert.True(File.Exists(path), "Expected output file to exist after save.");
            Assert.True(new FileInfo(path).Length > 0, "Expected non-empty .docx file.");
        }
        finally
        {
            if (File.Exists(path)) File.Delete(path);
            DocumentBuilder.Dispose(doc);
        }
    }

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
    public void GetCount_Paragraphs_AfterAddingThree_ReturnsThree()
    {
        var doc = DocumentBuilder.CreateDocument();
        Append(doc, "paragraph");
        Append(doc, "paragraph");
        Append(doc, "paragraph");
        Assert.Equal(3, Count(doc, "paragraphs"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetCount_InvalidHandle_ReturnsMinusOne()
    {
        Assert.Equal(-1, Count(9999, "paragraphs"));
    }

    // ------------------------------------------------------------------
    // GetStr — text and style read-back
    // ------------------------------------------------------------------

    [Fact]
    public void GetStr_ParagraphText_ReturnsCorrectText()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "text", "Hello NavyFox");
        Assert.Equal("Hello NavyFox", ReadStr(para, "text"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetStr_ParagraphStyle_ReturnsStyleId()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "style", "Normal");
        Assert.Equal("Normal", ReadStr(para, "style"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void GetStr_ParagraphStyle_NoStyle_ReturnsEmpty()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        Assert.Equal("", ReadStr(para, "style"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public unsafe void GetStr_BufferTooSmall_ReturnsZeroAndSetsRequired()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        SetStr(para, "text", "Hello");

        var nameBytes = TestHelper.U("text");
        var buf = new byte[2];
        int required = 0, written;
        fixed (byte* pName = nameBytes, pBuf = buf)
            written = DocumentBuilder.GetStr(para, pName, nameBytes.Length, pBuf, buf.Length, &required);

        Assert.Equal(0, written);
        Assert.Equal(5, required);  // "Hello" = 5 bytes
        DocumentBuilder.Dispose(doc);
    }

    // ------------------------------------------------------------------
    // RemoveChild — replaces old RemoveParagraph API
    // ------------------------------------------------------------------

    [Fact]
    public void RemoveChild_Paragraph_DecreasesCount()
    {
        var doc = DocumentBuilder.CreateDocument();
        var p1 = Append(doc, "paragraph");
        Append(doc, "paragraph");
        Assert.Equal(2, Count(doc, "paragraphs"));
        Assert.Equal(0, DocumentBuilder.RemoveChild(p1));
        Assert.Equal(1, Count(doc, "paragraphs"));
        DocumentBuilder.Dispose(doc);
    }

    [Fact]
    public void RemoveChild_InvalidHandle_ReturnsMinusOne()
    {
        Assert.Equal(-1, DocumentBuilder.RemoveChild(9999));
    }

    [Fact]
    public void RemoveChild_AlreadyRemovedHandle_ReturnsMinusOne()
    {
        var doc = DocumentBuilder.CreateDocument();
        var para = Append(doc, "paragraph");
        DocumentBuilder.RemoveChild(para);
        Assert.Equal(-1, DocumentBuilder.RemoveChild(para));
        DocumentBuilder.Dispose(doc);
    }
}
