using System.Collections.Concurrent;
using System.Text;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

// ---------------------------------------------------------------------------
// DocumentState — lifetime-managed wrapper around an open WordprocessingDocument
// ---------------------------------------------------------------------------

internal sealed record DocumentState(WordprocessingDocument Document, MemoryStream Stream);

// ---------------------------------------------------------------------------
// Element wrappers — one sealed class per element type
// ---------------------------------------------------------------------------

internal abstract class ElemWrapper(nint docHandle)
{
    public readonly nint DocHandle = docHandle;
    public abstract string TypeName { get; }
}

internal sealed class DocElem(DocumentState state) : ElemWrapper(0)
{
    public override string TypeName => "document";
    public readonly DocumentState State = state;
}

internal sealed class ParaElem(Paragraph para, nint docHandle) : ElemWrapper(docHandle)
{
    public override string TypeName => "paragraph";
    public readonly Paragraph Para = para;
}

internal sealed class RunElem(Run run, nint docHandle) : ElemWrapper(docHandle)
{
    public override string TypeName => "run";
    public readonly Run Run = run;
}

internal sealed class TableElem(Table table, TableCell[,] cells, int rows, int cols, nint docHandle)
    : ElemWrapper(docHandle)
{
    public override string TypeName => "table";
    public readonly Table Table = table;
    public readonly TableCell[,] Cells = cells;
    public readonly int Rows = rows;
    public readonly int Cols = cols;
}

internal sealed class RowElem(TableRow row, int rowIdx, nint tableHandle, nint docHandle)
    : ElemWrapper(docHandle)
{
    public override string TypeName => "row";
    public readonly TableRow Row = row;
    public readonly int RowIdx = rowIdx;
    public readonly nint TableHandle = tableHandle;
}

internal sealed class CellElem(TableCell cell, int rowIdx, int colIdx, nint rowHandle, nint docHandle)
    : ElemWrapper(docHandle)
{
    public override string TypeName => "cell";
    public readonly TableCell Cell = cell;
    public readonly int RowIdx = rowIdx;
    public readonly int ColIdx = colIdx;
    public readonly nint RowHandle = rowHandle;
}

internal sealed class ImageElem(Run run, string relId, nint docHandle) : ElemWrapper(docHandle)
{
    public override string TypeName => "image";
    public readonly Run Run = run;
    public readonly string RelId = relId;
}

internal sealed class StyleElem(Style style, nint docHandle) : ElemWrapper(docHandle)
{
    public override string TypeName => "style";
    public readonly Style Style = style;
}

internal sealed class SectElem(SectionProperties sectPr, nint docHandle) : ElemWrapper(docHandle)
{
    public override string TypeName => "section";
    public readonly SectionProperties SectPr = sectPr;
}

// ---------------------------------------------------------------------------
// DocumentBuilder — unified handle registry and static helpers
// ---------------------------------------------------------------------------

internal static unsafe partial class DocumentBuilder
{
    // Unified element registry
    private static readonly ConcurrentDictionary<nint, ElemWrapper> SElements = new();

    // Per-document child handle sets — enables O(children) Dispose instead of O(all elements)
    private static readonly ConcurrentDictionary<nint, ConcurrentBag<nint>> SDocumentChildren = new();

    // Reverse maps for stable handles (OpenXml object → handle integer)
    private static readonly ConcurrentDictionary<Paragraph, nint> SParagraphHandles = new();
    private static readonly ConcurrentDictionary<Run, nint> SRunHandles = new();
    private static readonly ConcurrentDictionary<Table, nint> STableHandles = new();
    private static readonly ConcurrentDictionary<TableRow, nint> SRowHandles = new();
    private static readonly ConcurrentDictionary<TableCell, nint> SCellHandles = new();
    private static readonly ConcurrentDictionary<Run, nint> SImageHandles = new();
    private static readonly ConcurrentDictionary<Style, nint> SStyleHandles = new();
    private static readonly ConcurrentDictionary<SectionProperties, nint> SSectHandles = new();

    private static long _sNextHandle = 1;
    private static nint NextHandle() => (nint)Interlocked.Increment(ref _sNextHandle);

    // --- String helpers ---

    private static string ReadStr(byte* ptr, int len) =>
        Encoding.UTF8.GetString(ptr, len);

    private static int WriteStr(string s, byte* buf, int bufLen, int* required)
    {
        var byteCount = Encoding.UTF8.GetByteCount(s);
        *required = byteCount;
        if (byteCount == 0) return 0;
        if (byteCount > bufLen) return 0;
        return Encoding.UTF8.GetBytes(s, new Span<byte>(buf, byteCount));
    }

    // --- Body helper ---

    private static Body GetBody(DocElem d) =>
        d.State.Document.MainDocumentPart!.Document!.Body!;

    // --- Handle factory methods (lazy, stable) ---
    // Pattern: pre-allocate in SElements, then race to claim the reverse-map slot via GetOrAdd.
    // The loser cleans up its own SElements entry; only the winner registers in SDocumentChildren.

    private static void TrackChild(nint docHandle, nint childHandle) =>
        SDocumentChildren.GetOrAdd(docHandle, static _ => new ConcurrentBag<nint>()).Add(childHandle);

    private static nint GetOrCreateParagraphHandle(Paragraph para, nint docHandle)
    {
        if (SParagraphHandles.TryGetValue(para, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new ParaElem(para, docHandle);
        var winner = SParagraphHandles.GetOrAdd(para, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static nint GetOrCreateRunHandle(Run run, nint docHandle)
    {
        if (SRunHandles.TryGetValue(run, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new RunElem(run, docHandle);
        var winner = SRunHandles.GetOrAdd(run, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static nint GetOrCreateTableHandle(
        Table table, TableCell[,] cells, int rows, int cols, nint docHandle)
    {
        if (STableHandles.TryGetValue(table, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new TableElem(table, cells, rows, cols, docHandle);
        var winner = STableHandles.GetOrAdd(table, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static nint GetOrCreateRowHandle(
        TableRow row, int rowIdx, nint tableHandle, nint docHandle)
    {
        if (SRowHandles.TryGetValue(row, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new RowElem(row, rowIdx, tableHandle, docHandle);
        var winner = SRowHandles.GetOrAdd(row, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static nint GetOrCreateCellHandle(
        TableCell cell, int rowIdx, int colIdx, nint rowHandle, nint docHandle)
    {
        if (SCellHandles.TryGetValue(cell, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new CellElem(cell, rowIdx, colIdx, rowHandle, docHandle);
        var winner = SCellHandles.GetOrAdd(cell, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static nint GetOrCreateImageHandle(Run run, string relId, nint docHandle)
    {
        if (SImageHandles.TryGetValue(run, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new ImageElem(run, relId, docHandle);
        var winner = SImageHandles.GetOrAdd(run, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static nint GetOrCreateStyleHandle(Style style, nint docHandle)
    {
        if (SStyleHandles.TryGetValue(style, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new StyleElem(style, docHandle);
        var winner = SStyleHandles.GetOrAdd(style, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static nint GetOrCreateSectHandle(SectionProperties sp, nint docHandle)
    {
        if (SSectHandles.TryGetValue(sp, out var h)) return h;
        var newH = NextHandle();
        SElements[newH] = new SectElem(sp, docHandle);
        var winner = SSectHandles.GetOrAdd(sp, newH);
        if (winner != newH) { SElements.TryRemove(newH, out _); return winner; }
        TrackChild(docHandle, newH);
        return newH;
    }

    private static void AppendToBody(Body body, OpenXmlElement element)
    {
        var sectPr = body.GetFirstChild<SectionProperties>();
        if (sectPr is not null)
            body.InsertBefore(element, sectPr);
        else
            body.AppendChild(element);
    }

    // --- OpenXml bool helper ---
    // Returns -1 (unset), 0 (explicit false), or 1 (true/present).

    private static int GetOoxmlBool(OpenXmlElement? elem)
    {
        if (elem is null) return -1;
        // Fast path: Bold, Italic, Strike, etc. all inherit OnOffType and expose Val directly.
        if (elem is OnOffType oo)
            return oo.Val is null ? 1 : ((bool)oo.Val ? 1 : 0);
        foreach (var attr in elem.GetAttributes())
        {
            if (attr.LocalName == "val")
                return string.Equals(attr.Value, "false", StringComparison.OrdinalIgnoreCase) || attr.Value == "0" ? 0 : 1;
        }
        return 1; // element present, no val → true
    }
}
