#!/usr/bin/env python3
"""Project Brain CLI. Python standard library only."""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
AI = ROOT / ".ai"
SKILLS = AI / "skills"
CANDIDATES = AI / "skill-candidates"
GENERATED = AI / "generated"
RUNTIME = AI / "runtime"
SCHEMA = "1.0"
BRIEF_LIMIT = 12_000
GENERATED_WARNING = "<!-- GENERATED FILE — DO NOT EDIT DIRECTLY -->"
MAX_COMMAND_LENGTH = 240
ALLOWED_COMMAND = re.compile(r"^[A-Za-z0-9_./ '*-]+$")
ALLOWED_EXECUTABLES = {
    "python", "python3", "pytest", "npm", "npx", "pnpm", "yarn", "bun",
    "cargo", "go", "mvn", "gradle", "./gradlew", "make", "just", "ruff",
    "black", "eslint", "prettier", "tsc", "php", "composer", "dotnet", "java",
    "kotlinc",
}
FORBIDDEN_COMMAND_ARGUMENTS = {"-c", "--command", "--eval", "-e"}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(r"(?:api[_-]?key|secret|password|token|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=.]{12,}", re.I),
    re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9_\-.=+/]{20,}\b", re.I),
]
REQUIRED = [
    AI / "project.json", AI / "policy/core.md", AI / "policy/approvals.md", AI / "policy/security.md",
    AI / "knowledge/project-brief.md", AI / "knowledge/business-rules.md", AI / "knowledge/architecture.md",
    AI / "knowledge/glossary.md", AI / "knowledge/active-state.md", AI / "knowledge/decisions.md",
    AI / "knowledge/operations.md", AI / "knowledge/doc-map.json",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_path(path: Path, root: Path = ROOT, allow_missing: bool = False) -> bool:
    """Reject symlinks and paths resolving outside the allowed root."""
    try:
        root_resolved = root.resolve()
        current = path
        while True:
            if current.is_symlink():
                return False
            if current.exists():
                break
            if not allow_missing:
                return False
            if current == current.parent:
                return False
            current = current.parent
        resolved = path.resolve(strict=not allow_missing)
        return resolved == root_resolved or root_resolved in resolved.parents
    except (OSError, RuntimeError):
        return False


def safe_read(path: Path, root: Path = ROOT) -> str:
    if not safe_path(path, root):
        raise ValueError(f"Path không an toàn hoặc là symlink: {path}")
    return path.read_text(encoding="utf-8")


def safe_write(path: Path, content: str, root: Path = ROOT) -> None:
    if path.exists() and path.is_symlink():
        raise ValueError(f"Từ chối ghi qua symlink: {path}")
    if not safe_path(path.parent, root, allow_missing=True):
        raise ValueError(f"Thư mục ghi không an toàn: {path.parent}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise ValueError(f"Từ chối ghi qua symlink: {path}")
    # Atomic replacement in the trusted directory avoids partial output.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
    try:
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def command_argv(command: str) -> list[str]:
    """Parse a configured command without invoking a shell; reject dangerous commands."""
    if not isinstance(command, str) or len(command) > MAX_COMMAND_LENGTH or not ALLOWED_COMMAND.fullmatch(command):
        raise ValueError(f"command không hợp lệ: {str(command)[:60]}")
    argv = shlex.split(command)
    if not argv or any(any(op in item for op in (";", "&&", "|", "\n", "\r")) for item in argv):
        raise ValueError(f"command chứa shell operator: {command[:60]}")
    executable = argv[0]
    if executable not in ALLOWED_EXECUTABLES:
        raise ValueError(f"executable không được phép: {executable}")
    for arg in argv[1:]:
        if any(arg.startswith(f"{prefix}") for prefix in FORBIDDEN_COMMAND_ARGUMENTS):
            raise ValueError(f"argument nguy hiểm bị từ chối: {arg}")
    return argv


def validate_project(project: dict) -> list[str]:
    errors: list[str] = []
    list_fields = ("language", "framework", "build_commands", "test_commands", "lint_commands", "format_commands", "source_paths", "test_paths", "documentation_paths", "context_exclude_paths", "high_risk_areas")
    for field in list_fields:
        if not isinstance(project.get(field), list) or not all(isinstance(item, str) for item in project[field]):
            errors.append(f"{field} phải là danh sách chuỗi")
    for field in ("project_name", "purpose", "project_type", "verification_status"):
        if not isinstance(project.get(field), str):
            errors.append(f"{field} phải là chuỗi")
    for field in ("build_commands", "test_commands", "lint_commands", "format_commands"):
        for command in project.get(field, []):
            try:
                command_argv(command)
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def load_json(path: Path) -> dict:
    value = json.loads(safe_read(path))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root phải là object: {path}")
    errors = validate_project(value) if path == AI / "project.json" else []
    if errors:
        raise ValueError("project.json không hợp lệ: " + "; ".join(errors))
    return value


def run(command: list[str], cwd: Path = ROOT) -> tuple[int, str]:
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=60, shell=False)
        return result.returncode, (result.stdout + result.stderr).strip()[:4000]
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)


def git_info() -> dict[str, str]:
    info = {"branch": "not verified", "head": "not verified", "status": "Git is unavailable or not initialized", "recent": ""}
    code, out = run(["git", "branch", "--show-current"])
    if code == 0:
        info["branch"] = out or "detached HEAD"
        _, info["head"] = run(["git", "rev-parse", "--short", "HEAD"])
        _, info["status"] = run(["git", "status", "--short"])
        _, info["recent"] = run(["git", "log", "-5", "--oneline"])
    return info


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_dirs() -> list[Path]:
    if not safe_path(SKILLS):
        raise ValueError(f"Thư mục skills không an toàn: {SKILLS}")
    return sorted(
        p for p in SKILLS.iterdir()
        if p.is_dir() and not p.is_symlink() and safe_path(p)
        and (p / "SKILL.md").is_file() and not (p / "SKILL.md").is_symlink()
        and safe_path(p / "SKILL.md")
    )


def parse_frontmatter(path: Path) -> dict[str, str] | None:
    text = safe_read(path)
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def markdown_safe(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("`", "\\`").replace("\n", " ").replace("\r", " ")


def scan_paths(paths: Iterable[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_file() and safe_path(path):
            try:
                if contains_secret(safe_read(path)):
                    found.append(path)
            except (OSError, ValueError, UnicodeDecodeError):
                found.append(path)
    return found


def protected_paths() -> list[Path]:
    paths = [
        AI / "project.json", ROOT / "AGENTS.md", ROOT / "CLAUDE.md",
        ROOT / ".claude" / "settings.json",
    ]
    for root in (
        AI / "knowledge", AI / "policy", AI / "skills", AI / "changes", AI / "runtime",
        ROOT / ".agents" / "skills", ROOT / ".claude" / "skills",
    ):
        if root.exists() and safe_path(root):
            paths.extend(
                path for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt", ".log"}
            )
    return paths


def adapter_text(source: Path, generated_at: str) -> str:
    return (
        f"{GENERATED_WARNING}\n<!-- canonical: {rel(source)} -->\n"
        f"<!-- generated_at: {generated_at} -->\n<!-- source_sha256: {sha256(source)} -->\n"
        f"<!-- schema_version: {SCHEMA} -->\n\n{safe_read(source)}"
    )


def adapter_is_valid(source: Path, target: Path) -> bool:
    if not target.is_file() or target.is_symlink() or not safe_path(target):
        return False
    try:
        actual = safe_read(target)
        expected = adapter_text(source, "__GENERATED_AT__")
        actual_lines = actual.splitlines()
        expected_lines = expected.splitlines()
        if len(actual_lines) != len(expected_lines):
            return False
        if actual_lines[:2] != expected_lines[:2] or actual_lines[3:] != expected_lines[3:]:
            return False
        return actual_lines[2].startswith("<!-- generated_at: ") and actual_lines[2].endswith(" -->")
    except (OSError, ValueError, UnicodeDecodeError):
        return False


def path_matches_scope(path: str, scopes: Iterable[str]) -> bool:
    normalized = path.rstrip("/")
    return any(
        normalized == scope.rstrip("/")
        or normalized.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def approved_change_exists(changed: Iterable[str] | None = None) -> bool:
    changed_paths_set = list(changed or [])
    for folder in sorted((AI / "changes").glob("*")):
        approval = folder / "approval.md"
        request = folder / "request.md"
        impact = folder / "impact.md"
        scope_path = folder / "scope.json"
        try:
            approval_text = safe_read(approval)
            if not re.search(r"(?im)^status:\s*approved\s*$", approval_text):
                continue
            request_text = safe_read(request)
            if not request.is_file() or not impact.is_file() or not scope_path.is_file():
                continue
            scope = load_json(scope_path)
            if scope.get("change_id") not in request_text and scope.get("change_id") not in approval_text:
                continue
            affected = scope.get("affected_paths", [])
            if isinstance(affected, list) and all(isinstance(item, str) for item in affected):
                if not changed_paths_set or all(path_matches_scope(path, affected) for path in changed_paths_set):
                    return True
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return False


SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VIETNAMESE_TEXT_PATTERN = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.I,
)
SKILL_LAYERS = ("governance", "development", "operations", "domain")


def parse_skill_metadata(path: Path) -> dict[str, object]:
    """Return name, description, layer, and trigger_keywords from a SKILL.md frontmatter."""
    front = parse_frontmatter(path)
    if not front:
        raise ValueError(f"Skill frontmatter không hợp lệ: {path}")
    raw = safe_read(path)
    end = raw.find("\n---", 4)
    body = raw[end + 5:] if end >= 0 else ""
    first_heading = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), "")
    layer = front.get("layer", "").strip()
    if layer not in SKILL_LAYERS:
        # Infer from heading keywords as a fallback so existing skills are not broken.
        lower = (front.get("description", "") + " " + first_heading).lower()
        layer = "governance" if any(w in lower for w in ("approval", "policy", "reconnaissance", "change", "doctor", "sync", "start", "skill")) else "development"
    keywords = [kw.strip() for kw in re.split(r"[,;]", front.get("trigger_keywords", "")) if kw.strip()]
    if not keywords:
        words = re.findall(r"[a-z]{4,}", (front.get("description", "") + " " + first_heading).lower())
        keywords = sorted(set(words), key=words.index)[:3]
    return {
        "name": front.get("name", path.parent.name).strip(),
        "description": front.get("description", "").strip(),
        "layer": layer,
        "trigger_keywords": keywords,
    }


def render_skills_catalog() -> str:
    """Render a compact catalog table of every canonical skill for fast discovery."""
    rows: list[str] = [
        GENERATED_WARNING,
        "# Skills catalog",
        "",
        "| Skill | Layer | Trigger keywords | Description |",
        "|---|---|---|---|",
    ]
    for directory in skill_dirs():
        metadata = parse_skill_metadata(directory / "SKILL.md")
        name = metadata["name"]
        layer = metadata["layer"]
        keywords = ", ".join(metadata["trigger_keywords"])
        description = markdown_safe(metadata["description"])[:120]
        rows.append(f"| `{name}` | {layer} | {keywords} | {description} |")
    rows.append("")
    return "\n".join(rows) + "\n"


def build_skills_catalog() -> Path:
    target = GENERATED / "skills-catalog.md"
    write_generated(target, render_skills_catalog())
    return target


_EVIDENCE_MANIFESTS = {
    "package.json": "JavaScript/Node capability detected",
    "pyproject.toml": "Python capability detected",
    "requirements.txt": "Python capability detected",
    "go.mod": "Go capability detected",
    "Cargo.toml": "Rust capability detected",
    "pom.xml": "Java/Maven capability detected",
    "composer.json": "PHP capability detected",
}
_EVIDENCE_SOURCE = {
    ".ts": "TypeScript source detected",
    ".tsx": "TypeScript source detected",
    ".js": "JavaScript source detected",
    ".jsx": "JavaScript source detected",
    ".py": "Python source detected",
    ".go": "Go source detected",
    ".rs": "Rust source detected",
    ".java": "Java source detected",
    ".php": "PHP source detected",
    ".rb": "Ruby source detected",
    ".cs": "C# source detected",
    ".kt": "Kotlin source detected",
    ".swift": "Swift source detected",
}
_EVIDENCE_INFRA = {
    "docker-compose.yml": "container capability detected",
    "docker-compose.yaml": "container capability detected",
    "Dockerfile": "container capability detected",
    ".github/workflows": "CI/CD capability detected",
    "Makefile": "build automation capability detected",
}
_EVIDENCE_DB = {
    "migrations": "database migration path detected",
    "migration": "database migration path detected",
    "schema.sql": "database schema file detected",
    "prisma": "database schema capability detected",
}
_EVIDENCE_AI = {
    "CLAUDE.md": "Claude Code adapter detected",
    "AGENTS.md": "Codex adapter detected",
    ".claude": "Claude Code configuration detected",
    ".agents": "Codex configuration detected",
    ".cursorrules": "Cursor configuration detected",
    ".cursor/rules": "Cursor configuration detected",
    ".github/copilot-instructions.md": "Copilot configuration detected",
}


def _detect_evidence() -> list[str]:
    """Detect safe evidence from manifest, source, infra, and AI-config files."""
    findings: list[str] = []
    seen_descriptions: set[str] = set()

    def add(path: Path, description: str) -> None:
        key = description
        if key not in seen_descriptions and safe_path(path, allow_missing=True):
            findings.append(f"- `{rel(path)}` — {description}")
            seen_descriptions.add(key)

    for name, description in _EVIDENCE_MANIFESTS.items():
        candidate = ROOT / name
        if candidate.is_file() and not candidate.is_symlink() and safe_path(candidate):
            add(candidate, description)
    for name, description in _EVIDENCE_INFRA.items():
        candidate = ROOT / name
        if candidate.exists() and not candidate.is_symlink() and safe_path(candidate):
            add(candidate, description)
    for pattern, description in _EVIDENCE_DB.items():
        for candidate in ROOT.rglob(pattern):
            if candidate.is_file() and not candidate.is_symlink() and safe_path(candidate) and not should_exclude(Path(rel(candidate))):
                add(candidate, description)
                break
    extensions_found: set[str] = set()
    for candidate in ROOT.rglob("*"):
        if not candidate.is_file() or candidate.is_symlink() or not safe_path(candidate):
            continue
        if should_exclude(Path(rel(candidate))):
            continue
        suffix = candidate.suffix.lower()
        if suffix in _EVIDENCE_SOURCE and suffix not in extensions_found:
            extensions_found.add(suffix)
            add(candidate, _EVIDENCE_SOURCE[suffix])
    for name, description in _EVIDENCE_AI.items():
        candidate = ROOT / name
        if candidate.exists() and not candidate.is_symlink() and safe_path(candidate):
            add(candidate, description)

    return sorted(findings)


def render_recommended_skills() -> str:
    """Render evidence-based skill recommendations with honest unknowns."""
    evidence = _detect_evidence()
    lines = [
        GENERATED_WARNING,
        "# Recommended skills",
        "",
        "## Always recommended",
        "",
        "- `project-start`",
        "- `project-doctor`",
        "- `project-reconnaissance`",
        "",
    ]
    if evidence:
        lines += ["## Evidence detected", ""]
        lines += evidence
        lines += [""]
    else:
        lines += ["## Evidence detected", "", "- No supported manifest, source, or infrastructure evidence was detected.", ""]
    lines += [
        "## Recommended next action",
        "",
        "1. Load `project-reconnaissance`.",
        "2. Confirm detected capabilities.",
        "3. Read only files relevant to the current request.",
        "4. Do not infer unverified database, auth, API, provider, or deployment facts.",
        "",
        "## Unknown areas",
        "",
        "- Database: not verified",
        "- Authentication: not verified",
        "- Authorization: not verified",
        "- Deployment: not verified",
        "- CI/CD: not verified",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_recommended_skills() -> Path:
    target = GENERATED / "recommended-skills.md"
    write_generated(target, render_recommended_skills())
    return target



def candidate_content_sha256(candidate: dict) -> str:
    """Bind approval to the exact canonical skill body presented for creation."""
    content = candidate.get("canonical_skill_md", "")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def validate_skill_candidate(candidate: dict) -> list[str]:
    """Validate an approval proposal without writing canonical project knowledge."""
    errors: list[str] = []
    required_strings = (
        "schema_version", "candidate_id", "status", "action", "skill_name",
        "scope", "reason_vi", "canonical_skill_md",
    )
    for field in required_strings:
        if not isinstance(candidate.get(field), str) or not candidate[field].strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ("triggers_vi", "workflow_vi", "verification_vi", "pitfalls_vi", "affected_files"):
        value = candidate.get(field)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
            errors.append(f"{field} must be a non-empty string list")
    if candidate.get("schema_version") != SCHEMA:
        errors.append(f"schema_version must be {SCHEMA}")
    if candidate.get("scope") != "project-local":
        errors.append("scope must be project-local; global Hermes skills are outside Project Brain")
    if candidate.get("action") not in {"create", "update"}:
        errors.append("action must be create or update")
    name = candidate.get("skill_name", "")
    if not SKILL_NAME_PATTERN.fullmatch(name):
        errors.append("skill_name must use lowercase kebab-case")
    expected = f".ai/skills/{name}/SKILL.md"
    if expected not in candidate.get("affected_files", []):
        errors.append(f"affected_files must include {expected}")
    canonical = candidate.get("canonical_skill_md", "")
    if not canonical.startswith("---\n") or f"name: {name}" not in canonical:
        errors.append("canonical_skill_md must have valid frontmatter matching skill_name")
    if VIETNAMESE_TEXT_PATTERN.search(canonical):
        errors.append("canonical_skill_md must be written in English")
    if contains_secret(canonical) or any(contains_secret(str(candidate.get(field, ""))) for field in required_strings):
        errors.append("candidate contains a secret pattern")
    return errors


def render_skill_proposal_vi(candidate: dict) -> str:
    """Render the mandatory user-facing approval preview in Vietnamese."""
    errors = validate_skill_candidate(candidate)
    if errors:
        raise ValueError("Skill candidate không hợp lệ: " + "; ".join(errors))
    action = "tạo" if candidate["action"] == "create" else "cập nhật"
    bullets = lambda values: "\n".join(f"- {item}" for item in values)
    return f"""## Đề xuất {action} skill

### Lý do
{candidate['reason_vi']}

### Skill dự kiến
- **Tên:** `{candidate['skill_name']}`
- **Phạm vi:** project-local
- **File canonical:** `.ai/skills/{candidate['skill_name']}/SKILL.md`

### Điều kiện kích hoạt
{bullets(candidate['triggers_vi'])}

### Workflow sẽ lưu
{bullets(candidate['workflow_vi'])}

### Verification bắt buộc
{bullets(candidate['verification_vi'])}

### Pitfall và giới hạn
{bullets(candidate['pitfalls_vi'])}

### File dự kiến thay đổi
{bullets(candidate['affected_files'])}

Canonical `SKILL.md` sẽ được viết bằng tiếng Anh. Proposal này chưa tạo hoặc sửa skill.

**A. Phê duyệt đúng nội dung trên**
**B. Sửa proposal trước khi tạo**
**C. Chỉ giữ candidate draft**
**D. Không tạo**
"""


def save_skill_candidate(candidate: dict) -> Path:
    """Persist a proposal record only; never create the canonical skill here."""
    errors = validate_skill_candidate(candidate)
    if errors:
        raise ValueError("Skill candidate không hợp lệ: " + "; ".join(errors))
    candidate_id = candidate["candidate_id"]
    if not SKILL_NAME_PATTERN.fullmatch(candidate_id.replace("_", "-")):
        raise ValueError("candidate_id không an toàn")
    path = CANDIDATES / candidate_id / "candidate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_write(path, json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True) + "\n", root=AI)
    return path


def promote_skill_candidate(candidate_path: Path) -> Path:
    """Promote only a separately approved, hash-bound project-local candidate."""
    candidate = load_json(candidate_path)
    errors = validate_skill_candidate(candidate)
    if errors:
        raise ValueError("Skill candidate không hợp lệ: " + "; ".join(errors))
    approval = candidate.get("approval")
    if candidate.get("status") != "approved" or not isinstance(approval, dict):
        raise ValueError("Skill candidate requires separate user approval")
    if approval.get("candidate_id") != candidate["candidate_id"]:
        raise ValueError("Skill approval is not bound to this candidate")
    if approval.get("content_sha256") != candidate_content_sha256(candidate):
        raise ValueError("Skill approval content hash does not match the canonical skill")
    if approval.get("approved_by") != "user" or not approval.get("approved_at"):
        raise ValueError("Skill approval must record the user and approval time")
    target = SKILLS / candidate["skill_name"] / "SKILL.md"
    if candidate["action"] == "create" and target.exists():
        raise ValueError(f"Skill already exists: {rel(target)}")
    if candidate["action"] == "update" and not target.is_file():
        raise ValueError(f"Skill does not exist for update: {rel(target)}")
    safe_write(target, candidate["canonical_skill_md"].rstrip() + "\n")
    candidate = dict(candidate)
    candidate["status"] = "promoted"
    candidate["promoted_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    safe_write(candidate_path, json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    sync_skills()
    return target


def sync_skills() -> list[str]:
    found = scan_paths([p for p in protected_paths() if p.is_file()])
    if found:
        raise ValueError("Phát hiện secret pattern trước khi sync: " + ", ".join(rel(p) for p in found))
    changed: list[str] = []
    for destination_root in skill_adapter_roots_for_targets():
        if destination_root.exists() and destination_root.is_symlink():
            raise ValueError(f"Từ chối adapter root là symlink: {destination_root}")
        destination_root.mkdir(parents=True, exist_ok=True)
        for source_dir in skill_dirs():
            source = source_dir / "SKILL.md"
            destination = destination_root / source_dir.name
            if destination.exists() and destination.is_symlink():
                raise ValueError(f"Từ chối adapter directory là symlink: {destination}")
            destination.mkdir(parents=True, exist_ok=True)
            target = destination / "SKILL.md"
            if target.exists() and target.is_symlink():
                raise ValueError(f"Từ chối adapter file là symlink: {target}")
            if adapter_is_valid(source, target):
                continue
            generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
            safe_write(target, adapter_text(source, generated_at))
            changed.append(rel(target))
    return changed


def sync_adapter(path: Path, generated: str) -> bool:
    if path.exists() and (path.is_symlink() or not safe_path(path)):
        raise ValueError(f"Từ chối adapter không an toàn: {path}")
    if contains_secret(generated):
        raise ValueError(f"Từ chối đồng bộ adapter có secret pattern: {path}")
    begin, end = "<!-- BEGIN AI-GENERATED -->", "<!-- END AI-GENERATED -->"
    # Legacy files are user-owned: only replace a block previously managed by us.
    # A file without our marker receives an opt-in marker only through adopt().
    if path.exists() and begin not in safe_read(path):
        return False
    existing = safe_read(path) if path.exists() else ""
    if begin in existing and end not in existing:
        raise ValueError(f"Adapter marker không đầy đủ: {path}")

    block = f"{begin}\n{generated.rstrip()}\n{end}"
    existing = safe_read(path) if path.exists() else ""
    if begin in existing and end in existing:
        before, after = existing.split(begin, 1)[0], existing.split(end, 1)[1]
        content = before + block + after
    else:
        content = (existing.rstrip() + "\n\n" if existing.strip() else "") + block + "\n"
    if content != existing:
        safe_write(path, content)
        return True
    return False


def canonical_adapter_block(kind: str) -> str:
    project_path = AI / "project.json"
    project = load_json(project_path)
    tests = "\n".join(f"- `{markdown_safe(command)}`" for command in project.get("test_commands", [])) or "- Not verified"
    risks = ", ".join(markdown_safe(item) for item in project.get("high_risk_areas", []))
    status = markdown_safe(project.get("verification_status", "not verified"))
    return f"""{GENERATED_WARNING}
<!-- canonical: .ai/project.json + .ai/policy/ -->
<!-- generated_at: {dt.datetime.fromtimestamp(project_path.stat().st_mtime, dt.timezone.utc).replace(microsecond=0).isoformat()} -->
<!-- source_sha256: {sha256(project_path)} -->
<!-- schema_version: {SCHEMA} -->
# Project Brain instructions

The source of truth is under `.ai/`; do not read the entire repository at session start.

Before work, run `./ai start`. Before a significant change, use the `change-intake` skill and obtain explicit user approval.

After a change, run `./ai check`; before ending, run `./ai doctor`. Do not edit generated files directly.

## Verified commands
{tests}

## High-risk areas
{risks}

## Project status
{status}

## Language contract

- Use English for canonical/internal instructions and all prompts sent to agents.
- Return user-facing responses in Vietnamese.

{('Claude Code: read the session brief and only the proposed files; do not infer unverified areas.' if kind == 'claude' else 'Codex: use the skill adapters under `.agents/skills/`; keep canonical content under `.ai/.')}
"""


def should_exclude(relative: Path, patterns: Iterable[str] | None = None) -> bool:
    defaults = [".env", ".env.*", "*.pem", "*.key", "*credential*", "*secret*", "*token*", "*.db", "*.sqlite*", ".git", ".ai/generated", ".ai/runtime", ".aws", ".ssh", ".gnupg", ".npmrc", ".pypirc", "credentials", "credentials.json", "node_modules", "vendor", "dist", "build", "coverage", "__pycache__"]
    normalized = relative.as_posix().lstrip("./")
    parts = Path(normalized).parts
    for pattern in defaults + list(patterns or []):
        clean = pattern.lstrip("./")
        if fnmatch.fnmatch(normalized, clean) or fnmatch.fnmatch(Path(normalized).name, clean) or any(fnmatch.fnmatch(part, clean) for part in parts) or normalized.startswith(clean.rstrip("/") + "/"):
            return True
    return False


def write_generated(path: Path, content: str) -> None:
    if contains_secret(content):
        raise ValueError(f"Từ chối ghi generated context có secret pattern: {path}")
    safe_write(path, content, GENERATED)


def within_brief_limit(content: str) -> str:
    """Trim UTF-8 output while reserving one byte for a final newline."""
    encoded = content.encode("utf-8")[:BRIEF_LIMIT - 1]
    return encoded.decode("utf-8", errors="ignore").rstrip() + "\n"


def build_repo_map() -> Path:
    project = load_json(AI / "project.json")
    lines = [GENERATED_WARNING, "# Repository map", "", f"- Generated from: Git HEAD `{markdown_safe(git_info()['head'])}`", "- Scope: metadata-only; no full source dump", "", "## Structure"]
    entries: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and not should_exclude(Path(rel(path)), project.get("context_exclude_paths", [])) and path.stat().st_size <= 512_000:
            entries.append(f"- `{markdown_safe(rel(path))}`")
    lines.extend(entries[:500] or ["- No business application source code."])
    lines.extend(["", "## Entry points", "- Not verified.", "", "## Main modules", "- Not verified.", "", "## Commands"])
    for key in ("build_commands", "test_commands", "lint_commands", "format_commands"):
        lines.append(f"- {key}: {', '.join(markdown_safe(item) for item in project.get(key, [])) or 'Not verified'}")
    lines.extend(["", "## Main documentation", "- `.ai/knowledge/`", "- `.ai/policy/`", "- `docs/i18n/vi/`"])
    target = GENERATED / "repo-map.md"
    write_generated(target, within_brief_limit("\n".join(lines)))
    return target


def create_brief() -> Path:
    project = load_json(AI / "project.json")
    active = safe_read(AI / "knowledge/active-state.md")
    decisions = safe_read(AI / "knowledge/decisions.md")
    git = git_info()
    text = f"""{GENERATED_WARNING}
# Session brief

## 1. Project purpose
{markdown_safe(project.get('purpose', 'Not verified'))}

## 2. Current branch and commit
- Branch: {markdown_safe(git['branch'])}
- HEAD: {markdown_safe(git['head'])}

## 3. Working tree status
{markdown_safe(git['status'] or 'Clean')}

## 4. Active work
{active}

## 5. Recent decisions
{decisions}

## 6. Known risks
{', '.join(markdown_safe(item) for item in project.get('high_risk_areas', []))}

## 7. Test commands
{chr(10).join('- ' + markdown_safe(x) for x in project.get('test_commands', ['Not verified']))}

## 8. Sources read
- `.ai/project.json`
- `.ai/knowledge/active-state.md`
- `.ai/knowledge/decisions.md`
- `.ai/knowledge/operations.md`
- `.ai/generated/repo-map.md`

## 9. Not verified
The repository has no business application source code. Language, framework, build/lint/format, database, authentication, external integrations, and CI/CD are not verified.

## 10. Suggested next steps
- Confirm the project name and purpose when application source code appears.
- Run `./ai doctor`.
- Read only the files relevant to the current request; do not read the entire repository.

## 11. Language contract
- Canonical content and prompts sent to agents use English.
- User-facing responses use Vietnamese.
"""
    target = GENERATED / "session-brief.md"
    write_generated(target, within_brief_limit(text))
    return target


def find_symlinks() -> list[Path]:
    roots = [AI / "knowledge", AI / "policy", AI / "skills", ROOT / ".agents", ROOT / ".claude"]
    found: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for base, dirs, files in os.walk(root, followlinks=False):
            base_path = Path(base)
            for name in dirs + files:
                candidate = base_path / name
                if candidate.is_symlink():
                    found.append(candidate)
    return found


def run_configured_commands(project: dict) -> list[tuple[str, int, str]]:
    results = []
    for field in ("build_commands", "test_commands", "lint_commands", "format_commands"):
        for command in project.get(field, []):
            results.append((field, *run(command_argv(command))))
    return results


def doctor(quick: bool = False) -> int:
    results: list[tuple[str, str, str]] = []
    leaked = scan_paths(protected_paths())
    if leaked:
        results.append(("FAIL", "secret-scan", "Phát hiện mẫu secret trong: " + ", ".join(rel(p) for p in leaked)))
    else:
        results.append(("PASS", "secret-scan", ""))
    for path in REQUIRED:
        results.append(("PASS" if path.is_file() and not path.is_symlink() else "FAIL", f"required:{rel(path)}", "" if path.is_file() and not path.is_symlink() else "Tạo file hoặc xóa symlink."))
    project: dict | None = None
    try:
        project = load_json(AI / "project.json")
        results.append(("PASS", "project.json valid", ""))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        results.append(("FAIL", "project.json valid", str(exc)))
    try:
        skills = skill_dirs()
        for directory in skills:
            front = parse_frontmatter(directory / "SKILL.md")
            metadata = parse_skill_metadata(directory / "SKILL.md") if front else {}
            valid = (
                bool(front)
                and front.get("name") == directory.name
                and len(front.get("description", "")) >= 20
                and front.get("layer") in SKILL_LAYERS
                and bool(front.get("trigger_keywords", "").strip())
                and bool(metadata.get("trigger_keywords"))
            )
            if not valid:
                results.append(("FAIL", f"skill:{directory.name}", "Frontmatter/name/description/layer/trigger_keywords không hợp lệ."))
            else:
                results.append(("PASS", f"skill:{directory.name}", ""))
    except (OSError, ValueError) as exc:
        results.append(("FAIL", "skills boundary", str(exc)))
    symlinks = find_symlinks()
    if symlinks:
        results.append(("FAIL", "symlink-boundary", "Từ chối symlink: " + ", ".join(rel(p) for p in symlinks[:10])))
    if not quick:
        for source in skill_dirs():
            for root in skill_adapter_roots_for_targets():
                target = root / source.name / "SKILL.md"
                results.append(("PASS" if adapter_is_valid(source / "SKILL.md", target) else "FAIL", f"adapter:{rel(target)}", "" if adapter_is_valid(source / "SKILL.md", target) else "Chạy `./ai sync`."))
        for generated in (GENERATED / "session-brief.md", GENERATED / "repo-map.md"):
            valid = generated.is_file() and not generated.is_symlink() and generated.stat().st_size <= BRIEF_LIMIT and not contains_secret(safe_read(generated))
            results.append(("PASS" if valid else "FAIL", f"generated:{rel(generated)}", "" if valid else "Thiếu, quá dài, symlink hoặc có secret."))
        if project is not None:
            if not (ROOT / ".git").exists():
                results.append(("WARNING", "git", "Repository chưa có Git; branch/HEAD/history chưa xác minh."))
            for key in ("build_commands", "lint_commands", "format_commands"):
                if not project.get(key):
                    results.append(("WARNING", key, "Chưa có lệnh ứng dụng được xác minh trong repository."))
            for field, code, output in run_configured_commands(project):
                results.append(("PASS" if code == 0 else "FAIL", field, output or "command thành công"))
    for status, name, fix in results:
        print(f"{status:7} {name}" + (f" — {fix}" if fix else ""))
    return 1 if any(status == "FAIL" for status, _, _ in results) else 0


def active_targets() -> tuple[str, ...]:
    """Resolve adapters from env or the project-local installer manifest."""
    value = os.environ.get("PROJECT_BRAIN_TARGET", "").strip().lower()
    if not value:
        try: value = json.loads((ROOT / ".ecc/install-manifest.json").read_text())["selection"]
        except (OSError, ValueError, KeyError, TypeError): value = "both"
    aliases = {"both": ("claude", "codex"), "all": ("claude", "codex", "kiro", "hermes", "generic")}
    return aliases.get(value, (value,)) if value in {"claude", "codex", "kiro", "hermes", "generic", "all", "both"} else aliases["both"]


def active_target() -> str:
    return os.environ.get("PROJECT_BRAIN_TARGET", "both").strip().lower()


def skill_adapter_roots_for_targets() -> list[Path]:
    """Return only skill adapter roots selected for this installation."""
    mapping = {"codex": ROOT / ".agents" / "skills", "claude": ROOT / ".claude" / "skills"}
    return [mapping[name] for name in active_targets() if name in mapping]


def adapter_paths_for_target() -> list[Path]:
    mapping = {"claude": ROOT / "CLAUDE.md", "codex": ROOT / "AGENTS.md",
               "kiro": ROOT / ".kiro/steering/project-brain.md",
               "hermes": AI / "adapters/hermes/SKILL.md",
               "generic": AI / "adapters/generic/README.md"}
    return [mapping[name] for name in active_targets()]


def discover_facts(confirmations: dict | None = None, interactive: bool = False) -> dict:
    """Classify evidence without turning dependency presence into runtime claims."""
    confirmations = confirmations or {}
    facts = {"project.root": {"status": "verified", "value": str(ROOT), "evidence": "CLI location"}}
    for name in ("speech_to_text.provider", "speech_to_text.model", "text_to_speech.provider", "text_to_speech.model"):
        value = confirmations.get(name)
        if not value and interactive:
            value = input(f"{name} đang unknown. Nhập giá trị đã xác nhận, hoặc Enter để giữ unknown: ").strip() or None
        facts[name] = {"status": "verified" if value else "unknown", "value": value, "evidence": "project confirmation" if value else "none"}
    return facts


def discover() -> int:
    path = AI / "confirmations.json"
    try: confirmations = load_json(path) if path.exists() else {}
    except (ValueError, OSError): confirmations = {}
    facts = discover_facts(confirmations, interactive=sys.stdin.isatty())
    safe_write(AI / "recon/discovery.json", json.dumps({"schema_version": SCHEMA, "facts": facts}, indent=2) + "\n")
    for name, fact in facts.items(): print(f"{fact['status']:10} {name}: {fact.get('value') or 'unknown'}")
    return 0


def start_next_steps() -> str:
    """Render actionable Vietnamese guidance after a successful session start."""
    inventory = AI / "imports" / "inventory.json"
    report = AI / "imports" / "report.md"
    adapters = adapter_paths_for_target()
    has_adopt_marker = False
    for path in adapters:
        if path.is_file():
            try:
                if "<!-- PROJECT-BRAIN: read canonical instructions from .ai/ -->" in safe_read(path):
                    has_adopt_marker = True
                    break
            except (OSError, ValueError, UnicodeDecodeError):
                continue
    lines = ["", "## Bước tiếp theo", ""]
    if not inventory.is_file():
        lines.extend([
            "1. Khảo sát các hướng dẫn AI cũ trong project:",
            "   `./ai onboard`",
            "   Chưa có inventory onboarding.",
        ])
    else:
        lines.extend([
            "1. Kiểm tra kết quả khảo sát:",
            f"   `{rel(report)}`" if report.is_file() else "   Chạy lại `./ai onboard` để tạo report.",
            "   Đã có inventory onboarding.",
        ])
        if not has_adopt_marker:
            lines.extend([
                "",
                "2. Tích hợp Project Brain với hướng dẫn AI cũ, không ghi đè nội dung:",
                "   `./ai adopt`",
            ])
        else:
            lines.extend(["", "2. Project Brain đã được tích hợp vào adapter project-local."])
    lines.extend([
        "",
        "3. Xem bối cảnh session:",
        "   `./ai brief`",
        "",
        "4. Khi muốn yêu cầu agent thay đổi code:",
        "   Làm rõ phạm vi, chờ approval, rồi mới triển khai.",
        "",
        "5. Sau khi thay đổi:",
        "   `./ai check`",
        "   `./ai close`",
        "",
        "6. Kiểm tra sức khỏe bất kỳ lúc nào:",
        "   `./ai doctor`",
    ])
    return "\n".join(lines) + "\n"


def start() -> int:
    # Re-scan safe project evidence every session; runtime model/provider claims
    # are accepted only from explicit runtime evidence.
    recon_script = ROOT / ".ai" / "scripts" / "recon.py"
    if recon_script.is_file():
        spec = __import__("importlib.util").util.spec_from_file_location("project_brain_recon", recon_script)
        module = __import__("importlib.util").util.module_from_spec(spec); spec.loader.exec_module(module)
        module.reconnoitre(ROOT)
    if RUNTIME.exists() and (RUNTIME.is_symlink() or not RUNTIME.is_dir()):
        raise ValueError(f"Thư mục runtime không an toàn: {RUNTIME}")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    sync_skills()
    for adapter in adapter_paths_for_target():
        sync_adapter(adapter, canonical_adapter_block("claude" if adapter.name == "CLAUDE.md" else "agents"))
    build_repo_map()
    build_skills_catalog()
    build_recommended_skills()
    create_brief()
    code = doctor(quick=True)
    if code == 0:
        print(start_next_steps())
    return code


def changed_paths() -> list[str]:
    paths: set[str] = set()
    for command in (["git", "diff", "--name-only", "HEAD"], ["git", "ls-files", "--others", "--exclude-standard"]):
        code, output = run(command)
        if code == 0:
            paths.update(line.strip() for line in output.splitlines() if line.strip())
    return sorted(paths)


def doc_impact_results() -> list[tuple[str, str, str]]:
    if not (ROOT / ".git").exists():
        return [("WARNING", "doc-impact", "Chưa có Git diff để kiểm tra code–tài liệu.")]
    paths = changed_paths()
    if not paths:
        return [("PASS", "doc-impact", "Không có Git diff cần ánh xạ.")]
    try:
        entries = load_json(AI / "knowledge/doc-map.json").get("entries", [])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [("FAIL", "doc-impact", str(exc))]
    findings: list[tuple[str, str, str]] = []
    for changed in paths:
        if changed in {"AGENTS.md", "CLAUDE.md"}:
            continue
        matching = [entry for entry in entries if isinstance(entry.get("code_path"), str) and changed.startswith(entry["code_path"].rstrip("/"))]
        if not matching:
            findings.append(("WARNING", f"doc-impact:{changed}", "Chưa có mapping; cập nhật doc-map hoặc ghi no-doc-impact."))
        elif not any(entry.get("documentation") or entry.get("no_doc_impact_reason") for entry in matching):
            findings.append(("FAIL", f"doc-impact:{changed}", "Thiếu tài liệu hoặc lý do no-doc-impact."))
    if not approved_change_exists(paths):
        findings.append(("FAIL", "approval", "Thay đổi cần approval có change_id, scope và affected paths khớp."))
    return findings or [("PASS", "doc-impact", "Các path thay đổi đã có mapping và approval.")]


def update_active_state(exit_code: int) -> None:
    path = AI / "knowledge/active-state.md"
    text = safe_read(path)
    marker = "- **Latest quality gate:**"
    line = f"{marker} {'PASS' if exit_code == 0 else 'FAIL'} (`./ai close`)."
    lines = [item for item in text.splitlines() if not item.startswith(marker)]
    lines.append(line)
    safe_write(path, "\n".join(lines).rstrip() + "\n")


def check() -> int:
    build_repo_map()
    create_brief()
    code = doctor(quick=False)
    impact = doc_impact_results()
    for status, name, fix in impact:
        print(f"{status:7} {name}" + (f" — {fix}" if fix else ""))
    return 1 if code or any(status == "FAIL" for status, _, _ in impact) else 0


LEGACY_CANDIDATES = (
    "AGENTS.md", "CLAUDE.md", ".claude/settings.json", ".claude/settings.local.json",
    ".cursorrules", ".cursor/rules", ".github/copilot-instructions.md", ".agents/skills", ".claude/skills",
)


def legacy_files() -> list[Path]:
    found: list[Path] = []
    for item in LEGACY_CANDIDATES:
        path = ROOT / item
        if path.is_file() and safe_path(path):
            found.append(path)
        elif path.is_dir() and safe_path(path):
            found.extend(p for p in sorted(path.rglob("*")) if p.is_file() and safe_path(p))
    return sorted(set(found))


def onboard() -> int:
    import datetime as dt
    destination = AI / "imports"
    inventory = []
    for path in legacy_files():
        # Do not ingest likely secret-bearing files into onboarding context.
        if any(token in path.name.lower() for token in ("secret", "token", "credential", "password")):
            inventory.append({"path": rel(path), "sha256": None, "status": "skipped-sensitive-name"})
            continue
        text = safe_read(path)
        status = "skipped-secret" if contains_secret(text) else "available"
        inventory.append({"path": rel(path), "sha256": sha256(path), "status": status})
    safe_write(destination / "inventory.json", json.dumps({"schema_version": "1.0", "files": inventory}, indent=2) + "\n")
    lines = ["# Legacy AI onboarding report", "", "Project-local inventory only.", ""]
    if inventory:
        lines += [f"- `{item['path']}` — `{item['status']}` — `{item['sha256']}`" for item in inventory]
    else:
        lines.append("No supported legacy AI configuration was found.")
    lines += ["", "## Next step", "Review this report, then run `./ai adopt` to add Project Brain guidance without overwriting legacy files."]
    safe_write(destination / "report.md", "\n".join(lines) + "\n")
    print(f"Đã tạo {rel(destination / 'inventory.json')} và {rel(destination / 'report.md')}")
    return 0


def adopt() -> int:
    marker = "<!-- PROJECT-BRAIN: read canonical instructions from .ai/ -->"
    for path in adapter_paths_for_target():
        name = path.name
        if path.exists():
            text = safe_read(path)
            begin, end = "<!-- BEGIN AI-GENERATED -->", "<!-- END AI-GENERATED -->"
            if (begin in text) != (end in text) or text.count(begin) > 1 or text.count(end) > 1:
                raise ValueError(f"Adapter marker không đầy đủ hoặc không hợp lệ: {path}")
            if marker not in text:
                text = text.rstrip() + "\n\n" + marker + "\n"
            if "<!-- BEGIN AI-GENERATED -->" not in text:
                generated = canonical_adapter_block("claude" if name == "CLAUDE.md" else "agents")
                text = text.rstrip() + "\n\n<!-- BEGIN AI-GENERATED -->\n" + generated.rstrip() + "\n<!-- END AI-GENERATED -->\n"
            safe_write(path, text)
        else:
            generated = canonical_adapter_block("claude" if name == "CLAUDE.md" else "agents")
            safe_write(path, marker + "\n\n<!-- BEGIN AI-GENERATED -->\n" + generated.rstrip() + "\n<!-- END AI-GENERATED -->\n")
    print("Đã tích hợp Project Brain vào adapter project-local; nội dung cũ được giữ nguyên.")
    return 0


def launch(cli: str) -> int:
    code = start()
    if code:
        return code
    executable = shutil.which(cli)
    if not executable:
        print(f"Không tìm thấy `{cli}` trong PATH. Hãy cài {cli} rồi chạy lại `./ai {cli}`.", file=sys.stderr)
        return 2
    return subprocess.call([executable], cwd=ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quản trị Project Brain")
    parser.add_argument("command", choices=["start", "discover", "sync", "doctor", "brief", "skills", "recommendations", "check", "close", "onboard", "adopt", "skill-proposal", "skill-promote", "claude", "codex"])
    parser.add_argument("candidate", nargs="?", help="Skill candidate JSON path for skill-proposal or skill-promote")
    parser.add_argument("--quick", action="store_true", help="Skip configured project test commands")
    args = parser.parse_args(argv)
    try:
        if args.command == "discover": return discover()
        if args.command == "onboard": return onboard()
        if args.command == "adopt": return adopt()
        if args.command == "skill-proposal":
            if not args.candidate:
                print("Cần đường dẫn candidate JSON.", file=sys.stderr); return 2
            candidate = load_json(Path(args.candidate))
            print(render_skill_proposal_vi(candidate)); return 0
        if args.command == "skill-promote":
            if not args.candidate:
                print("Cần đường dẫn candidate JSON.", file=sys.stderr); return 2
            target = promote_skill_candidate(Path(args.candidate))
            sync_skills()
            print(f"Đã promote skill: {rel(target)}"); return 0
        if args.command == "sync":
            sync_skills()
            for path in adapter_paths_for_target(): sync_adapter(path, canonical_adapter_block(path.stem.lower()))
            print("Đã đồng bộ canonical skills và adapter đã chọn."); return 0
        if args.command == "doctor": return doctor(quick=args.quick)
        if args.command == "brief": build_repo_map(); target = create_brief(); print(f"Đã tạo {rel(target)}"); return 0
        if args.command == "skills":
            target = build_skills_catalog(); print(safe_read(target)); return 0
        if args.command == "recommendations":
            target = build_recommended_skills(); print(safe_read(target)); return 0
        if args.command == "check": return check()
        if args.command == "close":
            code = check(); update_active_state(code); print(f"Đã cập nhật active-state.md với quality gate: {'PASS' if code == 0 else 'FAIL'}." ); return code
        if args.command == "claude": return launch("claude")
        if args.command == "codex": return launch("codex")
        return start()
    except Exception as exc:
        print(f"Project Brain không thể hoàn tất lệnh `{args.command}`: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
