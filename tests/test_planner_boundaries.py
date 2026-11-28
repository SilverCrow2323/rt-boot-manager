import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.planner import compatibility, make_plan


class PlannerBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = json.loads((ROOT / "catalog" / "os" / "rocknix.json").read_text(encoding="utf-8"))

    def plan(self, **overrides):
        device = {
            "device_id": "anbernic-rg35xx-h",
            "ram_type": "ddr4",
            "panel_revision": "rg35xx-h-rev6",
        }
        device.update(overrides)
        return make_plan(self.profile, device)

    def test_wrong_device_is_blocked(self):
        plan = self.plan(device_id="unknown-handheld")
        self.assertEqual(plan["compatibility"], "blocked")
        self.assertFalse(plan["destructive_operations_enabled"])
        self.assertTrue(plan["dry_run"])

    def test_wrong_ram_variant_is_blocked(self):
        plan = self.plan(ram_type="lpddr4")
        self.assertEqual(plan["compatibility"], "blocked")
        self.assertFalse(plan["destructive_operations_enabled"])

    def test_unknown_ram_requires_verification(self):
        plan = self.plan(ram_type="unknown", panel_revision="unknown")
        self.assertEqual(plan["compatibility"], "needs_verification")
        self.assertFalse(plan["destructive_operations_enabled"])

    def test_known_ram_but_unknown_panel_requires_dtb_verification(self):
        plan = self.plan(panel_revision="unknown")
        self.assertEqual(plan["compatibility"], "needs_verification")
        self.assertFalse(plan["destructive_operations_enabled"])

    def test_matching_hardware_is_still_only_a_dry_run(self):
        plan = self.plan()
        self.assertEqual(plan["compatibility"], "research_only")
        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["destructive_operations_enabled"])


if __name__ == "__main__":
    unittest.main()
