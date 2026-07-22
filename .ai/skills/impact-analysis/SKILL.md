---
name: impact-analysis
description: Analyze code, data, security, tests, documentation, operations, and integrations affected by an approved request.
layer: governance
trigger_keywords: impact analysis, affected files, risk assessment
---

# Impact Analysis

## Preconditions

- A change folder and `approval.md` with `approved` status exist.
- A session brief/repository map exists or can be created.

## Procedure

1. Read the approved request and scope.
2. Use the repository map and targeted search; do not read the entire repository unnecessarily.
3. Identify impact on code, data, security, tests, documentation, operations, and integrations.
4. Write `.ai/changes/<change>/impact.md` with a technical English analysis. Add a Vietnamese user-facing summary when presenting results.
5. Mark files to read, risks, assumptions, and verification methods.
6. Request separate approval for database migration, authentication/permission, data transformation, production dependency, API contract, infrastructure/deployment, or external service cost.

## Stop conditions

Stop if approval is missing, status is not `approved`, or the plan exceeds approved scope.

## Missing information

Mark unknowns as `not verified` in canonical English records and explain them in Vietnamese. Do not turn assumptions into facts.

## Expected output

An `impact.md` containing scope, affected files, risks, tests, and any required additional approvals. User-facing reporting is Vietnamese.

## Failure handling

Do not proceed to implementation until risks and verification methods are recorded. Report blockers in Vietnamese.
