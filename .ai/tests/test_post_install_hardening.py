"""Post-install, adopt-marker, and archive-hardening regression tests."""
import importlib.util, io, json, os, subprocess, sys, tarfile, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = Path(__file__).resolve().parents[1] / "scripts" / "agentctl.py"
INSTALL_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
RELEASE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "release.py"

aspec = importlib.util.spec_from_file_location("pb_agentctl", AGENTS_PATH)
agentctl = importlib.util.module_from_spec(aspec); sys.modules["pb_agentctl"] = agentctl; aspec.loader.exec_module(agentctl)
ispec = importlib.util.spec_from_file_location("pb_installer", INSTALL_PATH)
installer = importlib.util.module_from_spec(ispec); sys.modules["pb_installer"] = installer; ispec.loader.exec_module(installer)
rspec = importlib.util.spec_from_file_location("pb_release", RELEASE_PATH)
release = importlib.util.module_from_spec(rspec); sys.modules["pb_release"] = release; rspec.loader.exec_module(release)


class TestPostInstallTargetAware(unittest.TestCase):
    def test_active_target_reads_env(self):
        with mock_env(PROJECT_BRAIN_TARGET="claude"):
            self.assertEqual(agentctl.active_target(), "claude")
        with mock_env(PROJECT_BRAIN_TARGET="codex"):
            self.assertEqual(agentctl.active_target(), "codex")
        self.assertEqual(agentctl.active_target(), "both")

    def test_adapter_paths_match_target(self):
        with mock_env(PROJECT_BRAIN_TARGET="claude"):
            self.assertEqual(agentctl.adapter_paths_for_target(), [agentctl.ROOT / "CLAUDE.md"])
        with mock_env(PROJECT_BRAIN_TARGET="codex"):
            self.assertEqual(agentctl.adapter_paths_for_target(), [agentctl.ROOT / "AGENTS.md"])


class TestAdoptMalformedMarker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=str(agentctl.AI / "runtime"))
        self.workspace = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_adopt_rejects_orphan_begin_marker(self):
        path = self.workspace / "AGENTS.md"
        path.write_text("# legacy\n\n<!-- BEGIN AI-GENERATED -->\n", encoding="utf-8")
        target_root = self.workspace
        with mock_env(PROJECT_BRAIN_TARGET="codex"):
            with self.assertRaisesRegex(ValueError, "marker"):
                run_adopt_against(target_root)


class TestArchiveHardening(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); self.output = self.root / "dist"
    def tearDown(self): self.tmp.cleanup()

    def test_archive_rejects_secret_payload(self):
        secret_payload = {"ai": "#!/bin/sh\n", ".ai/project.json": "{}\n",
                          ".ai/scripts/leak.py": "pass" + "word=abcdefghijklmn\n"}
        for rel, body in secret_payload.items():
            p = self.root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body)
        with self.assertRaises(ValueError):
            release.build_release_archive(self.root, "1.0.4", self.output)

    def test_archive_rejects_symlink_payload(self):
        files = {"ai": "#!/bin/sh\n", ".ai/project.json": "{}\n", "README.md": "# x\n"}
        for rel, body in files.items():
            p = self.root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(body)
        (self.root / ".ai/link.md").symlink_to(self.root / "README.md")
        archive = release.build_release_archive(self.root, "1.0.4", self.output)
        with tarfile.open(archive, "r:gz") as tar:
            self.assertFalse(any(m.issym() or m.islnk() for m in tar.getmembers()))


def run_adopt_against(workspace: Path):
    """Run agentctl.adopt with ROOT temporarily swapped to workspace."""
    import unittest.mock as m
    with m.patch.object(agentctl, "ROOT", workspace), m.patch.object(agentctl, "AI", workspace / ".ai"):
        return agentctl.adopt()


class mock_env:
    def __init__(self, **kwargs): self.kwargs = kwargs; self.old = {}
    def __enter__(self):
        for k, v in self.kwargs.items(): self.old[k] = os.environ.get(k); os.environ[k] = v
    def __exit__(self, *a):
        for k, v in self.old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


if __name__ == "__main__": unittest.main()
