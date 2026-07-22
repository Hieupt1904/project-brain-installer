# Core principles

> This is the canonical source. Adapters outside `.ai/` only point to or are generated from this content.

- The source of truth for Project Brain and Agent Skills is under `.ai/`.
- Do not read the entire repository at session start. Read `session-brief.md`, then only the files relevant to the request.
- Use English for canonical/internal instructions and every prompt or input sent to agents.
- Return user-facing responses in Vietnamese, using clear everyday language unless the user explicitly requests another output language.
- Do not modify source code before explaining the request to the user in Vietnamese and receiving approval.
- Do not expand approved scope. If the plan is wrong, stop and report it.
- Do not read or place secrets, credentials, private keys, or production data into context.
- Do not edit generated files directly; edit canonical sources and run `./ai sync` or `./ai brief`.
- Do not claim to understand the entire repository without evidence of the scope read.
- Prefer the Python standard library for governance scripts.
- Report verification honestly: include commands run, results, and unverified areas.
