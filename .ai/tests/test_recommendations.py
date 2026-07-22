"""Tests for evidence-based recommended skills."""
import importlib.util, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / "scripts" / "agentctl.py"
SPEC = importlib.util.spec_from_file_location("pb_recommendations", PATH)
agentctl = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = agentctl; SPEC.loader.exec_module(agentctl)

class TestRecommendations(unittest.TestCase):
    def test_recommendations_are_evidence_based_and_explicit_about_unknowns(self):
        with tempfile.TemporaryDirectory(dir=str(agentctl.AI / "runtime")) as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}\n")
            (root / "src").mkdir()
            (root / "src/app.ts").write_text("export const app = true\n")
            (root / "docker-compose.yml").write_text("services: {}\n")
            with mock.patch.object(agentctl, "ROOT", root), mock.patch.object(agentctl, "AI", root / ".ai"), mock.patch.object(agentctl, "GENERATED", root / ".ai/generated"):
                text = agentctl.render_recommended_skills()
            self.assertIn("package.json", text)
            self.assertIn("JavaScript/Node capability detected", text)
            self.assertIn("TypeScript source detected", text)
            self.assertIn("container capability detected", text)
            self.assertIn("Database: not verified", text)
            self.assertNotIn("PostgreSQL", text)

    def test_recommendations_always_include_core_governance_skills(self):
        text = agentctl.render_recommended_skills()
        for skill in ("project-start", "project-doctor", "project-reconnaissance"):
            self.assertIn(f"`{skill}`", text)

    def test_build_recommendations_writes_generated_file(self):
        with tempfile.TemporaryDirectory(dir=str(agentctl.AI / "runtime")) as tmp:
            generated = Path(tmp)
            with mock.patch.object(agentctl, "GENERATED", generated):
                target = agentctl.build_recommended_skills()
            self.assertEqual(target, generated / "recommended-skills.md")
            self.assertTrue(target.is_file())

    def test_recommendations_build_during_start(self):
        with mock.patch.object(agentctl, "doctor", return_value=0), mock.patch.object(agentctl, "sync_skills"), mock.patch.object(agentctl, "adapter_paths_for_target", return_value=[]), mock.patch.object(agentctl, "build_repo_map"), mock.patch.object(agentctl, "build_skills_catalog"), mock.patch.object(agentctl, "build_recommended_skills") as recommendations, mock.patch.object(agentctl, "create_brief"), mock.patch.object(agentctl, "start_next_steps", return_value="next"), mock.patch("builtins.print"), mock.patch.object(agentctl, "RUNTIME", agentctl.AI / "runtime"):
            self.assertEqual(agentctl.start(), 0)
            recommendations.assert_called_once()

if __name__ == "__main__": unittest.main()
