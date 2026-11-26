"""Verify a user-provided release image against pinned local manifest metadata."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any
from .releases import ReleaseCatalogError, validate_release_manifest

def verify_local_asset(manifest: dict[str, Any], filename: str, file_path: Path) -> dict[str, Any]:
    validate_release_manifest(manifest)
    if not isinstance(filename, str) or not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise ReleaseCatalogError("Asset filename must be a plain filename")
    assets = manifest.get("assets")
    entries = assets if assets is not None else [manifest.get("asset")]
    asset = next((item for item in entries if item.get("filename") == filename), None)
    if asset is None:
        raise ReleaseCatalogError(f"{filename}: not declared by this release manifest")
    path = Path(file_path)
    if path.is_symlink() or not path.is_file():
        raise ReleaseCatalogError("Local asset must be a regular, non-symlink file")
    expected = asset.get("sha256")
    if not expected:
        raise ReleaseCatalogError(f"{filename}: manifest has no verified SHA-256; this asset remains unverified")
    size = path.stat().st_size
    expected_size = asset.get("size_bytes")
    if expected_size is not None and size != expected_size:
        raise ReleaseCatalogError(f"{filename}: size mismatch (expected {expected_size}, got {size})")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:
        raise ReleaseCatalogError(f"{filename}: SHA-256 mismatch (expected {expected}, got {actual})")
    return {"verified": True, "os_id": manifest["os_id"], "tag": manifest["tag"],
            "filename": filename, "bytes": size, "sha256": actual,
            "source": manifest["source"], "writes_performed": False}
