#!/usr/bin/env python3
"""Generate native SGRUB profile and release tables from canonical JSON catalogues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.catalog import load_profiles  # noqa: E402
from rtbm.releases import load_release_history, load_release_manifests  # noqa: E402

MAIN_ORDER = ("muos", "rocknix", "knulli")
BOOT_LABELS = {
    "native_firmware": "NATIVE FIRMWARE",
    "uboot_profile": "UBOOT PROFILE",
    "muos_user_init": "MUOS USER INIT",
    "stock_dmenu_handoff": "STOCK DMENU",
    "shared_kernel_rootfs": "SHARED KERNEL",
    "legacy_rootfs": "LEGACY ROOTFS",
    "unknown": "UNKNOWN",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def c_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def release_records(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in profiles}
    manifests = load_release_manifests()
    histories = {item["os_id"]: item for item in load_release_history()}
    output: list[dict[str, Any]] = []

    for os_id in MAIN_ORDER:
        profile = by_id.get(os_id)
        if profile is None:
            continue
        known_version = str(profile["release"].get("known_version") or "")
        boot = profile["boot"]
        history = histories.get(os_id)

        if history:
            current = history["current"]
            output.append({
                "os_id": os_id,
                "tag": current["tag"],
                "label": current.get("name", current["tag"]),
                "channel": str(current.get("channel", "stable")).upper(),
                "verification": "BASELINE ONLY",
                "assets": "MUOS IMAGE",
                "is_current": True,
                "checksum_available": False,
                "requires_known_ram": bool(boot.get("requires_known_ram")),
                "requires_dtb": bool(boot.get("requires_dtb")),
            })
            for item in history.get("archived", []):
                output.append({
                    "os_id": os_id,
                    "tag": item["tag"],
                    "label": item.get("name", item["tag"]),
                    "channel": "LEGACY",
                    "verification": "ARCHIVE ONLY",
                    "assets": "PROVIDER LINK",
                    "is_current": False,
                    "checksum_available": False,
                    "requires_known_ram": bool(boot.get("requires_known_ram")),
                    "requires_dtb": bool(boot.get("requires_dtb")),
                })

        os_manifests = [item for item in manifests if item["os_id"] == os_id]
        os_manifests.sort(key=lambda item: str(item.get("published_at", item["tag"])), reverse=True)
        for manifest in os_manifests:
            asset_items = manifest.get("assets") or [manifest.get("asset", {})]
            digests = [asset.get("sha256") for asset in asset_items]
            checksum_available = bool(digests) and all(
                isinstance(digest, str) and SHA256.fullmatch(digest)
                for digest in digests
            )
            ram_variants = sorted({
                str(asset.get("ram_variant")).upper()
                for asset in asset_items
                if asset.get("ram_variant") in {"ddr3", "ddr4"}
            })
            if len(ram_variants) == 2:
                asset_label = "DDR3 OR DDR4"
            elif ram_variants:
                asset_label = " / ".join(ram_variants)
            elif os_id == "knulli":
                asset_label = "KNULLI BSP"
            else:
                asset_label = "GENERIC H700"
            label = str(manifest.get("name") or manifest["tag"])
            if label.startswith("KNULLI "):
                label = label[len("KNULLI "):]
            output.append({
                "os_id": os_id,
                "tag": manifest["tag"],
                "label": label,
                "channel": str(manifest["channel"]).upper(),
                "verification": "SHA256 AVAILABLE" if checksum_available else "VERIFY SHA256",
                "assets": asset_label,
                "is_current": manifest["tag"] in known_version,
                "checksum_available": checksum_available,
                "requires_known_ram": bool(boot.get("requires_known_ram")) or bool(ram_variants),
                "requires_dtb": bool(boot.get("requires_dtb")) or bool(manifest.get("validation", {}).get("dtb_match_required")),
            })

    if not output:
        raise SystemExit("SGRUB release table would be empty")
    return output


def render() -> str:
    profiles = load_profiles()
    by_id = {item["id"]: item for item in profiles}
    visible_ids = [
        profile_id
        for profile_id in MAIN_ORDER
        if profile_id in by_id and by_id[profile_id]["status"] != "disabled"
    ]
    if not visible_ids:
        raise SystemExit("SGRUB profile table would be empty")

    profile_rows: list[str] = []
    for profile_id in visible_ids:
        item = by_id[profile_id]
        boot = item["boot"]
        version = str(item["release"].get("known_version") or "UNRESOLVED")
        profile_rows.append(
            "    {"
            + ", ".join((
                c_string(item["id"]),
                c_string(item["name"]),
                c_string(version),
                c_string(item["status"]),
                c_string(BOOT_LABELS.get(boot["mode"], "UNKNOWN")),
                "true" if boot.get("requires_known_ram") else "false",
                "true" if boot.get("requires_dtb") else "false",
            ))
            + "},"
        )

    release_rows: list[str] = []
    for item in release_records(profiles):
        release_rows.append(
            "    {"
            + ", ".join((
                c_string(item["os_id"]),
                c_string(item["tag"]),
                c_string(item["label"]),
                c_string(item["channel"]),
                c_string(item["verification"]),
                c_string(item["assets"]),
                "true" if item["is_current"] else "false",
                "true" if item["checksum_available"] else "false",
                "true" if item["requires_known_ram"] else "false",
                "true" if item["requires_dtb"] else "false",
            ))
            + "},"
        )

    return (
        "/* Generated by tools/generate_sgrub_profiles.py; do not edit by hand. */\n"
        "#ifndef RTBM_SGRUB_PROFILES_GENERATED_H\n"
        "#define RTBM_SGRUB_PROFILES_GENERATED_H\n\n"
        "static const SgrubProfile SGRUB_PROFILES[] = {\n"
        + "\n".join(profile_rows)
        + "\n};\n"
        "#define SGRUB_PROFILE_COUNT (sizeof(SGRUB_PROFILES) / sizeof(SGRUB_PROFILES[0]))\n\n"
        "static const SgrubRelease SGRUB_RELEASES[] = {\n"
        + "\n".join(release_rows)
        + "\n};\n"
        "#define SGRUB_RELEASE_COUNT (sizeof(SGRUB_RELEASES) / sizeof(SGRUB_RELEASES[0]))\n\n"
        "#endif\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "ui/sgrub/native/profiles.generated.h",
        help="generated C header path",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed header differs from the catalogues",
    )
    args = parser.parse_args()
    expected = render()

    if args.check:
        try:
            actual = args.output.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"missing generated SGRUB header: {exc}", file=sys.stderr)
            return 1
        if actual != expected:
            print(f"{args.output} is stale; run tools/generate_sgrub_profiles.py", file=sys.stderr)
            return 1
        print("SGRUB native profile and release tables are up to date")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8")
    print(f"generated {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
