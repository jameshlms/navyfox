using System.Text;

namespace NavyFox.Native.Tests;

/// <summary>Shared helpers used by both SmokeTests and GenericApiTests.</summary>
internal static unsafe class TestHelper
{
    internal static byte[] U(string s) => Encoding.UTF8.GetBytes(s);

    internal static string ReadStr(nint handle, string name)
    {
        var n = U(name);
        var buf = new byte[256];
        int required = 0, written;
        fixed (byte* pN = n, pBuf = buf)
            written = DocumentBuilder.GetStr(handle, pN, n.Length, pBuf, buf.Length, &required);
        return written > 0 ? Encoding.UTF8.GetString(buf, 0, written) : "";
    }

    internal static string ReadType(nint handle)
    {
        var buf = new byte[64];
        int required = 0, written;
        fixed (byte* pBuf = buf)
            written = DocumentBuilder.GetElementType(handle, pBuf, buf.Length, &required);
        return written > 0 ? Encoding.UTF8.GetString(buf, 0, written) : "";
    }

    internal static nint Append(nint parent, string childType)
    {
        var ct = U(childType);
        fixed (byte* p = ct)
            return DocumentBuilder.AppendChild(parent, p, ct.Length);
    }

    internal static int Count(nint handle, string collection)
    {
        var col = U(collection);
        fixed (byte* p = col)
            return DocumentBuilder.GetCount(handle, p, col.Length);
    }

    internal static nint ChildAt(nint handle, string collection, int index)
    {
        var col = U(collection);
        fixed (byte* p = col)
            return DocumentBuilder.GetChildHandle(handle, p, col.Length, index);
    }

    internal static int SetInt(nint handle, string name, int value)
    {
        var n = U(name);
        fixed (byte* p = n)
            return DocumentBuilder.SetInt(handle, p, n.Length, value);
    }

    internal static int GetInt(nint handle, string name)
    {
        var n = U(name);
        fixed (byte* p = n)
            return DocumentBuilder.GetInt(handle, p, n.Length);
    }

    internal static int SetFloat(nint handle, string name, double value)
    {
        var n = U(name);
        fixed (byte* p = n)
            return DocumentBuilder.SetFloat(handle, p, n.Length, value);
    }

    internal static double GetFloat(nint handle, string name)
    {
        var n = U(name);
        fixed (byte* p = n)
            return DocumentBuilder.GetFloat(handle, p, n.Length);
    }

    internal static int SetStr(nint handle, string name, string value)
    {
        var n = U(name);
        var v = U(value);
        fixed (byte* pN = n, pV = v)
            return DocumentBuilder.SetStr(handle, pN, n.Length, pV, v.Length);
    }

    internal static unsafe string SaveToTempFile(nint docHandle)
    {
        var path = Path.GetTempFileName() + ".docx";
        var pathBytes = Encoding.UTF8.GetBytes(path);
        fixed (byte* pPath = pathBytes)
            DocumentBuilder.SaveDocument(docHandle, pPath, pathBytes.Length);
        return path;
    }
}
