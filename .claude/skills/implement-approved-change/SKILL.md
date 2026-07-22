<!-- GENERATED FILE — DO NOT EDIT DIRECTLY -->
<!-- canonical: .ai/skills/implement-approved-change/SKILL.md -->
<!-- generated_at: 2026-07-21T09:58:31+00:00 -->
<!-- source_sha256: 1f993aa998dc25c955cc58cd38b19eddfd12a022edbded63372005a0e89613a5 -->
<!-- schema_version: 1.0 -->

---
name: implement-approved-change
description: Implement exactly one approved change, run relevant checks, and record honest results; never use it for unapproved requests.
layer: development
trigger_keywords: approved implementation, code change, verification
---

# Implement Approved Change

## Preconditions

- The change has an `approval.md` with `approved` status.
- `impact.md` exists, with additional approvals for high-risk areas when required.
- File scope and acceptance criteria are clear.

## Procedure

1. Read approval, impact, and only the relevant files.
2. Write tests first when appropriate.
3. Make the smallest change within approved scope; do not modify unrelated business source.
4. Run verified test/lint/build commands, or record why a command cannot run.
5. Record commands and results in `implementation.md` and `verification.md` in English canonical format.
6. Explain the result to the user in Vietnamese.
7. If the plan is wrong, stop and request renewed approval.

## Stop conditions

- Stop when a required test fails, approval is missing, or impact exceeds scope.
- Do not mark the change complete merely because code was written.

## Missing information

Keep the change incomplete; ask the user or return to impact analysis. Explain the blocker in Vietnamese.

## Expected output

In-scope changes, honest test results, implementation/verification records, and an explicit completion state. User-facing output is Vietnamese.

## Failure handling

Do not hide failures, modify tests merely to make them pass, or commit/push automatically.
