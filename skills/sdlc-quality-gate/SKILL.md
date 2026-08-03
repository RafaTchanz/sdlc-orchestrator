---
name: sdlc-quality-gate
description: Detects the project's tech stack and runs every applicable quality gate (format/lint/types/coverage/race/vulnerability scan). Use when the user asks to run quality gates/checks outside the full /sdlc pipeline. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-quality-gate

## Contract

- **Input**: the current repo/stack (auto-detected) or an explicit file set.
- **Output**: `quality-gate.md` — PASS/FAIL per gate plus an overall verdict.
- **Boundary**: runs sensors only — never modifies code to force a gate to pass.

## Steps

1. Pick the output path: `docs/sdlc/epics/epic-{n}/quality-gate.md` if called from within an active `/sdlc` epic loop, otherwise `quality-gate.md` at the repo root (or wherever the user specifies).
2. Dispatch:

```

Agent(subagent_type: "sdlc-quality-gate", prompt: "Target: {repo/stack or explicit file set}. Write the report to {resolved path}, per your contract.")

```

3. Report the returned hand-off line back to the user verbatim. If overall verdict is `FAIL`, surface the failing gate rows directly in your response — don't make the user open the file to learn what broke.

**Done when**: `quality-gate.md` exists with every applicable gate row filled in and an overall PASS/FAIL line.
