using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace NavyFox.Native;

internal static unsafe partial class DocumentBuilder
{
    // -----------------------------------------------------------------------
    // List helpers — list_style / list_level
    // -----------------------------------------------------------------------

    private static string? GetParaListStyle(ParaElem p)
    {
        var numPr = p.Para.ParagraphProperties?.NumberingProperties;
        var numIdVal = numPr?.NumberingId?.Val?.Value;
        if (numIdVal is null or 0) return "";

        if (!SElements.TryGetValue(p.DocHandle, out var docElem) || docElem is not DocElem d)
            return "";

        var numbering = d.State.Document.MainDocumentPart?.NumberingDefinitionsPart?.Numbering;
        if (numbering is null) return "";

        var ilvl = numPr?.NumberingLevelReference?.Val?.Value ?? 0;

        var numInst = numbering.Elements<NumberingInstance>()
            .FirstOrDefault(n => n.NumberID?.Value == numIdVal);
        if (numInst is null) return "";

        var abstractNumIdVal = numInst.AbstractNumId?.Val?.Value;

        var abstractNum = numbering.Elements<AbstractNum>()
            .FirstOrDefault(an => an.AbstractNumberId?.Value == abstractNumIdVal);
        if (abstractNum is null) return "";

        var level = abstractNum.Elements<Level>()
            .FirstOrDefault(l => l.LevelIndex?.Value == ilvl)
            ?? abstractNum.Elements<Level>().FirstOrDefault();
        if (level is null) return "";

        var fmt = level.NumberingFormat?.Val?.Value;
        return fmt == NumberFormatValues.Bullet ? "bullet" : "number";
    }

    private static int SetParaListStyle(ParaElem p, string value)
    {
        var para = p.Para;
        para.ParagraphProperties ??= new ParagraphProperties();
        var pp = para.ParagraphProperties;

        if (string.IsNullOrEmpty(value))
        {
            pp.NumberingProperties = null;
            return 0;
        }

        if (!SElements.TryGetValue(p.DocHandle, out var docElem) || docElem is not DocElem d)
            return -1;

        var fmt = value == "bullet" ? NumberFormatValues.Bullet : NumberFormatValues.Decimal;
        var numId = FindOrCreateNumId(d, fmt);
        if (numId <= 0) return -1;

        var existingLevel = pp.NumberingProperties?.NumberingLevelReference?.Val?.Value ?? 0;
        pp.NumberingProperties = new NumberingProperties(
            new NumberingLevelReference { Val = existingLevel },
            new NumberingId { Val = numId }
        );
        return 0;
    }

    private static int FindOrCreateNumId(DocElem d, NumberFormatValues fmt)
    {
        var mainPart = d.State.Document.MainDocumentPart!;

        var numPart = mainPart.NumberingDefinitionsPart;
        if (numPart is null)
        {
            numPart = mainPart.AddNewPart<NumberingDefinitionsPart>();
            numPart.Numbering = new Numbering();
        }

        var numbering = numPart.Numbering!;

        // Look for existing abstractNum matching the format at level 0
        var abstractNum = numbering.Elements<AbstractNum>()
            .FirstOrDefault(an => an.Elements<Level>()
                .Any(l => l.LevelIndex?.Value == 0 && l.NumberingFormat?.Val?.Value == fmt));

        int abstractNumId;
        if (abstractNum is null)
        {
            abstractNumId = (numbering.Elements<AbstractNum>()
                .Select(an => an.AbstractNumberId?.Value ?? 0)
                .DefaultIfEmpty(-1).Max()) + 1;

            abstractNum = BuildAbstractNum(abstractNumId, fmt);
            var firstNum = numbering.Elements<NumberingInstance>().FirstOrDefault();
            if (firstNum is not null)
                numbering.InsertBefore(abstractNum, firstNum);
            else
                numbering.Append(abstractNum);
        }
        else
        {
            abstractNumId = abstractNum.AbstractNumberId?.Value ?? 0;
        }

        var numInst = numbering.Elements<NumberingInstance>()
            .FirstOrDefault(n => n.AbstractNumId?.Val?.Value == abstractNumId);
        if (numInst is not null)
            return numInst.NumberID?.Value ?? -1;

        var newNumId = (numbering.Elements<NumberingInstance>()
            .Select(n => n.NumberID?.Value ?? 0)
            .DefaultIfEmpty(0).Max()) + 1;

        numInst = new NumberingInstance(new AbstractNumId { Val = abstractNumId })
        {
            NumberID = newNumId
        };
        numbering.Append(numInst);
        return newNumId;
    }

    private static AbstractNum BuildAbstractNum(int id, NumberFormatValues fmt)
    {
        var an = new AbstractNum { AbstractNumberId = id };
        an.AppendChild(new MultiLevelType { Val = MultiLevelValues.HybridMultilevel });

        for (var i = 0; i < 9; i++)
        {
            var level = new Level { LevelIndex = i };
            level.AppendChild(new StartNumberingValue { Val = 1 });
            level.AppendChild(new NumberingFormat { Val = fmt });

            if (fmt == NumberFormatValues.Bullet)
            {
                level.AppendChild(new LevelText { Val = "•" });
                var rp = new RunProperties();
                rp.AppendChild(new RunFonts { Ascii = "Symbol", HighAnsi = "Symbol" });
                level.AppendChild(rp);
            }
            else
            {
                level.AppendChild(new LevelText { Val = $"%{i + 1}." });
            }

            var indent = 720 + i * 720;
            var pp = new ParagraphProperties();
            pp.AppendChild(new Indentation { Left = indent.ToString(), Hanging = "360" });
            level.AppendChild(pp);

            an.AppendChild(level);
        }

        return an;
    }
}
