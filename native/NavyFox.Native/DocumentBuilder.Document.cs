using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

internal static unsafe partial class DocumentBuilder
{
    internal static nint CreateDocument()
    {
        try
        {
            var stream = new MemoryStream();
            var wp = WordprocessingDocument.Create(stream, WordprocessingDocumentType.Document);
            var mainPart = wp.AddMainDocumentPart();
            var sectPr = new SectionProperties(
                new PageSize { Width = 12240, Height = 15840 },
                new PageMargin { Top = 1440, Bottom = 1440, Left = 1800, Right = 1800, Header = 720, Footer = 720 }
            );
            mainPart.Document = new Document(new Body(sectPr));
            AddDefaultStyles(mainPart);

            var h = NextHandle();
            SElements[h] = new DocElem(new DocumentState(wp, stream));
            return h;
        }
        catch
        {
            return 0;
        }
    }

    internal static nint OpenDocument(byte* path, int pathLen)
    {
        try
        {
            var pathStr = ReadStr(path, pathLen);
            var bytes = File.ReadAllBytes(pathStr);
            var stream = new MemoryStream(capacity: bytes.Length + 4096);
            stream.Write(bytes, 0, bytes.Length);
            stream.Position = 0;

            var wp = WordprocessingDocument.Open(stream, isEditable: true);

            var h = NextHandle();
            SElements[h] = new DocElem(new DocumentState(wp, stream));
            return h;
        }
        catch
        {
            return 0;
        }
    }

    // edit_document behaves identically to open_document for handle registration;
    // the Python layer remembers the edit path and saves-on-exit.
    internal static nint EditDocument(byte* path, int pathLen) =>
        OpenDocument(path, pathLen);

    internal static int SaveDocument(nint handle, byte* path, int pathLen)
    {
        if (!SElements.TryGetValue(handle, out var elem) || elem is not DocElem d)
            return -1;

        try
        {
            var pathStr = ReadStr(path, pathLen);
            var body = d.State.Document.MainDocumentPart!.Document!.Body!;
            EnsureTrailingParagraph(body);
            d.State.Document.Save();
            var bytes = d.State.Stream.ToArray();
            File.WriteAllBytes(pathStr, bytes);
            return 0;
        }
        catch
        {
            return -1;
        }
    }

    private static void EnsureTrailingParagraph(Body body)
    {
        var sectPr = body.GetFirstChild<SectionProperties>();
        var candidate = sectPr?.PreviousSibling() ?? body.LastChild;
        bool needsTrailing = candidate is not Paragraph p
            || p.ParagraphProperties?.ParagraphBorders?.GetFirstChild<BottomBorder>() is not null;
        if (!needsTrailing) return;
        var trailing = new Paragraph();
        if (sectPr is not null)
            body.InsertBefore(trailing, sectPr);
        else
            body.AppendChild(trailing);
    }

    internal static void Dispose(nint handle)
    {
        if (!SElements.TryRemove(handle, out var elem) || elem is not DocElem d)
            return;

        // Remove every child element registered under this document handle.
        foreach (var kvp in SElements.ToArray())
        {
            if (kvp.Value.DocHandle == handle)
            {
                if (SElements.TryRemove(kvp.Key, out var child))
                    RemoveReverseMapEntry(child);
            }
        }

        try { d.State.Document.Dispose(); } catch { /* best effort */ }
        try { d.State.Stream.Dispose(); } catch { /* best effort */ }
    }

    private static void RemoveReverseMapEntry(ElemWrapper elem)
    {
        switch (elem)
        {
            case ParaElem p:  SParagraphHandles.TryRemove(p.Para, out _);  break;
            case RunElem r:   SRunHandles.TryRemove(r.Run, out _);         break;
            case TableElem t: STableHandles.TryRemove(t.Table, out _);     break;
            case RowElem row: SRowHandles.TryRemove(row.Row, out _);       break;
            case CellElem c:  SCellHandles.TryRemove(c.Cell, out _);       break;
            case StyleElem s: SStyleHandles.TryRemove(s.Style, out _);     break;
            case SectElem  e: SSectHandles.TryRemove(e.SectPr, out _);    break;
        }
    }
}
