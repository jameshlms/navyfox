using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using A   = DocumentFormat.OpenXml.Drawing;
using WP  = DocumentFormat.OpenXml.Drawing.Wordprocessing;
using PIC = DocumentFormat.OpenXml.Drawing.Pictures;

namespace NavyFox.Native;

internal static unsafe partial class DocumentBuilder
{
    private const double EmuPerInch = 914400.0;

    // -----------------------------------------------------------------------
    // Helpers — identify image runs and extract relationship IDs
    // -----------------------------------------------------------------------

    internal static bool IsImageRun(Run run) =>
        run.GetFirstChild<Drawing>() is not null;

    internal static string? GetRunImageRelId(Run run) =>
        run.GetFirstChild<Drawing>()
            ?.GetFirstChild<WP.Inline>()
            ?.GetFirstChild<A.Graphic>()
            ?.GetFirstChild<A.GraphicData>()
            ?.GetFirstChild<PIC.Picture>()
            ?.GetFirstChild<PIC.BlipFill>()
            ?.GetFirstChild<A.Blip>()
            ?.Embed?.Value;

    private static WP.Inline? GetInline(ImageElem img) =>
        img.Run.GetFirstChild<Drawing>()?.GetFirstChild<WP.Inline>();

    // -----------------------------------------------------------------------
    // AddImage — attach an inline image run to a paragraph
    // -----------------------------------------------------------------------

    internal static nint AddImage(
        nint paraHandle,
        byte* data, int dataLen,
        byte* contentType, int contentTypeLen,
        int widthEmu, int heightEmu)
    {
        if (!SElements.TryGetValue(paraHandle, out var elem) || elem is not ParaElem p)
            return 0;
        if (!SElements.TryGetValue(p.DocHandle, out var docElem) || docElem is not DocElem d)
            return 0;

        try
        {
            var mainPart = d.State.Document.MainDocumentPart!;
            var ct       = ReadStr(contentType, contentTypeLen);
            var partType = ContentTypeToImagePartType(ct);

            var imagePart = mainPart.AddImagePart(partType);
            var imageBytes = new ReadOnlySpan<byte>(data, dataLen).ToArray();
            using (var stream = imagePart.GetStream())
                stream.Write(imageBytes, 0, imageBytes.Length);

            var relId = mainPart.GetIdOfPart(imagePart);

            long cx, cy;
            if (widthEmu > 0 && heightEmu > 0)
            {
                cx = widthEmu;
                cy = heightEmu;
            }
            else
            {
                (cx, cy) = GetNaturalDimensions(imageBytes, ct);
                if (widthEmu > 0)  cx = widthEmu;
                if (heightEmu > 0) cy = heightEmu;
            }

            var drawingId = (uint)((long)NextHandle() & 0x7FFFFFFF);
            var inline    = BuildInlineDrawing(relId, drawingId, cx, cy);
            var run       = new Run(new Drawing(inline));
            p.Para.AppendChild(run);

            return GetOrCreateImageHandle(run, relId, p.DocHandle);
        }
        catch { return 0; }
    }

    // -----------------------------------------------------------------------
    // GetImageData — read raw image bytes back to caller
    // -----------------------------------------------------------------------

    internal static int GetImageData(nint handle, byte* buf, int bufLen, int* required)
    {
        if (!SElements.TryGetValue(handle, out var elem) || elem is not ImageElem img)
            return -1;
        if (!SElements.TryGetValue(img.DocHandle, out var docElem) || docElem is not DocElem d)
            return -1;

        try
        {
            var mainPart  = d.State.Document.MainDocumentPart!;
            var imagePart = mainPart.GetPartById(img.RelId) as ImagePart;
            if (imagePart is null) return -1;

            using var ms = new MemoryStream();
            using (var stream = imagePart.GetStream())
                stream.CopyTo(ms);

            var length = (int)ms.Length;
            *required = length;
            if (length > bufLen) return 0;
            ms.GetBuffer().AsSpan(0, length).CopyTo(new Span<byte>(buf, length));
            return length;
        }
        catch { return -1; }
    }

    // -----------------------------------------------------------------------
    // Property access for ImageElem
    // -----------------------------------------------------------------------

    internal static double GetImageFloat(ImageElem img, string name)
    {
        if (name is not ("width" or "height")) return double.NaN;
        var inline = GetInline(img);
        if (inline is null) return 0.0;
        var extent = inline.GetFirstChild<WP.Extent>();
        if (extent is null) return 0.0;
        var emu = name == "width" ? (extent.Cx?.Value ?? 0L) : (extent.Cy?.Value ?? 0L);
        return emu / EmuPerInch;
    }

    internal static int SetImageFloat(ImageElem img, string name, double value)
    {
        if (name is not ("width" or "height")) return -1;
        var inline = GetInline(img);
        if (inline is null) return -1;

        var emu = (long)(value * EmuPerInch);

        var extent = inline.GetFirstChild<WP.Extent>();
        if (extent is not null)
        {
            if (name == "width") extent.Cx = emu; else extent.Cy = emu;
        }

        // Keep a:ext in sync
        var extents = inline
            .GetFirstChild<A.Graphic>()
            ?.GetFirstChild<A.GraphicData>()
            ?.GetFirstChild<PIC.Picture>()
            ?.GetFirstChild<PIC.ShapeProperties>()
            ?.GetFirstChild<A.Transform2D>()
            ?.GetFirstChild<A.Extents>();
        if (extents is not null)
        {
            if (name == "width") extents.Cx = emu; else extents.Cy = emu;
        }

        return 0;
    }

    internal static string? GetImageStr(ImageElem img, string name)
    {
        if (name == "alt_text")
        {
            var inline = GetInline(img);
            var docPr  = inline?.GetFirstChild<WP.DocProperties>();
            return docPr?.Description?.Value ?? docPr?.Name?.Value ?? "";
        }

        if (name == "content_type")
        {
            if (!SElements.TryGetValue(img.DocHandle, out var docElem) || docElem is not DocElem d)
                return "";
            try
            {
                var mainPart  = d.State.Document.MainDocumentPart!;
                var imagePart = mainPart.GetPartById(img.RelId) as ImagePart;
                return imagePart?.ContentType ?? "";
            }
            catch { return ""; }
        }

        return null;
    }

    internal static int SetImageStr(ImageElem img, string name, string value)
    {
        if (name == "alt_text")
        {
            var inline = GetInline(img);
            var docPr  = inline?.GetFirstChild<WP.DocProperties>();
            if (docPr is null) return -1;
            docPr.Description = value;
            return 0;
        }
        return -1;
    }

    // -----------------------------------------------------------------------
    // OOXML construction helpers
    // -----------------------------------------------------------------------

    private static WP.Inline BuildInlineDrawing(string relId, uint drawingId, long cx, long cy)
    {
        var nvProps = new PIC.NonVisualPictureProperties(
            new PIC.NonVisualDrawingProperties { Id = drawingId, Name = $"Image{drawingId}" },
            new PIC.NonVisualPictureDrawingProperties());

        var blipFill = new PIC.BlipFill(
            new A.Blip { Embed = relId },
            new A.Stretch(new A.FillRectangle()));

        var spPr = new PIC.ShapeProperties(
            new A.Transform2D(
                new A.Offset { X = 0L, Y = 0L },
                new A.Extents { Cx = cx, Cy = cy }),
            new A.PresetGeometry(new A.AdjustValueList())
            {
                Preset = A.ShapeTypeValues.Rectangle
            });

        var pic = new PIC.Picture(nvProps, blipFill, spPr);

        var graphicData = new A.GraphicData(pic)
        {
            Uri = "http://schemas.openxmlformats.org/drawingml/2006/picture"
        };

        var inline = new WP.Inline(
            new WP.Extent           { Cx = cx, Cy = cy },
            new WP.EffectExtent     { LeftEdge = 0L, TopEdge = 0L, RightEdge = 0L, BottomEdge = 0L },
            new WP.DocProperties    { Id = drawingId, Name = $"Image{drawingId}" },
            new WP.NonVisualGraphicFrameDrawingProperties(
                new A.GraphicFrameLocks { NoChangeAspect = true }),
            new A.Graphic(graphicData))
        {
            DistanceFromTop    = 0U,
            DistanceFromBottom = 0U,
            DistanceFromLeft   = 0U,
            DistanceFromRight  = 0U
        };

        return inline;
    }

    private static PartTypeInfo ContentTypeToImagePartType(string ct)
    {
        if (ct.Equals("image/jpeg", StringComparison.OrdinalIgnoreCase) ||
            ct.Equals("image/jpg",  StringComparison.OrdinalIgnoreCase)) return ImagePartType.Jpeg;
        if (ct.Equals("image/gif",  StringComparison.OrdinalIgnoreCase)) return ImagePartType.Gif;
        if (ct.Equals("image/bmp",  StringComparison.OrdinalIgnoreCase)) return ImagePartType.Bmp;
        if (ct.Equals("image/tiff", StringComparison.OrdinalIgnoreCase) ||
            ct.Equals("image/tif",  StringComparison.OrdinalIgnoreCase)) return ImagePartType.Tiff;
        if (ct.Equals("image/x-emf", StringComparison.OrdinalIgnoreCase)) return ImagePartType.Emf;
        if (ct.Equals("image/x-wmf", StringComparison.OrdinalIgnoreCase)) return ImagePartType.Wmf;
        return ImagePartType.Png;
    }

    // -----------------------------------------------------------------------
    // Natural-size detection from image headers (PNG and JPEG)
    // -----------------------------------------------------------------------

    private static (long cx, long cy) GetNaturalDimensions(byte[] data, string contentType)
    {
        return data.Length switch
        {
            >= 8 when data[0] == 0x89 && data[1] == (byte)'P' => GetPngNaturalSize(data),
            >= 2 when data[0] == 0xFF && data[1] == 0xD8 => GetJpegNaturalSize(data),
            _ => (914400L, 914400L)
        };
    }

    private static (long, long) GetPngNaturalSize(byte[] data)
    {
        if (data.Length < 24) return (914400L, 914400L);

        var w = ((uint)data[16] << 24) | ((uint)data[17] << 16) | ((uint)data[18] << 8) | data[19];
        var h = ((uint)data[20] << 24) | ((uint)data[21] << 16) | ((uint)data[22] << 8) | data[23];
        if (w == 0 || h == 0) return (914400L, 914400L);

        double dpiX = 96.0, dpiY = 96.0;

        // Walk chunks looking for pHYs (must appear before IDAT)
        var pos = 8;
        while (pos + 12 <= data.Length)
        {
            var chunkLen = (int)(((uint)data[pos] << 24) | ((uint)data[pos+1] << 16) |
                                  ((uint)data[pos+2] << 8) | data[pos+3]);
            if (chunkLen < 0) break;

            var isPhys = pos + 8 + chunkLen <= data.Length &&
                          data[pos+4] == (byte)'p' && data[pos+5] == (byte)'H' &&
                          data[pos+6] == (byte)'Y' && data[pos+7] == (byte)'s' &&
                          chunkLen == 9;
            if (isPhys)
            {
                var o = pos + 8;
                var xPpu = ((uint)data[o]   << 24) | ((uint)data[o+1] << 16) |
                             ((uint)data[o+2] <<  8) |  data[o+3];
                var yPpu = ((uint)data[o+4] << 24) | ((uint)data[o+5] << 16) |
                             ((uint)data[o+6] <<  8) |  data[o+7];
                if (data[o+8] == 1 && xPpu > 0 && yPpu > 0)
                {
                    dpiX = xPpu / 39.3701;
                    dpiY = yPpu / 39.3701;
                }
                break;
            }

            // Stop at IDAT — pHYs always precedes it
            if (data[pos+4] == (byte)'I' && data[pos+5] == (byte)'D' &&
                data[pos+6] == (byte)'A' && data[pos+7] == (byte)'T')
                break;

            pos += 12 + chunkLen;
        }

        return ((long)(w * EmuPerInch / dpiX), (long)(h * EmuPerInch / dpiY));
    }

    private static (long, long) GetJpegNaturalSize(byte[] data)
    {
        var dpi = 96.0;
        var pos = 2; // Skip SOI

        while (pos + 4 <= data.Length && data[pos] == 0xFF)
        {
            var marker = data[pos + 1];
            var segLen  = (data[pos + 2] << 8) | data[pos + 3];

            switch (marker)
            {
                // APP0 (JFIF) — check density
                case 0xE0 when segLen >= 14 && pos + 4 + segLen <= data.Length &&
                               data[pos+4]=='J' && data[pos+5]=='F' && data[pos+6]=='I' && data[pos+7]=='F':
                {
                    var unit     = data[pos + 11];
                    var  xDensity = (data[pos + 12] << 8) | data[pos + 13];
                    dpi = unit switch
                    {
                        1 when xDensity > 0 => xDensity,
                        2 when xDensity > 0 => xDensity * 2.54,
                        _ => dpi
                    };
                    break;
                }
                // SOF0/SOF1/SOF2 — image dimensions
                case 0xC0 or 0xC1 or 0xC2 when
                    pos + 9 <= data.Length:
                {
                    var imgH = (data[pos + 5] << 8) | data[pos + 6];
                    var imgW = (data[pos + 7] << 8) | data[pos + 8];
                    if (imgW > 0 && imgH > 0)
                        return ((long)(imgW * EmuPerInch / dpi), (long)(imgH * EmuPerInch / dpi));
                    break;
                }
            }

            pos += 2 + segLen;
        }

        return (914400L, 914400L);
    }
}
