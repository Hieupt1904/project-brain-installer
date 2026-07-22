---
name: sync-project-knowledge
description: Update Project Brain and documentation after a change using Git diff and the documentation map before closing a change.
layer: governance
trigger_keywords: sync knowledge, update documentation, close change
---

# Sync Project Knowledge

## Preconditions

- A Git diff or change list exists.
- `.ai/knowledge/doc-map.json` exists.
- Approval exists when the change belongs to a deployed change record.

## Procedure

1. Read a filtered Git diff; never place secrets into context.
2. Match each code path against `doc-map.json`.
3. Update knowledge, active state, and decisions when architecture or business behavior changes.
4. Create `implementation.md` and `verification.md` for the change.
5. If documentation does not need changes, record a `no-doc-impact` reason.
6. Run adapter synchronization and doctor.
7. Present in Vietnamese: what changed, why, what users see, how to verify, documentation updated, and remaining unknowns. Keep the canonical records and agent-facing prompts in English.

## Stop conditions

Stop if the diff touches a high-risk area without matching approval or the documentation map is insufficient.

## Missing information

Mark unmapped paths as `not verified`; do not delete documentation merely because no impact is visible.

## Expected output

Evidence-based knowledge and documentation updates, verification records, updated active state, and a documentation-impact report. User-facing output is Vietnamese.

## Failure handling

Report unmapped paths, skip reasons, and next actions clearly. Do not claim synchronization completed when doctor fails.
