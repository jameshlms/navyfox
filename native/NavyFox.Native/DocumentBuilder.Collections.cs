using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

internal static unsafe partial class DocumentBuilder
{
    // -----------------------------------------------------------------------
    // GetCount — number of children in a named collection
    // -----------------------------------------------------------------------

    internal static int GetCount(nint handle, byte* collection, int collectionLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var col = ReadStr(collection, collectionLen);
        try
        {
            return elem switch
            {
                DocElem d => CountBodyCollection(d, col),
                ParaElem p => col switch
                {
                    "runs"   => p.Para.Elements<Run>().Count(r => !IsImageRun(r)),
                    "images" => p.Para.Elements<Run>().Count(IsImageRun),
                    _        => -1
                },
                TableElem t => col switch
                {
                    "rows" => t.Table.Elements<TableRow>().Count(),
                    "cells" => t.Rows * t.Cols,
                    _ => -1
                },
                RowElem r => col is "cells" ? r.Row.Elements<TableCell>().Count() : -1,
                CellElem c => col switch
                {
                    "paragraphs" => c.Cell.Elements<Paragraph>().Count(),
                    "tables"     => c.Cell.Elements<Table>().Count(),
                    "body"       => c.Cell.ChildElements.Count(e => e is Paragraph or Table),
                    _            => -1
                },
                _ => -1
            };
        }
        catch { return -1; }
    }

    private static int CountBodyCollection(DocElem d, string col)
    {
        if (col == "styles")
        {
            return d.State.Document.MainDocumentPart
                ?.StyleDefinitionsPart?.Styles?.Elements<Style>().Count() ?? 0;
        }
        var body = GetBody(d);
        return col switch
        {
            "body"       => body.ChildElements.Count(e => e is Paragraph or Table),
            "paragraphs" => body.Elements<Paragraph>().Count(),
            "tables"     => body.Elements<Table>().Count(),
            "sections"   => body.Elements<Paragraph>().Count(p => p.ParagraphProperties?.SectionProperties is not null) + 1,
            _ => -1
        };
    }

    // -----------------------------------------------------------------------
    // GetChildHandle — handle for the i-th element of a named collection
    // -----------------------------------------------------------------------

    internal static nint GetChildHandle(
        nint handle, byte* collection, int collectionLen, int index)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return 0;
        var col = ReadStr(collection, collectionLen);
        try
        {
            return elem switch
            {
                DocElem d => GetBodyChild(d, handle, col, index),
                ParaElem p when col is "runs"   => GetRunChild(p, handle, index),
                ParaElem p when col is "images" => GetImageRunChild(p, handle, index),
                TableElem t when col is "rows" => GetRowChild(t, handle, index),
                TableElem t when col is "cells" => GetFlatCellChild(t, handle, index),
                RowElem r when col is "cells" => GetCellChild(r, handle, index),
                CellElem c when col is "paragraphs" => GetCellParaChild(c, handle, index),
                CellElem c when col is "tables"     => GetCellTableChild(c, handle, index),
                CellElem c when col is "body"       => GetCellBodyChild(c, handle, index),
                _ => 0
            };
        }
        catch { return 0; }
    }

    private static nint GetBodyChild(DocElem d, nint docHandle, string col, int index)
    {
        if (col == "styles")
        {
            var styles = d.State.Document.MainDocumentPart
                ?.StyleDefinitionsPart?.Styles?.Elements<Style>().ToList();
            if (styles is null) return 0;
            if (index < 0) index = styles.Count + index;
            if (index < 0 || index >= styles.Count) return 0;
            return GetOrCreateStyleHandle(styles[index], docHandle);
        }
        if (col.StartsWith("style:", StringComparison.Ordinal))
        {
            var styleId = col[6..];
            var stylesElem = d.State.Document.MainDocumentPart?.StyleDefinitionsPart?.Styles;
            if (stylesElem is null) return 0;
            var style = stylesElem.Elements<Style>()
                .FirstOrDefault(s => s.StyleId?.Value == styleId);
            return style is null ? 0 : GetOrCreateStyleHandle(style, docHandle);
        }
        if (col == "default_style")
        {
            var stylesElem = d.State.Document.MainDocumentPart?.StyleDefinitionsPart?.Styles;
            if (stylesElem is null) return 0;
            var style = stylesElem.Elements<Style>()
                .FirstOrDefault(s => s.Default?.Value == true);
            return style is null ? 0 : GetOrCreateStyleHandle(style, docHandle);
        }
        var body = GetBody(d);
        switch (col)
        {
            case "body":
            {
                var all = body.ChildElements.Where(e => e is Paragraph || e is Table).ToList();
                if (index < 0) index = all.Count + index;
                if (index < 0 || index >= all.Count) return 0;
                return all[index] switch
                {
                    Paragraph p => GetOrCreateParagraphHandle(p, docHandle),
                    Table t => GetOrCreateTableHandle(t, GetTableCells(t), GetTableRows(t), GetTableCols(t), docHandle),
                    _ => 0
                };
            }
            case "paragraphs":
            {
                var paras = body.Elements<Paragraph>().ToList();
                if (index < 0) index = paras.Count + index;
                if (index < 0 || index >= paras.Count) return 0;
                return GetOrCreateParagraphHandle(paras[index], docHandle);
            }
            case "tables":
            {
                var tables = body.Elements<Table>().ToList();
                if (index < 0) index = tables.Count + index;
                if (index < 0 || index >= tables.Count) return 0;
                var table = tables[index];
                return GetOrCreateTableHandle(
                    table, GetTableCells(table), GetTableRows(table), GetTableCols(table), docHandle);
            }
            case "sections":
            {
                var sectParas = body.Elements<Paragraph>()
                    .Where(p => p.ParagraphProperties?.SectionProperties is not null)
                    .ToList();
                int total = sectParas.Count + 1;
                if (index < 0) index = total + index;
                if (index < 0 || index >= total) return 0;
                SectionProperties sp;
                if (index < sectParas.Count)
                    sp = sectParas[index].ParagraphProperties!.SectionProperties!;
                else
                    sp = body.GetFirstChild<SectionProperties>()
                        ?? (SectionProperties)body.AppendChild(new SectionProperties());
                return GetOrCreateSectHandle(sp, docHandle);
            }
            default:
                return 0;
        }
    }

    private static nint GetRunChild(ParaElem p, nint docHandle, int index)
    {
        var runs = p.Para.Elements<Run>().Where(r => !IsImageRun(r)).ToList();
        if (index < 0) index = runs.Count + index;
        if (index < 0 || index >= runs.Count) return 0;
        return GetOrCreateRunHandle(runs[index], docHandle);
    }

    private static nint GetImageRunChild(ParaElem p, nint docHandle, int index)
    {
        var imageRuns = p.Para.Elements<Run>().Where(IsImageRun).ToList();
        if (index < 0) index = imageRuns.Count + index;
        if (index < 0 || index >= imageRuns.Count) return 0;
        var run = imageRuns[index];
        var relId = GetRunImageRelId(run);
        if (relId is null) return 0;
        return GetOrCreateImageHandle(run, relId, p.DocHandle);
    }

    private static nint GetRowChild(TableElem t, nint tableHandle, int index)
    {
        var rows = t.Table.Elements<TableRow>().ToList();
        if (index < 0) index = rows.Count + index;
        if (index < 0 || index >= rows.Count) return 0;
        return GetOrCreateRowHandle(rows[index], index, tableHandle, t.DocHandle);
    }

    private static nint GetFlatCellChild(TableElem t, nint tableHandle, int index)
    {
        // Flat access: table[i] → row = i/cols, col = i%cols
        if (t.Cols == 0) return 0;
        var row = index / t.Cols;
        var col = index % t.Cols;
        if (row < 0 || row >= t.Rows) return 0;
        var rowElem = t.Table.Elements<TableRow>().ElementAtOrDefault(row);
        if (rowElem is null) return 0;
        var rowHandle = GetOrCreateRowHandle(rowElem, row, tableHandle, t.DocHandle);
        var cellElem = rowElem.Elements<TableCell>().ElementAtOrDefault(col);
        if (cellElem is null) return 0;
        return GetOrCreateCellHandle(cellElem, row, col, rowHandle, t.DocHandle);
    }

    private static nint GetCellChild(RowElem r, nint rowHandle, int index)
    {
        var cells = r.Row.Elements<TableCell>().ToList();
        if (index < 0) index = cells.Count + index;
        if (index < 0 || index >= cells.Count) return 0;
        return GetOrCreateCellHandle(cells[index], r.RowIdx, index, rowHandle, r.DocHandle);
    }

    private static nint GetCellParaChild(CellElem c, nint docHandle, int index)
    {
        var paras = c.Cell.Elements<Paragraph>().ToList();
        if (index < 0) index = paras.Count + index;
        if (index < 0 || index >= paras.Count) return 0;
        return GetOrCreateParagraphHandle(paras[index], docHandle);
    }

    private static nint GetCellTableChild(CellElem c, nint docHandle, int index)
    {
        var tables = c.Cell.Elements<Table>().ToList();
        if (index < 0) index = tables.Count + index;
        if (index < 0 || index >= tables.Count) return 0;
        var table = tables[index];
        return GetOrCreateTableHandle(
            table, GetTableCells(table), GetTableRows(table), GetTableCols(table), docHandle);
    }

    private static nint GetCellBodyChild(CellElem c, nint docHandle, int index)
    {
        var all = c.Cell.ChildElements.Where(e => e is Paragraph || e is Table).ToList();
        if (index < 0) index = all.Count + index;
        if (index < 0 || index >= all.Count) return 0;
        return all[index] switch
        {
            Paragraph p => GetOrCreateParagraphHandle(p, docHandle),
            Table t     => GetOrCreateTableHandle(
                t, GetTableCells(t), GetTableRows(t), GetTableCols(t), docHandle),
            _ => 0
        };
    }

    // -----------------------------------------------------------------------
    // AppendChild — create and append a new child element
    // -----------------------------------------------------------------------

    internal static nint AppendChild(nint handle, byte* childType, int childTypeLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return 0;
        var ct = ReadStr(childType, childTypeLen);
        try
        {
            return (elem, ct) switch
            {
                (DocElem d, "paragraph") => AppendParagraphToDoc(d, handle),
                (DocElem d, "style") => AppendStyleToDoc(d, handle),
                (ParaElem p, "run") => AppendRunToParagraph(p),
                (CellElem c, "paragraph") => AppendParagraphToCell(c),
                _ => 0
            };
        }
        catch { return 0; }
    }

    private static nint AppendParagraphToDoc(DocElem d, nint docHandle)
    {
        var para = new Paragraph();
        AppendToBody(GetBody(d), para);
        return GetOrCreateParagraphHandle(para, docHandle);
    }

    private static nint AppendStyleToDoc(DocElem d, nint docHandle)
    {
        var mainPart = d.State.Document.MainDocumentPart!;
        var stylesPart = mainPart.StyleDefinitionsPart
            ?? mainPart.AddNewPart<StyleDefinitionsPart>();
        stylesPart.Styles ??= new Styles();
        var style = new Style { Type = StyleValues.Paragraph };
        stylesPart.Styles.AppendChild(style);
        return GetOrCreateStyleHandle(style, docHandle);
    }

    private static nint AppendRunToParagraph(ParaElem p)
    {
        var run = new Run();
        p.Para.AppendChild(run);
        return GetOrCreateRunHandle(run, p.DocHandle);
    }

    private static nint AppendParagraphToCell(CellElem c)
    {
        var para = new Paragraph();
        c.Cell.AppendChild(para);
        return GetOrCreateParagraphHandle(para, c.DocHandle);
    }

    // -----------------------------------------------------------------------
    // RemoveChild — remove an element and clean up registrations
    // -----------------------------------------------------------------------

    internal static int RemoveChild(nint handle)
    {
        if (!SElements.TryRemove(handle, out var elem)) return -1;
        try
        {
            switch (elem)
            {
                case ParaElem p:
                    SParagraphHandles.TryRemove(p.Para, out _);
                    RemoveRunRegistrations(p.Para);
                    p.Para.Remove();
                    return 0;

                case RunElem r:
                    SRunHandles.TryRemove(r.Run, out _);
                    r.Run.Remove();
                    return 0;

                case ImageElem img:
                    SImageHandles.TryRemove(img.Run, out _);
                    img.Run.Remove();
                    return 0;

                case TableElem t:
                    STableHandles.TryRemove(t.Table, out _);
                    RemoveTableRegistrations(t.Table);
                    t.Table.Remove();
                    return 0;

                case RowElem r:
                    SRowHandles.TryRemove(r.Row, out _);
                    RemoveCellRegistrations(r.Row);
                    r.Row.Remove();
                    return 0;

                case CellElem c:
                    SCellHandles.TryRemove(c.Cell, out _);
                    return 0;

                case StyleElem s:
                    SStyleHandles.TryRemove(s.Style, out _);
                    s.Style.Remove();
                    return 0;

                default:
                    return -1;
            }
        }
        catch { return -1; }
    }

    private static void RemoveRunRegistrations(Paragraph para)
    {
        foreach (var run in para.Elements<Run>())
        {
            if (SRunHandles.TryRemove(run, out var rh))
                SElements.TryRemove(rh, out _);
            if (SImageHandles.TryRemove(run, out var ih))
                SElements.TryRemove(ih, out _);
        }
    }

    private static void RemoveTableRegistrations(Table table)
    {
        foreach (var row in table.Elements<TableRow>())
        {
            RemoveCellRegistrations(row);
            if (SRowHandles.TryRemove(row, out var rh))
                SElements.TryRemove(rh, out _);
        }
    }

    private static void RemoveCellRegistrations(TableRow row)
    {
        foreach (var cell in row.Elements<TableCell>())
        {
            if (SCellHandles.TryRemove(cell, out var ch))
                SElements.TryRemove(ch, out _);
        }
    }

    // -----------------------------------------------------------------------
    // GetElementType — write the type name string to a caller-supplied buffer
    // -----------------------------------------------------------------------

    internal static int GetElementType(nint handle, byte* buf, int bufLen, int* required)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        return WriteStr(elem.TypeName, buf, bufLen, required);
    }

    // -----------------------------------------------------------------------
    // AddTable — table creation requires rows/cols at construction time
    // -----------------------------------------------------------------------

    internal static nint AddTable(nint parentHandle, int rows, int cols)
    {
        if (!SElements.TryGetValue(parentHandle, out var elem)) return 0;
        try
        {
            return elem switch
            {
                DocElem d  => AddTableToDoc(d, parentHandle, rows, cols),
                CellElem c => AddTableToCell(c, rows, cols),
                _          => 0
            };
        }
        catch { return 0; }
    }

    private static nint AddTableToDoc(DocElem d, nint docHandle, int rows, int cols)
    {
        var table = BuildTable(rows, cols, out var cells);
        AppendToBody(GetBody(d), table);
        return RegisterTableHandles(table, cells, rows, cols, docHandle);
    }

    private static nint AddTableToCell(CellElem c, int rows, int cols)
    {
        var table = BuildTable(rows, cols, out var cells);
        // OpenXML requires cells to end with a paragraph; insert before the terminal one.
        var lastPara = c.Cell.Elements<Paragraph>().LastOrDefault();
        if (lastPara is not null)
            c.Cell.InsertBefore(table, lastPara);
        else
            c.Cell.AppendChild(table);
        return RegisterTableHandles(table, cells, rows, cols, c.DocHandle);
    }

    private static nint RegisterTableHandles(
        Table table, TableCell[,] cells, int rows, int cols, nint docHandle)
    {
        var tableHandle = GetOrCreateTableHandle(table, cells, rows, cols, docHandle);
        var rowList = table.Elements<TableRow>().ToList();
        for (var r = 0; r < rowList.Count; r++)
        {
            var rowHandle = GetOrCreateRowHandle(rowList[r], r, tableHandle, docHandle);
            var cellList = rowList[r].Elements<TableCell>().ToList();
            for (var c = 0; c < cellList.Count; c++)
                GetOrCreateCellHandle(cellList[c], r, c, rowHandle, docHandle);
        }
        return tableHandle;
    }

    private static int GetTableRows(Table table) => table.Elements<TableRow>().Count();
    private static int GetTableCols(Table table) =>
        table.Elements<TableRow>().FirstOrDefault()?.Elements<TableCell>().Count() ?? 0;

    private static TableCell[,] GetTableCells(Table table)
    {
        var rowList = table.Elements<TableRow>().ToList();
        var rows = rowList.Count;
        var cols = rows > 0 ? rowList[0].Elements<TableCell>().Count() : 0;
        var cells = new TableCell[rows, cols];
        for (var r = 0; r < rows; r++)
        {
            var cellList = rowList[r].Elements<TableCell>().ToList();
            for (var c = 0; c < Math.Min(cols, cellList.Count); c++)
                cells[r, c] = cellList[c];
        }
        return cells;
    }
}
