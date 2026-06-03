using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

internal static partial class DocumentBuilder
{
    // ---------------------------------------------------------------------------
    // Default styles — all use explicit fonts/colors; no theme attributes.
    // ---------------------------------------------------------------------------

    private static readonly string[] HeadingStyleNames =
        ["heading 1", "heading 2", "heading 3", "heading 4", "heading 5", "heading 6"];

    private static readonly int[] HeadingFontSizesHalfPt = [32, 26, 24, 22, 20, 18];

    // -----------------------------------------------------------------------
    // Style property access — get/set for StyleElem handles
    // -----------------------------------------------------------------------

    internal static string? GetStyleStr(Style style, string name)
    {
        switch (name)
        {
            case "style_name":
                return style.StyleName?.Val?.Value ?? "";
            case "style_id":
                return style.StyleId?.Value ?? "";
            case "style_type":
            {
                var sv = style.Type?.Value;
                if (sv == StyleValues.Character) return "character";
                if (sv == StyleValues.Table)     return "table";
                if (sv == StyleValues.Numbering) return "numbering";
                return sv == StyleValues.Paragraph ? "paragraph" : "";
            }
            case "based_on":
                return style.BasedOn?.Val?.Value ?? "";
            case "next_style":
                return style.NextParagraphStyle?.Val?.Value ?? "";
        }

        // Character run properties in <w:rPr>
        var rPr = style.StyleRunProperties;
        switch (name)
        {
            case "font_name":
                return rPr?.RunFonts?.Ascii ?? "";
            case "color":
                return rPr?.Color?.Val?.Value ?? "";
            case "language":
                return rPr?.Languages?.Val?.Value ?? "";
            case "underline":
            {
                var ulVal = rPr?.Underline?.Val;
                if (ulVal is null) return "";
                if (ulVal.Value == UnderlineValues.Single) return "single";
                if (ulVal.Value == UnderlineValues.Double) return "double";
                if (ulVal.Value == UnderlineValues.Dotted) return "dotted";
                if (ulVal.Value == UnderlineValues.Dash)   return "dashed";
                return ulVal.Value == UnderlineValues.Wave ? "wave" : "";
            }
        }

        // Paragraph properties in <w:pPr>
        var pPr = style.StyleParagraphProperties;
        if (name != "alignment") return null;
        var jcVal = pPr?.Justification?.Val;
        if (jcVal is null) return "";
        if (jcVal.Value == JustificationValues.Left)   return "left";
        if (jcVal.Value == JustificationValues.Center) return "center";
        if (jcVal.Value == JustificationValues.Right)  return "right";
        return jcVal.Value == JustificationValues.Both ? "justify" : "";
    }

    internal static int SetStyleStr(Style style, string name, string value)
    {
        switch (name)
        {
            case "style_name":
                style.StyleName = string.IsNullOrEmpty(value) ? null : new StyleName { Val = value };
                return 0;
            case "style_id":
                style.StyleId = value; return 0;
            case "style_type":
            {
                style.Type = value switch
                {
                    "character" => StyleValues.Character,
                    "table" => StyleValues.Table,
                    "numbering" => StyleValues.Numbering,
                    _ => StyleValues.Paragraph
                };
                return 0;
            }
            case "based_on":
                style.BasedOn = string.IsNullOrEmpty(value) ? null : new BasedOn { Val = value };
                return 0;
            case "next_style":
                style.NextParagraphStyle = string.IsNullOrEmpty(value)
                    ? null : new NextParagraphStyle { Val = value };
                return 0;
        }

        // Character run properties
        style.StyleRunProperties ??= new StyleRunProperties();
        var rPr = style.StyleRunProperties;
        switch (name)
        {
            case "font_name":
                rPr.RunFonts ??= new RunFonts();
                rPr.RunFonts.Ascii = value;
                rPr.RunFonts.HighAnsi = value;
                return 0;
            case "color":
                rPr.Color = string.IsNullOrEmpty(value) ? null : new Color { Val = value };
                return 0;
            case "language":
                rPr.Languages = string.IsNullOrEmpty(value) ? null : new Languages { Val = value };
                return 0;
            case "underline" when string.IsNullOrEmpty(value):
                rPr.Underline = null; return 0;
            case "underline":
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
                rPr.Underline = uv.HasValue ? new Underline { Val = uv.Value } : null;
                return 0;
            }
        }

        // Paragraph properties
        style.StyleParagraphProperties ??= new StyleParagraphProperties();
        var pPr = style.StyleParagraphProperties;
        if (name != "alignment") return -1;
        if (string.IsNullOrEmpty(value)) { pPr.Justification = null; return 0; }
        JustificationValues? jv = value switch
        {
            "left"    => JustificationValues.Left,
            "center"  => JustificationValues.Center,
            "right"   => JustificationValues.Right,
            "justify" => JustificationValues.Both,
            _         => null
        };
        pPr.Justification = jv.HasValue ? new Justification { Val = jv.Value } : null;
        return 0;

    }

    internal static int GetStyleInt(Style style, string name)
    {
        if (name == "is_default")
        {
            var def = style.Default;
            return def is not null && (bool)def ? 1 : 0;
        }

        var rPr = style.StyleRunProperties;
        switch (name)
        {
            case "bold":
                return GetOoxmlBool(rPr?.Bold);
            case "italic":
                return GetOoxmlBool(rPr?.Italic);
            case "strikethrough":
                return GetOoxmlBool(rPr?.Strike);
            case "all_caps":
                return GetOoxmlBool(rPr?.Caps);
            case "small_caps":
                return GetOoxmlBool(rPr?.SmallCaps);
            case "hidden":
                return GetOoxmlBool(rPr?.Vanish);
            case "emboss":
                return GetOoxmlBool(rPr?.Emboss);
            case "imprint":
                return GetOoxmlBool(rPr?.Imprint);
            case "outline":
                return GetOoxmlBool(rPr?.Outline);
            case "shadow":
                return GetOoxmlBool(rPr?.Shadow);
            case "superscript":
            {
                var vta = rPr?.VerticalTextAlignment?.Val;
                if (vta is null) return -1;
                return vta.Value == VerticalPositionValues.Superscript ? 1 : 0;
            }
            case "subscript":
            {
                var vta = rPr?.VerticalTextAlignment?.Val;
                if (vta is null) return -1;
                return vta.Value == VerticalPositionValues.Subscript ? 1 : 0;
            }
            default:
                return -2;
        }
    }

    internal static int SetStyleInt(Style style, string name, int value)
    {
        if (name == "is_default")
        {
            style.Default = value == 1 ? (OnOffValue)true : null;
            return 0;
        }
        style.StyleRunProperties ??= new StyleRunProperties();
        var rPr = style.StyleRunProperties;
        switch (name)
        {
            case "bold":
                rPr.Bold = value switch { 1 => new Bold(), 0 => new Bold { Val = false }, _ => null }; return 0;
            case "italic":
                rPr.Italic = value switch { 1 => new Italic(), 0 => new Italic { Val = false }, _ => null }; return 0;
            case "strikethrough":
                rPr.Strike = value switch { 1 => new Strike(), 0 => new Strike { Val = false }, _ => null }; return 0;
            case "all_caps":
                rPr.Caps = value switch { 1 => new Caps(), 0 => new Caps { Val = false }, _ => null }; return 0;
            case "small_caps":
                rPr.SmallCaps = value switch { 1 => new SmallCaps(), 0 => new SmallCaps { Val = false }, _ => null }; return 0;
            case "hidden":
                rPr.Vanish = value switch { 1 => new Vanish(), 0 => new Vanish { Val = false }, _ => null }; return 0;
            case "emboss":
                rPr.Emboss = value switch { 1 => new Emboss(), 0 => new Emboss { Val = false }, _ => null }; return 0;
            case "imprint":
                rPr.Imprint = value switch { 1 => new Imprint(), 0 => new Imprint { Val = false }, _ => null }; return 0;
            case "outline":
                rPr.Outline = value switch { 1 => new Outline(), 0 => new Outline { Val = false }, _ => null }; return 0;
            case "shadow":
                rPr.Shadow = value switch { 1 => new Shadow(), 0 => new Shadow { Val = false }, _ => null }; return 0;
            case "superscript":
                rPr.VerticalTextAlignment = value == 1
                    ? new VerticalTextAlignment { Val = VerticalPositionValues.Superscript } : null;
                return 0;
            case "subscript":
                rPr.VerticalTextAlignment = value == 1
                    ? new VerticalTextAlignment { Val = VerticalPositionValues.Subscript } : null;
                return 0;
            default:
                return -1;
        }
    }

    internal static double GetStyleFloat(Style style, string name)
    {
        if (name == "font_size")
        {
            var sizeStr = style.StyleRunProperties?.FontSize?.Val?.Value;
            if (sizeStr is null) return 0.0;
            return double.TryParse(sizeStr, out var v) ? v / 2.0 : 0.0;
        }
        var pPr = style.StyleParagraphProperties;
        switch (name)
        {
            case "space_before" or "space_after":
            {
                var sbl = pPr?.SpacingBetweenLines;
                var raw = name == "space_before" ? sbl?.Before?.Value : sbl?.After?.Value;
                if (raw is null || !int.TryParse(raw, out var twips)) return 0.0;
                return twips / 20.0;
            }
            case "line_spacing":
            {
                var raw = pPr?.SpacingBetweenLines?.Line?.Value;
                if (raw is null || !int.TryParse(raw, out var val)) return 1.0;
                return val / 240.0;
            }
            case "indent_left" or "indent_right" or "indent_hanging":
            {
                var ind = pPr?.Indentation;
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
            default:
                return double.NaN;
        }
    }

    internal static int SetStyleFloat(Style style, string name, double value)
    {
        if (name == "font_size")
        {
            style.StyleRunProperties ??= new StyleRunProperties();
            var halfPt = (int)Math.Round(value * 2);
            style.StyleRunProperties.FontSize = halfPt > 0
                ? new FontSize { Val = halfPt.ToString() } : null;
            return 0;
        }
        style.StyleParagraphProperties ??= new StyleParagraphProperties();
        var pPr = style.StyleParagraphProperties;
        switch (name)
        {
            case "space_before" or "space_after":
            {
                pPr.SpacingBetweenLines ??= new SpacingBetweenLines();
                var twips = ((int)Math.Round(value * 20)).ToString();
                if (name == "space_before") pPr.SpacingBetweenLines.Before = twips;
                else                        pPr.SpacingBetweenLines.After  = twips;
                return 0;
            }
            case "line_spacing":
                pPr.SpacingBetweenLines ??= new SpacingBetweenLines();
                pPr.SpacingBetweenLines.Line     = ((int)Math.Round(value * 240)).ToString();
                pPr.SpacingBetweenLines.LineRule = LineSpacingRuleValues.Auto;
                return 0;
            case "indent_left" or "indent_right" or "indent_hanging":
            {
                pPr.Indentation ??= new Indentation();
                var twips = ((int)Math.Round(value * 1440)).ToString();
                if      (name == "indent_left")    pPr.Indentation.Left    = twips;
                else if (name == "indent_right")   pPr.Indentation.Right   = twips;
                else                               pPr.Indentation.Hanging = twips;
                return 0;
            }
            default:
                return -1;
        }
    }

    // -----------------------------------------------------------------------
    // Default styles
    // -----------------------------------------------------------------------

    private static void AddDefaultStyles(MainDocumentPart mainPart)
    {
        var stylesPart = mainPart.AddNewPart<StyleDefinitionsPart>();
        var styles = new Styles();

        // Normal — document default; explicit Calibri 11pt.
        styles.AppendChild(new Style(
            new StyleName { Val = "Normal" },
            new PrimaryStyle(),
            new StyleRunProperties(
                new RunFonts { Ascii = "Calibri", HighAnsi = "Calibri" },
                new FontSize { Val = "22" }))
        {
            Type = StyleValues.Paragraph,
            StyleId = "Normal",
            Default = true
        });

        // Title — Calibri Light 28pt.
        styles.AppendChild(new Style(
            new StyleName { Val = "Title" },
            new BasedOn { Val = "Normal" },
            new PrimaryStyle(),
            new StyleRunProperties(
                new RunFonts { Ascii = "Calibri Light", HighAnsi = "Calibri Light" },
                new FontSize { Val = "56" }))
        {
            Type = StyleValues.Paragraph,
            StyleId = "Title"
        });

        // Subtitle — Calibri 12pt italic, muted grey.
        styles.AppendChild(new Style(
            new StyleName { Val = "Subtitle" },
            new BasedOn { Val = "Normal" },
            new PrimaryStyle(),
            new StyleRunProperties(
                new RunFonts { Ascii = "Calibri", HighAnsi = "Calibri" },
                new Italic(),
                new FontSize { Val = "24" },
                new Color { Val = "595959" }))
        {
            Type = StyleValues.Paragraph,
            StyleId = "Subtitle"
        });

        // Headings 1–6 — Calibri Light bold.
        for (var i = 0; i < HeadingStyleNames.Length; i++)
        {
            var level = i + 1;
            styles.AppendChild(new Style(
                new StyleName { Val = HeadingStyleNames[i] },
                new BasedOn { Val = "Normal" },
                new NextParagraphStyle { Val = "Normal" },
                new PrimaryStyle(),
                new StyleRunProperties(
                    new RunFonts { Ascii = "Calibri Light", HighAnsi = "Calibri Light" },
                    new Bold(),
                    new FontSize { Val = HeadingFontSizesHalfPt[i].ToString() }))
            {
                Type = StyleValues.Paragraph,
                StyleId = $"Heading{level}"
            });
        }

        // TableGrid — simple grid table style.
        styles.AppendChild(new Style(
            new StyleName { Val = "Table Grid" },
            new PrimaryStyle())
        {
            Type = StyleValues.Table,
            StyleId = "TableGrid"
        });

        stylesPart.Styles = styles;
    }

}
