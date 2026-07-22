<!-- GENERATED FILE — DO NOT EDIT DIRECTLY -->
<!-- canonical: .ai/skills/change-intake/SKILL.md -->
<!-- generated_at: 2026-07-21T09:58:31+00:00 -->
<!-- source_sha256: 55892dea303e27cb267cf7e0d74e2182d6aa2c05521b4335a00ec782284c205f -->
<!-- schema_version: 1.0 -->

---
name: change-intake
description: Clarify and obtain approval for a significant request before planning or modifying source code.
layer: governance
trigger_keywords: approval, significant change, clarify request
---

# Change Intake

## Preconditions

- A request from the user or a ticket exists.
- `project-start` has run or a current session brief exists.
- No code has been changed for this request.

## Procedure

1. Prepare the internal request analysis in English, covering current state, desired outcome, affected people/processes, possible files to change, and uncertainty.
2. Present the explanation to the user in Vietnamese using clear everyday language.
3. End with choice A: correct, continue; B: revise.
4. Wait for explicit confirmation; silence is not approval.
5. After A, create `.ai/changes/YYYYMMDD-slug/request.md` and `approval.md`.
6. Record `approved` status, date, approved content, and scope boundaries.

## Stop conditions

- Stop immediately before any edit if approval is missing.
- Ask again if the request is ambiguous or lacks a decision maker.

## Missing information

Record uncertainty explicitly in English canonical records and explain it in Vietnamese to the user. Do not choose an interpretation with business impact without approval.

## Expected output

A request and approval record with status, scope, confirmation, and open questions. User-facing summaries and confirmations are Vietnamese.

## Failure handling

If records cannot be created, do not continue to impact analysis or implementation; report the exact path and error to the user in Vietnamese.
