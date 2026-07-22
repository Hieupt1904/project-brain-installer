---
name: project-start
description: Start a project session by checking Project Brain, synchronizing adapters, and creating a session brief before reading or changing code.
layer: operations
trigger_keywords: session start, initialize project, session brief
---

# Project Start

## Preconditions

- The current directory is a repository containing `.ai/`.
- Python 3 can run.
- The entire source tree does not need to be read.

## Procedure

1. Run `./ai start` or `python3 .ai/scripts/agentctl.py start`.
2. Run the quick doctor and stop for serious framework-structure errors.
3. Synchronize `.ai/skills/` to `.agents/skills/` and `.claude/skills/`.
4. Read `.ai/project.json`, `.ai/knowledge/active-state.md`, `.ai/knowledge/decisions.md`, and the generated session brief.
5. Read branch, HEAD, status, and recent changes with Git when the repository has Git.
6. Based on the current request, propose only the files that need to be read next; do not read the entire repository.
7. Keep all canonical planning and agent-facing inputs in English; explain the session status to the user in Vietnamese.

## Stop conditions

- Stop if Project Brain is missing, JSON is invalid, or sensitive content is detected in generated context.
- Stop before code edits if the request has not passed `change-intake`.

## Missing information

Mark unknowns as `not verified` in canonical records. Do not infer framework, build/test commands, or impact scope.

## Expected output

- A short, size-limited `.ai/generated/session-brief.md`.
- PASS/WARNING/FAIL quick-doctor report.
- Sources read and files proposed for the next step. User-facing summary is Vietnamese.

## Failure handling

Record the failed command, evidence-based cause, and specific remediation. Do not claim the session is ready if the brief was not created.
