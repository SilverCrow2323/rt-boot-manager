import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtbm.device import probe_device


class DeviceProbeTests(unittest.TestCase):
    def test_probe_never_guesses_ram_or_panel(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            proc = root / "proc"
            (proc / "device-tree").mkdir(parents=True)
            (proc / "device-tree/model").write_text("Anbernic RG35XX H")
            (proc / "device-tree/compatible").write_text("anbernic,rg35xx-h allwinner,sun50i-h700")
            (proc / "cpuinfo").write_text("Hardware : sun50iw9")
            (proc / "meminfo").write_text("MemTotal:       950000 kB")
            result = probe_device(temp)
            self.assertEqual(result["device_id"], "anbernic-rg35xx-h")
            self.assertEqual(result["soc_family"], "allwinner-h700")
            self.assertEqual(result["ram_type"], "unknown")
            self.assertEqual(result["panel_revision"], "unknown")


if __name__ == "__main__":
    unittest.main()
