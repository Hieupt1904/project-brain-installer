# Architecture

## Plain-language explanation

Project Brain is a set of governance records and tools under `.ai/`. It stores canonical project information, changes, decisions, and procedures. Claude Code and Codex do not maintain separate canonical documents: they use adapters generated from canonical content. `./ai start` performs a quick check, synchronizes adapters, and creates a short session brief.

The language boundary is explicit:

- `.ai/` is the English canonical/internal source.
- `docs/i18n/vi/` contains Vietnamese user-facing translations.
- `README.md` remains a Vietnamese entry point for users.
- Agent-facing instructions and prompts use English.
- Agent responses shown to users use Vietnamese.

## Distribution boundary

The public installer is distributed through GitHub Release. The bootstrap URL is pinned to a release tag and downloads an archive whose SHA-256 is verified before extraction. GitHub permits owners to replace release assets, so immutability is enforced as a project non-replacement policy: publish a new version and update the bootstrap when a payload changes. The distribution payload excludes change records, generated context, and runtime state.

## Technical view

Only the governance framework architecture is currently verified. No business application architecture is available to describe.

- `.ai/project.json`: metadata and verified commands.
- `.ai/knowledge/`: canonical project knowledge.
- `.ai/changes/`: request, approval, impact, implementation, and verification records.
- `.ai/skills/`: six canonical Agent Skills, written in English.
- `.ai/policy/`: canonical governance, approval, and security policies.
- `.ai/scripts/agentctl.py`: Python standard-library administration CLI.
- `.ai/generated/`: reproducible repository map and session brief.
- `.ai/runtime/`: temporary state, not committed by default.
- `.agents/skills/`, `.claude/skills/`: generated skill adapters.
- `AGENTS.md`, `CLAUDE.md`: generated root instruction adapters.
- `docs/i18n/vi/`: Vietnamese user-facing translation layer.

## Data flow

`./ai start` → quick doctor → adapter synchronization → safe metadata scan → `session-brief.md`.

`change-intake` → approval → impact analysis → implementation → verification → knowledge synchronization.

`Vietnamese user request` → `English internal agent prompt` → `agent processing` → `Vietnamese user-facing response`.

## Integrations

External integrations, database, authentication, API, and deployment are not verified because the repository has no business application source code.
