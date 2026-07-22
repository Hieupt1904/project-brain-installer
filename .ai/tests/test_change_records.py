"""Implemented changes must have approval and required records."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANGES = ROOT / ".ai" / "changes"


class TestChangeRecords(unittest.TestCase):
    def test_implementation_requires_approval(self):
        for implementation in CHANGES.glob("*/implementation.md"):
            folder = implementation.parent
            approval = folder / "approval.md"
            self.assertTrue(approval.exists(), f"Thiếu approval: {folder}")
            text = approval.read_text(encoding="utf-8")
            self.assertRegex(text, r"(?im)^status:\s*approved\s*$", f"Approval chưa approved: {folder}")
            self.assertTrue((folder / "request.md").exists(), f"Thiếu request: {folder}")
            self.assertTrue((folder / "impact.md").exists(), f"Thiếu impact: {folder}")
            self.assertTrue((folder / "verification.md").exists(), f"Thiếu verification: {folder}")


if __name__ == "__main__":
    unittest.main()
