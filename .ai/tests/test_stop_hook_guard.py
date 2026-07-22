"""Stop hook treats only boolean true as the loop guard."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_stop_hook():
    spec = importlib.util.spec_from_file_location(
        "stop_hook_guard_test_module", ROOT / ".ai" / "scripts" / "stop_hook.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestStopHookGuard(unittest.TestCase):
    def test_only_boolean_true_skips_safety_check(self):
        stop_hook = _load_stop_hook()
        self.assertTrue(stop_hook.should_skip_stop_hook({"stop_hook_active": True}))
        for value in ("true", "false", "1", 1, [], {"value": True}):
            self.assertFalse(stop_hook.should_skip_stop_hook({"stop_hook_active": value}))


if __name__ == "__main__":
    unittest.main()
