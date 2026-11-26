import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rtbm.asset_verify import verify_local_asset
from rtbm.releases import ReleaseCatalogError

class LocalAssetVerificationTests(unittest.TestCase):
    def manifest(self, payload):
        return {
            "schema_version": 1, "os_id": "test-os", "tag": "1.2.3",
            "channel": "stable", "source": "https://example.org/releases",
            "device_family": "h700", "device": "rg35xx-h",
            "installation_model": "full_image", "validation": {},
            "asset": {"filename": "image.img.gz", "size_bytes": len(payload),
                      "sha256": hashlib.sha256(payload).hexdigest()}
        }

    def test_verifies_matching_file_and_reports_read_only_result(self):
        payload = b"fixture image payload"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.img.gz"
            path.write_bytes(payload)
            result = verify_local_asset(self.manifest(payload), path.name, path)
        self.assertTrue(result["verified"])
        self.assertFalse(result["writes_performed"])
        self.assertEqual(result["bytes"], len(payload))

    def test_rejects_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.img.gz"
            path.write_bytes(b"tampered")
            with self.assertRaisesRegex(ReleaseCatalogError, "SHA-256 mismatch"):
                verify_local_asset(self.manifest(b"expected"), path.name, path)

    def test_rejects_missing_manifest_checksum(self):
        manifest = self.manifest(b"payload")
        manifest["asset"]["sha256"] = None
        manifest["asset"]["sha256_policy"] = "verify_against_local_sidecar"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.img.gz"
            path.write_bytes(b"payload")
            with self.assertRaisesRegex(ReleaseCatalogError, "remains unverified"):
                verify_local_asset(manifest, path.name, path)

    def test_rejects_undeclared_filename_and_path_traversal(self):
        payload = b"payload"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "image.img.gz"
            path.write_bytes(payload)
            with self.assertRaisesRegex(ReleaseCatalogError, "not declared"):
                verify_local_asset(self.manifest(payload), "other.img.gz", path)
            with self.assertRaisesRegex(ReleaseCatalogError, "plain filename"):
                verify_local_asset(self.manifest(payload), "../image.img.gz", path)

    def test_rejects_symlinked_asset(self):
        payload = b"payload"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.img.gz"; target.write_bytes(payload)
            link = root / "image.img.gz"; link.symlink_to(target)
            with self.assertRaisesRegex(ReleaseCatalogError, "non-symlink"):
                verify_local_asset(self.manifest(payload), link.name, link)

if __name__ == "__main__":
    unittest.main()
