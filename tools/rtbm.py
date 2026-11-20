#!/usr/bin/env python3
"""Rt:BOOT MANAGER phase-0 CLI. All commands are read-only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.catalog import CatalogError, get_profile, load_profiles, profile_summary  # noqa: E402
from rtbm.device import probe_device  # noqa: E402
from rtbm.planner import make_plan  # noqa: E402
from rtbm.releases import load_release_history, load_release_manifests  # noqa: E402


def output(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def command_list(_args: argparse.Namespace) -> int:
    profiles = [profile_summary(item) for item in load_profiles()]
    output({"project": "Rt:BOOT MANAGER", "selector": "SGRUB", "profiles": profiles})
    return 0


def command_probe(args: argparse.Namespace) -> int:
    output(probe_device(args.root))
    return 0


def command_validate(_args: argparse.Namespace) -> int:
    profiles = load_profiles()
    releases = load_release_manifests()
    output({
        "valid": True,
        "profile_count": len(profiles),
        "profile_ids": [item["id"] for item in profiles],
        "release_count": len(releases),
        "releases": [f'{item["os_id"]}:{item["tag"]}' for item in releases],
    })
    return 0


def command_releases(args: argparse.Namespace) -> int:
    manifests = load_release_manifests()
    histories = load_release_history()
    if args.os:
        manifests = [item for item in manifests if item["os_id"] == args.os]
        histories = [item for item in histories if item["os_id"] == args.os]
    output({
        "release_manifests": manifests,
        "history_indexes": histories,
        "manifest_count": len(manifests),
        "history_index_count": len(histories),
    })
    return 0


def command_plan(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    device = {
        "device_id": args.device,
        "ram_type": args.ram,
        "panel_revision": args.panel,
    }
    output(make_plan(profile, device))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rtbm",
        description="Rt:BOOT MANAGER phase-0 read-only inventory and dry-run planner.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", help="list OS profile manifests")
    listing.set_defaults(func=command_list)

    probing = sub.add_parser("probe", help="read device-tree and memory information")
    probing.add_argument("--root", default="/", help="alternate root for fixtures/tests")
    probing.set_defaults(func=command_probe)

    validating = sub.add_parser("validate", help="validate local OS profiles")
    validating.set_defaults(func=command_validate)

    releases = sub.add_parser("releases", help="list retained release manifests and history indexes")
    releases.add_argument("--os", choices=["muos", "rocknix", "knulli"])
    releases.set_defaults(func=command_releases)

    planning = sub.add_parser("plan", help="create a non-destructive boot plan")
    planning.add_argument("profile", help="profile id")
    planning.add_argument("--device", default="unknown")
    planning.add_argument("--ram", choices=["ddr3", "ddr4", "unknown"], default="unknown")
    planning.add_argument("--panel", default="unknown")
    planning.add_argument("--dry-run", action="store_true", help="all phase-0 plans are dry-run")
    planning.set_defaults(func=command_plan)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (CatalogError, OSError, ValueError) as exc:
        print(f"rtbm: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
