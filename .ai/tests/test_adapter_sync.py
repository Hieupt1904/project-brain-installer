"""Adapter files match canonical source hash."""
import unittest

import _paths  # noqa: F401
import agentctl


class TestAdapterSync(unittest.TestCase):
    def test_hashes_match(self):
        for source in agentctl.skill_dirs():
            for base in (agentctl.ROOT / ".agents" / "skills", agentctl.ROOT / ".claude" / "skills"):
                target = base / source.name / "SKILL.md"
                self.assertTrue(target.exists(), f"Thiếu adapter: {target}")
                self.assertTrue(agentctl.adapter_is_valid(source / "SKILL.md", target),
                                f"Adapter lệch canonical: {target}")

    def test_sync_repairs_drift(self):
        source = agentctl.skill_dirs()[0] / "SKILL.md"
        target = agentctl.ROOT / ".claude" / "skills" / source.parent.name / "SKILL.md"
        original = target.read_text(encoding="utf-8")
        try:
            target.write_text(original + "\nDRIFT\n", encoding="utf-8")
            agentctl.sync_skills()
            self.assertTrue(agentctl.adapter_is_valid(source, target))
        finally:
            agentctl.sync_skills()

    def test_generated_warning(self):
        for source in agentctl.skill_dirs():
            target = agentctl.ROOT / ".claude" / "skills" / source.name / "SKILL.md"
            self.assertIn(agentctl.GENERATED_WARNING, target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
