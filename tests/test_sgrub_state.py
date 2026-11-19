import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.catalog import load_profiles
from rtbm.sgrub_state import SgrubState


class SgrubStateTests(unittest.TestCase):
    def setUp(self):
        self.state = SgrubState(load_profiles(ROOT / "catalog" / "os"), timeout_seconds=5)

    def test_main_systems_are_first_in_requested_order(self):
        self.assertEqual([entry.profile_id for entry in self.state.entries[:3]], ["muos", "rocknix", "knulli"])

    def test_disabled_profiles_are_hidden(self):
        self.assertNotIn("minos", [entry.profile_id for entry in self.state.entries])

    def test_navigation_wraps(self):
        self.state.selected_index = 0
        self.state.move(-1)
        self.assertEqual(self.state.selected.profile_id, self.state.entries[-1].profile_id)

    def test_timeout_selects_default_not_current_highlight(self):
        self.state.move(2)
        selected = self.state.tick(5)
        self.assertEqual(selected, "muos")

    def test_disabled_profile_cannot_become_default(self):
        state = SgrubState(load_profiles(ROOT / "catalog" / "os"),
                           default_profile="minos", timeout_seconds=1)
        self.assertEqual(state.tick(1), "muos")

    def test_confirm_returns_selected_profile(self):
        self.state.move(1)
        self.assertEqual(self.state.handle("a"), "rocknix")

    def test_cancel_never_selects_a_profile(self):
        self.assertIsNone(self.state.handle("b"))
        self.assertTrue(self.state.cancelled)


if __name__ == "__main__":
    unittest.main()
