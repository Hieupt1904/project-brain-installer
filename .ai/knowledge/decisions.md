# Decisions

## 2026-07-18 — Build Project Brain in an empty repository

- **Decision:** Create the agent governance framework in `.ai/` without creating or modifying business application source code.
- **Reason:** The repository had no source code or existing configuration; a canonical knowledge source was needed for Claude Code and Codex.
- **Options considered:** Wait for application code; create the framework with an unverified status; create separate documentation for each agent. We chose the second option and avoided duplicating canonical content.
- **Consequence:** Application metadata remains placeholder data and must be verified later.
- **Approval:** The user selected A to continue after the read-only survey.
- **Related:** `.ai/`, `AGENTS.md`, `CLAUDE.md`, `.ai/scripts/agentctl.py`.

## 2026-07-18 — Separate canonical agent language from user-facing language

- **Decision:** Use English for canonical/internal Project Brain content and all input sent to agents. Keep Vietnamese as the user-facing i18n layer and output language.
- **Reason:** English provides one consistent internal language for agent instructions while Vietnamese remains accessible to the user.
- **Canonical source:** `.ai/`.
- **User-facing i18n:** `docs/i18n/vi/` and the Vietnamese `README.md` entry point.
- **Generated artifacts:** `.agents/skills/`, `.claude/skills/`, `.ai/generated/`, `AGENTS.md`, and `CLAUDE.md` must be regenerated from canonical sources rather than edited directly.
- **Scope boundary:** Do not translate identifiers, command names, paths, source code, or application behavior.
- **Approval:** The user selected A on 2026-07-18.
