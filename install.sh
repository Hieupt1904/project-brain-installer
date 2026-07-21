#!/bin/sh
# Project Brain bootstrap. Download this file first, review it, then execute locally.
set -eu
umask 077

BASE_URL='https://github.com/Hieupt1904/project-brain-installer/releases/download'
VERSION='1.0.7'
# Local 1.0.7 build placeholder; replace only during an explicit release publication.
ARCHIVE_SHA256='6766833b87b0c24371233f2bffe43e5c0cd3b5b771220195ac9cd27d8473f942'

command -v python3 >/dev/null 2>&1 || { echo "Project Brain installer: python3 is required" >&2; exit 2; }

temporary=$(python3 -c 'import tempfile; print(tempfile.mkdtemp(prefix="project-brain-"))')
trap 'rm -rf "$temporary"' EXIT HUP INT TERM

case " $* " in
  *" --uninstall "*)
    directory=$(pwd)
    previous=''
    for argument in "$@"; do
      if [ "$previous" = "--directory" ]; then
        directory=$argument
      fi
      previous=$argument
    done
    installer="$directory/.ai/scripts/install.py"
    if [ ! -f "$installer" ]; then
      echo "Project Brain installer: no installed installer found in $directory" >&2
      exit 2
    fi
    python3 "$installer" "$@"
    exit $?
    ;;
esac

command -v curl >/dev/null 2>&1 || { echo "Project Brain installer: curl is required" >&2; exit 2; }
archive="$temporary/project-brain-$VERSION.tar.gz"
payload="$temporary/project-brain-$VERSION"

curl --fail --show-error --silent --location \
    --proto '=https' --proto-redir '=https' --tlsv1.2 \
    --output "$archive" "$BASE_URL/$VERSION/project-brain-$VERSION.tar.gz"

python3 - "$archive" "$payload" "project-brain-$VERSION" "$ARCHIVE_SHA256" <<'PY'
import hashlib
import os
from pathlib import Path, PurePosixPath
import sys
import tarfile

archive_path, destination, expected_root, expected_digest = sys.argv[1:]
digest = hashlib.sha256(Path(archive_path).read_bytes()).hexdigest()
if digest != expected_digest:
    raise SystemExit("Project Brain installer: archive checksum mismatch")

with tarfile.open(archive_path, "r:gz") as archive:
    members = archive.getmembers()
    if len(members) > 2000:
        raise SystemExit("Project Brain installer: archive has too many members")
    if sum(member.size for member in members if member.isfile()) > 100 * 1024 * 1024:
        raise SystemExit("Project Brain installer: archive is too large")

    seen = set()
    validated = []
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != expected_root:
            raise SystemExit(f"Project Brain installer: unsafe archive path: {member.name}")
        if any(part in {"", ".", ".."} for part in path.parts):
            raise SystemExit(f"Project Brain installer: unsafe archive path: {member.name}")
        relative = PurePosixPath(*path.parts[1:])
        if relative in seen:
            raise SystemExit(f"Project Brain installer: duplicate archive path: {member.name}")
        seen.add(relative)
        if not (member.isfile() or member.isdir()):
            raise SystemExit(f"Project Brain installer: unsupported archive member: {member.name}")
        validated.append((member, relative))

    root = Path(destination)
    root.mkdir()
    for member, relative in validated:
        output = root.joinpath(*relative.parts)
        if member.isdir():
            output.mkdir(parents=True, exist_ok=True)
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            raise SystemExit(f"Project Brain installer: unreadable archive member: {member.name}")
        with source, output.open("wb") as handle:
            while chunk := source.read(1024 * 1024):
                handle.write(chunk)
        output.chmod(member.mode & 0o777)
PY

directory=$(pwd)
target=both
dry_run=0
previous=''
for argument in "$@"; do
    if [ "$previous" = "--directory" ]; then directory=$argument; fi
    if [ "$previous" = "--target" ]; then target=$argument; fi
    if [ "$argument" = "--dry-run" ]; then dry_run=1; fi
    previous=$argument
done

python3 "$payload/.ai/scripts/install.py" "$@" --source "$payload" --version "$VERSION"

post_install() {
    phase=$1; shift
    echo "Project Brain post-install: $phase" >&2
    if PROJECT_BRAIN_TARGET="$target" "$@"; then
        :
    else
        code=$?
        echo "Project Brain post-install failed during '$phase' for target '$target' (exit $code)" >&2
        return "$code"
    fi
}
# All phases are project-local and target-aware. Tests may suppress autorun.
# Dry-run reports the planned action and must not create any side effects.
if [ "${PROJECT_BRAIN_SKIP_AUTORUN:-0}" != "1" ] && [ "$dry_run" != "1" ]; then
    post_install reconnaissance python3 "$directory/.ai/scripts/agentctl.py" onboard
    if [ "${PROJECT_BRAIN_AUTO_ADOPT:-0}" = "1" ]; then
        post_install adoption python3 "$directory/.ai/scripts/agentctl.py" adopt
    fi
    post_install start python3 "$directory/.ai/scripts/agentctl.py" start
    post_install doctor python3 "$directory/.ai/scripts/agentctl.py" doctor --quick
fi
