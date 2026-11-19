"""Load and validate local OS profiles using only the Python standard library."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,31}$")
VALID_TIERS = {"main", "additional", "research"}
VALID_STATUS = {"supported_upstream", "legacy_upstream", "research_required", "disabled"}
VALID_BOOT_MODES = {
    "native_firmware", "uboot_profile", "muos_user_init",
    "stock_dmenu_handoff", "shared_kernel_rootfs", "legacy_rootfs", "unknown",
}


class CatalogError(ValueError):
    """A profile is missing or violates the local contract."""


def default_catalog_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "catalog" / "os"


def validate_profile(data: Any, source: str = "<memory>") -> dict[str, Any]:
    if not isinstance(data, dict):
        raise CatalogError(f"{source}: profile must be a JSON object")
    required = {"schema_version", "id", "name", "tier", "status", "devices", "release", "boot", "requirements"}
    missing = sorted(required - data.keys())
    if missing:
        raise CatalogError(f"{source}: missing fields: {', '.join(missing)}")
    if data["schema_version"] != 1:
        raise CatalogError(f"{source}: unsupported schema_version")
    if not isinstance(data["id"], str) or not PROFILE_ID.fullmatch(data["id"]):
        raise CatalogError(f"{source}: invalid profile id")
    if not isinstance(data["name"], str) or not data["name"].strip():
        raise CatalogError(f"{source}: empty name")
    if data["tier"] not in VALID_TIERS or data["status"] not in VALID_STATUS:
        raise CatalogError(f"{source}: invalid tier or status")
    if not isinstance(data["devices"], list):
        raise CatalogError(f"{source}: devices must be a list")

    release = data["release"]
    boot = data["boot"]
    requirements = data["requirements"]
    if not isinstance(release, dict) or release.get("channel") not in {"stable", "legacy", "manual"}:
        raise CatalogError(f"{source}: invalid release block")
    if release.get("policy") not in {"follow_latest_compatible", "pinned", "manual"}:
        raise CatalogError(f"{source}: invalid release policy")
    if not isinstance(release.get("source"), str) or not release["source"].startswith("https://"):
        raise CatalogError(f"{source}: release source must be HTTPS")
    if not isinstance(release.get("version_pin_allowed"), bool):
        raise CatalogError(f"{source}: version_pin_allowed must be boolean")

    if not isinstance(boot, dict) or boot.get("mode") not in VALID_BOOT_MODES:
        raise CatalogError(f"{source}: invalid boot block")
    if not isinstance(boot.get("adapter"), str) or not boot["adapter"]:
        raise CatalogError(f"{source}: adapter must be named")
    if boot.get("kernel_model") not in {"own_kernel", "host_kernel", "legacy_launcher", "unknown"}:
        raise CatalogError(f"{source}: invalid kernel model")
    if boot.get("write_capable") is not False:
        raise CatalogError(f"{source}: phase-0 profiles cannot declare write-capable operations")
    if not isinstance(boot.get("artifacts"), list):
        raise CatalogError(f"{source}: artifacts must be a list")

    if not isinstance(requirements, dict):
        raise CatalogError(f"{source}: invalid requirements block")
    for key in ("board", "ram", "panel"):
        if not isinstance(requirements.get(key), list):
            raise CatalogError(f"{source}: requirements.{key} must be a list")
    if not isinstance(requirements.get("minimum_free_bytes"), int) or requirements["minimum_free_bytes"] < 0:
        raise CatalogError(f"{source}: minimum_free_bytes must be non-negative")
    for key in ("dependencies", "warnings"):
        if key in data and not isinstance(data[key], list):
            raise CatalogError(f"{source}: {key} must be a list")
    return data


def load_profiles(catalog_dir: Path | None = None) -> list[dict[str, Any]]:
    directory = catalog_dir or default_catalog_dir()
    if not directory.is_dir():
        raise CatalogError(f"catalogue directory not found: {directory}")
    profiles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CatalogError(f"{path.name}: cannot read JSON: {exc}") from exc
        profile = validate_profile(data, path.name)
        if profile["id"] in seen:
            raise CatalogError(f"{path.name}: duplicate profile id {profile['id']}")
        seen.add(profile["id"])
        profiles.append(profile)
    return profiles


def get_profile(profile_id: str, catalog_dir: Path | None = None) -> dict[str, Any]:
    for profile in load_profiles(catalog_dir):
        if profile["id"] == profile_id:
            return profile
    raise CatalogError(f"unknown OS profile: {profile_id}")


def profile_summary(profile: dict[str, Any]) -> dict[str, str]:
    return {
        "id": profile["id"],
        "name": profile["name"],
        "tier": profile["tier"],
        "status": profile["status"],
        "version": str(profile["release"].get("known_version") or "unresolved"),
        "boot_mode": profile["boot"]["mode"],
        "adapter": profile["boot"]["adapter"],
    }
