# Operations

## Installation

There are no production dependencies. Python 3 and a shell are required on Linux/macOS; Windows can use `ai.cmd` when Python is available on `PATH`.

A local installer is available for Project Brain:

```bash
./install.sh --dry-run --target both
./install.sh --target both --version 1.0.1
./install.sh --uninstall
```

The installer copies only the verified Project Brain repository content. It defaults to the current directory, stops before writing when any destination file already exists, rejects symlinks, and records checksums in `.ecc/install-manifest.json`. `--dry-run` never writes. Uninstall removes only unchanged files recorded in that manifest and refuses modified files. A bootstrap uninstall locates the already installed `.ai/scripts/install.py`, so it does not download the archive or require network access.

The public version `1.0.1` bootstrap is served from the GitHub Release asset URL:

```bash
curl -fsSL https://github.com/Hieupt1904/project-brain-installer/releases/download/1.0.1/install.sh -o /tmp/project-brain-install.sh
```

Download and review the script before executing it. The bootstrap downloads `project-brain-1.0.1.tar.gz` from the same GitHub Release and verifies its pinned SHA-256 before extraction. GitHub permits release owners to replace assets, but this project has a non-replacement policy: never replace an existing release asset; publish a new version and update the bootstrap version and checksum together.

The first supported bootstrap is POSIX shell on Linux/macOS. Windows receives `ai.cmd` in the payload but does not have a PowerShell bootstrap in this change.

The source-of-truth boundary remains `.ai/`; generated adapters must be regenerated with `./ai sync` rather than edited directly.

## Install conflict policy

The installer does not merge or overwrite existing `CLAUDE.md`, `AGENTS.md`, `.ai/`, `.claude/`, or `.agents/` files. Stop, inspect the reported paths, and run it in a clean project directory or move the conflicting files manually.

## Release distribution

The public release uses `Hieupt1904/project-brain-installer` with a tag matching the bootstrap `VERSION` (for example, `1.0.1`). GitHub does not enforce asset immutability; this project enforces a non-replacement policy. Build the archive with `.ai/scripts/release.py`, verify its member list, update the pinned checksum in `install.sh`, run the local test suite, and then upload the exact reviewed bootstrap and archive bytes.

If publication or checksum verification fails, delete the draft release before it becomes public. After publication, do not mutate the release assets; publish a corrected version instead. If an integrity incident occurs, remove public availability of the affected release, preserve evidence, and publish a new reviewed version. Do not run a remote script without downloading and reviewing it first.

## Uninstall and recovery

Use `./install.sh --uninstall --dry-run` to inspect the removal set. Uninstall is scoped by `.ecc/install-manifest.json`; it never recursively deletes arbitrary project directories. If a managed file changed after installation, uninstall stops and leaves the project untouched.

## Rollback/recovery

There is no application rollback procedure because the repository has no business application. Generated files can be recreated with `./ai brief` and `./ai sync`. Before manually changing an existing adapter, preserve content outside generated markers.

The installer also rolls back files created during a failed transaction, but it does not overwrite or back up pre-existing files because conflicts stop before mutation.

## Run

```bash
./ai start
./ai doctor
./ai brief
```

## Test

```bash
./ai doctor
python3 -m unittest discover -s .ai/tests -p 'test_*.py'
```

## Health checks

`./ai doctor` checks required files, JSON schema, skill format, adapter integrity, symlinks, context limits, and secret patterns. `./ai check` runs the build/test/lint/format commands verified in `project.json`, then checks documentation impact and approval.

Claude Code's stop hook performs read-only safety checks only: it does not run repository-controlled tests or create/write generated context. Use `./ai check` or `./ai close` for a complete quality gate.

All canonical sources, adapters, and generated context reject symlinks or paths outside the repository. Generated context, change records, settings, and runtime text are checked for secret patterns before writing or quality gates. Command metadata only runs allowlisted executables and may not contain eval or dangerous command operations. Approval must be tied to the current change ID and affected paths.

## Rollback/recovery

There is no application rollback procedure because the repository has no business application. Generated files can be recreated with `./ai brief` and `./ai sync`. Before manually changing an existing adapter, preserve content outside generated markers.

## Agent launch commands

`./ai claude` and `./ai codex` run `start` first and then invoke the corresponding CLI if installed; otherwise they report a clear error.

## Language contract

- Write canonical instructions, policies, knowledge, and agent-facing prompts in English.
- Translate user-facing guidance into Vietnamese under `docs/i18n/vi/`.
- Convert user requests into English before sending them to agents when an agent prompt is required.
- Present agent results to users in Vietnamese.
- Keep command names, paths, schema keys, identifiers, and code unchanged.
