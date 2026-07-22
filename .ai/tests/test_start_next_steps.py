"""Tests for actionable Vietnamese guidance after Project Brain start."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

AGENTCTL_PATH = Path(__file__).resolve().parents[1] / "scripts" / "agentctl.py"
SPEC = importlib.util.spec_from_file_location("project_brain_agentctl_start_guidance", AGENTCTL_PATH)
agentctl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = agentctl
SPEC.loader.exec_module(agentctl)


class TestStartNextSteps(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(agentctl.AI / "runtime"))
        self.root = Path(self.temp.name)
        self.ai = self.root / ".ai"
        self.ai.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def patch_roots(self):
        return mock.patch.multiple(agentctl, ROOT=self.root, AI=self.ai)

    def test_missing_onboard_inventory_recommends_onboard_first(self):
        with self.patch_roots():
            text = agentctl.start_next_steps()
        self.assertIn("Bước tiếp theo", text)
        self.assertIn("./ai onboard", text)
        self.assertIn("Chưa có inventory", text)
        self.assertIn("./ai brief", text)
        self.assertIn("./ai check", text)
        self.assertIn("./ai close", text)

    def test_existing_inventory_recommends_report_and_adopt_when_marker_missing(self):
        imports = self.ai / "imports"
        imports.mkdir()
        (imports / "inventory.json").write_text("{}\n", encoding="utf-8")
        (imports / "report.md").write_text("# report\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("# Legacy instructions\n", encoding="utf-8")
        with self.patch_roots(), mock.patch.object(agentctl, "active_target", return_value="codex"):
            text = agentctl.start_next_steps()
        self.assertIn("Đã có inventory", text)
        self.assertIn(".ai/imports/report.md", text)
        self.assertIn("./ai adopt", text)

    def test_adopted_project_does_not_recommend_adopt_again(self):
        imports = self.ai / "imports"
        imports.mkdir()
        (imports / "inventory.json").write_text("{}\n", encoding="utf-8")
        marker = "<!-- PROJECT-BRAIN: read canonical instructions from .ai/ -->"
        (self.root / "AGENTS.md").write_text(marker + "\n", encoding="utf-8")
        with self.patch_roots(), mock.patch.object(agentctl, "active_target", return_value="codex"):
            text = agentctl.start_next_steps()
        self.assertIn("Project Brain đã được tích hợp", text)
        self.assertNotIn("Chạy `./ai adopt`", text)

    def test_start_prints_guidance_only_after_successful_doctor(self):
        with mock.patch.object(agentctl, "doctor", return_value=0), \
             mock.patch.object(agentctl, "start_next_steps", return_value="GUIDANCE"), \
             mock.patch.object(agentctl, "sync_skills"), \
             mock.patch.object(agentctl, "adapter_paths_for_target", return_value=[]), \
             mock.patch.object(agentctl, "build_repo_map"), \
             mock.patch.object(agentctl, "create_brief"), \
             mock.patch("builtins.print") as output, \
             mock.patch.object(agentctl, "ROOT", self.root), \
             mock.patch.object(agentctl, "RUNTIME", self.ai / "runtime"):
            code = agentctl.start()
        self.assertEqual(code, 0)
        output.assert_called_once_with("GUIDANCE")

    def test_start_does_not_print_guidance_when_doctor_fails(self):
        with mock.patch.object(agentctl, "doctor", return_value=1), \
             mock.patch.object(agentctl, "start_next_steps", return_value="GUIDANCE"), \
             mock.patch.object(agentctl, "sync_skills"), \
             mock.patch.object(agentctl, "adapter_paths_for_target", return_value=[]), \
             mock.patch.object(agentctl, "build_repo_map"), \
             mock.patch.object(agentctl, "create_brief"), \
             mock.patch("builtins.print") as output, \
             mock.patch.object(agentctl, "ROOT", self.root), \
             mock.patch.object(agentctl, "RUNTIME", self.ai / "runtime"):
            code = agentctl.start()
        self.assertEqual(code, 1)
        output.assert_not_called()


if __name__ == "__main__":
    unittest.main()
