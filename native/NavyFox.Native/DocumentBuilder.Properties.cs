using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

internal static unsafe partial class DocumentBuilder
{
    // -----------------------------------------------------------------------
    // GetInt — read an integer property from any element type
    // -----------------------------------------------------------------------

    internal static int GetInt(nint handle, byte* name, int nameLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -2;
        var n = ReadStr(name, nameLen);
        try
        {
            return elem switch
            {
                ParaElem p  => GetParaInt(p.Para, n),
                RunElem r   => GetRunInt(r.Run, n),
                StyleElem s => GetStyleInt(s.Style, n),
                SectElem  e => GetSectionInt(e.SectPr, n),
                _ => -2
            };
        }
        catch { return -2; }
    }

    private static int GetParaInt(Paragraph para, string name)
    {
        var pp = para.ParagraphProperties;
        switch (name)
        {
            case "keep_together":
                return GetOoxmlBool(pp?.KeepLines);
            case "keep_with_next":
                return GetOoxmlBool(pp?.KeepNext);
            case "page_break_before":
                return GetOoxmlBool(pp?.PageBreakBefore);
            case "list_level":
            {
                var numPr = pp?.NumberingProperties;
                if (numPr is null) return 0;
                return numPr.NumberingLevelReference?.Val?.Value ?? 0;
            }
            case "_horizontal_line":
                return pp?.ParagraphBorders?.GetFirstChild<BottomBorder>() is not null ? 1 : 0;
            default:
                return -2;
        }
    }

    private static int GetRunInt(Run run, string name)
    {
        var rp = run.RunProperties;
        switch (name)
        {
            case "bold":          return GetOoxmlBool(rp?.Bold);
            case "italic":        return GetOoxmlBool(rp?.Italic);
            case "strikethrough": return GetOoxmlBool(rp?.Strike);
            case "all_caps":      return GetOoxmlBool(rp?.Caps);
            case "small_caps":    return GetOoxmlBool(rp?.SmallCaps);
            case "hidden":        return GetOoxmlBool(rp?.Vanish);
            case "emboss":        return GetOoxmlBool(rp?.Emboss);
            case "imprint":       return GetOoxmlBool(rp?.Imprint);
            case "outline":       return GetOoxmlBool(rp?.Outline);
            case "shadow":        return GetOoxmlBool(rp?.Shadow);
            case "no_spell_check": return GetOoxmlBool(rp?.NoProof);
            case "superscript":
                {
                    var vta = rp?.VerticalTextAlignment?.Val;
                    if (vta is null) return -1;
                    return vta.Value == VerticalPositionValues.Superscript ? 1 : 0;
                }
            case "subscript":
                {
                    var vta = rp?.VerticalTextAlignment?.Val;
                    if (vta is null) return -1;
                    return vta.Value == VerticalPositionValues.Subscript ? 1 : 0;
                }
            default: return -2;
        }
    }

    // -----------------------------------------------------------------------
    // SetInt — write an integer property
    // -----------------------------------------------------------------------

    internal static int SetInt(nint handle, byte* name, int nameLen, int value)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        try
        {
            if (elem is ParaElem p)  return SetParaInt(p.Para, n, value);
            if (elem is RunElem r)   return SetRunInt(r.Run, n, value);
            if (elem is StyleElem s) return SetStyleInt(s.Style, n, value);
            if (elem is SectElem e)  return SetSectionInt(e.SectPr, n, value);
            return -1;
        }
        catch { return -1; }
    }

    private static int SetParaInt(Paragraph para, string name, int value)
    {
        para.ParagraphProperties ??= new ParagraphProperties();
        var pp = para.ParagraphProperties;
        switch (name)
        {
            case "keep_together":
                pp.KeepLines      = value == 1 ? new KeepLines()      : null; return 0;
            case "keep_with_next":
                pp.KeepNext       = value == 1 ? new KeepNext()       : null; return 0;
            case "page_break_before":
                pp.PageBreakBefore = value == 1 ? new PageBreakBefore() : null; return 0;
            case "list_level" when pp.NumberingProperties is null:
                return -1;
            case "list_level":
                pp.NumberingProperties.NumberingLevelReference = new NumberingLevelReference { Val = value };
                return 0;
        }

        if (name != "_horizontal_line") return -1;
        if (value == 1)
        {
            pp.ParagraphBorders ??= new ParagraphBorders();
            if (pp.ParagraphBorders.GetFirstChild<BottomBorder>() is null)
                pp.ParagraphBorders.AppendChild(new BottomBorder
                    { Val = BorderValues.Single, Size = 48U, Space = 1U, Color = "auto" });
        }
        else
        {
            var bdr = pp.ParagraphBorders?.GetFirstChild<BottomBorder>();
            if (bdr is null) return 0;
            bdr.Remove();
            if (pp.ParagraphBorders?.HasChildren == false)
                pp.ParagraphBorders = null;
        }
        return 0;
    }

    private static int SetRunInt(Run run, string name, int value)
    {
        run.RunProperties ??= new RunProperties();
        var rp = run.RunProperties;
        switch (name)
        {
            case "bold":
                rp.Bold = value switch { 1 => new Bold(), 0 => new Bold { Val = false }, _ => null }; return 0;
            case "italic":
                rp.Italic = value switch { 1 => new Italic(), 0 => new Italic { Val = false }, _ => null }; return 0;
            case "strikethrough":
                rp.Strike = value switch { 1 => new Strike(), 0 => new Strike { Val = false }, _ => null }; return 0;
            case "all_caps":
                rp.Caps = value switch { 1 => new Caps(), 0 => new Caps { Val = false }, _ => null }; return 0;
            case "small_caps":
                rp.SmallCaps = value switch { 1 => new SmallCaps(), 0 => new SmallCaps { Val = false }, _ => null }; return 0;
            case "hidden":
                rp.Vanish = value switch { 1 => new Vanish(), 0 => new Vanish { Val = false }, _ => null }; return 0;
            case "emboss":
                rp.Emboss = value switch { 1 => new Emboss(), 0 => new Emboss { Val = false }, _ => null }; return 0;
            case "imprint":
                rp.Imprint = value switch { 1 => new Imprint(), 0 => new Imprint { Val = false }, _ => null }; return 0;
            case "outline":
                rp.Outline = value switch { 1 => new Outline(), 0 => new Outline { Val = false }, _ => null }; return 0;
            case "shadow":
                rp.Shadow = value switch { 1 => new Shadow(), 0 => new Shadow { Val = false }, _ => null }; return 0;
            case "no_spell_check":
                rp.NoProof = value switch { 1 => new NoProof(), 0 => new NoProof { Val = false }, _ => null }; return 0;
            case "superscript":
                rp.VerticalTextAlignment = value == 1
                    ? new VerticalTextAlignment { Val = VerticalPositionValues.Superscript }
                    : null;
                return 0;
            case "subscript":
                rp.VerticalTextAlignment = value == 1
                    ? new VerticalTextAlignment { Val = VerticalPositionValues.Subscript }
                    : null;
                return 0;
            default:
                return -1;
        }
    }

    // -----------------------------------------------------------------------
    // GetFloat — read a float property
    // -----------------------------------------------------------------------

    internal static double GetFloat(nint handle, byte* name, int nameLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return double.NaN;
        var n = ReadStr(name, nameLen);
        try
        {
            return elem switch
            {
                ParaElem p  => GetParaFloat(p.Para, n),
                RunElem r   => GetRunFloat(r.Run, n),
                ImageElem i => GetImageFloat(i, n),
                StyleElem s => GetStyleFloat(s.Style, n),
                SectElem  e => GetSectionFloat(e.SectPr, n),
                _ => double.NaN
            };
        }
        catch { return double.NaN; }
    }

    private static double GetParaFloat(Paragraph para, string name)
    {
        var pp = para.ParagraphProperties;

        switch (name)
        {
            case "space_before" or "space_after":
            {
                var sbl = pp?.SpacingBetweenLines;
                var raw = name == "space_before" ? sbl?.Before?.Value : sbl?.After?.Value;
                if (raw is null || !int.TryParse(raw, out var twips)) return 0.0;
                return twips / 20.0;
            }
            case "line_spacing":
            {
                var raw = pp?.SpacingBetweenLines?.Line?.Value;
                if (raw is null || !int.TryParse(raw, out var val)) return 1.0;
                return val / 240.0;
            }
            case "indent_left" or "indent_right" or "indent_hanging":
            {
                var ind = pp?.Indentation;
                var raw = name switch
                {
                    "indent_left"    => ind?.Left?.Value,
                    "indent_right"   => ind?.Right?.Value,
                    "indent_hanging" => ind?.Hanging?.Value,
                    _                => null
                };
                if (raw is null || !int.TryParse(raw, out var twips)) return 0.0;
                return twips / 1440.0;
            }
        }

        if (name != "hr_width") return double.NaN;
        var bottom = pp?.ParagraphBorders?.GetFirstChild<BottomBorder>();
        if (bottom is null) return 0.0;
        return (bottom.Size?.Value ?? 0U) / 8.0;

    }

    private static double GetRunFloat(Run run, string name)
    {
        var rp = run.RunProperties;
        if (name != "font_size") return double.NaN;
        var sizeStr = rp?.FontSize?.Val?.Value;
        if (sizeStr is null) return 0.0;
        return double.TryParse(sizeStr, out var v) ? v / 2.0 : 0.0;
    }

    // -----------------------------------------------------------------------
    // SetFloat — write a float property
    // -----------------------------------------------------------------------

    internal static int SetFloat(nint handle, byte* name, int nameLen, double value)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        try
        {
            return elem switch
            {
                ParaElem p  => SetParaFloat(p.Para, n, value),
                RunElem r   => SetRunFloat(r.Run, n, value),
                ImageElem i => SetImageFloat(i, n, value),
                StyleElem s => SetStyleFloat(s.Style, n, value),
                SectElem  e => SetSectionFloat(e.SectPr, n, value),
                _ => -1
            };
        }
        catch { return -1; }
    }

    private static int SetParaFloat(Paragraph para, string name, double value)
    {
        para.ParagraphProperties ??= new ParagraphProperties();
        var pp = para.ParagraphProperties;

        switch (name)
        {
            case "space_before" or "space_after":
            {
                pp.SpacingBetweenLines ??= new SpacingBetweenLines();
                var twips = ((int)Math.Round(value * 20)).ToString();
                if (name == "space_before") pp.SpacingBetweenLines.Before = twips;
                else                        pp.SpacingBetweenLines.After  = twips;
                return 0;
            }
            case "line_spacing":
                pp.SpacingBetweenLines ??= new SpacingBetweenLines();
                pp.SpacingBetweenLines.Line     = ((int)Math.Round(value * 240)).ToString();
                pp.SpacingBetweenLines.LineRule = LineSpacingRuleValues.Auto;
                return 0;
            case "indent_left" or "indent_right" or "indent_hanging":
            {
                pp.Indentation ??= new Indentation();
                var twips = ((int)Math.Round(value * 1440)).ToString();
                switch (name)
                {
                    case "indent_left":
                        pp.Indentation.Left    = twips;
                        break;
                    case "indent_right":
                        pp.Indentation.Right   = twips;
                        break;
                    default:
                        pp.Indentation.Hanging = twips;
                        break;
                }
                return 0;
            }
            case "hr_width":
            {
                pp.ParagraphBorders ??= new ParagraphBorders();
                var bottom = pp.ParagraphBorders.GetFirstChild<BottomBorder>()
                             ?? pp.ParagraphBorders.AppendChild(new BottomBorder
                                 { Val = BorderValues.Single, Space = 1U, Color = "auto" });
                bottom.Size = (uint)Math.Round(value * 8);
                return 0;
            }
            default:
                return -1;
        }
    }

    private static int SetRunFloat(Run run, string name, double value)
    {
        run.RunProperties ??= new RunProperties();
        var rp = run.RunProperties;
        if (name != "font_size") return -1;
        var halfPt = (int)Math.Round(value * 2);
        rp.FontSize = halfPt > 0 ? new FontSize { Val = halfPt.ToString() } : null;
        return 0;
    }

    // -----------------------------------------------------------------------
    // GetStr — read a string property into a caller-supplied buffer
    // -----------------------------------------------------------------------

    internal static int GetStr(
        nint handle, byte* name, int nameLen, byte* buf, int bufLen, int* required)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        try
        {
            var val = elem switch
            {
                ParaElem p  => n == "list_style" ? GetParaListStyle(p) : GetParaStr(p.Para, n),
                RunElem r   => GetRunStr(r.Run, n),
                ImageElem i => GetImageStr(i, n),
                TableElem t => GetTableStr(t.Table, n),
                RowElem row => GetRowStr(row.Row, n),
                CellElem c  => GetCellStr(c.Cell, n),
                StyleElem s => GetStyleStr(s.Style, n),
                SectElem  e => GetSectionStr(e.SectPr, n),
                DocElem d   => GetDocStr(d, n),
                _ => null
            };

            if (val is null) return -1;
            return WriteStr(val, buf, bufLen, required);
        }
        catch { return -1; }
    }

    private static string? GetParaStr(Paragraph para, string name)
    {
        if (name == "text") return string.Concat(para.Descendants<Text>().Select(t => t.Text));

        var pp = para.ParagraphProperties;
        switch (name)
        {
            case "style":
                return pp?.ParagraphStyleId?.Val?.Value ?? "";
            case "alignment":
            {
                var jcVal = pp?.Justification?.Val;
                if (jcVal is null) return "";
                if (jcVal.Value == JustificationValues.Left)   return "left";
                if (jcVal.Value == JustificationValues.Center) return "center";
                if (jcVal.Value == JustificationValues.Right)  return "right";
                if (jcVal.Value == JustificationValues.Both)   return "justify";
                return "";
            }
            case "hr_style":
            {
                var bottom = pp?.ParagraphBorders?.GetFirstChild<BottomBorder>();
                if (bottom is null) return "single";
                var bv = bottom.Val;
                if (bv is null) return "single";
                if (bv.Value == BorderValues.Double) return "double";
                if (bv.Value == BorderValues.Dotted) return "dotted";
                if (bv.Value == BorderValues.Dashed) return "dashed";
                if (bv.Value == BorderValues.Wave)   return "wave";
                return "single";
            }
            case "hr_color":
            {
                var bottom = pp?.ParagraphBorders?.GetFirstChild<BottomBorder>();
                return bottom?.Color?.Value ?? "auto";
            }
            default:
                return null;
        }
    }

    private static string? GetRunStr(Run run, string name)
    {
        var rp = run.RunProperties;
        switch (name)
        {
            case "text":
                return string.Concat(run.Descendants<Text>().Select(t => t.Text));
            case "style":
                return rp?.RunStyle?.Val?.Value ?? "";
            case "font_name":
                return rp?.RunFonts?.Ascii ?? "";
            case "font_name_eastasia":
                return rp?.RunFonts?.EastAsia ?? "";
            case "font_name_complex":
                return rp?.RunFonts?.ComplexScript ?? "";
            case "color":
                return rp?.Color?.Val?.Value ?? "";
            case "language":
                return rp?.Languages?.Val?.Value ?? "";
            case "underline":
            {
                var ulVal = rp?.Underline?.Val;
                if (ulVal is null) return "";
                if (ulVal.Value == UnderlineValues.Single) return "single";
                if (ulVal.Value == UnderlineValues.Double) return "double";
                if (ulVal.Value == UnderlineValues.Dotted) return "dotted";
                if (ulVal.Value == UnderlineValues.Dash)   return "dashed";
                if (ulVal.Value == UnderlineValues.Wave)   return "wave";
                return "";
            }
            default:
                return null;
        }
    }

    private static string? GetTableStr(Table table, string name)
    {
        var tp = table.GetFirstChild<TableProperties>();
        switch (name)
        {
            case "style":
                return tp?.TableStyle?.Val?.Value ?? "";
            case "alignment":
            {
                var tjVal = tp?.TableJustification?.Val;
                if (tjVal is null) return "";
                if (tjVal.Value == TableRowAlignmentValues.Left)   return "left";
                if (tjVal.Value == TableRowAlignmentValues.Center) return "center";
                return tjVal.Value == TableRowAlignmentValues.Right ? "right" : "";
            }
            default:
                return null;
        }
    }

    private static string? GetRowStr(TableRow row, string name)
    {
        return name == "height_rule" ? "auto" : // simplified for v1
            null;
    }

    private static string? GetCellStr(TableCell cell, string name)
    {
        switch (name)
        {
            case "text":
                return string.Concat(cell.Descendants<Text>().Select(t => t.Text));
            case "vertical_alignment":
            {
                var vaVal = cell.TableCellProperties?.TableCellVerticalAlignment?.Val;
                if (vaVal is null) return "top";
                if (vaVal.Value == TableVerticalAlignmentValues.Top)    return "top";
                if (vaVal.Value == TableVerticalAlignmentValues.Center) return "center";
                return vaVal.Value == TableVerticalAlignmentValues.Bottom ? "bottom" : "top";
            }
            default:
                return null;
        }
    }

    private static string? GetDocStr(DocElem d, string name)
    {
        var cp = d.State.Document.PackageProperties;
        return name switch
        {
            "author" => cp.Creator ?? "",
            "title" => cp.Title ?? "",
            "subject" => cp.Subject ?? "",
            "description" => cp.Description ?? "",
            _ => null
        };
    }

    // -----------------------------------------------------------------------
    // SetStr — write a string property
    // -----------------------------------------------------------------------

    internal static int SetStr(
        nint handle, byte* name, int nameLen, byte* value, int valueLen)
    {
        if (!SElements.TryGetValue(handle, out var elem)) return -1;
        var n = ReadStr(name, nameLen);
        var v = ReadStr(value, valueLen);
        try
        {
            return elem switch
            {
                ParaElem p  => n == "list_style" ? SetParaListStyle(p, v) : SetParaStr(p.Para, n, v),
                RunElem r   => SetRunStr(r.Run, n, v),
                ImageElem i => SetImageStr(i, n, v),
                TableElem t => SetTableStr(t.Table, n, v),
                RowElem row => SetRowStr(row.Row, n, v),
                CellElem c  => SetCellStr(c.Cell, n, v),
                StyleElem s => SetStyleStr(s.Style, n, v),
                SectElem  e => SetSectionStr(e.SectPr, n, v),
                DocElem d   => SetDocStr(d, n, v),
                _ => -1
            };
        }
        catch { return -1; }
    }

    private static int SetParaStr(Paragraph para, string name, string value)
    {
        switch (name)
        {
            case "text":
            {
                foreach (var r in para.Elements<Run>().ToList()) r.Remove();
                para.AppendChild(new Run(
                    new Text(value) { Space = SpaceProcessingModeValues.Preserve }));
                return 0;
            }
            case "style":
                para.ParagraphProperties ??= new ParagraphProperties();
                para.ParagraphProperties.ParagraphStyleId = string.IsNullOrEmpty(value)
                    ? null
                    : new ParagraphStyleId { Val = value };
                return 0;
            case "alignment":
            {
                para.ParagraphProperties ??= new ParagraphProperties();
                if (string.IsNullOrEmpty(value))
                {
                    para.ParagraphProperties.Justification = null;
                }
                else
                {
                    JustificationValues? jv = value switch
                    {
                        "left"    => JustificationValues.Left,
                        "center"  => JustificationValues.Center,
                        "right"   => JustificationValues.Right,
                        "justify" => JustificationValues.Both,
                        _         => null
                    };
                    para.ParagraphProperties.Justification = jv.HasValue
                        ? new Justification { Val = jv.Value }
                        : null;
                }
                return 0;
            }
            case "hr_style":
            {
                para.ParagraphProperties ??= new ParagraphProperties();
                var pp = para.ParagraphProperties;
                pp.ParagraphBorders ??= new ParagraphBorders();
                var bottom = pp.ParagraphBorders.GetFirstChild<BottomBorder>()
                             ?? pp.ParagraphBorders.AppendChild(new BottomBorder
                                 { Size = 48U, Space = 1U, Color = "auto" });
                bottom.Val = value switch
                {
                    "double" => BorderValues.Double,
                    "dotted" => BorderValues.Dotted,
                    "dashed" => BorderValues.Dashed,
                    "wave"   => BorderValues.Wave,
                    _        => BorderValues.Single
                };
                return 0;
            }
            case "hr_color":
            {
                para.ParagraphProperties ??= new ParagraphProperties();
                var pp = para.ParagraphProperties;
                pp.ParagraphBorders ??= new ParagraphBorders();
                var bottom = pp.ParagraphBorders.GetFirstChild<BottomBorder>()
                             ?? pp.ParagraphBorders.AppendChild(new BottomBorder
                                 { Val = BorderValues.Single, Size = 48U, Space = 1U });
                bottom.Color = value;
                return 0;
            }
            default:
                return -1;
        }
    }

    private static int SetRunStr(Run run, string name, string value)
    {
        run.RunProperties ??= new RunProperties();
        var rp = run.RunProperties;

        switch (name)
        {
            case "text":
            {
                foreach (var t in run.Elements<Text>().ToList()) t.Remove();
                run.AppendChild(new Text(value) { Space = SpaceProcessingModeValues.Preserve });
                return 0;
            }
            case "style":
                rp.RunStyle = string.IsNullOrEmpty(value) ? null : new RunStyle { Val = value };
                return 0;
            case "font_name":
                rp.RunFonts ??= new RunFonts();
                rp.RunFonts.Ascii = value;
                rp.RunFonts.HighAnsi = value;
                return 0;
            case "font_name_eastasia":
                rp.RunFonts ??= new RunFonts();
                rp.RunFonts.EastAsia = value;
                return 0;
            case "font_name_complex":
                rp.RunFonts ??= new RunFonts();
                rp.RunFonts.ComplexScript = value;
                return 0;
            case "color":
                rp.Color = string.IsNullOrEmpty(value) ? null : new Color { Val = value };
                return 0;
            case "underline":
            {
                if (string.IsNullOrEmpty(value))
                {
                    rp.Underline = null;
                }
                else
                {
                    UnderlineValues? uv = value switch
                    {
                        "single" => UnderlineValues.Single,
                        "double" => UnderlineValues.Double,
                        "dotted" => UnderlineValues.Dotted,
                        "dashed" => UnderlineValues.Dash,
                        "wave"   => UnderlineValues.Wave,
                        _        => null
                    };
                    rp.Underline = uv.HasValue ? new Underline { Val = uv.Value } : null;
                }
                return 0;
            }
            case "language":
                rp.Languages = string.IsNullOrEmpty(value) ? null : new Languages { Val = value };
                return 0;
            default:
                return -1;
        }
    }

    private static int SetTableStr(Table table, string name, string value)
    {
        var tp = table.GetFirstChild<TableProperties>()
            ?? table.PrependChild(new TableProperties());

        switch (name)
        {
            case "style":
                tp.TableStyle = string.IsNullOrEmpty(value) ? null : new TableStyle { Val = value };
                return 0;
            case "alignment":
            {
                TableRowAlignmentValues? tv = value switch
                {
                    "left"   => TableRowAlignmentValues.Left,
                    "center" => TableRowAlignmentValues.Center,
                    "right"  => TableRowAlignmentValues.Right,
                    _        => null
                };
                tp.TableJustification = tv.HasValue
                    ? new TableJustification { Val = tv.Value }
                    : null;
                return 0;
            }
            default:
                return -1;
        }
    }

    private static int SetRowStr(TableRow row, string name, string value) =>
        name switch { _ => -1 };

    private static int SetCellStr(TableCell cell, string name, string value)
    {
        switch (name)
        {
            case "text":
            {
                var para = cell.GetFirstChild<Paragraph>() ?? cell.AppendChild(new Paragraph());
                foreach (var r in para.Elements<Run>().ToList()) r.Remove();
                para.AppendChild(new Run(
                    new Text(value) { Space = SpaceProcessingModeValues.Preserve }));
                return 0;
            }
            case "vertical_alignment":
            {
                cell.TableCellProperties ??= new TableCellProperties();
                TableVerticalAlignmentValues? vv = value switch
                {
                    "top"    => TableVerticalAlignmentValues.Top,
                    "center" => TableVerticalAlignmentValues.Center,
                    "bottom" => TableVerticalAlignmentValues.Bottom,
                    _        => null
                };
                cell.TableCellProperties.TableCellVerticalAlignment = vv.HasValue
                    ? new TableCellVerticalAlignment { Val = vv.Value }
                    : null;
                return 0;
            }
            default:
                return -1;
        }
    }

    private static int SetDocStr(DocElem d, string name, string value)
    {
        var cp = d.State.Document.PackageProperties;
        switch (name)
        {
            case "author":
                cp.Creator     = value; return 0;
            case "title":
                cp.Title       = value; return 0;
            case "subject":
                cp.Subject     = value; return 0;
            case "description":
                cp.Description = value; return 0;
            default:
                return -1;
        }
    }
}
