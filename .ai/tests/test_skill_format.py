"""Skill format: frontmatter, name matches folder, description present."""
import unittest
from pathlib import Path

import _paths  # noqa: F401
import agentctl

SKILLS = ROOT = agentctl.ROOT / ".ai" / "skills"


class TestSkillFormat(unittest.TestCase):
    def test_skills(self):
        dirs = agentctl.skill_dirs()
        self.assertGreaterEqual(len(dirs), 6, "Cần ít nhất 6 skill canonical")
        names = {d.name for d in dirs}
        expected = {"project-start", "change-intake", "impact-analysis",
                    "implement-approved-change", "sync-project-knowledge", "project-doctor"}
        self.assertTrue(expected.issubset(names), f"Thiếu skill: {expected - names}")
        for directory in dirs:
            front = agentctl.parse_frontmatter(directory / "SKILL.md")
            self.assertIsNotNone(front, f"Frontmatter lỗi: {directory.name}")
            self.assertEqual(front.get("name"), directory.name, f"name không khớp thư mục: {directory.name}")
            self.assertGreaterEqual(len(front.get("description", "")), 20, f"description quá ngắn: {directory.name}")


if __name__ == "__main__":
    unittest.main()
