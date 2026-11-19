"""Release manifest validation and loading."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ReleaseCatalogError(ValueError):
    """An OS release manifest is invalid."""


def default_release_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "catalog" / "releases"


def validate_release_manifest(data: Any, source: str = "<memory>") -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ReleaseCatalogError(f"{source}: release manifest must be an object")
    required = {"schema_version", "os_id", "tag", "channel", "source", "device_family", "device", "installation_model", "validation"}
    missing = sorted(required - data.keys())
    if missing:
        raise ReleaseCatalogError(f"{source}: missing fields: {', '.join(missing)}")
    if data["schema_version"] != 1:
        raise ReleaseCatalogError(f"{source}: unsupported schema_version")
    if not isinstance(data["os_id"], str) or not data["os_id"]:
        raise ReleaseCatalogError(f"{source}: invalid os_id")
    if not isinstance(data["tag"], str) or not data["tag"]:
        raise ReleaseCatalogError(f"{source}: invalid tag")
    if data["channel"] not in {"stable", "legacy", "beta", "nightly"}:
        raise ReleaseCatalogError(f"{source}: invalid channel")
    if not isinstance(data["source"], str) or not data["source"].startswith("https://"):
        raise ReleaseCatalogError(f"{source}: source must be HTTPS")
    if data["installation_model"] not in {"full_image", "delta_update", "rootfs_bundle", "manual"}:
        raise ReleaseCatalogError(f"{source}: invalid installation_model")
    if not isinstance(data["validation"], dict):
        raise ReleaseCatalogError(f"{source}: validation block must be an object")

    assets = data.get("assets")
    asset = data.get("asset")
    if assets is None and asset is None:
        raise ReleaseCatalogError(f"{source}: asset or assets is required")
    asset_list = assets if assets is not None else [asset]
    if not isinstance(asset_list, list) or not asset_list:
        raise ReleaseCatalogError(f"{source}: assets must be a non-empty list")
    for entry in asset_list:
        if not isinstance(entry, dict) or not isinstance(entry.get("filename"), str) or not entry["filename"]:
            raise ReleaseCatalogError(f"{source}: every asset needs a filename")
        digest = entry.get("sha256")
        if digest is not None and (not isinstance(digest, str) or not SHA256.fullmatch(digest)):
            raise ReleaseCatalogError(f"{source}: invalid SHA-256 for {entry['filename']}")
        if digest is None and not entry.get("sha256_policy"):
            raise ReleaseCatalogError(f"{source}: missing checksum policy for {entry['filename']}")
    return data


def load_release_manifests(release_dir: Path | None = None) -> list[dict[str, Any]]:
    directory = release_dir or default_release_dir()
    if not directory.is_dir():
        return []
    manifests: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(directory.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReleaseCatalogError(f"{path}: cannot read JSON: {exc}") from exc
        manifest = validate_release_manifest(data, str(path.relative_to(directory)))
        key = (manifest["os_id"], manifest["tag"])
        if key in seen:
            raise ReleaseCatalogError(f"{path}: duplicate release {key}")
        seen.add(key)
        manifests.append(manifest)
    return manifests
