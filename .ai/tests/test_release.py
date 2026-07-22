"""Tests for the Project Brain release archive builder."""
import importlib.util
import tarfile
import tempfile
import unittest
from pathlib import Path

RELEASE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "release.py"
SPEC = importlib.util.spec_from_file_location("project_brain_release", RELEASE_PATH)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class TestReleaseBuilder(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.output = self.root / "dist"
        files = {
            "ai": "#!/bin/sh\n",
            "ai.cmd": "@echo off\n",
            "install.sh": "#!/bin/sh\n",
            "README.md": "# Project Brain\n",
            ".ai/project.json": "{}\n",
            ".ai/scripts/install.py": "print('install')\n",
            ".ai/knowledge/architecture.md": "# Architecture\n",
            ".ai/policy/core.md": "# Core\n",
            ".ai/skills/example/SKILL.md": "---\nname: example\n---\n",
            ".ai/tests/test_example.py": "pass\n",
            "docs/README.md": "# Docs\n",
            "CLAUDE.md": "# Claude\n",
            ".claude/settings.json": "{}\n",
            ".claude/skills/example/SKILL.md": "generated\n",
            "AGENTS.md": "# Codex\n",
            ".agents/skills/example/SKILL.md": "generated\n",
            ".ai/changes/private/request.md": "do not publish\n",
            ".ai/generated/brief.md": "generated\n",
            ".ai/runtime/state.json": "{}\n",
        }
        for relative, content in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_archive_has_unique_safe_payload_members(self):
        archive_path = release.build_release_archive(self.root, "1.0.0", self.output)

        with tarfile.open(archive_path, "r:gz") as archive:
            names = [member.name for member in archive.getmembers()]

        self.assertEqual(len(names), len(set(names)))
        self.assertIn("project-brain-1.0.0/.ai/scripts/install.py", names)
        self.assertFalse(any("/.ai/changes/" in name for name in names))
        self.assertFalse(any("/.ai/generated/" in name for name in names))
        self.assertFalse(any("/.ai/runtime/" in name for name in names))

    def test_archive_is_byte_reproducible(self):
        first = release.build_release_archive(self.root, "1.0.0", self.output)
        first_digest = release.calculate_sha256(first)
        first.unlink()

        second = release.build_release_archive(self.root, "1.0.0", self.output)

        self.assertEqual(first_digest, release.calculate_sha256(second))

    def test_archive_ignores_source_modes_but_preserves_launcher_mode(self):
        (self.root / "ai").chmod(0o700)
        (self.root / "README.md").chmod(0o600)
        first = release.build_release_archive(self.root, "1.0.0", self.output)
        first_digest = release.calculate_sha256(first)
        first.unlink()

        (self.root / "ai").chmod(0o755)
        (self.root / "README.md").chmod(0o644)
        second = release.build_release_archive(self.root, "1.0.0", self.output)

        self.assertEqual(first_digest, release.calculate_sha256(second))
        with tarfile.open(second, "r:gz") as archive:
            self.assertEqual(archive.getmember("project-brain-1.0.0/ai").mode & 0o777, 0o755)
            self.assertEqual(archive.getmember("project-brain-1.0.0/README.md").mode & 0o777, 0o644)


if __name__ == "__main__":
    unittest.main()
