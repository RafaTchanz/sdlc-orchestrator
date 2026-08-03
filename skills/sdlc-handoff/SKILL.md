---
name: sdlc-handoff
description: Closes out the current session — reads every docs/sdlc/ artifact touched, appends a PROGRESS.md entry, prints a recap. Use when the user asks to wrap up/close out a session, or as the final step of any /sdlc, /sdlc-bug-fix, or /sdlc-task run. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-handoff

## Contract

- **Input**: none — reads the current `docs/sdlc/` tree and `PROGRESS.md` state.
- **Output**: an updated `PROGRESS.md` entry (`Done`/`Failed`/`Current State`/`Next`) plus a short recap to the user.
- **Boundary**: never starts new work — purely closes out the current state for the next session.

## Steps

1. Dispatch:

```

Agent(subagent_type: "sdlc-handoff", prompt: "Close out this session. Phase(s) that ran: {whatever the dispatching context knows, or 'unspecified — infer from docs/sdlc/ file mtimes' if called standalone with no context}.")

```

2. Print the agent's recap back to the user verbatim.

**Done when**: `PROGRESS.md` has a new entry and the user has seen the recap.
