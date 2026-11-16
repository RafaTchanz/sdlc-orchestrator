---
name: sdlc-write-task
description: Writes one fully-specified, grounded task document (Context/DoR/Acceptance Criteria/Technical Notes/DoD/Open Questions) — no pipeline, no implementation. Use when the user wants a well-documented task/ticket written without running /sdlc-task's full Coder/QA/Review/Stress loop. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-write-task

## Contract

- **Input**: a free-form task description — ask if not provided.
- **Output**: `docs/sdlc/tasks/task-{slug}.md` plus `docs/sdlc/tasks/INDEX.md`; optionally, one GitHub Issue — on a board using the Iniciativa/Épico/História model, created as a `História` sub-issue of its Épico.
- **Boundary**: writes documentation only — never dispatches `sdlc-coder` or any QA/Review/Stress/Verdict agent. Never creates a GitHub Issue without explicit user confirmation.

## Steps

1. Collect the task description from the user if not already given.
2. Dispatch:

```

Agent(subagent_type: "sdlc-task-writer", prompt: "Task: {description}. Write the task document per your contract.")

```

3. Report the returned hand-off line verbatim. If it flags a possible overlap or open questions, surface those directly rather than only pointing at the file.
4. Ask the user: open a GitHub Issue for this task now? Tell them upfront, before they confirm, that this reuses `sdlc-github-issue` (designed for real epics) for a standalone task, so the resulting "Epic" custom field and hand-off line will read "Epic {task ID}" — a known cosmetic quirk, not a true epic reference. If yes, ask for every input `sdlc-github-issue`'s own contract actually requires — target repo (`owner/repo`), the Project board (`owner` + number), `tribo`, `squad` — plus the optional `project_name`. Collect all four required values or don't dispatch it — `sdlc-github-issue` has no fallback for a missing board/tribo/squad. In the same question, also ask (all optional — say you'll look them up on the board if not given): the tribe repo where Iniciativas and Épicos live (`owner/repo`), and the Iniciativa and Épico this task belongs to (number, link or part of the title).
   4b. If confirmed, dispatch `sdlc-board-planner` to resolve the board hierarchy — no roadmap here, so it never creates an Épico; it only finds the Iniciativa/Épico and links the Épico under the Iniciativa when it has no parent yet:

```

Agent(subagent_type: "sdlc-board-planner", prompt: "Board: {owner}/{number}. Tribe repo: {tribe repo, if given}. Tribo: {tribo}. Squad: {squad}. Project: {project_name, if given}. Iniciativa: {iniciativa, if given}. Épicos: {épico, if given}. Resolve and link per your contract.")

```

Omit every clause whose value wasn't given — never ask for the tribe repo before dispatching. Act on its hand-off exactly as `/sdlc`'s Step 1a does (`skills/sdlc/references/phases.md`), for the Iniciativa line and the Épico line alike: `MODELO AUSENTE` → `board_model = off` (step 5 is sent exactly as before this feature); otherwise `board_model = on` and the task's Épico is its resolved `Épico "…": owner/repo#N` line. Every line that needs the human — `AMBÍGUA`/`AMBÍGUO`, `NÃO ENCONTRADA`/`NÃO ENCONTRADO`, `NÃO É INICIATIVA`/`NÃO É ÉPICO`, `NÃO CLASSIFICADA`/`NÃO CLASSIFICADO`, or a `Candidatos sob a iniciativa` line — is asked in one message ("nenhum" accepted), then re-dispatch once with the answers (chosen `owner/repo#N`, `Confirmados: …`). Still unresolved → continue without it. Never block step 5 on this: a failed dispatch is a non-fatal warning with `board_model = off`.

5. If confirmed, dispatch `sdlc-github-issue` reusing its existing contract: pass the task's own file path directly as the single explicit story/task file (its step 1 accepts this in place of an epic-directory Glob), and this task's own ID in place of an epic number:

```

Agent(subagent_type: "sdlc-github-issue", prompt: "Story/task file: docs/sdlc/tasks/task-{slug}.md (single explicit file — no epic directory to Glob). Epic number: {task ID} (standalone task, not a true epic — the resulting 'Epic' custom field and hand-off line will read 'Epic {task ID}'; this is expected). Target repo: {repo}. Board: {owner}/{number}. Tribo: {tribo}. Squad: {squad}. Project: {project_name, if given}. Create the issue per your contract.")

```

When `board_model` is on (step 4b), insert `Origem: Upstream. Status: Ready to dev. Parent epic: {the task's Épico, owner/repo#N}.` before `Create the issue per your contract.` — omit `Parent epic:` when no Épico was resolved, but keep `Origem`/`Status`. A task written by this skill already has its DoR and Acceptance Criteria, hence `Ready to dev`.

`sdlc-github-issue`'s existing dedup rule (skip any file that already has a `**GitHub Issue**:` line) applies unchanged.

6. Report `sdlc-github-issue`'s hand-off line verbatim, and remind the user (as told upfront in step 4) that the "epic-N"/"Epic N" appearing in that line (or in the board's `Epic` custom field) refers to this task's own ID, not a true epic. If it reports a non-fatal warning (network/`gh`-auth/board-resolution failure — its own contract already logs these and continues), relay that warning to the user as a partial-success note, not as a failure of the whole `/sdlc-write-task` call — the task document from step 2 is already written and valid regardless of Issue-creation outcome.

**Done when**: `docs/sdlc/tasks/task-{slug}.md` and `INDEX.md` exist, and — if the user opted in — the GitHub Issue is created and linked in the task file.
