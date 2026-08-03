---
name: sdlc-security-review
description: Runs a full OWASP Top 10 (plus OWASP LLM Top 10 when AI/LLM code is present) security audit against a diff, file set, or branch. Use when the user asks for a security review/audit outside the full /sdlc pipeline. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-security-review

## Contract

- **Input**: a diff, an explicit file set, or "the current branch" — ask if ambiguous.
- **Output**: `security-review.md` — OWASP Top 10 (+ LLM Top 10 when relevant) threat table and a CRITICAL-found/none verdict.
- **Boundary**: read-only — proposes fixes but never edits code itself.

## Steps

1. Resolve the target: if the user didn't specify a diff/file set/branch, ask which.
2. Pick the output path: `docs/sdlc/epics/epic-{n}/security-review.md` if called from within an active `/sdlc` epic loop, otherwise `security-review.md` at the repo root (or wherever the user specifies).
3. Dispatch:

```

Agent(subagent_type: "sdlc-security", prompt: "Target: {diff/files/branch}. Write the report to {resolved path}, per your contract.")

```

4. Report the returned hand-off line back to the user verbatim.

**Done when**: `security-review.md` exists with both coverage tables filled and a top-3-5 summary.
