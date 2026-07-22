"""Repository mapping excludes sensitive and generated paths."""
import unittest
from pathlib import Path

import _paths  # noqa: F401
import agentctl


class TestRepoMapFilter(unittest.TestCase):
    def test_sensitive_names_excluded(self):
        blocked = [".env", ".env.local", "service.key", "private.pem", "credentials.json", "prod.sqlite3"]
        for name in blocked:
            self.assertTrue(agentctl.should_exclude(Path(name)), f"Phải loại khỏi context: {name}")

    def test_normal_source_allowed(self):
        self.assertFalse(agentctl.should_exclude(Path("src/app.py")))


if __name__ == "__main__":
    unittest.main()
