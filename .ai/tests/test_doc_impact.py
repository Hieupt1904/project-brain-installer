"""Doc map entries reference existing files; high-risk paths flagged."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401
import agentctl

ROOT = Path(__file__).resolve().parents[2]


class TestDocImpact(unittest.TestCase):
    def test_doc_map_shape(self):
        data = json.loads((ROOT / ".ai" / "knowledge" / "doc-map.json").read_text(encoding="utf-8"))
        self.assertIn("entries", data)
        for entry in data["entries"]:
            self.assertIn("code_path", entry)
            self.assertIn("risk", entry)
            self.assertIn("separate_approval", entry)
            self.assertTrue(
                entry["documentation"] or entry.get("no_doc_impact_reason"),
                f"code_path {entry['code_path']} thiếu tài liệu hoặc lý do no-doc-impact",
            )

    def test_no_git_produces_honest_warning(self):
        if not (ROOT / ".git").exists():
            results = agentctl.doc_impact_results()
            self.assertEqual(results[0][0], "WARNING")
            self.assertIn("Git", results[0][2])

    def test_approval_must_cover_changed_path(self):
        with mock.patch.object(agentctl, "changed_paths", return_value=["src/new.py"]):
            with mock.patch.object(agentctl, "ROOT", ROOT):
                with mock.patch.object(Path, "exists", return_value=True):
                    self.assertFalse(agentctl.approved_change_exists(["src/new.py"]))

    def test_approval_fixture_covers_its_declared_scope(self):
        paths = [".ai/scripts/agentctl.py", ".ai/tests/test_doc_impact.py"]
        changes = agentctl.AI / "changes"
        changes.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=changes) as temp_dir:
            folder = Path(temp_dir)
            change_id = folder.name
            (folder / "request.md").write_text(f"change_id: {change_id}\n", encoding="utf-8")
            (folder / "approval.md").write_text(f"status: approved\nchange_id: {change_id}\n", encoding="utf-8")
            (folder / "impact.md").write_text("# Impact\n", encoding="utf-8")
            (folder / "scope.json").write_text(
                json.dumps({"change_id": change_id, "affected_paths": [".ai/scripts", ".ai/tests"]}),
                encoding="utf-8",
            )
            self.assertTrue(agentctl.approved_change_exists(paths))

    def test_ai_security_controller_requires_approval(self):
        changed = [".ai/scripts/agentctl.py"]
        with mock.patch.object(agentctl, "changed_paths", return_value=changed):
            with mock.patch.object(agentctl, "approved_change_exists", return_value=False):
                with mock.patch.object(Path, "exists", return_value=True):
                    results = agentctl.doc_impact_results()
        self.assertTrue(any(name == "approval" and status == "FAIL" for status, name, _ in results))


if __name__ == "__main__":
    unittest.main()
