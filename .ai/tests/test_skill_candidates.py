"""Tests for approval-gated project-local skill candidates."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

AGENTCTL_PATH = Path(__file__).resolve().parents[1] / "scripts" / "agentctl.py"
SPEC = importlib.util.spec_from_file_location("project_brain_agentctl_skill_candidates", AGENTCTL_PATH)
agentctl = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = agentctl
SPEC.loader.exec_module(agentctl)


class SkillCandidateFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(agentctl.AI / "runtime"))
        self.root = Path(self.temp.name)
        self.ai = self.root / ".ai"
        (self.ai / "skill-candidates").mkdir(parents=True)
        (self.ai / "skills").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def patch_roots(self):
        return mock.patch.multiple(
            agentctl,
            ROOT=self.root,
            AI=self.ai,
            SKILLS=self.ai / "skills",
            CANDIDATES=self.ai / "skill-candidates",
        )

    def proposal(self, status="proposed"):
        return {
            "schema_version": "1.0",
            "candidate_id": "20260721-safe-import",
            "status": status,
            "action": "create",
            "skill_name": "safe-import",
            "scope": "project-local",
            "reason_vi": "Quy trình đã được kiểm chứng và có thể tái sử dụng.",
            "triggers_vi": ["Khi nhập dữ liệu từ nhà cung cấp."],
            "workflow_vi": ["Kiểm tra file đầu vào.", "Tạo output riêng."],
            "verification_vi": ["File gốc không bị sửa."],
            "pitfalls_vi": ["Không tự điền dữ liệu giả."],
            "affected_files": [".ai/skills/safe-import/SKILL.md"],
            "canonical_skill_md": "---\nname: safe-import\ndescription: Use when importing supported supplier data safely.\n---\n# Safe Import\n\n## Workflow\n\n1. Validate the input.\n2. Write a separate output.\n",
        }


class TestSkillCandidateValidation(SkillCandidateFixture):
    def test_valid_proposal_renders_vietnamese_approval_preview(self):
        with self.patch_roots():
            text = agentctl.render_skill_proposal_vi(self.proposal())
        self.assertIn("Đề xuất tạo skill", text)
        self.assertIn("safe-import", text)
        self.assertIn("Điều kiện kích hoạt", text)
        self.assertIn("Workflow sẽ lưu", text)
        self.assertIn("Verification bắt buộc", text)
        self.assertIn("Pitfall và giới hạn", text)
        self.assertIn("A. Phê duyệt", text)

    def test_canonical_skill_must_be_english(self):
        proposal = self.proposal()
        proposal["canonical_skill_md"] = proposal["canonical_skill_md"].replace(
            "Validate the input.", "Kiểm tra dữ liệu đầu vào."
        )
        with self.patch_roots():
            errors = agentctl.validate_skill_candidate(proposal)
        self.assertTrue(any("English" in error for error in errors), errors)

    def test_global_scope_is_rejected(self):
        proposal = self.proposal()
        proposal["scope"] = "global"
        with self.patch_roots():
            errors = agentctl.validate_skill_candidate(proposal)
        self.assertTrue(any("project-local" in error for error in errors), errors)


class TestSkillCandidateLifecycle(SkillCandidateFixture):
    def test_propose_writes_draft_only_not_canonical_skill(self):
        with self.patch_roots():
            path = agentctl.save_skill_candidate(self.proposal())
        self.assertTrue(path.is_file())
        self.assertFalse((self.ai / "skills/safe-import/SKILL.md").exists())
        stored = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(stored["status"], "proposed")

    def test_promote_refuses_candidate_without_separate_approval(self):
        proposal = self.proposal(status="proposed")
        with self.patch_roots():
            path = agentctl.save_skill_candidate(proposal)
            with self.assertRaisesRegex(ValueError, "approval"):
                agentctl.promote_skill_candidate(path)
        self.assertFalse((self.ai / "skills/safe-import/SKILL.md").exists())

    def test_promote_requires_approval_bound_to_candidate_and_content_hash(self):
        proposal = self.proposal(status="approved")
        proposal["approval"] = {
            "candidate_id": proposal["candidate_id"],
            "content_sha256": "0" * 64,
            "approved_by": "user",
            "approved_at": "2026-07-21T00:00:00+00:00",
        }
        with self.patch_roots():
            path = agentctl.save_skill_candidate(proposal)
            with self.assertRaisesRegex(ValueError, "content hash"):
                agentctl.promote_skill_candidate(path)

    def test_approved_candidate_promotes_english_skill_then_syncs(self):
        proposal = self.proposal(status="approved")
        proposal["approval"] = {
            "candidate_id": proposal["candidate_id"],
            "content_sha256": agentctl.candidate_content_sha256(proposal),
            "approved_by": "user",
            "approved_at": "2026-07-21T00:00:00+00:00",
        }
        with self.patch_roots(), mock.patch.object(agentctl, "sync_skills", return_value=[]):
            path = agentctl.save_skill_candidate(proposal)
            target = agentctl.promote_skill_candidate(path)
        self.assertEqual(target, self.ai / "skills/safe-import/SKILL.md")
        content = target.read_text(encoding="utf-8")
        self.assertIn("# Safe Import", content)
        stored = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(stored["status"], "promoted")

    def test_promote_refuses_overwrite_for_create_action(self):
        proposal = self.proposal(status="approved")
        proposal["approval"] = {
            "candidate_id": proposal["candidate_id"],
            "content_sha256": agentctl.candidate_content_sha256(proposal),
            "approved_by": "user",
            "approved_at": "2026-07-21T00:00:00+00:00",
        }
        existing = self.ai / "skills/safe-import/SKILL.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("existing\n", encoding="utf-8")
        with self.patch_roots():
            path = agentctl.save_skill_candidate(proposal)
            with self.assertRaisesRegex(ValueError, "already exists"):
                agentctl.promote_skill_candidate(path)
        self.assertEqual(existing.read_text(encoding="utf-8"), "existing\n")


if __name__ == "__main__":
    unittest.main()
