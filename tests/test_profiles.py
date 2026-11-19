import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.catalog import CatalogError, load_profiles, validate_profile
from rtbm.planner import make_plan


class ProfileTests(unittest.TestCase):
    def test_catalog_loads_unique_profiles(self):
        profiles = load_profiles(ROOT / "catalog" / "os")
        self.assertGreaterEqual(len(profiles), 8)
        self.assertEqual(len({p["id"] for p in profiles}), len(profiles))

    def test_three_main_systems(self):
        profiles = load_profiles(ROOT / "catalog" / "os")
        main_ids = {p["id"] for p in profiles if p["tier"] == "main"}
        self.assertEqual(main_ids, {"muos", "rocknix", "knulli"})

    def test_no_profile_can_enable_writes(self):
        for profile in load_profiles(ROOT / "catalog" / "os"):
            self.assertIs(profile["boot"]["write_capable"], False)

    def test_write_capability_is_rejected(self):
        profile = dict(load_profiles(ROOT / "catalog" / "os")[0])
        profile["boot"] = dict(profile["boot"], write_capable=True)
        with self.assertRaises(CatalogError):
            validate_profile(profile)

    def test_unknown_ram_blocks_native_rocknix(self):
        profile = next(p for p in load_profiles(ROOT / "catalog" / "os") if p["id"] == "rocknix")
        device = {"device_id": "anbernic-rg35xx-h", "ram_type": "unknown", "panel_revision": "unknown"}
        plan = make_plan(profile, device)
        self.assertEqual(plan["compatibility"], "needs_verification")
        self.assertFalse(plan["destructive_operations_enabled"])
        self.assertTrue(plan["dry_run"])

    def test_minos_is_disabled(self):
        profile = next(p for p in load_profiles(ROOT / "catalog" / "os") if p["id"] == "minos")
        plan = make_plan(profile, {"device_id": "anbernic-rg35xx-h", "ram_type": "unknown", "panel_revision": "unknown"})
        self.assertEqual(plan["compatibility"], "disabled")


if __name__ == "__main__":
    unittest.main()
