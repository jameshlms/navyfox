using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

namespace NavyFox.Native;

public static unsafe class NativeExports
{
    // -----------------------------------------------------------------------
    // Document lifecycle
    // -----------------------------------------------------------------------

    [UnmanagedCallersOnly(EntryPoint = "create_document", CallConvs = [typeof(CallConvCdecl)])]
    public static nint CreateDocument() => DocumentBuilder.CreateDocument();

    [UnmanagedCallersOnly(EntryPoint = "open_document", CallConvs = [typeof(CallConvCdecl)])]
    public static nint OpenDocument(byte* path, int pathLen) =>
        DocumentBuilder.OpenDocument(path, pathLen);

    [UnmanagedCallersOnly(EntryPoint = "edit_document", CallConvs = [typeof(CallConvCdecl)])]
    public static nint EditDocument(byte* path, int pathLen) =>
        DocumentBuilder.EditDocument(path, pathLen);

    [UnmanagedCallersOnly(EntryPoint = "save_document", CallConvs = [typeof(CallConvCdecl)])]
    public static int SaveDocument(nint handle, byte* path, int pathLen) =>
        DocumentBuilder.SaveDocument(handle, path, pathLen);

    [UnmanagedCallersOnly(EntryPoint = "dispose", CallConvs = [typeof(CallConvCdecl)])]
    public static void Dispose(nint handle) => DocumentBuilder.Dispose(handle);

    // -----------------------------------------------------------------------
    // Generic property access
    // -----------------------------------------------------------------------

    [UnmanagedCallersOnly(EntryPoint = "get_int", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetInt(nint handle, byte* name, int nameLen) =>
        DocumentBuilder.GetInt(handle, name, nameLen);

    [UnmanagedCallersOnly(EntryPoint = "set_int", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetInt(nint handle, byte* name, int nameLen, int value) =>
        DocumentBuilder.SetInt(handle, name, nameLen, value);

    [UnmanagedCallersOnly(EntryPoint = "get_float", CallConvs = [typeof(CallConvCdecl)])]
    public static double GetFloat(nint handle, byte* name, int nameLen) =>
        DocumentBuilder.GetFloat(handle, name, nameLen);

    [UnmanagedCallersOnly(EntryPoint = "set_float", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetFloat(nint handle, byte* name, int nameLen, double value) =>
        DocumentBuilder.SetFloat(handle, name, nameLen, value);

    [UnmanagedCallersOnly(EntryPoint = "get_str", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetStr(
        nint handle, byte* name, int nameLen, byte* buf, int bufLen, int* required) =>
        DocumentBuilder.GetStr(handle, name, nameLen, buf, bufLen, required);

    [UnmanagedCallersOnly(EntryPoint = "set_str", CallConvs = [typeof(CallConvCdecl)])]
    public static int SetStr(
        nint handle, byte* name, int nameLen, byte* value, int valueLen) =>
        DocumentBuilder.SetStr(handle, name, nameLen, value, valueLen);

    // -----------------------------------------------------------------------
    // Collection operations
    // -----------------------------------------------------------------------

    [UnmanagedCallersOnly(EntryPoint = "get_count", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetCount(nint handle, byte* collection, int collectionLen) =>
        DocumentBuilder.GetCount(handle, collection, collectionLen);

    [UnmanagedCallersOnly(EntryPoint = "get_child_handle", CallConvs = [typeof(CallConvCdecl)])]
    public static nint GetChildHandle(
        nint handle, byte* collection, int collectionLen, int index) =>
        DocumentBuilder.GetChildHandle(handle, collection, collectionLen, index);

    [UnmanagedCallersOnly(EntryPoint = "append_child", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AppendChild(nint handle, byte* childType, int childTypeLen) =>
        DocumentBuilder.AppendChild(handle, childType, childTypeLen);

    [UnmanagedCallersOnly(EntryPoint = "remove_child", CallConvs = [typeof(CallConvCdecl)])]
    public static int RemoveChild(nint handle) => DocumentBuilder.RemoveChild(handle);

    [UnmanagedCallersOnly(EntryPoint = "get_element_type", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetElementType(nint handle, byte* buf, int bufLen, int* required) =>
        DocumentBuilder.GetElementType(handle, buf, bufLen, required);

    // -----------------------------------------------------------------------
    // Table creation — requires rows/cols dimensions
    // -----------------------------------------------------------------------

    [UnmanagedCallersOnly(EntryPoint = "add_table", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddTable(nint docHandle, int rows, int cols) =>
        DocumentBuilder.AddTable(docHandle, rows, cols);

    // -----------------------------------------------------------------------
    // Image creation — requires bytes + dimensions at construction time
    // -----------------------------------------------------------------------

    [UnmanagedCallersOnly(EntryPoint = "add_image", CallConvs = [typeof(CallConvCdecl)])]
    public static nint AddImage(
        nint paraHandle,
        byte* data, int dataLen,
        byte* contentType, int contentTypeLen,
        int widthEmu, int heightEmu) =>
        DocumentBuilder.AddImage(paraHandle, data, dataLen, contentType, contentTypeLen, widthEmu, heightEmu);

    [UnmanagedCallersOnly(EntryPoint = "get_image_data", CallConvs = [typeof(CallConvCdecl)])]
    public static int GetImageData(nint handle, byte* buf, int bufLen, int* required) =>
        DocumentBuilder.GetImageData(handle, buf, bufLen, required);
}
