import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.releases import (DuplicateJSONKeyError, ReleaseCatalogError, _strict_json_loads, load_release_history, load_release_manifests, validate_release_manifest)

class ReleaseManifestTests(unittest.TestCase):
    def test_json_parser_rejects_duplicate_keys_at_every_object_depth(self):
        for payload in (
            '{"os_id":"rocknix","os_id":"knulli"}',
            '{"asset":{"filename":"one.img","filename":"two.img"}}',
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(DuplicateJSONKeyError, "duplicate JSON key"):
                    _strict_json_loads(payload)

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


    def _valid_manifest(self):
        return {
            "schema_version": 1,
            "os_id": "example-os",
            "tag": "1.2.3",
            "channel": "stable",
            "source": "https://example.com/releases",
            "device_family": "h700",
            "device": "test-device",
            "installation_model": "full_image",
            "validation": {},
            "asset": {"filename": "image.img.gz", "sha256": "a" * 64},
        }

    def test_asset_filename_cannot_escape_manifest_asset_scope(self):
        for filename in ("../image.img.gz", "folder/image.img.gz", "folder" + chr(92) + "image.img.gz", "..", "bad" + chr(10) + "name"):
            with self.subTest(filename=filename):
                manifest = self._valid_manifest()
                manifest["asset"]["filename"] = filename
                with self.assertRaises(ReleaseCatalogError):
                    validate_release_manifest(manifest)

    def test_source_and_asset_urls_reject_downgrades_and_credentials(self):
        for url in ("http://example.com/release", "https://user:pass@example.com/release", "https:///missing-host", "https://example.com:99999/release"):
            with self.subTest(url=url):
                manifest = self._valid_manifest()
                manifest["source"] = url
                with self.assertRaises(ReleaseCatalogError):
                    validate_release_manifest(manifest)
        manifest = self._valid_manifest()
        manifest["asset"]["url"] = "http://example.com/image.img.gz"
        with self.assertRaises(ReleaseCatalogError):
            validate_release_manifest(manifest)

    def test_https_urls_reject_invalid_dns_hostnames_and_fragments(self):
        for url in (
            "https://bad_host.example/release",
            "https://example..com/release",
            "https://-bad.example/release",
            "https://example.com./release",
            "https://example.com/release#fragment",
            "https://example.com\\\\evil.test/release",
        ):
            with self.subTest(url=url):
                manifest = self._valid_manifest()
                manifest["source"] = url
                with self.assertRaises(ReleaseCatalogError):
                    validate_release_manifest(manifest)

    def test_asset_and_assets_cannot_be_ambiguous(self):
        manifest = self._valid_manifest()
        manifest["assets"] = [{"filename": "other.img.gz", "sha256": "b" * 64}]
        with self.assertRaisesRegex(ReleaseCatalogError, "either asset or assets"):
            validate_release_manifest(manifest)

    def test_duplicate_asset_names_are_rejected_case_insensitively(self):
        manifest = self._valid_manifest()
        manifest.pop("asset")
        manifest["assets"] = [
            {"filename": "IMAGE.img.gz", "sha256": "a" * 64},
            {"filename": "image.IMG.GZ", "sha256": "b" * 64},
        ]
        with self.assertRaisesRegex(ReleaseCatalogError, "duplicate asset filename"):
            validate_release_manifest(manifest)

    def test_size_bytes_must_be_a_positive_integer(self):
        for size in (0, -1, True, "1024"):
            with self.subTest(size=size):
                manifest = self._valid_manifest()
                manifest["asset"]["size_bytes"] = size
                with self.assertRaises(ReleaseCatalogError):
                    validate_release_manifest(manifest)

    def test_valid_policy_without_published_digest_remains_supported(self):
        manifest = self._valid_manifest()
        manifest["asset"]["sha256"] = None
        manifest["asset"]["sha256_policy"] = "calculate_on_download_and_store_local_verification"
        self.assertEqual(validate_release_manifest(manifest)["os_id"], "example-os")


    def test_schema_version_rejects_boolean_and_wrong_type(self):
        for value in (True, "1", 2):
            with self.subTest(value=value):
                manifest = self._valid_manifest()
                manifest["schema_version"] = value
                with self.assertRaises(ReleaseCatalogError):
                    validate_release_manifest(manifest)

    def test_channel_and_installation_model_require_strings(self):
        for field, value in (("channel", []), ("installation_model", {})):
            with self.subTest(field=field):
                manifest = self._valid_manifest()
                manifest[field] = value
                with self.assertRaises(ReleaseCatalogError):
                    validate_release_manifest(manifest)

    def test_https_urls_reject_non_public_ip_literals(self):
        for url in (
            "https://127.0.0.1/release",
            "https://10.0.0.1/release",
            "https://192.168.1.10/release",
            "https://169.254.169.254/latest",
            "https://[::1]/release",
            "https://[fe80::1]/release",
            "https://0.0.0.0/release",
        ):
            with self.subTest(url=url):
                manifest = self._valid_manifest()
                manifest["source"] = url
                with self.assertRaisesRegex(ReleaseCatalogError, "non-public IP"):
                    validate_release_manifest(manifest)

    def test_https_urls_allow_public_ip_literals(self):
        manifest = self._valid_manifest()
        manifest["source"] = "https://8.8.8.8/releases"
        self.assertEqual(validate_release_manifest(manifest)["os_id"], "example-os")

if __name__ == "__main__": unittest.main()
