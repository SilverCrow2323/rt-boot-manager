import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_sgrub_muxapp import (
    ELF64_HEADER,
    ELF64_PROGRAM_HEADER,
    PackageError,
    verify,
)


README = (
    b"SGRUB preview. This package does not boot another operating system. "
    b"It does not reboot the device. It does not write partitions. "
    b"BOOT HANDOFF is NOT CONNECTED."
)


def make_elf(
    machine=183,
    elf_class=2,
    endian=1,
    segment_type=1,
    segment_offset=0,
    segment_file_size=None,
    segment_memory_size=None,
    entry=0x400000,
    segment_vaddr=0x400000,
    segment_flags=5,
    segment_align=0x1000,
):
    ident = b"\x7fELF" + bytes([elf_class, endian, 1, 0, 0]) + bytes(7)
    payload_size = ELF64_HEADER.size + ELF64_PROGRAM_HEADER.size
    if segment_file_size is None:
        segment_file_size = payload_size
    if segment_memory_size is None:
        segment_memory_size = segment_file_size
    header = ELF64_HEADER.pack(
        ident, 3, machine, 1, entry, ELF64_HEADER.size, 0, 0,
        ELF64_HEADER.size, ELF64_PROGRAM_HEADER.size, 1, 64, 0, 0,
    )
    program_header = ELF64_PROGRAM_HEADER.pack(
        segment_type, segment_flags, segment_offset, segment_vaddr, segment_vaddr,
        segment_file_size, segment_memory_size, segment_align,
    )
    return header + program_header


def make_package(path, readme=README, binary=None):
    if binary is None:
        binary = make_elf()
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload, mode in (
            ("RTBM-SGRUB/sgrub", binary, 0o100755),
            (
                "RTBM-SGRUB/mux_launch.sh",
                b"#!/bin/sh\nSETUP_APP sgrub modern\nAPP_DIRECTORY=/mnt/SDCARD/MUOS/application/RTBM-SGRUB\n./$APP_BIN --fullscreen\n",
                0o100755,
            ),
            ("RTBM-SGRUB/README.txt", readme, 0o100644),
        ):
            info = zipfile.ZipInfo(name)
            info.external_attr = mode << 16
            archive.writestr(info, payload)


class SgrubPackageTests(unittest.TestCase):
    def test_accepts_aarch64_preview_package(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path)
            result = verify(str(path))
            self.assertEqual(result["members"], 3)
            self.assertEqual(result["architecture"], "AArch64")
            self.assertEqual(result["load_segments"], 1)
            self.assertGreater(result["binary_bytes"], ELF64_HEADER.size)

    def test_rejects_x86_64_elf(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(machine=62))
            with self.assertRaisesRegex(PackageError, "EM_AARCH64"):
                verify(str(path))

    def test_rejects_elf32(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(elf_class=1))
            with self.assertRaisesRegex(PackageError, "ELF64"):
                verify(str(path))

    def test_rejects_big_endian(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(endian=2))
            with self.assertRaisesRegex(PackageError, "little-endian"):
                verify(str(path))

    def test_rejects_no_loadable_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(segment_type=0))
            with self.assertRaisesRegex(PackageError, "no loadable PT_LOAD"):
                verify(str(path))

    def test_rejects_load_segment_outside_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(segment_offset=4096, segment_file_size=16))
            with self.assertRaisesRegex(PackageError, "extends beyond"):
                verify(str(path))

    def test_rejects_file_segment_larger_than_memory_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(segment_file_size=32, segment_memory_size=16))
            with self.assertRaisesRegex(PackageError, "file size exceeds"):
                verify(str(path))

    def test_rejects_entrypoint_outside_executable_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(entry=0x500000))
            with self.assertRaisesRegex(PackageError, "entry point is not inside"):
                verify(str(path))

    def test_rejects_non_executable_entry_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(segment_flags=4))
            with self.assertRaisesRegex(PackageError, "entry point is not inside"):
                verify(str(path))

    def test_rejects_non_power_of_two_load_alignment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(segment_align=24))
            with self.assertRaisesRegex(PackageError, "not a power of two"):
                verify(str(path))

    def test_rejects_incongruent_load_alignment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(segment_offset=1, segment_file_size=1))
            with self.assertRaisesRegex(PackageError, "violate alignment"):
                verify(str(path))

    def test_rejects_truncated_program_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf()[:-8])
            with self.assertRaisesRegex(PackageError, "program header"):
                verify(str(path))

    def test_rejects_missing_safety_notice(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, b"generic app")
            with self.assertRaises(PackageError):
                verify(str(path))

    def test_rejects_extra_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path)
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("RTBM-SGRUB/bootloader.img", b"not allowed")
            with self.assertRaises(PackageError):
                verify(str(path))


if __name__ == "__main__":
    unittest.main()
