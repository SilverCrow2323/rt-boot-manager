import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SgrubDiagnosticsSourceTests(unittest.TestCase):
    def test_native_frontend_uses_read_only_hardware_sources(self):
        source = (ROOT / "ui" / "sgrub" / "native" / "sgrub.c").read_text()
        self.assertIn("/proc/device-tree/model", source)
        self.assertIn("/proc/device-tree/compatible", source)
        self.assertIn("/proc/meminfo", source)
        self.assertIn("NOT IDENTIFIED", source)
        self.assertIn("NOT VERIFIED", source)
        self.assertIn("SDL_GetRendererOutputSize", source)

    def test_diagnostics_action_is_available_to_controller_and_keyboard(self):
        source = (ROOT / "ui" / "sgrub" / "native" / "sgrub.c").read_text()
        self.assertIn("SDL_CONTROLLER_BUTTON_X", source)
        self.assertIn("SDLK_d", source)
        self.assertIn("RTBM_RAW_X_BUTTON", source)

    def test_diagnostics_do_not_add_mutating_system_calls(self):
        source = (ROOT / "ui" / "sgrub" / "native" / "sgrub.c").read_text()
        forbidden = ("system(", "popen(", "execv(", "reboot(", "mount(", "umount(")
        for marker in forbidden:
            self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
