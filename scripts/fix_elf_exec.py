#!/usr/bin/env python3
"""
Fix two linker bugs in .NET AOT linux-x64 NativeLib=Shared ELF output:

Bug 1 – Non-executable init segment:
  The linker places .init and .plt in a LOAD segment without the execute bit
  (PF_X).  The dynamic linker maps it RW-only, so when it calls DT_INIT the
  page is non-executable and the process faults with SIGSEGV (SEGV_ACCERR).

Bug 2 – Wrong DT_INIT value:
  The .dynamic section's DT_INIT entry contains a vaddr (0x25c) that points
  into the ELF program-header table rather than to the actual .init section
  (at vaddr 0x2468028).  The dynamic linker jumps to the wrong address and
  immediately crashes executing ELF header bytes as x86-64 instructions.

This script reads section headers to locate the true .init vaddr, then:
  • Patches any LOAD segment that contains executable sections but lacks PF_X.
  • Patches the DT_INIT dynamic entry to the correct .init vaddr.

Usage: python3 fix_elf_exec.py <path/to/NavyFox.Native.so>
"""
import struct
import sys
from pathlib import Path

PT_LOAD = 1
PT_DYNAMIC = 2
PF_X, PF_W, PF_R = 1, 2, 4
SHT_PROGBITS = 1
SHT_STRTAB = 3
SHF_EXECINSTR = 4
DT_NULL = 0
DT_INIT = 0xC


def _read_section_strtab(data: bytearray, e_shstrndx: int, e_shoff: int, e_shentsize: int) -> bytes:
    off = e_shoff + e_shstrndx * e_shentsize
    (sh_offset,) = struct.unpack_from("<Q", data, off + 24)
    (sh_size,) = struct.unpack_from("<Q", data, off + 32)
    return bytes(data[sh_offset : sh_offset + sh_size])


def fix_elf(path: str) -> int:
    data = bytearray(Path(path).read_bytes())

    assert data[:4] == b"\x7fELF", f"{path}: not an ELF file"
    assert data[4] == 2, f"{path}: not a 64-bit ELF"
    assert data[5] == 1, f"{path}: not little-endian"

    (e_phoff,) = struct.unpack_from("<Q", data, 0x20)
    (e_shoff,) = struct.unpack_from("<Q", data, 0x28)
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x36)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x3A)

    # --- Find the vaddr of the .init section via section headers ---
    strtab = _read_section_strtab(data, e_shstrndx, e_shoff, e_shentsize)
    init_vaddr: int | None = None
    exec_ranges: list[tuple[int, int]] = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        (sh_name,) = struct.unpack_from("<I", data, off)
        sh_type, = struct.unpack_from("<I", data, off + 4)
        (sh_flags,) = struct.unpack_from("<Q", data, off + 8)
        (sh_addr,) = struct.unpack_from("<Q", data, off + 16)
        (sh_size,) = struct.unpack_from("<Q", data, off + 32)

        name = strtab[sh_name : strtab.index(b"\x00", sh_name)].decode()
        if name == ".init" and sh_type == SHT_PROGBITS:
            init_vaddr = sh_addr

        if sh_type == SHT_PROGBITS and (sh_flags & SHF_EXECINSTR) and sh_size > 0:
            exec_ranges.append((sh_addr, sh_addr + sh_size))

    fixed = 0

    # --- Bug 1: Patch LOAD segments that contain executable sections but lack PF_X ---
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        (p_type,) = struct.unpack_from("<I", data, off)
        (p_flags,) = struct.unpack_from("<I", data, off + 4)
        (p_vaddr,) = struct.unpack_from("<Q", data, off + 16)
        (p_memsz,) = struct.unpack_from("<Q", data, off + 40)

        if p_type != PT_LOAD or (p_flags & PF_X):
            continue

        seg_end = p_vaddr + p_memsz
        if not any(sh_start < seg_end and sh_end > p_vaddr for sh_start, sh_end in exec_ranges):
            continue

        new_flags = p_flags | PF_X
        struct.pack_into("<I", data, off + 4, new_flags)
        old_str = "".join(c for c, b in zip("RWX", [PF_R, PF_W, PF_X]) if p_flags & b)
        new_str = "".join(c for c, b in zip("RWX", [PF_R, PF_W, PF_X]) if new_flags & b)
        print(f"  phdr[{i}]: vaddr=0x{p_vaddr:x} flags {old_str} -> {new_str}  [exec-segment fix]")
        fixed += 1

    # --- Bug 2: Patch DT_INIT to point to the actual .init vaddr ---
    if init_vaddr is not None:
        # Locate PT_DYNAMIC segment to find the .dynamic section in the file
        for i in range(e_phnum):
            off = e_phoff + i * e_phentsize
            (p_type,) = struct.unpack_from("<I", data, off)
            if p_type != PT_DYNAMIC:
                continue
            (p_offset,) = struct.unpack_from("<Q", data, off + 8)
            (p_filesz,) = struct.unpack_from("<Q", data, off + 32)

            # Walk dynamic entries (each is two 8-byte words: tag, val)
            dyn_off = p_offset
            while dyn_off < p_offset + p_filesz:
                (d_tag,) = struct.unpack_from("<Q", data, dyn_off)
                (d_val,) = struct.unpack_from("<Q", data, dyn_off + 8)
                if d_tag == DT_NULL:
                    break
                if d_tag == DT_INIT and d_val != init_vaddr:
                    struct.pack_into("<Q", data, dyn_off + 8, init_vaddr)
                    print(
                        f"  DT_INIT: 0x{d_val:x} -> 0x{init_vaddr:x}  [DT_INIT fix]"
                    )
                    fixed += 1
                dyn_off += 16
            break

    if fixed:
        Path(path).write_bytes(data)
    return fixed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <elf-file> [...]")
        sys.exit(1)

    total = 0
    for arg in sys.argv[1:]:
        print(f"Checking {arg}")
        n = fix_elf(arg)
        if n:
            print(f"  -> patched {n} fix(es)")
        else:
            print("  -> no fixup needed")
        total += n

    sys.exit(0 if total >= 0 else 1)
