using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

internal static unsafe partial class DocumentBuilder
{
    private static string? GetSectionStr(SectionProperties sp, string name)
    {
        switch (name)
        {
            case "orientation":
            {
                var orient = sp.GetFirstChild<PageSize>()?.Orient;
                return orient?.Value == PageOrientationValues.Landscape ? "landscape" : "portrait";
            }
            case "start_type":
            {
                var st = sp.GetFirstChild<SectionType>();
                if (st is null) return "newPage";
                var sv = st.Val?.Value;
                if (sv == SectionMarkValues.Continuous) return "continuous";
                if (sv == SectionMarkValues.EvenPage)   return "evenPage";
                if (sv == SectionMarkValues.OddPage)    return "oddPage";
                return "newPage";
            }
            default:
                return null;
        }
    }

    private static int GetSectionInt(SectionProperties sp, string name)
    {
        if (name == "different_first_page")
            return sp.GetFirstChild<TitlePage>() is not null ? 1 : 0;
        return -2;
    }

    private static double GetSectionFloat(SectionProperties sp, string name)
    {
        switch (name)
        {
            case "page_width":
            {
                var w = sp.GetFirstChild<PageSize>()?.Width;
                return w?.HasValue == true ? w.Value / 1440.0 : 8.5;
            }
            case "page_height":
            {
                var h = sp.GetFirstChild<PageSize>()?.Height;
                return h?.HasValue == true ? h.Value / 1440.0 : 11.0;
            }
        }
        var mar = sp.GetFirstChild<PageMargin>();
        return name switch
        {
            "margin_top"    => mar?.Top    is { } t   ? t.Value   / 1440.0 : 1.0,
            "margin_bottom" => mar?.Bottom is { } b   ? b.Value   / 1440.0 : 1.0,
            "margin_left"   => mar?.Left   is { } l   ? l.Value   / 1440.0 : 1.25,
            "margin_right"  => mar?.Right  is { } r   ? r.Value   / 1440.0 : 1.25,
            "margin_header" => mar?.Header is { } hdr ? hdr.Value / 1440.0 : 0.5,
            "margin_footer" => mar?.Footer is { } ftr ? ftr.Value / 1440.0 : 0.5,
            _               => double.NaN
        };
    }

    private static int SetSectionStr(SectionProperties sp, string name, string value)
    {
        switch (name)
        {
            case "orientation":
            {
                var sz = sp.GetFirstChild<PageSize>();
                if (sz is null) { sz = new PageSize(); sp.AppendChild(sz); }
                sz.Orient = value == "landscape"
                    ? PageOrientationValues.Landscape
                    : PageOrientationValues.Portrait;
                return 0;
            }
            case "start_type":
            {
                sp.GetFirstChild<SectionType>()?.Remove();
                SectionMarkValues? sv = value switch
                {
                    "continuous" => (SectionMarkValues?)SectionMarkValues.Continuous,
                    "evenPage"   => SectionMarkValues.EvenPage,
                    "oddPage"    => SectionMarkValues.OddPage,
                    _            => null
                };
                if (sv is not null)
                    sp.AppendChild(new SectionType { Val = sv });
                return 0;
            }
            default:
                return -1;
        }
    }

    private static int SetSectionInt(SectionProperties sp, string name, int value)
    {
        if (name != "different_first_page") return -1;
        sp.GetFirstChild<TitlePage>()?.Remove();
        if (value == 1) sp.AppendChild(new TitlePage());
        return 0;
    }

    private static int SetSectionFloat(SectionProperties sp, string name, double value)
    {
        var twips = (int)Math.Round(value * 1440);
        switch (name)
        {
            case "page_width":
            {
                var sz = sp.GetFirstChild<PageSize>();
                if (sz is null) { sz = new PageSize(); sp.AppendChild(sz); }
                sz.Width = (uint)twips;
                return 0;
            }
            case "page_height":
            {
                var sz = sp.GetFirstChild<PageSize>();
                if (sz is null) { sz = new PageSize(); sp.AppendChild(sz); }
                sz.Height = (uint)twips;
                return 0;
            }
            case "margin_top":
            case "margin_bottom":
            case "margin_left":
            case "margin_right":
            case "margin_header":
            case "margin_footer":
            {
                var mar = sp.GetFirstChild<PageMargin>();
                if (mar is null) { mar = new PageMargin(); sp.AppendChild(mar); }
                switch (name)
                {
                    case "margin_top":    mar.Top    = twips;        break;
                    case "margin_bottom": mar.Bottom = twips;        break;
                    case "margin_left":   mar.Left   = (uint)twips;  break;
                    case "margin_right":  mar.Right  = (uint)twips;  break;
                    case "margin_header": mar.Header = (uint)twips;  break;
                    case "margin_footer": mar.Footer = (uint)twips;  break;
                }
                return 0;
            }
            default:
                return -1;
        }
    }
}
