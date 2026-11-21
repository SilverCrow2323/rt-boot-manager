import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_sgrub_muxapp import ELF64_HEADER, PackageError, verify


README = (
    b"SGRUB preview. This package does not boot another operating system. "
    b"It does not reboot the device. It does not write partitions. "
    b"BOOT HANDOFF is NOT CONNECTED."
)


def make_elf(machine=183, elf_class=2, endian=1, truncate_program_headers=False):
    ident = b"\x7fELF" + bytes([elf_class, endian, 1, 0, 0]) + bytes(7)
    header = ELF64_HEADER.pack(
        ident, 3, machine, 1, 0x400000, ELF64_HEADER.size, 0, 0,
        ELF64_HEADER.size, 56, 1, 64, 0, 0,
    )
    payload = header + (b"\0" * 56)
    return payload[:-8] if truncate_program_headers else payload


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

    def test_rejects_truncated_program_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path, binary=make_elf(truncate_program_headers=True))
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
