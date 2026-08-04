---
name: sdlc
description: Runs a complete software project lifecycle from a raw idea to release — Brief, PRD, Architecture, per-story TDD implementation with QA/Review/Stress/Verdict, Security Review, Quality Gate, PR, and Release, with mandatory human gates. Use when the user asks to build/create a new feature, epic, or greenfield project. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc — Greenfield Orchestrator

Drives a project from idea to release by dispatching one isolated sub-agent per lifecycle phase and persisting every phase's output to `.md`.

## Contract

- **Input**: a project idea/feature description — ask if not provided.
- **Output**: the full artifact chain under `docs/sdlc/` (see `references/output-format.md` for the exact file skeletons) plus a `PROGRESS.md` entry at every checkpoint.
- **Boundary**: orchestration only — this skill never writes code, tests, or artifacts itself; every artifact comes from the sub-agent it dispatches via `Agent(subagent_type: "sdlc-...")`. Never auto-advances past a `[GATE]`. `sdlc-tuner` is dispatched only for `NIT`/`MINOR` findings routed by QA or Review — it never reopens architecture, story, or test-authoring decisions. `sdlc-slack-notify` is dispatched at gates 1/2/3 only when the session opted in during Intake; it never gates the pipeline — any failure, whether reported by the agent itself or from the dispatch failing outright (e.g. the agent is unavailable in the running session), is logged as a non-fatal warning and the trunk proceeds to the gate regardless. `NIT`/`MINOR` and `MAJOR` routing loops are capped at 3 rounds each, tracked independently per audit (see Global Constraints and `references/phases.md`) — a loop still unresolved beyond that escalates to a human gate rather than looping indefinitely.

## Steps

Full phase-by-phase dispatch prompts and routing logic: `references/phases.md`. Summary:

1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id?"_ Hold the answer (opted in yes/no, and `channel_id` if yes) only in this session's running context — never write it to any file.
2. Dispatch `sdlc-analyst` → `product-brief.md` → if this session opted in, dispatch `sdlc-slack-notify` → **[GATE 1]**.
3. Dispatch `sdlc-pm` with the Brief → `PRD.md` → if this session opted in, dispatch `sdlc-slack-notify` → **[GATE 2]**.
4. Dispatch `sdlc-architect` with Brief+PRD → `architecture.md` + `epic-manifest.md`; run `/sdlc-grill-me` against `architecture.md` → if this session opted in, dispatch `sdlc-slack-notify` on `architecture.md` → **[GATE 3]**.
5. **Epic loop** (repeat per `pending` row in the manifest) — full routing table in `references/phases.md`:
   - a. `sdlc-scrum-master` → story files for this epic.
   - b. Per story: Coder squad (`sdlc-coder` + tier overlay) → TDD implementation.
   - c. `sdlc-qa` → route on signal (`APPROVE` → d; `NIT`/`MINOR` → `sdlc-tuner` then re-run `sdlc-qa`; `MAJOR` → back to (b); `CRITICAL`/`BLOCKED` → escalate, **[GATE]**).
   - d. `sdlc-reviewer` + `sdlc-stress` in parallel → route on Review's signal only (`APPROVE`/clean → e; `NIT`/`MINOR`-only → `sdlc-tuner` then re-run both; `MAJOR`/`CRITICAL` → back to (b)).
   - e. `sdlc-verdict` → **[GATE 4]** before commit.
6. Dispatch `sdlc-security` and `sdlc-quality-gate` over the full diff (can run in parallel — independent, read-only, no shared state).
7. **[GATE 5]** → dispatch `sdlc-pr` to open the PR.
8. **[GATE 6]** → dispatch `sdlc-devops` (release half).
9. Dispatch `sdlc-handoff` to close the session.

**Done when**: `sdlc-handoff` has appended the final `PROGRESS.md` entry for this run, whether the run ended at a gate awaiting the human or completed through release.

## References

- `references/phases.md` — exact dispatch prompts and full routing logic per phase.
- `references/output-format.md` — file skeletons for every artifact this skill's sub-agents produce.
- `references/progress-file.md` — `PROGRESS.md` entry template and the session-start read convention.
