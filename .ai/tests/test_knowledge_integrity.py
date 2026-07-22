"""Project Brain links and canonical ownership stay unambiguous."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AI = ROOT / ".ai"


class TestKnowledgeIntegrity(unittest.TestCase):
    def test_markdown_internal_links_exist(self):
        link = re.compile(r"\[[^]]+\]\((?!https?://|#)([^)]+)\)")
        for path in AI.rglob("*.md"):
            for target in link.findall(path.read_text(encoding="utf-8")):
                clean = target.split("#", 1)[0]
                if clean:
                    self.assertTrue((path.parent / clean).resolve().exists(), f"Link hỏng: {path} -> {target}")

    def test_only_ai_claims_canonical_ownership(self):
        phrase = re.compile(r"nguồn (?:sự thật|canonical)", re.I)
        for path in ROOT.rglob("*.md"):
            if any(part in {".git", "generated", "runtime"} for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8")
            if phrase.search(text) and ".ai" not in path.parts:
                self.assertIn("`.ai/`", text, f"Nguồn canonical khác .ai/: {path}")

    def test_doc_map_references_exist_or_are_marked_unverified(self):
        data = json.loads((AI / "knowledge" / "doc-map.json").read_text(encoding="utf-8"))
        for entry in data["entries"]:
            if "chưa có" in entry["code_path"]:
                self.assertIn("no_doc_impact_reason", entry)
                continue
            for field in ("documentation", "tests"):
                for item in entry[field]:
                    self.assertTrue((ROOT / item).exists(), f"Path hỏng trong doc-map: {item}")


if __name__ == "__main__":
    unittest.main()
