import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_sgrub_muxapp import PackageError, verify


README = (
    b"SGRUB preview. This package does not boot another operating system. "
    b"It does not reboot the device. It does not write partitions. "
    b"BOOT HANDOFF is NOT CONNECTED."
)


def make_package(path, readme=README):
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload, mode in (
            ("RTBM-SGRUB/sgrub", b"\x7fELF" + b"\0" * 128, 0o100755),
            ("RTBM-SGRUB/mux_launch.sh", b"#!/bin/sh\nexec ./sgrub\n", 0o100755),
            ("RTBM-SGRUB/README.txt", readme, 0o100644),
        ):
            info = zipfile.ZipInfo(name)
            info.external_attr = mode << 16
            archive.writestr(info, payload)


class SgrubPackageTests(unittest.TestCase):
    def test_accepts_preview_package(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preview.muxapp"
            make_package(path)
            result = verify(str(path))
            self.assertEqual(result["members"], 3)
            self.assertGreater(result["binary_bytes"], 64)

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
