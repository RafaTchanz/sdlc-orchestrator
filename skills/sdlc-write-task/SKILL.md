---
name: sdlc-write-task
description: Writes one fully-specified, grounded task document (Context/DoR/Acceptance Criteria/Technical Notes/DoD/Open Questions) — no pipeline, no implementation. Use when the user wants a well-documented task/ticket written without running /sdlc-task's full Coder/QA/Review/Stress loop. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-write-task

## Contract

- **Input**: a free-form task description — ask if not provided.
- **Output**: `docs/sdlc/tasks/task-{slug}.md` plus `docs/sdlc/tasks/INDEX.md`; optionally, one GitHub Issue.
- **Boundary**: writes documentation only — never dispatches `sdlc-coder` or any QA/Review/Stress/Verdict agent. Never creates a GitHub Issue without explicit user confirmation.

## Steps

1. Collect the task description from the user if not already given.
2. Dispatch:

```

Agent(subagent_type: "sdlc-task-writer", prompt: "Task: {description}. Write the task document per your contract.")

```

3. Report the returned hand-off line verbatim. If it flags a possible overlap or open questions, surface those directly rather than only pointing at the file.
4. Ask the user: open a GitHub Issue for this task now? Tell them upfront, before they confirm, that this reuses `sdlc-github-issue` (designed for real epics) for a standalone task, so the resulting "Epic" custom field and hand-off line will read "Epic {task ID}" — a known cosmetic quirk, not a true epic reference. If yes, ask for every input `sdlc-github-issue`'s own contract actually requires — target repo (`owner/repo`), the Project board (`owner` + number), `tribo`, `squad` — plus the optional `project_name`. Collect all four required values or don't dispatch it — `sdlc-github-issue` has no fallback for a missing board/tribo/squad.
5. If confirmed, dispatch `sdlc-github-issue` reusing its existing contract: pass the task's own file path directly as the single explicit story/task file (its step 1 accepts this in place of an epic-directory Glob), and this task's own ID in place of an epic number:

```

Agent(subagent_type: "sdlc-github-issue", prompt: "Story/task file: docs/sdlc/tasks/task-{slug}.md (single explicit file — no epic directory to Glob). Epic number: {task ID} (standalone task, not a true epic — the resulting 'Epic' custom field and hand-off line will read 'Epic {task ID}'; this is expected). Target repo: {repo}. Board: {owner}/{number}. Tribo: {tribo}. Squad: {squad}. Project: {project_name, if given}. Create the issue per your contract.")

```

`sdlc-github-issue`'s existing dedup rule (skip any file that already has a `**GitHub Issue**:` line) applies unchanged.

6. Report `sdlc-github-issue`'s hand-off line verbatim, and remind the user (as told upfront in step 4) that the "epic-N"/"Epic N" appearing in that line (or in the board's `Epic` custom field) refers to this task's own ID, not a true epic. If it reports a non-fatal warning (network/`gh`-auth/board-resolution failure — its own contract already logs these and continues), relay that warning to the user as a partial-success note, not as a failure of the whole `/sdlc-write-task` call — the task document from step 2 is already written and valid regardless of Issue-creation outcome.

**Done when**: `docs/sdlc/tasks/task-{slug}.md` and `INDEX.md` exist, and — if the user opted in — the GitHub Issue is created and linked in the task file.
