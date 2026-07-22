#!/usr/bin/env python3
"""Safe, evidence-based project reconnaissance (standard library only)."""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path

SCHEMA = "1.0"
SKIP_NAMES = {".git", ".env", ".env.local", ".env.production", "node_modules", "vendor", "dist", "build", "coverage", "__pycache__"}
MANIFESTS = {"package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml", "Makefile", "docker-compose.yml", "docker-compose.yaml"}
SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs", ".rb", ".php"}

def safe(path: Path, root: Path) -> bool:
    try:
        if path.is_symlink(): return False
        resolved, base = path.resolve(), root.resolve()
        return resolved == base or base in resolved.parents
    except OSError: return False

def excluded(path: Path, root: Path) -> bool:
    return any(part in SKIP_NAMES or part.startswith(".env") for part in path.relative_to(root).parts)

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def evidence(root: Path) -> list[dict]:
    found = []
    for base, dirs, files in os.walk(root, followlinks=False):
        base_path = Path(base); dirs[:] = [d for d in dirs if d not in SKIP_NAMES and not d.startswith(".env")]
        for name in files:
            path = base_path / name
            if excluded(path, root) or not safe(path, root): continue
            rel = path.relative_to(root).as_posix()
            if name in MANIFESTS or path.suffix.lower() in SOURCE_EXTENSIONS:
                try: size = path.stat().st_size
                except OSError: continue
                found.append({"path": rel, "sha256": digest(path), "kind": "manifest" if name in MANIFESTS else "source", "size": size})
    return sorted(found, key=lambda x: x["path"])

def runtime_facts(root: Path) -> dict:
    result = {}
    path = root / ".ai/runtime/model-evidence.json"
    if safe(path, root) and path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError): data = {}
    else: data = {}
    for key in ("stt_model", "stt_provider", "tts_model", "tts_provider"):
        value = data.get(key)
        result[key] = {"value": value if isinstance(value, str) else None, "certainty": "verified" if isinstance(value, str) and value else "unknown", "evidence": ".ai/runtime/model-evidence.json" if value else None}
    return result

def reconnoitre(root: Path) -> tuple[Path, Path, Path]:
    root = root.expanduser().absolute(); out = root / ".ai/recon"; out.mkdir(parents=True, exist_ok=True)
    files = evidence(root)
    inventory = {"schema_version": SCHEMA, "files": files}
    evidence_doc = {"schema_version": SCHEMA, "evidence": [{"path": x["path"], "kind": x["kind"], "sha256": x["sha256"]} for x in files]}
    facts = {"schema_version": SCHEMA, "facts": runtime_facts(root), "certainty_values": ["verified", "inherited", "inferred", "unknown", "conflicted"]}
    paths = (out / "inventory.json", out / "evidence.json", out / "facts.json")
    for path, data in zip(paths, (inventory, evidence_doc, facts)):
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return paths

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", nargs="?", default=".")
    for path in reconnoitre(Path(parser.parse_args().root)): print(path)

reconnaissance = reconnoitre
