"""Evidence-based project reconnaissance tests."""
import importlib.util, json, sys, tempfile, unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts" / "recon.py"
SPEC = importlib.util.spec_from_file_location("project_brain_recon", PATH)
recon = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = recon; SPEC.loader.exec_module(recon)

class TestRecon(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_scans_safe_manifest_and_source_without_env_values(self):
        (self.root / "package.json").write_text(json.dumps({"name":"voice-app","dependencies":{"express":"1","openai":"1"},"scripts":{"test":"node test.js"}}))
        (self.root / "app.py").write_text("import flask\n")
        (self.root / ".env").write_text("OPENAI_API_KEY=super-secret-value\nTTS_MODEL=secret-model\n")
        outputs = recon.reconnoitre(self.root)
        inventory = json.loads(outputs[0].read_text())
        facts = json.loads(outputs[2].read_text())
        blob = " ".join(path.read_text() for path in outputs)
        self.assertIn("package.json", [x["path"] for x in inventory["files"]])
        self.assertNotIn(".env", [x["path"] for x in inventory["files"]])
        self.assertNotIn("super-secret-value", blob)
        self.assertNotIn("secret-model", blob)
        self.assertNotIn("tts_model", facts["facts"])
        self.assertNotIn("stt_provider", facts["facts"])

    def test_runtime_evidence_can_verify_model_and_changed_evidence_is_revalidated(self):
        runtime = self.root / ".ai/runtime/model-evidence.json"; runtime.parent.mkdir(parents=True)
        runtime.write_text(json.dumps({"tts_model":"gpt-4o-mini-tts","tts_provider":"openai"}))
        outputs = recon.reconnoitre(self.root)
        first = json.loads(outputs[2].read_text())
        self.assertEqual(first["facts"]["tts_model"]["certainty"], "verified")
        runtime.write_text(json.dumps({"tts_model":"other"}))
        second = json.loads(recon.reconnoitre(self.root)[2].read_text())
        self.assertEqual(second["facts"]["tts_model"]["value"], "other")
        self.assertNotIn("tts_provider", second["facts"])

    def test_symlink_evidence_is_ignored(self):
        outside = self.root.parent / "outside-package.json"; outside.write_text('{"name":"outside"}')
        (self.root / "package.json").symlink_to(outside)
        inventory = json.loads(recon.reconnoitre(self.root)[0].read_text())
        self.assertEqual(inventory["files"], [])

if __name__ == "__main__": unittest.main()
