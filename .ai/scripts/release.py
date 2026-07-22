#!/usr/bin/env python3
"""
Project Brain release builder.

Creates a reproducible archive for GitHub Release:
- Uses the same file selection logic as the installer.
- Packages the verified Project Brain payload.
- Excludes .ai/changes/, .ai/generated/, .ai/runtime/, install.sh, __pycache__.
- The standalone bootstrap is excluded to avoid an archive-checksum self-reference.
- Prints the archive SHA-256 to stdout.
"""

import gzip
import hashlib
import re
import sys
import tarfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from install import source_files

def normalized_metadata(info: tarfile.TarInfo) -> tarfile.TarInfo:
    """Normalize metadata so a release archive has stable bytes."""
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.mode = 0o755 if info.name.count("/") == 1 and info.name.endswith("/ai") else 0o644
    return info


def build_release_archive(repo_root: Path, version: str, output_dir: Path) -> Path:
    """Build a deterministic archive from the installer's verified payload."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload_files = [
        path for path in source_files(repo_root, target="all")
        if path.relative_to(repo_root) != Path("install.sh")
    ]
    secret_pattern = re.compile(r"(?:password|api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-/+=.]{12,}", re.I)
    for path in payload_files:
        if path.is_symlink():
            raise ValueError(f"Archive refuses symlink payload: {path}")
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        # Test fixtures intentionally contain fake secret-shaped strings to
        # verify redaction behavior. They are not runtime payload/configuration.
        if not path.relative_to(repo_root).is_relative_to(Path(".ai/tests")) and secret_pattern.search(text):
            raise ValueError(f"Archive refuses secret-like payload: {path}")
    archive_path = output_dir / f"project-brain-{version}.tar.gz"
    archive_root = f"project-brain-{version}"

    with archive_path.open("wb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0, filename="") as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for source_file in payload_files:
                    if "__pycache__" in source_file.parts:
                        continue
                    relative = source_file.relative_to(repo_root)
                    archive.add(
                        source_file,
                        arcname=f"{archive_root}/{relative}",
                        recursive=False,
                        filter=normalized_metadata,
                    )

    return archive_path

def calculate_sha256(archive_path: Path) -> str:
    """Calculate SHA-256 hash of the archive."""
    sha256 = hashlib.sha256()
    with open(archive_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main() -> None:
    """Main function to build and verify the release archive."""
    # Get the repository root (assuming this script is in .ai/scripts)
    repo_root = Path(__file__).resolve().parents[2]
    version = "1.0.9"
    output_dir = repo_root / "dist"

    print(f"Building Project Brain {version} release archive...")
    archive_path = build_release_archive(repo_root, version, output_dir)

    print(f"Archive created: {archive_path}")

    # Calculate and print SHA-256
    sha256_hash = calculate_sha256(archive_path)
    print(f"SHA-256: {sha256_hash}")

    # Verify archive contents (basic checks)
    print("\nVerifying archive contents...")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        print(f"Total members: {len(members)}")

        # Check for forbidden paths
        forbidden_patterns = [
            ".ai/changes/",
            ".ai/generated/",
            ".ai/runtime/",
            "__pycache__"
        ]

        for member in members:
            member_path = member.name
            if any(pattern in member_path for pattern in forbidden_patterns):
                raise ValueError(f"Archive contains forbidden path: {member_path}")

        print("Archive verification passed - no forbidden paths found.")

if __name__ == "__main__":
    main()