# Board Model Integration Implementation Plan

**Goal:** stories/tasks created by `/sdlc` and `/sdlc-write-task` land on the squad's board already inside the Iniciativa → Épico → História hierarchy, with `Nível`/`Origem`/`Status` set, and an optional roadmap plans épico dates.

**Spec:** `docs/superpowers/specs/2026-11-13-board-model-integration-design.md`

**Architecture:** one new agent, `sdlc-board-planner`, owns every board-hierarchy lookup and write above the story level (resolve/create épicos, link épico → iniciativa, plan dates). `sdlc-github-issue` gains a best-effort "board model" step for each story it creates. The `/sdlc` trunk dispatches the planner at Intake (new Step 1a); `/sdlc-write-task` dispatches it before creating its Issue. Ambiguity is always resolved by the skill (main session) asking the human — subagents never ask.

## Global constraints

- Backward compatible: on a board without a `Nível` field, nothing new runs.
- Best-effort: no board step ever blocks the pipeline; failures are named warnings.
- Never hardcode field/option/board IDs, nor the tribe repo — all resolved at runtime or passed in the dispatch.
- Never overwrite a field that already has a value; never move an épico that already has a different parent; never create an iniciativa.
- `scripts/check_contracts.py` must pass.

## Tasks

1. **New `agents/sdlc-board-planner.md`** — Contract/Procedure/Hand-off per spec §3.5, plus: resolves iniciativa and épicos by number/URL/partial title/`project_name`; with a roadmap, creates missing épicos (`Nível=Épico`, `Origem=Upstream`, `Projeto`, `Status=Ready to Refin`), links them to the iniciativa, and plans dates in working days computed with `python3` (never mentally); structured hand-off lines (`AMBÍGUA`/`NÃO ENCONTRADA`/`MODELO AUSENTE`) the skill acts on.
2. **`agents/sdlc-github-issue.md`** — new inputs `Origem`, `Status`, `Parent epic`; new step 3.vii-b (Nível/Origem/Status via `gh project item-edit`, `addSubIssue` to the parent épico); hand-off suffix.
3. **`skills/sdlc/SKILL.md` + `references/phases.md`** — Intake question extended (tribe repo, iniciativa, épicos, roadmap); new Step 1a (planner dispatch + ambiguity handling → `epic_map`); Step 4 architect prompt gets roadmap épico names; Step 5a maps each epic to its board épico at GATE 4 and passes the new fields to `sdlc-github-issue`.
4. **`skills/sdlc-write-task/SKILL.md`** — Step 4 collects tribe repo/iniciativa/épico; new step 4b dispatches the planner (no roadmap) and resolves ambiguity; step 5 passes the new fields.
5. **Docs & release** — README (22 agents, responsibility matrix, design history), `plugin.json`/`marketplace.json` description + version 1.3.0, CHANGELOG 1.3.0, spec updated with implementation rulings.
6. **Verify** — `python3 scripts/check_contracts.py`; read-only smoke test of the planner's lookups against board 7.
