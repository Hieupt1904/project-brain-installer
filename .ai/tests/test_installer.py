"""Tests for the project-local Project Brain installer."""
import importlib.util
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

INSTALLER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
SPEC = importlib.util.spec_from_file_location("project_brain_installer", INSTALLER_PATH)
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class InstallerFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.target = self.root / "target"
        self.source.mkdir()
        self.target.mkdir()
        files = {
            "ai": "#!/bin/sh\n",
            "ai.cmd": "@echo off\n",
            "install.sh": "#!/bin/sh\n",
            ".ai/project.json": "{}\n",
            ".ai/scripts/agentctl.py": "print('ok')\n",
            ".ai/knowledge/architecture.md": "# Architecture\n",
            ".ai/policy/core.md": "# Core\n",
            ".ai/skills/example/SKILL.md": "---\nname: example\n---\n",
            ".ai/tests/test_example.py": "pass\n",
            "CLAUDE.md": "# Claude\n",
            ".claude/settings.json": "{}\n",
            ".claude/skills/example/SKILL.md": "generated\n",
            "AGENTS.md": "# Codex\n",
            ".agents/skills/example/SKILL.md": "generated\n",
        }
        for relative, content in files.items():
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        (self.source / ".ai/generated").mkdir()
        (self.source / ".ai/generated/brief.md").write_text("generated", encoding="utf-8")
        (self.source / ".ai/runtime").mkdir()
        (self.source / ".ai/changes/old").mkdir(parents=True)
        (self.source / ".ai/changes/old/request.md").write_text("old", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()


class TestInstaller(InstallerFixture):
    def test_both_installs_verified_payload_and_manifest(self):
        result = installer.install(self.source, self.target, "both", dry_run=False, version="1.2.3")

        self.assertEqual(result.action, "install")
        self.assertTrue((self.target / "CLAUDE.md").is_file())
        self.assertTrue((self.target / "AGENTS.md").is_file())
        self.assertTrue((self.target / ".ai/scripts/agentctl.py").is_file())
        self.assertTrue((self.target / ".claude/settings.json").is_file())
        self.assertTrue((self.target / ".agents/skills/example/SKILL.md").is_file())
        self.assertTrue((self.target / "install.sh").is_file())
        self.assertFalse((self.target / ".ai/generated/brief.md").exists())
        self.assertFalse((self.target / ".ai/changes/old/request.md").exists())
        manifest = json.loads((self.target / installer.MANIFEST_PATH).read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.2.3")
        self.assertIn("CLAUDE.md", manifest["files"])
        self.assertIn(".ai/scripts/agentctl.py", manifest["files"])
        self.assertIn(".claude/settings.json", manifest["files"])
        self.assertNotIn("ai/scripts/agentctl.py", manifest["files"])

    def test_legacy_manifest_upgrades_framework_but_preserves_project_files(self):
        legacy_script = self.target / ".ai/scripts/agentctl.py"
        legacy_script.parent.mkdir(parents=True)
        legacy_script.write_text("legacy runtime\n", encoding="utf-8")
        project_readme = self.target / "README.md"
        project_readme.write_text("project-owned README\n", encoding="utf-8")
        manifest_path = self.target / installer.MANIFEST_PATH
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps({
            "schema_version": installer.SCHEMA_VERSION,
            "version": "1.0.8",
            "selection": "both",
            "files": {"README.md": hashlib.sha256(b"original release README\n").hexdigest()},
            "directories": [],
        }), encoding="utf-8")

        installer.install(self.source, self.target, "both", dry_run=False, version="1.0.9")

        self.assertEqual(legacy_script.read_text(encoding="utf-8"), "print('ok')\n")
        self.assertEqual(project_readme.read_text(encoding="utf-8"), "project-owned README\n")

    def test_target_selection_isolated(self):
        installer.install(self.source, self.target, "claude", dry_run=False, version="dev")

        self.assertTrue((self.target / "CLAUDE.md").exists())
        self.assertTrue((self.target / ".claude/settings.json").exists())
        self.assertFalse((self.target / "AGENTS.md").exists())
        self.assertFalse((self.target / ".agents").exists())

    def test_dry_run_does_not_mutate_target(self):
        result = installer.install(self.source, self.target, "both", dry_run=True, version="dev")

        self.assertGreater(len(result.files), 0)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_existing_project_files_are_preserved_and_install_continues(self):
        (self.target / "CLAUDE.md").write_text("user content\n", encoding="utf-8")

        result = installer.install(self.source, self.target, "both", dry_run=False, version="dev")

        self.assertEqual(result.action, "install")
        self.assertTrue((self.target / "AGENTS.md").exists())
        self.assertTrue((self.target / installer.MANIFEST_PATH).exists())
        self.assertEqual((self.target / "CLAUDE.md").read_text(encoding="utf-8"), "user content\n")

    def test_source_symlink_is_rejected(self):
        (self.source / "CLAUDE.md").unlink()
        (self.source / "CLAUDE.md").symlink_to("/etc/hosts")

        with self.assertRaisesRegex(installer.InstallError, "symlink"):
            installer.install(self.source, self.target, "claude", dry_run=False, version="dev")

    def test_target_symlink_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.target / ".claude").symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(installer.InstallError, "symlink"):
            installer.install(self.source, self.target, "claude", dry_run=False, version="dev")

    def test_transaction_rolls_back_partial_copy(self):
        original = installer.atomic_copy
        calls = 0

        def fail_second(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("induced failure")
            return original(source, destination)

        with mock.patch.object(installer, "atomic_copy", side_effect=fail_second):
            with self.assertRaisesRegex(installer.InstallError, "induced failure"):
                installer.install(self.source, self.target, "both", dry_run=False, version="dev")

        self.assertEqual(list(self.target.rglob("*")), [])

    def test_uninstall_removes_only_managed_unchanged_files(self):
        installer.install(self.source, self.target, "both", dry_run=False, version="dev")
        user_file = self.target / "user.txt"
        user_file.write_text("keep", encoding="utf-8")

        installer.uninstall(self.target, dry_run=False)

        self.assertTrue(user_file.is_file())
        self.assertFalse((self.target / "CLAUDE.md").exists())
        self.assertFalse((self.target / ".ai/scripts/agentctl.py").exists())
        self.assertFalse((self.target / ".claude/settings.json").exists())
        self.assertFalse((self.target / installer.MANIFEST_PATH).exists())

    def test_uninstall_refuses_modified_managed_file(self):
        installer.install(self.source, self.target, "both", dry_run=False, version="dev")
        (self.target / "CLAUDE.md").write_text("modified", encoding="utf-8")

        with self.assertRaisesRegex(installer.InstallError, "modified"):
            installer.uninstall(self.target, dry_run=False)

        self.assertTrue((self.target / "AGENTS.md").exists())
        self.assertTrue((self.target / installer.MANIFEST_PATH).exists())

    def test_manifest_path_traversal_is_rejected(self):
        manifest = self.target / installer.MANIFEST_PATH
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({
            "schema_version": "1.0", "version": "x", "selection": "both",
            "files": {"../outside": "0" * 64}, "directories": [],
        }), encoding="utf-8")

        with self.assertRaisesRegex(installer.InstallError, "unsafe"):
            installer.uninstall(self.target, dry_run=False)

    def test_repeat_install_upgrades_unchanged_managed_file_and_carries_manifest(self):
        installer.install(self.source, self.target, "both", dry_run=False, version="old")
        (self.source / "CLAUDE.md").write_text("# New Claude\n", encoding="utf-8")
        installer.install(self.source, self.target, "both", dry_run=False, version="new")
        manifest = installer.load_manifest(self.target)
        self.assertEqual((self.target / "CLAUDE.md").read_text(encoding="utf-8"), "# New Claude\n")
        self.assertEqual(manifest["version"], "new")
        self.assertIn("CLAUDE.md", manifest["files"])
        self.assertIn("AGENTS.md", manifest["files"])

    def test_repeat_install_preserves_modified_managed_file_and_keeps_prior_entry(self):
        installer.install(self.source, self.target, "both", dry_run=False, version="old")
        (self.target / "CLAUDE.md").write_text("project change\n", encoding="utf-8")
        (self.source / "CLAUDE.md").write_text("# New Claude\n", encoding="utf-8")
        installer.install(self.source, self.target, "both", dry_run=False, version="new")
        manifest = installer.load_manifest(self.target)
        self.assertEqual((self.target / "CLAUDE.md").read_text(encoding="utf-8"), "project change\n")
        self.assertIn("CLAUDE.md", manifest["files"])

    def test_manifest_requires_complete_strict_schema(self):
        manifest = self.target / installer.MANIFEST_PATH
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"schema_version": "1.0", "files": {}, "directories": []}), encoding="utf-8")
        with self.assertRaisesRegex(installer.InstallError, "schema"):
            installer.uninstall(self.target, dry_run=False)

    def test_dry_run_with_existing_manifest_has_no_side_effects(self):
        installer.install(self.source, self.target, "both", dry_run=False, version="old")
        before = (self.target / installer.MANIFEST_PATH).read_bytes()
        (self.source / "CLAUDE.md").write_text("# changed\n", encoding="utf-8")
        installer.install(self.source, self.target, "both", dry_run=True, version="new")
        self.assertEqual((self.target / installer.MANIFEST_PATH).read_bytes(), before)
        self.assertNotEqual((self.target / "CLAUDE.md").read_text(encoding="utf-8"), "# changed\n")

    def test_manifest_symlink_is_rejected_on_repeat_install(self):
        manifest = self.target / installer.MANIFEST_PATH
        manifest.parent.mkdir(parents=True)
        manifest.symlink_to(self.root / "outside")
        with self.assertRaisesRegex(installer.InstallError, "symlink"):
            installer.install(self.source, self.target, "both", dry_run=False, version="new")


@unittest.skipUnless((Path(__file__).resolve().parents[2] / "install.sh").is_file(), "bootstrap asset is tested in the source repository")
class TestPublicBootstrap(InstallerFixture):
    bootstrap = Path(__file__).resolve().parents[2] / "install.sh"

    def build_archive(self, path: Path, root: str = "project-brain-1.0.10", extra: tarfile.TarInfo | None = None) -> None:
        with tarfile.open(path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            for source in sorted(self.source.rglob("*")):
                if source.is_file():
                    archive.add(source, arcname=f"{root}/{source.relative_to(self.source)}", recursive=False)
            archive.add(INSTALLER_PATH, arcname=f"{root}/.ai/scripts/install.py", recursive=False)
            if extra is not None:
                archive.addfile(extra, io.BytesIO(b"x") if extra.isreg() else None)

    def run_bootstrap(self, archive: Path, checksum: str, target: Path) -> subprocess.CompletedProcess[str]:
        script = self.root / "install.sh"
        text = self.bootstrap.read_text(encoding="utf-8")
        text = re.sub(r"ARCHIVE_SHA256='[0-9a-f]*'", f"ARCHIVE_SHA256='{checksum}'", text)
        script.write_text(text, encoding="utf-8")
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_curl = fake_bin / "curl"
        fake_curl.write_text(
            "#!/bin/sh\nwhile [ $# -gt 0 ]; do\n  if [ \"$1\" = --output ]; then cp \"$FAKE_ARCHIVE\" \"$2\"; exit 0; fi\n  shift\ndone\nexit 1\n",
            encoding="utf-8",
        )
        fake_curl.chmod(0o755)
        environment = os.environ | {"FAKE_ARCHIVE": str(archive), "PATH": f"{fake_bin}:{os.environ['PATH']}", "PROJECT_BRAIN_SKIP_AUTORUN": "1"}
        return subprocess.run(
            ["sh", str(script), "--directory", str(target), "--target", "both"],
            cwd=self.root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_public_bootstrap_installs_verified_payload(self):
        archive = self.root / "payload.tar.gz"
        self.build_archive(archive)
        result = self.run_bootstrap(archive, hashlib.sha256(archive.read_bytes()).hexdigest(), self.target)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / "CLAUDE.md").is_file())
        manifest = json.loads((self.target / installer.MANIFEST_PATH).read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.0.10")

    def test_public_bootstrap_rejects_checksum_mismatch_before_install(self):
        archive = self.root / "payload.tar.gz"
        self.build_archive(archive)
        result = self.run_bootstrap(archive, "0" * 64, self.target)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_public_bootstrap_rejects_archive_link_before_install(self):
        archive = self.root / "payload.tar.gz"
        link = tarfile.TarInfo("project-brain-1.0.10/link")
        link.type = tarfile.SYMTYPE
        link.linkname = "CLAUDE.md"
        self.build_archive(archive, extra=link)
        result = self.run_bootstrap(archive, hashlib.sha256(archive.read_bytes()).hexdigest(), self.target)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_public_bootstrap_enforces_https_pinned_transport(self):
        text = self.bootstrap.read_text(encoding="utf-8")

        self.assertIn("--proto '=https'", text)
        self.assertIn("--proto-redir '=https'", text)
        self.assertIn("--tlsv1.2", text)
        self.assertIn("github.com/Hieupt1904/project-brain-installer/releases/download", text)
        self.assertRegex(text, r"ARCHIVE_SHA256='[0-9a-f]{64}'")

    def test_uninstall_skips_archive_download(self):
        script = self.root / "install.sh"
        script.write_text(self.bootstrap.read_text(encoding="utf-8"), encoding="utf-8")
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_curl = fake_bin / "curl"
        fake_curl.write_text("#!/bin/sh\necho curl-called >&2\nexit 99\n", encoding="utf-8")
        fake_curl.chmod(0o755)

        result = subprocess.run(
            ["sh", str(script), "--uninstall", "--directory", str(self.target)],
            cwd=self.root,
            env=os.environ | {"PATH": f"{fake_bin}:{os.environ['PATH']}"},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotIn("curl-called", result.stderr)
        self.assertNotEqual(result.returncode, 99)
        self.assertIn("no installed installer found", result.stderr)


if __name__ == "__main__":
    unittest.main()
