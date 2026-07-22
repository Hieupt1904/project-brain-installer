<!-- GENERATED FILE — DO NOT EDIT DIRECTLY -->
<!-- canonical: .ai/skills/skill-candidate-lifecycle/SKILL.md -->
<!-- generated_at: 2026-07-21T09:58:31+00:00 -->
<!-- source_sha256: 188237d7abae9f8e7b3c53c8aebf38582b2a8e63b0fa4dba923a77caa1a13416 -->
<!-- schema_version: 1.0 -->

---
name: skill-candidate-lifecycle
description: Detect reusable project workflows after verified work, present a complete Vietnamese proposal, require separate user approval, and promote only approved English canonical skills.
layer: governance
trigger_keywords: reusable workflow, create skill, update skill
---

# Skill Candidate Lifecycle

## Purpose

Use this skill after verified project work reveals a reusable workflow, correction, pitfall, or high-risk procedure. Project Brain may detect and draft a candidate automatically, but it must never create or update a canonical skill without separate user approval.

Canonical project skills live under `.ai/skills/` and must be written in English. User-facing proposals, explanations, and approval choices must be written in Vietnamese.

## Trigger Conditions

Evaluate a skill candidate after the task result has been verified and before the final close gate. Propose a candidate when at least one strong signal or two moderate signals exist.

### Strong signals

- The user corrected the agent and the corrected workflow was verified.
- A difficult failure was resolved with a reproducible root cause and fix.
- The workflow has five or more ordered steps that are likely to recur.
- The workflow controls a high-risk operation such as migration, authentication, deployment, production data, or external cost.
- The user explicitly asks to remember, standardize, or save the workflow as a skill.

### Moderate signals

- A similar task has appeared at least twice.
- The workflow requires three or more dependent tool calls.
- The result has an objective verification command or runtime check.
- The workflow contains a non-obvious pitfall that another agent could repeat.
- The workflow produces a reusable project-local template or script.

Do not propose a skill for trivial edits, one-off output, unverified experiments, temporary task state, secrets, credentials, personal data, production datasets, commit identifiers, or facts likely to become stale within a week.

## Candidate Scope

Project Brain candidates are always `project-local`. Store approved canonical skills under:

```text
.ai/skills/<skill-name>/SKILL.md
```

Do not create or modify global Hermes skills, memory, profiles, plugins, or configuration. A workflow that may belong globally must be handled separately by the user's global skill-management process.

## Duplicate Check

Before drafting a new candidate:

1. Read the names and descriptions of existing `.ai/skills/*/SKILL.md` files.
2. Compare triggers, workflow steps, verification, and pitfalls.
3. If an existing skill substantially overlaps, propose an `update` candidate instead of a `create` candidate.
4. If the existing skill already covers the workflow, do not create a candidate.

## Mandatory Vietnamese Proposal

Before canonical creation or update, show the user a Vietnamese proposal containing all of the following:

1. Why the skill is useful.
2. Proposed skill name.
3. Project-local scope and canonical path.
4. Trigger conditions.
5. Workflow steps that will be stored.
6. Required verification.
7. Pitfalls, boundaries, and stop conditions.
8. Related or overlapping skills.
9. Every file that will be created or modified.
10. Data that will explicitly not be stored.
11. A statement that canonical `SKILL.md` content will be written in English.

End with these choices in Vietnamese:

```text
A. Phê duyệt đúng nội dung trên
B. Sửa proposal trước khi tạo
C. Chỉ giữ candidate draft
D. Không tạo
```

Task approval is not skill approval. Silence, prior task approval, or a general instruction to continue does not authorize skill creation unless the user is responding directly to the complete skill proposal.

## Candidate Record

Store a draft only under:

```text
.ai/skill-candidates/<candidate-id>/candidate.json
```

The record must include:

- `schema_version`
- `candidate_id`
- `status`
- `action`: `create` or `update`
- `skill_name`
- `scope`: `project-local`
- Vietnamese proposal fields for reason, triggers, workflow, verification, and pitfalls
- `affected_files`
- Complete English `canonical_skill_md`

Saving a candidate must not create or modify `.ai/skills/<name>/SKILL.md`.

## Separate Approval Binding

Promotion requires:

- `status: approved`
- `approval.candidate_id` matching the candidate
- `approval.content_sha256` matching the exact English canonical skill body
- `approval.approved_by: user`
- `approval.approved_at`

If the canonical content changes after approval, the hash no longer matches. Present the revised Vietnamese proposal and obtain approval again.

## Canonical Skill Requirements

The promoted `SKILL.md` must:

- Be written in English.
- Use lowercase kebab-case for `name`.
- Include frontmatter with a useful trigger-oriented `description`.
- Define purpose, when to use, when not to use, workflow, safety boundaries, pitfalls, stop conditions, failure handling, and verification.
- Avoid secrets, credentials, personal data, production records, temporary task state, and stale identifiers.

## Promotion Workflow

1. Verify the completed task with real commands or runtime evidence.
2. Evaluate trigger signals.
3. Check existing skills for overlap.
4. Draft the complete English canonical skill body.
5. Create the candidate record only.
6. Render and show the complete Vietnamese proposal.
7. Wait for separate user approval.
8. Bind approval to the candidate ID and canonical content SHA-256.
9. Promote the candidate to `.ai/skills/<name>/SKILL.md`.
10. Run `./ai sync`.
11. Run `./ai doctor`.
12. Report created or updated files and real verification results in Vietnamese.

## Stop Conditions

Stop without promotion when:

- Separate approval is absent.
- The user chooses B, C, or D.
- The candidate contains secret-like content or sensitive data.
- The canonical skill contains Vietnamese prose.
- The scope is not project-local.
- A `create` action would overwrite an existing skill.
- An `update` action targets a missing skill.
- Approval does not match the candidate ID or canonical content hash.
- Verification of the original workflow is incomplete.

## Failure Handling

- Validation failure: keep the canonical skill unchanged and report the exact failed field.
- Sync failure: keep the canonical source, report the adapter failure, and run `./ai doctor` after correction.
- Promotion write failure: do not mark the candidate as promoted.
- Duplicate discovered after drafting: convert the proposal to an update or discard it; do not create a second overlapping skill.

## Verification Checklist

- [ ] The original workflow was verified with real evidence.
- [ ] The proposal was shown in Vietnamese.
- [ ] The proposal listed triggers, workflow, verification, pitfalls, and affected files.
- [ ] Separate user approval was obtained.
- [ ] Approval matches the candidate ID and canonical content SHA-256.
- [ ] Canonical `SKILL.md` is in English.
- [ ] Scope is project-local.
- [ ] No secret, credential, personal data, or production dataset is stored.
- [ ] `./ai sync` passed.
- [ ] `./ai doctor` passed.
