import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.releases import ReleaseCatalogError, load_release_manifests, validate_release_manifest


class ReleaseManifestTests(unittest.TestCase):
    def test_release_catalog_loads(self):
        releases = load_release_manifests(ROOT / "catalog" / "releases")
        self.assertGreaterEqual(len(releases), 2)
        self.assertEqual({(item["os_id"], item["tag"]) for item in releases},
                         {("rocknix", "20261101"), ("knulli", "20260511")})

    def test_rocknix_has_distinct_ram_assets_and_real_sha256(self):
        releases = load_release_manifests(ROOT / "catalog" / "releases")
        manifest = next(item for item in releases if item["os_id"] == "rocknix")
        self.assertEqual({asset["ram_variant"] for asset in manifest["assets"]}, {"ddr3", "ddr4"})
        self.assertTrue(all(len(asset["sha256"]) == 64 for asset in manifest["assets"]))

    def test_missing_checksum_policy_is_rejected(self):
        manifest = {
            "schema_version": 1,
            "os_id": "example",
            "tag": "1.0",
            "channel": "stable",
            "source": "https://example.com/release",
            "device_family": "h700",
            "device": "test-device",
            "installation_model": "full_image",
            "validation": {},
            "asset": {"filename": "image.img.gz", "sha256": None}
        }
        with self.assertRaises(ReleaseCatalogError):
            validate_release_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
