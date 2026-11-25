"""Release manifest validation and loading."""

from __future__ import annotations

import json
import re
from urllib.parse import urlsplit
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ReleaseCatalogError(ValueError):
    """An OS release manifest is invalid."""


class DuplicateJSONKeyError(ValueError):
    """A JSON object contains the same key more than once."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _strict_json_loads(text: str) -> Any:
    """Parse JSON without accepting ambiguous duplicate keys at any depth."""
    return json.loads(text, object_pairs_hook=_unique_object)


def default_release_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "catalog" / "releases"


def _validate_https_url(value: Any, source: str, label: str) -> None:
    if not isinstance(value, str) or not value or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise ReleaseCatalogError(f"{source}: {label} must be a valid HTTPS URL")
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError as exc:
        raise ReleaseCatalogError(f"{source}: invalid {label}: {exc}") from exc
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ReleaseCatalogError(f"{source}: {label} must use HTTPS without embedded credentials")


def _validate_release_tag(value: Any, source: str, label: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}", value):
        raise ReleaseCatalogError(f"{source}: invalid {label}")


def _validate_asset_filename(value: Any, source: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or value in {".", ".."}
        or "/" in value
        or chr(92) in value
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)
    ):
        raise ReleaseCatalogError(f"{source}: asset filename must be a plain filename without path components")
    return value


def validate_release_manifest(data: Any, source: str = "<memory>") -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ReleaseCatalogError(f"{source}: release manifest must be an object")
    required = {"schema_version", "os_id", "tag", "channel", "source", "device_family", "device", "installation_model", "validation"}
    missing = sorted(required - data.keys())
    if missing:
        raise ReleaseCatalogError(f"{source}: missing fields: {', '.join(missing)}")
    if isinstance(data["schema_version"], bool) or not isinstance(data["schema_version"], int) or data["schema_version"] != 1:
        raise ReleaseCatalogError(f"{source}: unsupported schema_version")
    if not isinstance(data["os_id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,31}", data["os_id"]):
        raise ReleaseCatalogError(f"{source}: invalid os_id")
    _validate_release_tag(data["tag"], source, "release tag")
    if not isinstance(data["channel"], str) or data["channel"] not in {"stable", "legacy", "beta", "nightly"}:
        raise ReleaseCatalogError(f"{source}: invalid channel")
    _validate_https_url(data["source"], source, "source")
    for field in ("device_family", "device"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ReleaseCatalogError(f"{source}: invalid {field}")
    if not isinstance(data["installation_model"], str) or data["installation_model"] not in {"full_image", "delta_update", "rootfs_bundle", "manual"}:
        raise ReleaseCatalogError(f"{source}: invalid installation_model")
    if not isinstance(data["validation"], dict):
        raise ReleaseCatalogError(f"{source}: validation block must be an object")

    assets = data.get("assets")
    asset = data.get("asset")
    if assets is not None and asset is not None:
        raise ReleaseCatalogError(f"{source}: use either asset or assets, not both")
    if assets is None and asset is None:
        raise ReleaseCatalogError(f"{source}: asset or assets is required")
    asset_list = assets if assets is not None else [asset]
    if not isinstance(asset_list, list) or not asset_list:
        raise ReleaseCatalogError(f"{source}: assets must be a non-empty list")

    seen_filenames: set[str] = set()
    for entry in asset_list:
        if not isinstance(entry, dict):
            raise ReleaseCatalogError(f"{source}: every asset must be an object")
        filename = _validate_asset_filename(entry.get("filename"), source)
        filename_key = filename.casefold()
        if filename_key in seen_filenames:
            raise ReleaseCatalogError(f"{source}: duplicate asset filename: {filename}")
        seen_filenames.add(filename_key)

        if "url" in entry:
            _validate_https_url(entry["url"], source, f"asset URL for {filename}")
        if "size_bytes" in entry and (
            isinstance(entry["size_bytes"], bool)
            or not isinstance(entry["size_bytes"], int)
            or entry["size_bytes"] <= 0
        ):
            raise ReleaseCatalogError(f"{source}: invalid size_bytes for {filename}")

        digest = entry.get("sha256")
        if digest is not None and (not isinstance(digest, str) or not SHA256.fullmatch(digest)):
            raise ReleaseCatalogError(f"{source}: invalid SHA-256 for {filename}")
        if digest is None and (
            not isinstance(entry.get("sha256_policy"), str)
            or not entry["sha256_policy"].strip()
        ):
            raise ReleaseCatalogError(f"{source}: missing checksum policy for {filename}")
    return data

def default_history_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "catalog" / "release-history"


def load_release_history(history_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load provider-indexed release history that is not yet an installable manifest."""
    directory = history_dir or default_history_dir()
    if not directory.is_dir():
        return []
    histories: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(directory.rglob("*.json")):
        try:
            data = _strict_json_loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, DuplicateJSONKeyError) as exc:
            raise ReleaseCatalogError(f"{path}: cannot read history JSON: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ReleaseCatalogError(f"{path}: invalid release history schema")
        os_id = data.get("os_id")
        if not isinstance(os_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,31}", os_id) or os_id in seen:
            raise ReleaseCatalogError(f"{path}: invalid or duplicate history os_id")
        _validate_https_url(data.get("source"), str(path), "history source")
        current = data.get("current")
        archived = data.get("archived")
        if not isinstance(current, dict):
            raise ReleaseCatalogError(f"{path}: history needs a current release tag")
        _validate_release_tag(current.get("tag"), str(path), "current release tag")
        if not isinstance(archived, list):
            raise ReleaseCatalogError(f"{path}: archived releases must be a list")
        tags = {current["tag"]}
        for entry in archived:
            if not isinstance(entry, dict):
                raise ReleaseCatalogError(f"{path}: archived release entry must be an object")
            tag = entry.get("tag")
            page = entry.get("release_page")
            _validate_release_tag(tag, str(path), "archived release tag")
            if tag in tags:
                raise ReleaseCatalogError(f"{path}: invalid or duplicate archived release tag")
            _validate_https_url(page, str(path), "archived release page")
            if entry.get("sha256") is not None and (
                not isinstance(entry["sha256"], str) or not SHA256.fullmatch(entry["sha256"])
            ):
                raise ReleaseCatalogError(f"{path}: invalid archived release SHA-256")
            tags.add(tag)
        seen.add(os_id)
        histories.append(data)
    return histories


def load_release_manifests(release_dir: Path | None = None) -> list[dict[str, Any]]:
    directory = release_dir or default_release_dir()
    if not directory.is_dir():
        return []
    manifests: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(directory.rglob("*.json")):
        try:
            data = _strict_json_loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, DuplicateJSONKeyError) as exc:
            raise ReleaseCatalogError(f"{path}: cannot read JSON: {exc}") from exc
        manifest = validate_release_manifest(data, str(path.relative_to(directory)))
        key = (manifest["os_id"], manifest["tag"])
        if key in seen:
            raise ReleaseCatalogError(f"{path}: duplicate release {key}")
        seen.add(key)
        manifests.append(manifest)
    return manifests
