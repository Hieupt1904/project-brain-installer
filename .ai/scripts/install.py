#!/usr/bin/env python3
"""Install Project Brain into another project using only the standard library."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

MANIFEST_PATH = ".ecc/install-manifest.json"
SCHEMA_VERSION = "1.0"
TARGETS = {"claude", "codex", "kiro", "hermes", "generic", "all", "both"}


class InstallError(RuntimeError):
    """Raised when an install cannot be completed safely."""


@dataclass(frozen=True)
class Result:
    action: str
    files: tuple[str, ...]


def relative(path: Path) -> str:
    value = path.as_posix()
    return value[2:] if value.startswith("./") else value


def reject_symlink(path: Path, label: str) -> None:
    if path.is_symlink():
        raise InstallError(f"{label} is a symlink: {path}")


def safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not value or ".." in path.parts or any(part == "" for part in path.parts):
        raise InstallError(f"unsafe manifest path: {value}")
    return path


def ensure_directory(path: Path, label: str) -> None:
    reject_symlink(path, label)
    if path.exists() and not path.is_dir():
        raise InstallError(f"{label} is not a directory: {path}")
    if not path.exists():
        path.mkdir()


def ensure_target(target: Path) -> Path:
    target = target.expanduser().absolute()
    reject_symlink(target, "target")
    if not target.is_dir():
        raise InstallError(f"target must be an existing directory: {target}")
    current = target
    while current != current.parent:
        reject_symlink(current, "target parent")
        current = current.parent
    return target


def source_files(source: Path, target: str) -> list[Path]:
    source = source.expanduser().absolute()
    reject_symlink(source, "source")
    if not source.is_dir():
        raise InstallError(f"source must be a directory: {source}")

    common = [
        Path(".ai/project.json"),
        Path(".ai/knowledge"),
        Path(".ai/policy"),
        Path(".ai/skills"),
        Path(".ai/scripts"),
        Path(".ai/tests"),
        Path("docs"),
        Path("README.md"),
        Path("ai"),
        Path("ai.cmd"),
        Path("install.sh"),
    ]
    selected = common[:]
    if target in {"claude", "both", "all"}:
        selected.extend([Path("CLAUDE.md"), Path(".claude/settings.json"), Path(".claude/skills")])
    if target in {"codex", "both", "all"}:
        selected.extend([Path("AGENTS.md"), Path(".agents/skills")])
        if (source / ".codex").exists(): selected.append(Path(".codex"))
    if target in {"kiro", "all"}: selected.append(Path(".kiro/steering"))
    if target in {"hermes", "all"}: selected.append(Path(".ai/adapters/hermes"))
    if target in {"generic", "all"}: selected.append(Path(".ai/adapters/generic"))

    files: list[Path] = []
    for entry in selected:
        path = source / entry
        if not path.exists() and not path.is_symlink():
            continue
        reject_symlink(path, "source path")
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                reject_symlink(child, "source path")
                if child.is_file() and "__pycache__" not in child.parts:
                    files.append(child)
    if not files:
        raise InstallError(f"source has no installable Project Brain files: {source}")
    return sorted(set(files))


def destination_for(source_file: Path, source: Path, target: Path) -> Path:
    return target / source_file.relative_to(source)


def check_parent_boundaries(path: Path, target: Path) -> None:
    current = path.parent
    while current != target.parent:
        reject_symlink(current, "destination parent")
        if current == target:
            return
        current = current.parent
    raise InstallError(f"destination escapes target: {path}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_copy(source: Path, destination: Path) -> None:
    reject_symlink(source, "source file")
    reject_symlink(destination, "destination")
    destination.parent.mkdir(parents=True, exist_ok=True)
    reject_symlink(destination.parent, "destination parent")
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        with source.open("rb") as input_handle:
            shutil.copyfileobj(input_handle, handle)
    try:
        shutil.copymode(source, temporary, follow_symlinks=False)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_manifest(target: Path) -> dict:
    manifest_path = target / MANIFEST_PATH
    reject_symlink(manifest_path, "manifest")
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InstallError(f"invalid installer manifest: {exc}") from exc
    required = {"schema_version", "version", "selection", "files", "directories"}
    if not isinstance(value, dict) or set(value) != required:
        raise InstallError("invalid installer manifest schema")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("selection") not in TARGETS:
        raise InstallError("invalid installer manifest schema")
    if not isinstance(value.get("files"), dict) or not isinstance(value.get("directories"), list) or not all(isinstance(item, str) for item in value["directories"]):
        raise InstallError("invalid installer manifest schema")
    for name, digest in value["files"].items():
        safe_relative_path(name)
        if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise InstallError(f"invalid manifest checksum: {name}")
    return value


def selected_plan(source: Path, target: Path, selection: str) -> tuple[list[tuple[Path, Path]], list[str]]:
    pairs = [(path, destination_for(path, source, target)) for path in source_files(source, selection)]
    manifest = target / MANIFEST_PATH
    # The manifest is an installer-owned update target on reinstall.
    pairs.append((Path(""), manifest))
    conflicts: list[str] = []
    for source_path, destination in pairs:
        if source_path == Path(""):
            reject_symlink(destination.parent, "manifest parent")
            reject_symlink(destination, "manifest")
            continue
        check_parent_boundaries(destination, target)
        # Existing project files are intentionally preserved. They are recorded
        # for onboarding instead of blocking installation.
        if destination.is_symlink():
            conflicts.append(relative(destination.relative_to(target)))
    return pairs, conflicts


def install(source: Path, target: Path, selection: str, dry_run: bool, version: str) -> Result:
    if selection not in TARGETS:
        raise InstallError(f"invalid target: {selection}")
    source = source.expanduser().absolute()
    target = ensure_target(target)
    pairs, conflicts = selected_plan(source, target, selection)
    if conflicts:
        names = ", ".join(conflicts[:10])
        suffix = "..." if len(conflicts) > 10 else ""
        raise InstallError(f"conflicts found; nothing changed: {names}{suffix}")
    manifest_path = target / MANIFEST_PATH
    prior = load_manifest(target) if manifest_path.exists() else None
    prior_files = dict(prior["files"]) if prior else {}
    names = tuple(relative(destination.relative_to(target)) for source_path, destination in pairs
                  if source_path != Path("") and (not destination.exists() or relative(destination.relative_to(target)) in prior_files))
    if dry_run:
        return Result("dry-run", names)

    created: list[Path] = []
    backups: dict[Path, bytes] = {}
    created_directories: list[Path] = []
    managed = dict(prior_files)
    try:
        for source_path, destination in pairs:
            if source_path == Path(""):
                continue
            check_parent_boundaries(destination, target)
            reject_symlink(destination, "destination")
            name = relative(destination.relative_to(target))
            # A previously managed, unchanged file is safe to upgrade. Any
            # project edit (including an adopted legacy file) wins and remains
            # tracked with its previous checksum so uninstall refuses deletion.
            overwrite = name in prior_files and destination.exists() and destination.is_file() and sha256(destination) == prior_files[name]
            if destination.exists() and not overwrite:
                continue
            if overwrite:
                backups[destination] = destination.read_bytes()
            else:
                missing: list[Path] = []
                parent = destination.parent
                while parent != target and not parent.exists():
                    missing.append(parent); parent = parent.parent
                for directory in reversed(missing):
                    reject_symlink(directory, "destination parent"); directory.mkdir(); created_directories.append(directory)
                created.append(destination)
            atomic_copy(source_path, destination)
            managed[name] = sha256(destination)
        manifest = {
            "schema_version": SCHEMA_VERSION, "version": version, "selection": selection,
            "files": dict(sorted(managed.items())),
            "directories": sorted({relative((target / safe_relative_path(name)).parent.relative_to(target)) for name in managed if (target / safe_relative_path(name)).parent != target}),
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        reject_symlink(manifest_path.parent, "manifest parent")
        reject_symlink(manifest_path, "manifest")
        atomic_copy_text(json.dumps(manifest, indent=2) + "\n", manifest_path)
    except (OSError, ValueError, InstallError) as exc:
        for path, content in backups.items():
            try: atomic_copy_text(content.decode("utf-8"), path)
            except (OSError, UnicodeDecodeError): pass
        for path in reversed(created):
            try:
                if path.is_file() and not path.is_symlink(): path.unlink()
            except OSError: pass
        for directory in sorted(created_directories, key=lambda item: len(item.parts), reverse=True):
            try:
                if directory.is_dir() and not directory.is_symlink(): directory.rmdir()
            except OSError: pass
        raise InstallError(f"install failed and was rolled back: {exc}") from exc
    return Result("install", names)


def atomic_copy_text(content: str, destination: Path) -> None:
    """Atomically write text in an already validated project-local directory."""
    reject_symlink(destination.parent, "destination parent")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, prefix=f".{destination.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def uninstall(target: Path, dry_run: bool) -> Result:
    target = ensure_target(target)
    manifest = load_manifest(target)
    files = manifest["files"]
    paths: list[tuple[str, Path]] = []
    for name, expected in files.items():
        path = target / safe_relative_path(name)
        check_parent_boundaries(path, target)
        reject_symlink(path, "managed path")
        if path.exists():
            if not path.is_file() or sha256(path) != expected:
                raise InstallError(f"managed file was modified: {name}")
            paths.append((name, path))
    names = tuple(name for name, _ in paths)
    if dry_run:
        return Result("dry-run-uninstall", names)
    for _, path in sorted(paths, reverse=True):
        path.unlink()
    manifest_path = target / MANIFEST_PATH
    manifest_path.unlink()
    for directory in sorted(manifest.get("directories", []), key=lambda value: len(Path(value).parts), reverse=True):
        path = target / safe_relative_path(directory)
        if path.is_dir() and not path.is_symlink():
            try:
                path.rmdir()
            except OSError:
                pass
    return Result("uninstall", names)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Project Brain into a project directory")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--directory", type=Path, default=Path.cwd())
    parser.add_argument("--target", choices=tuple(sorted(TARGETS)), default="both")
    parser.add_argument("--version", default="local")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.uninstall:
            result = uninstall(args.directory, args.dry_run)
        else:
            result = install(args.source, args.directory, args.target, args.dry_run, args.version)
    except InstallError as exc:
        print(f"Project Brain installer: {exc}", file=sys.stderr)
        return 2
    for name in result.files:
        print(f"{result.action}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
