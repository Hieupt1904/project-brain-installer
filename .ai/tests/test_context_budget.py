"""Generated context stays within byte budget and contains no secret patterns."""
import unittest

import _paths  # noqa: F401
import agentctl


class TestContextBudget(unittest.TestCase):
    def setUp(self):
        agentctl.build_repo_map()
        agentctl.create_brief()

    def test_budget(self):
        for name in ("session-brief.md", "repo-map.md"):
            path = agentctl.GENERATED / name
            self.assertTrue(path.exists(), f"Thiếu {name}")
            self.assertLessEqual(path.stat().st_size, agentctl.BRIEF_LIMIT, f"{name} vượt ngân sách")

    def test_budget_counts_bytes_not_characters(self):
        # Multi-byte UTF-8 content (Vietnamese) must not push the file past the byte limit.
        content = "đ" * agentctl.BRIEF_LIMIT
        trimmed = agentctl.within_brief_limit(content)
        self.assertLessEqual(len(trimmed.encode("utf-8")), agentctl.BRIEF_LIMIT)
        self.assertTrue(trimmed.endswith("\n"))

    def test_no_secrets(self):
        for name in ("session-brief.md", "repo-map.md"):
            text = (agentctl.GENERATED / name).read_text(encoding="utf-8")
            self.assertFalse(agentctl.contains_secret(text), f"Phát hiện secret pattern trong {name}")


if __name__ == "__main__":
    unittest.main()
