# Agent instructions

<!-- BEGIN AI-GENERATED -->
<!-- GENERATED FILE — DO NOT EDIT DIRECTLY -->
<!-- canonical: .ai/project.json + .ai/policy/ -->
<!-- generated_at: 2026-07-20T08:13:25+00:00 -->
<!-- source_sha256: a9f1275443615a5deb541787054fb3e051ecd4d13c11416a8af7c4f2e897f3dc -->
<!-- schema_version: 1.0 -->
# Project Brain instructions

The source of truth is under `.ai/`; do not read the entire repository at session start.

Before work, run `./ai start`. Before a significant change, use the `change-intake` skill and obtain explicit user approval.

After a change, run `./ai check`; before ending, run `./ai doctor`. Do not edit generated files directly.

## Verified commands
- `python3 -m unittest discover -s .ai/tests -p 'test_*.py'`

## High-risk areas
database migration, authentication, authorization, data deletion, API contract, production dependency, infrastructure, external service cost

## Project status
partial — repository had no application source code when surveyed

## Language contract

- Use English for canonical/internal instructions and all prompts sent to agents.
- Return user-facing responses in Vietnamese.

Codex: use the skill adapters under `.agents/skills/`; keep canonical content under `.ai/.
<!-- END AI-GENERATED -->

<!-- PROJECT-BRAIN: read canonical instructions from .ai/ -->
