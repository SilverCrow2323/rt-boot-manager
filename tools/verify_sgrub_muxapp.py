#!/usr/bin/env python3
"""Verify an RTBM SGRUB .muxapp is safe and contains a loadable ARM64 muOS executable."""

from __future__ import annotations

import argparse
import re
import stat
import struct
import sys
import zipfile
from pathlib import PurePosixPath
from typing import Dict

EXPECTED = {
    "RTBM-SGRUB/sgrub",
    "RTBM-SGRUB/mux_launch.sh",
    "RTBM-SGRUB/README.txt",
}
SAFETY_TEXT = (
    b"does not boot another operating system",
    b"does not reboot the device",
    b"does not write partitions",
    b"NOT CONNECTED",
)
ELF64_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
ELF64_PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
ELFCLASS64 = 2
ELFDATA2LSB = 1
ET_EXEC = 2
ET_DYN = 3
PT_LOAD = 1
PF_X = 1
EM_AARCH64 = 183
ELF64_MAX = (1 << 64) - 1


class PackageError(ValueError):
    """The archive is malformed or violates the preview-only safety contract."""


def verify_arm64_elf(data: bytes) -> Dict[str, int]:
    if len(data) < ELF64_HEADER.size:
        raise PackageError("SGRUB binary is shorter than an ELF64 header")

    (
        ident, elf_type, machine, version, entry, phoff, shoff, _flags,
        ehsize, phentsize, phnum, shentsize, shnum, _shstrndx,
    ) = ELF64_HEADER.unpack_from(data)

    if ident[:4] != b"\x7fELF":
        raise PackageError("SGRUB binary is missing ELF magic")
    if ident[4] != ELFCLASS64:
        raise PackageError("SGRUB must be ELF64; a 32-bit or x86 binary is not valid for H700")
    if ident[5] != ELFDATA2LSB:
        raise PackageError("SGRUB must be little-endian")
    if ident[6] != 1 or version != 1:
        raise PackageError("unsupported ELF version")
    if machine != EM_AARCH64:
        raise PackageError("SGRUB target must be EM_AARCH64 (H700); got machine %d" % machine)
    if elf_type not in {ET_EXEC, ET_DYN}:
        raise PackageError("SGRUB must be an executable ELF or PIE")
    if ehsize < ELF64_HEADER.size or ehsize > len(data):
        raise PackageError("invalid ELF64 header size")
    if entry == 0:
        raise PackageError("ELF entry point is zero")
    if (
        phnum == 0
        or phoff < ehsize
        or phentsize < ELF64_PROGRAM_HEADER.size
        or phoff + phentsize * phnum > len(data)
    ):
        raise PackageError("ELF64 program header table is missing or truncated")

    load_segments = 0
    entry_in_executable_segment = False
    for index in range(phnum):
        offset = phoff + index * phentsize
        p_type, p_flags, p_offset, p_vaddr, _p_paddr, p_filesz, p_memsz, p_align = (
            ELF64_PROGRAM_HEADER.unpack_from(data, offset)
        )
        if p_type != PT_LOAD:
            continue
        load_segments += 1
        if p_filesz > p_memsz:
            raise PackageError("ELF64 PT_LOAD file size exceeds its memory size")
        if p_offset > len(data) or p_filesz > len(data) - p_offset:
            raise PackageError("ELF64 PT_LOAD segment extends beyond the binary")
        if p_vaddr > ELF64_MAX - p_memsz:
            raise PackageError("ELF64 PT_LOAD memory range overflows the address space")
        if p_align > 1:
            if p_align & (p_align - 1):
                raise PackageError("ELF64 PT_LOAD alignment is not a power of two")
            if p_offset % p_align != p_vaddr % p_align:
                raise PackageError("ELF64 PT_LOAD offset and virtual address violate alignment")
        if p_flags & PF_X and p_vaddr <= entry < p_vaddr + p_memsz:
            entry_in_executable_segment = True

    if load_segments == 0:
        raise PackageError("ELF64 has no loadable PT_LOAD segment")
    if not entry_in_executable_segment:
        raise PackageError("ELF entry point is not inside an executable PT_LOAD segment")
    if shnum and (shentsize < 64 or shoff + shentsize * shnum > len(data)):
        raise PackageError("ELF64 section header table is truncated")

    return {
        "elf_bytes": len(data),
        "entry": entry,
        "machine": machine,
        "program_headers": phnum,
        "load_segments": load_segments,
        "type": elf_type,
    }


def verify(path: str) -> Dict[str, object]:
    try:
        archive = zipfile.ZipFile(path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise PackageError("cannot open .muxapp ZIP archive: %s" % exc) from exc

    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise PackageError("duplicate ZIP paths are not allowed")
        file_names = {info.filename for info in infos if not info.is_dir()}
        directory_names = {info.filename for info in infos if info.is_dir()}
        if file_names != EXPECTED or directory_names - {"RTBM-SGRUB/"}:
            missing = sorted(EXPECTED - file_names)
            extra = sorted((file_names - EXPECTED) | (directory_names - {"RTBM-SGRUB/"}))
            raise PackageError("unexpected package contents (missing=%r extra=%r)" % (missing, extra))

        for info in infos:
            name = info.filename
            path_parts = PurePosixPath(name).parts
            if name.startswith("/") or "\\" in name or ".." in path_parts:
                raise PackageError("unsafe archive path: %s" % name)
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise PackageError("symbolic links are not allowed: %s" % name)
            if info.file_size > 16 * 1024 * 1024:
                raise PackageError("unexpectedly large package member: %s" % name)

        if archive.testzip() is not None:
            raise PackageError("ZIP CRC verification failed")

        payload = {name: archive.read(name) for name in EXPECTED}
        binary = payload["RTBM-SGRUB/sgrub"]
        launcher = payload["RTBM-SGRUB/mux_launch.sh"]
        readme = payload["RTBM-SGRUB/README.txt"]
        elf = verify_arm64_elf(binary)

        if not launcher.startswith(b"#!/bin/sh"):
            raise PackageError("muOS launcher must be a POSIX shell script")
        if (
            b"SETUP_APP" not in launcher
            or b"APP_DIRECTORY" not in launcher
            or b"./$APP_BIN" not in launcher
        ):
            raise PackageError("muOS launcher is missing the expected muOS application hand-off")
        missing_safety = [item.decode("ascii") for item in SAFETY_TEXT if item not in readme]
        if missing_safety:
            raise PackageError("preview safety notice is incomplete: %s" % ", ".join(missing_safety))

        by_name = {info.filename: info for info in infos}
        for executable in ("RTBM-SGRUB/sgrub", "RTBM-SGRUB/mux_launch.sh"):
            mode = (by_name[executable].external_attr >> 16) & 0xFFFF
            if not mode & stat.S_IXUSR:
                raise PackageError("executable bit is missing: %s" % executable)

    return {
        "members": len(EXPECTED),
        "binary_bytes": len(binary),
        "launcher_bytes": len(launcher),
        "architecture": "AArch64",
        "elf_entry": elf["entry"],
        "load_segments": elf["load_segments"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="path to rtbm-sgrub.muxapp")
    args = parser.parse_args()
    try:
        result = verify(args.archive)
    except PackageError as exc:
        print("SGRUB package verification: ERROR: %s" % exc, file=sys.stderr)
        return 1
    print(
        "SGRUB package verification: OK (%d members; AArch64 ELF %d bytes; entry 0x%x; %d PT_LOAD segment(s); launcher %d bytes; preview-only safety notice present)"
        % (result["members"], result["binary_bytes"], result["elf_entry"], result["load_segments"], result["launcher_bytes"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
