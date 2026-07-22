# Approval policy

Before a significant change, the agent must prepare the request internally in English and present the following content to the user in Vietnamese:

```text
Tôi hiểu yêu cầu là:

1. Hiện tại hệ thống đang...
2. Sau thay đổi, hệ thống cần...
3. Người hoặc quy trình bị ảnh hưởng...
4. Những phần có thể cần chỉnh...
5. Những điều tôi chưa chắc...

Tôi chưa chỉnh sửa code.

Anh/chị xác nhận:
A. Đúng ý, tiếp tục
B. Sửa lại các điểm sau
```

Only after the user selects A or gives equivalent explicit confirmation may `approval.md` be written with status `approved`.

Separate approval is required for database migration, authentication/permission, data deletion or transformation, production dependency, API contract, infrastructure/deployment, external service cost, and every canonical Project Brain skill creation or update.

## Skill approval requirements

Skill approval is separate from task approval. Before creating or updating `.ai/skills/<name>/SKILL.md`, the agent must show a complete Vietnamese proposal with the name, trigger conditions, workflow, verification, pitfalls, affected files, scope, and the English canonical content that will be promoted. The user must explicitly approve that exact proposal. The approval record must bind the candidate ID and SHA-256 of the canonical English `SKILL.md` content. Any content change invalidates approval and requires a new proposal.

Project Brain skill candidates are project-local only. Do not create or modify global Hermes skills, memory, profiles, plugins, or configuration through this workflow.

## Language requirements

- Internal reasoning artifacts, canonical instructions, and prompts sent to agents use English.
- Approval explanations and all other user-facing output use Vietnamese.
- Store technical identifiers, paths, commands, and status values without translation.
