#!/usr/bin/env python3
"""Verify the safety boundary and structure of an RTBM SGRUB .muxapp preview."""

from __future__ import annotations

import argparse
import stat
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


class PackageError(ValueError):
    """The archive is malformed or violates the preview-only safety contract."""


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

        if len(binary) < 64 or not binary.startswith(b"\x7fELF"):
            raise PackageError("sgrub is not a plausible ELF executable")
        if not launcher.startswith(b"#!/bin/sh"):
            raise PackageError("muOS launcher must be a POSIX shell script")
        if b"zip" not in launcher and b"exec" not in launcher:
            raise PackageError("muOS launcher is missing its execution hand-off")
        missing_safety = [item.decode("ascii") for item in SAFETY_TEXT if item not in readme]
        if missing_safety:
            raise PackageError("preview safety notice is incomplete: %s" % ", ".join(missing_safety))

        by_name = {info.filename: info for info in infos}
        for executable in ("RTBM-SGRUB/sgrub", "RTBM-SGRUB/mux_launch.sh"):
            mode = (by_name[executable].external_attr >> 16) & 0xFFFF
            if not mode & stat.S_IXUSR:
                raise PackageError("executable bit is missing: %s" % executable)

    return {"members": len(EXPECTED), "binary_bytes": len(binary), "launcher_bytes": len(launcher)}


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
        "SGRUB package verification: OK (%d members; ELF %d bytes; launcher %d bytes; preview-only safety notice present)"
        % (result["members"], result["binary_bytes"], result["launcher_bytes"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
