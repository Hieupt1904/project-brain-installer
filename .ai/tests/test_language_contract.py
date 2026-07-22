"""Canonical agent instructions are English and user-facing output is Vietnamese."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AI = ROOT / ".ai"


def load_agentctl():
    path = AI / "scripts" / "agentctl.py"
    spec = importlib.util.spec_from_file_location("project_brain_agentctl", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestLanguageContract(unittest.TestCase):
    def test_canonical_governance_files_declare_language_boundary(self):
        core = (AI / "policy" / "core.md").read_text(encoding="utf-8")
        operations = (AI / "knowledge" / "operations.md").read_text(encoding="utf-8")
        self.assertIn("Use English for canonical/internal instructions", core)
        self.assertIn("Return user-facing responses in Vietnamese", core)
        self.assertIn("Write canonical instructions, policies, knowledge, and agent-facing prompts in English", operations)
        self.assertIn("Present agent results to users in Vietnamese", operations)

    def test_generated_agent_adapter_uses_english_internal_contract(self):
        agentctl = load_agentctl()
        block = agentctl.canonical_adapter_block("claude")
        self.assertIn("Use English for canonical/internal instructions", block)
        self.assertIn("Return user-facing responses in Vietnamese", block)
        self.assertIn("do not infer unverified areas", block.lower())
        self.assertNotIn("chờ người dùng xác nhận", block)

    def test_user_facing_i18n_layer_exists(self):
        i18n = ROOT / "docs" / "i18n" / "vi"
        self.assertTrue((i18n / "README.md").is_file())
        self.assertTrue((i18n / "workflow.md").is_file())
        self.assertIn("Input gửi vào agent: tiếng Anh", (i18n / "README.md").read_text(encoding="utf-8"))
        self.assertIn("Output agent trả về người dùng: tiếng Việt", (i18n / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
