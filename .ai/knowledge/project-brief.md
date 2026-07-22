# Project brief

## Verification status

**Not verified.** The repository was empty when surveyed. This document is an initial framework brief, not a confirmed description of a business application.

## What problem does the system solve?

Not determined. Project Brain was created to preserve durable knowledge and help agents work in a controlled way across sessions.

## Who are the users?

Not determined. The current context identifies the user as an enterprise digital-transformation lead.

## Main capabilities

No application source code is available for verification. Project Brain currently covers session brief generation, change intake and approval management, impact analysis, knowledge and skill synchronization, and quality checks.

## Out of scope

- Do not modify business application source code during this setup phase.
- Do not infer unverified application behavior.
- Do not place secrets or production data into project knowledge.

## Definition of working correctly

- `./ai doctor` runs and returns a non-zero exit code for serious failures.
- Adapters have hashes matching their canonical sources.
- The session brief is short, sourced, and explicit about unverified scope.
- Significant changes have approval before implementation.

## Language contract

- Canonical Project Brain instructions and agent-facing prompts are written in English.
- Inputs sent to agents use English.
- Agent outputs intended for users use Vietnamese.
- Vietnamese user-facing translations are maintained under `docs/i18n/vi/` and linked from the Vietnamese README.
