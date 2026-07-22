<!-- GENERATED FILE — DO NOT EDIT DIRECTLY -->
<!-- canonical: .ai/skills/project-doctor/SKILL.md -->
<!-- generated_at: 2026-07-21T09:58:31+00:00 -->
<!-- source_sha256: 4f18bef60d68b527b99457f0ae6c8e420a68b61d7959bcc0ec56e9bb71e9ad28 -->
<!-- schema_version: 1.0 -->

---
name: project-doctor
description: Check Project Brain health, skills, adapters, generated context, approvals, and documentation impact at session start and before completion.
layer: operations
trigger_keywords: doctor, health check, framework validation
---

# Project Doctor

## Preconditions

- The repository contains `.ai/`.
- Python 3 is available.

## Procedure

1. Check required files and parse JSON.
2. Check frontmatter, name, description, and directory name for every skill.
3. Check adapter hashes against canonical sources and detect generated drift.
4. Check the session brief size and secret patterns.
5. Check that configured build/test commands are plausible.
6. Check that code changes have documentation mapping or a `no-doc-impact` reason.
7. Check that change implementation has approval and active state updates.
8. Return PASS, WARNING, or FAIL for each item with a concrete fix.

## Stop conditions

FAIL when required JSON/skills are invalid, adapters are stale, generated context contains a secret pattern, or approval is missing.

## Missing information

Return WARNING `not verified`; do not convert missing data into PASS.

## Expected output

A PASS/WARNING/FAIL report and a non-zero exit code for serious failures. Present the report to users in Vietnamese while keeping diagnostic identifiers and commands unchanged.

## Failure handling

Do not silently edit files in doctor. Suggest the exact command or file to change, then run the check again.
