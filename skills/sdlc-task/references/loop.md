# Single-story loop — `/sdlc-task`

This is the same loop as `/sdlc`'s epic-loop step 5 (see the `sdlc` skill's `references/phases.md` for the fully-annotated version) run exactly once, since a task-manifest has exactly one row/story. Restated here in full so this skill is readable standalone:

## 1 — Scrum Master

```
Agent(subagent_type: "sdlc-scrum-master", prompt: "Task manifest row: docs/sdlc/task-manifest.md. Write one story file at docs/sdlc/epics/epic-1/stories/story-1.1.md.")
```

(Task-manifest flows use a synthetic `epic-1` so the persistence layout stays identical to the full `/sdlc` flow — no special-casing needed downstream.)

## 2 — Coder squad

```
Agent(subagent_type: "sdlc-coder", prompt: "Story: docs/sdlc/epics/epic-1/stories/story-1.1.md. Tier overlay: {from the task-manifest row}. Implement per your TDD contract.")
```

## 3 — QA, with Tuner routing

Same signal routing as `/sdlc` step 5c: `APPROVE` → 4; `NIT`/`MINOR` → `sdlc-tuner` then re-run; `MAJOR` → back to 2; `CRITICAL`/`BLOCKED` → escalate, **[GATE]**.

## 4 — Review + Stress in parallel, Tuner routing on Review only

Same signal routing as `/sdlc` step 5d.

## 5 — Verdict

```
Agent(subagent_type: "sdlc-verdict", prompt: "Story 1.1. Aggregate docs/sdlc/epics/epic-1/story-1.1/{qa,review,stress}.md.")
```

**[GATE]** before commit — same as `/sdlc`'s gate 4, unnumbered here since `/sdlc-task` only ever has one story.

## 6 — Rejoin trunk

Invoke `/sdlc`'s own step 6 onward.
