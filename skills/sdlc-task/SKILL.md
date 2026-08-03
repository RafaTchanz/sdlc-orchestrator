---
name: sdlc-task
description: Runs a single small task or feature through the same TDD/QA/Review/Stress/Verdict loop as /sdlc, skipping the Brief/PRD phases. Use when the user asks for a small, well-understood change — "add a field", "add an endpoint", "one focused task" — not a full epic. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-task — Small-task Entry Point

## Contract

- **Input**: a single small task/feature description — ask if not provided.
- **Output**: `docs/sdlc/task-manifest.md` plus one story's worth of `qa.md`/`review.md`/`stress.md`/`verdict.md`; then rejoins the common trunk.
- **Boundary**: skips Brief/PRD entirely. The Architect runs in light mode — `task-manifest.md` only, no full `architecture.md` sections. Never auto-advances past a `[GATE]`.

## Steps

Full loop content: `references/loop.md`. Summary:

1. Dispatch `sdlc-architect` in light mode → `docs/sdlc/task-manifest.md` → **[GATE]**.
2. Single-story loop (same shape as `/sdlc`'s epic-loop step 5, run exactly once) → **[GATE]** before commit.
3. Continue at `/sdlc`'s step 6 (Security Review onward).

**Done when**: the single story's `verdict.md` clears its gate and the trunk's remaining steps have been handed off to.

## References

- `references/loop.md` — the single-story loop written out in full (Coder → QA with Tuner routing → Review+Stress with Tuner routing → Verdict → gate).
