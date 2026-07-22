"""Adapter-neutral Project Brain behavior."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa
import agentctl
import test_installer


class TestTargets(test_installer.InstallerFixture):
    def setUp(self):
        super().setUp()
        extras = {
            ".kiro/steering/project-brain.md": "kiro\n",
            ".ai/adapters/hermes/SKILL.md": "hermes\n",
            ".ai/adapters/generic/README.md": "generic\n",
            ".codex/config.toml": "local=true\n",
        }
        for name, text in extras.items():
            path = self.source / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)

    def test_each_target_is_isolated_and_all_expands(self):
        expected = {
            "claude": ["CLAUDE.md", ".claude/skills/example/SKILL.md"],
            "codex": ["AGENTS.md", ".agents/skills/example/SKILL.md", ".codex/config.toml"],
            "kiro": [".kiro/steering/project-brain.md"],
            "hermes": [".ai/adapters/hermes/SKILL.md"],
            "generic": [".ai/adapters/generic/README.md"],
        }
        for target, wanted in expected.items():
            with self.subTest(target=target):
                destination = self.root / target; destination.mkdir()
                test_installer.installer.install(self.source, destination, target, False, "dev")
                for name in wanted: self.assertTrue((destination / name).is_file(), name)
                manifest = json.loads((destination / test_installer.installer.MANIFEST_PATH).read_text())
                self.assertEqual(manifest["selection"], target)
        destination = self.root / "all"; destination.mkdir()
        test_installer.installer.install(self.source, destination, "all", False, "dev")
        for names in expected.values():
            for name in names: self.assertTrue((destination / name).is_file(), name)

    def test_both_remains_alias_for_claude_and_codex(self):
        test_installer.installer.install(self.source, self.target, "both", False, "dev")
        self.assertTrue((self.target / "CLAUDE.md").exists())
        self.assertTrue((self.target / "AGENTS.md").exists())
        self.assertFalse((self.target / ".kiro").exists())


class TestTargetAwareRuntime(unittest.TestCase):
    def test_manifest_controls_runtime_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / ".ecc").mkdir()
            (root / ".ecc/install-manifest.json").write_text(json.dumps({"selection": "kiro"}))
            with mock.patch.object(agentctl, "ROOT", root), mock.patch.object(agentctl, "AI", root / ".ai"):
                self.assertEqual(agentctl.active_targets(), ("kiro",))
                self.assertEqual(agentctl.adapter_paths_for_target(), [root / ".kiro/steering/project-brain.md"])

    def test_discover_is_domain_neutral_by_default(self):
        facts = agentctl.discover_facts(confirmations={}, interactive=False)
        self.assertEqual(set(facts), {"project.root"})
        self.assertEqual(facts["project.root"]["status"], "verified")

    def test_discover_does_not_prompt_for_domain_specific_facts(self):
        with mock.patch("builtins.input", side_effect=AssertionError("must not prompt")):
            facts = agentctl.discover_facts(confirmations={}, interactive=True)
        self.assertEqual(set(facts), {"project.root"})

    def test_doctor_only_checks_selected_skill_adapters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".ecc").mkdir()
            (root / ".ecc/install-manifest.json").write_text(json.dumps({"selection": "kiro"}))
            with mock.patch.object(agentctl, "ROOT", root), mock.patch.object(agentctl, "AI", root / ".ai"):
                self.assertEqual(agentctl.skill_adapter_roots_for_targets(), [])


if __name__ == "__main__": unittest.main()
