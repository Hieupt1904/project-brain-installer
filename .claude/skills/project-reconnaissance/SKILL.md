<!-- GENERATED FILE — DO NOT EDIT DIRECTLY -->
<!-- canonical: .ai/skills/project-reconnaissance/SKILL.md -->
<!-- generated_at: 2026-07-21T10:05:39+00:00 -->
<!-- source_sha256: be125a981e1ea4855565a65e9f08f4e8878d633692c2689c118bd7d75409c6c8 -->
<!-- schema_version: 1.0 -->

---
name: project-reconnaissance
description: Safely inventory project evidence and classify facts without guessing runtime providers or models.
layer: governance
trigger_keywords: onboard project, inspect repository, reconnaissance
---
# Project reconnaissance

Use this skill at session start or when onboarding an existing project.

1. Run `./ai start`; it regenerates `.ai/recon/inventory.json`, `evidence.json`, and `facts.json`.
2. Read safe manifests/config/source metadata only. Never read `.env` values, credentials, secret-bearing paths, symlinks, generated build trees, or external paths.
3. Label every fact `verified`, `inherited`, `inferred`, `unknown`, or `conflicted`.
4. Treat dependency/config evidence as capability evidence only. Never claim an STT/TTS model or provider unless `.ai/runtime/model-evidence.json` records runtime evidence.
5. Re-run reconnaissance whenever evidence changes; do not preserve stale conclusions.
7. Read `.ai/generated/recommended-skills.md` when present. Treat every recommendation as evidence-based routing only, never as proof of a runtime provider, database, authentication system, or deployment state.
8. Present unknown/conflicted facts explicitly and ask for runtime verification where needed.
