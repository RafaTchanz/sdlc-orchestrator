# Changelog

## 1.3.0 — 2026-11-16

### Added

- New agent `sdlc-board-planner` (Oráculo): resolves the Iniciativa and Épicos a delivery belongs to on the squad's GitHub Project board — by number, link, part of the title, or `project_name` — and links each Épico under its Iniciativa. Given a roadmap (épicos with durations and a start date, as text or a document path), it also creates the Épicos that don't exist yet (`Nível = Épico`, `Origem = Upstream`, `Status = Ready to Refin`) and plans their dates in sequential working days (`Início dev`/`Fim dev`/`Entrega prod (plan.)`), plus the Iniciativa's. It never asks the human (it reports `AMBÍGUA`/`SEM CORRESPONDÊNCIA`/`NÃO CLASSIFICADO`… for the skill to ask), never creates an Iniciativa, never overwrites a field that already has a value, and creates an Épico only when the Iniciativa is resolved, every lookup succeeded and no existing Épico under it could be the same one (or the human confirmed it is new) — so a roadmap never duplicates épicos already on the board.
- `/sdlc` Intake asks, inside the existing GitHub-issue question, for the tribe repo, Iniciativa, Épico(s) and an optional roadmap; a new **Step 1a** dispatches `sdlc-board-planner` before the Analyst and asks the human once about anything ambiguous. At GATE 4 each epic is mapped to its board Épico together with the batch approval, and the architect is told the planned Épicos so epic boundaries can line up with them.
- `sdlc-github-issue` (Falcão) takes optional `Origem`, `Status` and `Parent epic`: each story is created with `Nível = História`, `Origem`, `Status` (`Ready to dev` after GATE 4) and as a sub-issue of its Épico. `/sdlc-write-task` resolves its task's Épico through `sdlc-board-planner` and does the same for its single Issue.
- Fully backward compatible: on a board without a `Nível` field (`MODELO AUSENTE`), every dispatch is sent exactly as in 1.2.0.

### Fixed

- `sdlc-github-issue`: adding a new `Projeto` option now explicitly re-sends every existing option with its `id`. Sent without it, `updateProjectV2Field` recreates the options and every card on the board loses its `Projeto` value.

### Breaking

None.

## 1.2.0 — 2026-09-22

### Added

- `sdlc-stress` is now skipped entirely for any story/task/bug whose `Complexity` is `simple`, across all three entry points (`/sdlc`, `/sdlc-task`, `/sdlc-bug-fix`) — every round, not just the first. `simple`'s own definition (single component/file area, no new integration, no concurrency/async coordination) already excludes every scenario Stress checks for, so running it there only ever produced a confirming `APPROVE` at the cost of a full agent dispatch.
- `sdlc-qa` and `sdlc-reviewer` still run in full regardless of `Complexity` — this change narrows only the resilience-under-load check, never correctness or test-quality auditing.
- `sdlc-verdict` treats a missing `stress.md` as N/A (not `NOT READY`) whenever the caller states `Complexity: simple`; any other missing report is still treated as before.

### Fixed

None.

### Breaking

None.

## 1.1.0 — 2026-09-22

### Added

- `/sdlc` story loop now writes every pending story in a batch (or a human-named subset) in parallel via `sdlc-scrum-master`, presents the whole batch together, and gates it as GATE 4 before any Coder-squad dispatch begins — previously implementation started right after a single story was written, with no checkpoint in between.
- `sdlc-github-issue` dispatch moves to after GATE 4 and now takes an explicit approved-file list instead of scanning an epic's story directory, so a story sent back for rework never gets a stale GitHub Issue (Issues are never edited once created).
- `/sdlc-task` gets the same single-story validation gate before its Coder dispatch, for consistency with `/sdlc`.

### Fixed

- Renumbered every downstream gate reference after inserting the new batch gate: per-story merge is now GATE 5, PR is GATE 6, release is GATE 7 — updated across `phases.md`, `SKILL.md` summaries, `sdlc-pr.md`, `sdlc-devops.md`, `sdlc-pr-review/SKILL.md`, and `sdlc-release/SKILL.md`, which use the gate number to decide whether the trunk already confirmed before dispatch.

### Breaking

None.
