# Glossary

| Term | Plain-language meaning | In code | User may call it |
|---|---|---|---|
| Project Brain | Shared memory and governance profile for a project | `.ai/` | Project memory |
| Canonical | The single source of truth to edit directly | `.ai/` | Source of truth |
| Adapter | Generated instruction set for another tool | `AGENTS.md`, `CLAUDE.md`, skill adapters | Tool-facing copy |
| Session brief | Short summary of one working session | `.ai/generated/session-brief.md` | Session summary |
| Change intake | Clarifying a request before modifying code | `.ai/changes/*/request.md` | Change intake record |
| Impact analysis | Identifying what a change may affect | `impact.md` | Impact record |
| Doctor | Framework health check | `./ai doctor` | System check |
| Generated | Content regenerated from canonical sources | `.ai/generated/` | Auto-generated files |
| i18n layer | Vietnamese user-facing translation set | `docs/i18n/vi/` | User-facing docs |
| Language contract | English internally and to agents; Vietnamese to users | `.ai/knowledge/business-rules.md` | Language rules |
