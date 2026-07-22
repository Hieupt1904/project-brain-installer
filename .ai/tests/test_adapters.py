"""Top-level adapters are generated safely from canonical .ai content."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WARNING = "GENERATED FILE — DO NOT EDIT DIRECTLY"


class TestTopLevelAdapters(unittest.TestCase):
    def test_generated_warning_and_markers(self):
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("BEGIN AI-GENERATED", text)
            self.assertIn("END AI-GENERATED", text)
            self.assertIn(WARNING, text)
            self.assertIn("`.ai/`", text)
            self.assertIn("source_sha256:", text)
            self.assertIn("schema_version:", text)
            self.assertIn("generated_at:", text)


if __name__ == "__main__":
    unittest.main()
