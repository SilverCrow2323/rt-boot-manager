import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.releases import ReleaseCatalogError, load_release_history, load_release_manifests, validate_release_manifest

class ReleaseManifestTests(unittest.TestCase):
    def test_release_catalog_loads_all_verified_and_legacy_manifests(self):
        releases = load_release_manifests(ROOT / "catalog" / "releases")
        expected = {
            ("rocknix", "20261101"), ("rocknix", "20261001"),
            ("rocknix", "20260901"), ("rocknix", "20260801"),
            ("rocknix", "20260701"), ("rocknix", "20260601"),
            ("knulli", "20260511"), ("knulli", "20250813"),
            ("knulli", "20250505"), ("knulli", "20241204"),
            ("knulli", "20240721"),
        }
        self.assertEqual({(item["os_id"], item["tag"]) for item in releases}, expected)

    def test_rocknix_latest_has_distinct_ram_assets_and_real_sha256(self):
        releases = load_release_manifests(ROOT / "catalog" / "releases")
        manifest = next(item for item in releases if item["os_id"] == "rocknix" and item["tag"] == "20261101")
        self.assertEqual({asset["ram_variant"] for asset in manifest["assets"]}, {"ddr3", "ddr4"})
        self.assertTrue(all(len(asset["sha256"]) == 64 for asset in manifest["assets"]))

    def test_historical_rocknix_assets_keep_release_specific_checksums(self):
        releases = load_release_manifests(ROOT / "catalog" / "releases")
        historical = [item for item in releases if item["os_id"] == "rocknix" and item["tag"] != "20261101"]
        self.assertEqual(len(historical), 5)
        for manifest in historical:
            self.assertTrue(all(len(asset["sha256"]) == 64 for asset in manifest["assets"]))
            self.assertTrue(manifest["validation"]["dtb_match_required"])

    def test_legacy_knulli_images_require_local_checksum_verification(self):
        releases = load_release_manifests(ROOT / "catalog" / "releases")
        legacy = [item for item in releases if item["os_id"] == "knulli" and item["channel"] == "legacy"]
        self.assertEqual(len(legacy), 4)
        for manifest in legacy:
            self.assertIsNone(manifest["asset"]["sha256"])
            self.assertIn("sha256_policy", manifest["asset"])
            self.assertTrue(manifest["validation"]["hardware_revision_required"])

    def test_muos_archive_is_history_only_until_provider_asset_is_resolved(self):
        history = json.loads((ROOT / "catalog" / "release-history" / "muos.json").read_text())
        self.assertEqual(history["current"]["tag"], "2606.0")
        self.assertEqual(len(history["archived"]), 15)
        self.assertTrue(all(item["sha256"] is None for item in history["archived"]))
        self.assertTrue(all(item["asset_state"] == "provider_download_not_yet_resolved" for item in history["archived"]))

    def test_history_indexes_load_and_are_kept_separate_from_install_manifests(self):
        histories = load_release_history(ROOT / "catalog" / "release-history")
        self.assertEqual([item["os_id"] for item in histories], ["muos"])
        self.assertEqual(histories[0]["current"]["tag"], "2606.0")
        manifests = load_release_manifests(ROOT / "catalog" / "releases")
        self.assertFalse(any(item["os_id"] == "muos" for item in manifests))

    def test_missing_checksum_policy_is_rejected(self):
        manifest = {"schema_version":1,"os_id":"example","tag":"1.0","channel":"stable","source":"https://example.com/release","device_family":"h700","device":"test-device","installation_model":"full_image","validation":{},"asset":{"filename":"image.img.gz","sha256":None}}
        with self.assertRaises(ReleaseCatalogError): validate_release_manifest(manifest)

if __name__ == "__main__": unittest.main()
