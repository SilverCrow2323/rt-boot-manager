import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.catalog import load_profiles

SPEC = importlib.util.spec_from_file_location(
    "generate_sgrub_profiles", ROOT / "tools" / "generate_sgrub_profiles.py"
)
GENERATOR = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(GENERATOR)


class SgrubCodegenTests(unittest.TestCase):
    def test_native_release_table_contains_all_main_os_history(self):
        records = GENERATOR.release_records(load_profiles())
        self.assertEqual(len(records), 27)
        counts = {
            os_id: sum(1 for item in records if item["os_id"] == os_id)
            for os_id in ("muos", "rocknix", "knulli")
        }
        self.assertEqual(counts, {"muos": 16, "rocknix": 6, "knulli": 5})

    def test_rocknix_current_and_historical_releases_have_sha_metadata(self):
        records = GENERATOR.release_records(load_profiles())
        rocknix = [item for item in records if item["os_id"] == "rocknix"]
        self.assertEqual(rocknix[0]["tag"], "20261101")
        self.assertTrue(all(item["checksum_available"] for item in rocknix))
        self.assertTrue(all(item["requires_known_ram"] for item in rocknix))

    def test_knulli_legacy_is_not_misrepresented_as_checksum_verified(self):
        records = GENERATOR.release_records(load_profiles())
        old = [item for item in records if item["os_id"] == "knulli" and not item["is_current"]]
        self.assertEqual(len(old), 4)
        self.assertTrue(all(not item["checksum_available"] for item in old))
        self.assertTrue(all(item["verification"] == "VERIFY SHA256" for item in old))

    def test_muos_archive_is_history_only_and_not_install_ready(self):
        records = GENERATOR.release_records(load_profiles())
        old = [item for item in records if item["os_id"] == "muos" and not item["is_current"]]
        self.assertEqual(len(old), 15)
        self.assertTrue(all(item["verification"] == "ARCHIVE ONLY" for item in old))
        self.assertTrue(all(not item["checksum_available"] for item in old))

    def test_generated_header_exports_profiles_and_release_tables(self):
        header = GENERATOR.render()
        self.assertIn("#define SGRUB_PROFILE_COUNT", header)
        self.assertIn("#define SGRUB_RELEASE_COUNT", header)
        self.assertIn('"20261101"', header)
        self.assertIn('"20250813"', header)
        self.assertIn('"2601.1"', header)


if __name__ == "__main__":
    unittest.main()
