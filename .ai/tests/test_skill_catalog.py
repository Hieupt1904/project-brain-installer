"""Tests for layered skill metadata and generated discovery catalog."""
import importlib.util, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / "scripts" / "agentctl.py"
SPEC = importlib.util.spec_from_file_location("pb_skill_catalog", PATH)
agentctl = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = agentctl; SPEC.loader.exec_module(agentctl)

class TestSkillCatalog(unittest.TestCase):
    def test_all_canonical_skills_declare_layer_and_trigger_keywords(self):
        for directory in agentctl.skill_dirs():
            metadata = agentctl.parse_skill_metadata(directory / "SKILL.md")
            self.assertIn(metadata["layer"], agentctl.SKILL_LAYERS, directory.name)
            self.assertTrue(metadata["trigger_keywords"], directory.name)

    def test_catalog_contains_every_skill_and_required_columns(self):
        text = agentctl.render_skills_catalog()
        self.assertIn("| Skill | Layer | Trigger keywords | Description |", text)
        for directory in agentctl.skill_dirs():
            self.assertIn(f"`{directory.name}`", text)

    def test_build_catalog_writes_generated_file(self):
        with tempfile.TemporaryDirectory(dir=str(agentctl.AI / "runtime")) as tmp:
            generated = Path(tmp)
            with mock.patch.object(agentctl, "GENERATED", generated):
                target = agentctl.build_skills_catalog()
                self.assertEqual(target, generated / "skills-catalog.md")
                self.assertIn("# Skills catalog", target.read_text(encoding="utf-8"))

    def test_catalog_is_built_during_start(self):
        with mock.patch.object(agentctl, "doctor", return_value=0), mock.patch.object(agentctl, "sync_skills"), mock.patch.object(agentctl, "adapter_paths_for_target", return_value=[]), mock.patch.object(agentctl, "build_repo_map"), mock.patch.object(agentctl, "build_skills_catalog") as catalog, mock.patch.object(agentctl, "create_brief"), mock.patch.object(agentctl, "start_next_steps", return_value="next"), mock.patch("builtins.print"), mock.patch.object(agentctl, "RUNTIME", agentctl.AI / "runtime"):
            self.assertEqual(agentctl.start(), 0)
            catalog.assert_called_once()

if __name__ == "__main__": unittest.main()
