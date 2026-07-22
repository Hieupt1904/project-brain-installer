"""Required files exist and JSON parses."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AI = ROOT / ".ai"

REQUIRED = [
    "project.json", "policy/core.md", "policy/approvals.md", "policy/security.md",
    "knowledge/project-brief.md", "knowledge/business-rules.md", "knowledge/architecture.md",
    "knowledge/glossary.md", "knowledge/active-state.md", "knowledge/decisions.md",
    "knowledge/operations.md", "knowledge/doc-map.json",
    "skills/project-start/SKILL.md", "skills/change-intake/SKILL.md",
    "skills/impact-analysis/SKILL.md", "skills/implement-approved-change/SKILL.md",
    "skills/sync-project-knowledge/SKILL.md", "skills/project-doctor/SKILL.md",
    "scripts/agentctl.py", "scripts/build_repo_map.py", "scripts/stop_hook.py", "AGENTS.md", "CLAUDE.md", "ai",
]


class TestRequiredFiles(unittest.TestCase):
    def test_files_exist(self):
        missing = []
        for name in REQUIRED:
            base = AI if not name.startswith(("AGENTS.md", "CLAUDE.md", "ai")) else ROOT
            if not (base / name).exists():
                missing.append(name)
        self.assertEqual(missing, [], f"Thiếu file: {missing}")

    def test_json_parses(self):
        for name in ("project.json", "knowledge/doc-map.json"):
            with (AI / name).open(encoding="utf-8") as handle:
                json.load(handle)


if __name__ == "__main__":
    unittest.main()
