using System.Runtime.InteropServices;

namespace NavyFox.Native.Marshalling;

/// <summary>
/// Structs that cross the FFI boundary must carry [StructLayout(LayoutKind.Sequential)]
/// so the CI check_struct_layouts.py script can verify layout stability.
/// </summary>

/// <summary>
/// Error information returned from native calls that need richer diagnostics.
/// Not yet used on the exported API surface — reserved for v0.2.
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public struct NativeError
{
    /// <summary>Numeric error code (0 = success).</summary>
    public int Code;

    /// <summary>
    /// Pointer to a null-terminated UTF-8 error message owned by the native side.
    /// Callers must not free this pointer.
    /// </summary>
    public unsafe byte* Message;
}

/// <summary>
/// A single UTF-8 string slice passed across the FFI boundary.
/// Used to represent one element of a flattened string list.
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public unsafe struct ByteSlice
{
    /// <summary>Pointer to UTF-8 encoded bytes. Not null-terminated.</summary>
    public byte* Data;

    /// <summary>Length of <see cref="Data"/> in bytes.</summary>
    public int Len;
}

/// <summary>
/// Carries font/style options for a paragraph across the FFI boundary.
/// Mirrors the Python-side RunOptions kwargs.
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public struct ParagraphOptions
{
    /// <summary>1 = bold, 0 = not bold.</summary>
    public int Bold;

    /// <summary>1 = italic, 0 = not italic.</summary>
    public int Italic;

    /// <summary>Half-point font size (e.g. 24 = 12pt). 0 = use document default.</summary>
    public int FontSize;
}

/// <summary>
/// Definition of a custom paragraph style passed across the FFI boundary.
/// String fields are UTF-8 byte pointers + lengths; 0/null means "not set".
/// </summary>
[StructLayout(LayoutKind.Sequential)]
public unsafe struct ParagraphStyleDef
{
    // --- identity ---

    /// <summary>Style ID string (e.g. "MyStyle"). Required.</summary>
    public byte* StyleId;
    public int StyleIdLen;

    /// <summary>Style ID of the parent style to inherit from. NULL = no base.</summary>
    public byte* BasedOn;
    public int BasedOnLen;

    // --- run properties ---

    /// <summary>1 = bold, 0 = not set.</summary>
    public int Bold;

    /// <summary>1 = italic, 0 = not set.</summary>
    public int Italic;

    /// <summary>Half-point font size (e.g. 24 = 12pt). 0 = not set.</summary>
    public int FontSize;

    /// <summary>RGB hex color string (e.g. "FF0000"). NULL = not set.</summary>
    public byte* Color;
    public int ColorLen;

    // --- paragraph properties ---

    /// <summary>
    /// Alignment: 0 = not set, 1 = left, 2 = center, 3 = right, 4 = both (justify).
    /// </summary>
    public int Alignment;

    /// <summary>Space before paragraph in twips. 0 = not set.</summary>
    public int SpaceBefore;

    /// <summary>Space after paragraph in twips. 0 = not set.</summary>
    public int SpaceAfter;
}
