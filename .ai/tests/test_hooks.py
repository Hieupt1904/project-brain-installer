"""Claude hooks are safe and avoid endless Stop loops."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestHooks(unittest.TestCase):
    def test_hook_config_and_guard(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertIn("SessionStart", settings["hooks"])
        self.assertIn("Stop", settings["hooks"])
        stop_script = ROOT / ".ai" / "scripts" / "stop_hook.py"
        self.assertTrue(stop_script.exists(), "Thiếu stop_hook.py")
        self.assertIn("stop_hook_active", stop_script.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
