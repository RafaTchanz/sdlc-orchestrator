# P0 Orchestrator Fixes — Implementation Plan

**Goal:** Fix the four load-bearing bugs found by a static, `sdlc-grill-me`-driven audit of `/sdlc`'s own agent/skill files — Scrum Master never receiving the PRD, an epic marked `done` after one story, Stress findings not driving routing, and the Coder committing before the review loop runs — plus two smaller consistency gaps (PM as sole owner of AC meaning; Verdict's missing-input handling as boundary prose, not a rule). Full problem statements, evidence, and rationale: `docs/superpowers/specs/2026-08-17-p0-orchestrator-fixes-design.md`.

**Architecture:** `epic-manifest.md` moves to one row per story (`Epic | Story | Title | Tier | Repo | Language/Stack | Depends-on | Status`), which lets Scrum Master's dispatch carry that exact story's PRD excerpt and makes the `Status → done` update correct by construction. Each story gets a dedicated `story-{n.m}-work` branch created before the Coder squad starts and merged into the base branch only once Gate 4 (renamed "before merge") confirms. Step 5d routes on the worse of Review's and Stress's signals instead of Review's alone.

**Tech Stack:** Markdown agent/skill definition files only (no application code, no test framework) — this repo's `sdlc-*` agents and `/sdlc`/`/sdlc-task` skills are prose contracts read by Claude Code, not executable modules.

## Global Constraints

- No direct commits on `main` — all work happens on `feature/p0-orchestrator-fixes-plan` (created off up-to-date `main`).
- Branch names must be prefixed `feature/`, `hotfix/`, or `release/`.
- Commit messages must be Conventional Commits.
- No automated test suite exists for these `.md` files — verification is static (grep + manual re-read), per the design doc §7.
- `agents/sdlc-github-issue.md` itself is never modified — its existing per-story dedup (via each story file's `**GitHub Issue**:` marker) already tolerates being called once per story instead of once per epic; only the trigger wording in `phases.md` changes.

---

### Task 1: Redefine the manifest schema — `agents/sdlc-architect.md`

**Files:** Modify `agents/sdlc-architect.md`.

**Interfaces:** Produces the one-row-per-story `epic-manifest.md`/`task-manifest.md` shape every other task in this plan assumes.

- [x] Full-mode Procedure step 4: manifest table becomes one row per story — `Epic | Story | Title | Tier | Repo | Language/Stack | Depends-on | Status`, pulling `ID`/`Title` straight from the PRD's Functional Requirements. `Depends-on` names story IDs. Hand-off line reports story count.
- [x] Light-mode Procedure step 2 (`task-manifest.md`): identical shape — `Task` always `1`, `Story` always `1.1`, `Title` from the task description, `Repo` always `—`.
- [x] Commit: `feat(sdlc-architect): restructure manifest to one row per story`.

### Task 2: Fix Scrum Master's PRD-blindness — `agents/sdlc-scrum-master.md`

**Files:** Modify `agents/sdlc-scrum-master.md`.

**Interfaces:** Consumes Task 1's one-row-per-story manifest. Its new Input line (manifest row + PRD story entry + architecture.md) is the contract Task 6's `phases.md` 5a dispatch prompt must satisfy.

- [x] Contract Input: manifest row (now always exactly one story) + that story's own PRD entry (full-mode sessions) + architecture.md if it exists.
- [x] Contract Boundary: never invent an AC beyond what the PRD/task description justifies; flag oversized stories as "needs upstream re-split" instead of silently splitting.
- [x] Procedure: drop the "for each story implied by the row" loop — always exactly one output file. AC rule: carry PRD ACs verbatim as baseline; a meaning-changing refinement must be flagged as a "PRD deviation" in the hand-off.
- [x] Hand-off: singular "Story file written" phrasing (was "N story files").
- [x] Commit: `feat(sdlc-scrum-master): consume PRD story entry, write exactly one story file`.

### Task 3: PM as sole owner of AC meaning — `agents/sdlc-pm.md`

**Files:** Modify `agents/sdlc-pm.md`.

**Interfaces:** Gives Task 2's "PRD deviation" flagging rule the upstream ownership line it points back to.

- [x] Boundary: one sentence — PM is the sole author of an AC's meaning; downstream agents may refine wording, never meaning.
- [x] Commit: `docs(sdlc-pm): state PM as sole owner of AC meaning`.

### Task 4: Coder works on the per-story branch by default — `agents/sdlc-coder.md`

**Files:** Modify `agents/sdlc-coder.md`.

**Interfaces:** Consumes the `story-{n.m}-work` branch Task 6's `phases.md` now creates before 5a.

- [x] Contract Input: work and commit on `story-{n.m}-work` by default (created by the dispatching skill before the Coder squad starts) — never directly on the base branch. The existing isolated-worktree case nests this branch inside the worktree rather than replacing it.
- [x] Commit: `feat(sdlc-coder): default to per-story branch instead of base branch`.

### Task 5: Verdict — BLOCKED clause, numbered missing-input rule, "before merge" — `agents/sdlc-verdict.md`

**Files:** Modify `agents/sdlc-verdict.md`.

**Interfaces:** None upstream; downstream is the human at Gate 4, which Task 6/7 also rename to "before merge".

- [x] Frontmatter description + Hand-off: "before commit" → "before merge".
- [x] Boundary: drop the missing/stale-input prose (promoted below).
- [x] Aggregation rule: new clause 1 — missing/stale input → automatic NOT READY. Clause 2 (was 1) — add `BLOCKED` alongside `CRITICAL`. Clauses 3–4 renumbered.
- [x] Commit: `fix(sdlc-verdict): add BLOCKED to the NOT READY clause, promote missing-input handling to a numbered rule`.

### Task 6: The bulk of the loop logic — `skills/sdlc/references/phases.md`

**Files:** Modify `skills/sdlc/references/phases.md`.

**Interfaces:** Consumes Task 1's manifest shape and Task 2's Scrum Master contract; produces the `story-{n.m}-work` branch Task 4's Coder contract and Task 5/7's Gate 4 wording depend on.

- [x] Step 5 heading: "Epic loop" → "Story loop" — one row is one story.
- [x] Before 5a: create `story-{n.m}-work` off the base branch for every story (the new default); the multi-epic `git worktree` case nests this branch inside the worktree instead of substituting for it.
- [x] 5a dispatch prompt: pass this story's PRD excerpt (full-mode) alongside the manifest row and architecture.md.
- [x] `sdlc-github-issue` trigger: reworded to "once per story, right after this story's Scrum Master dispatch" (no change to `agents/sdlc-github-issue.md`).
- [x] 5b note: Coder-squad/Tuner/gate-merge actions happen on `story-{n.m}-work`, nested in the epic worktree when one exists.
- [x] 5d: read both Review's and Stress's signals, route on the worse of the two, across all four branches.
- [x] 5e/Gate 4: "before merge"; on confirmation merge `story-{n.m}-work` into the base branch and delete it; on rejection/rework stay on the branch, no merge. `Status → done` update stays scoped to the one row just verdicted.
- [x] Commit: `fix(sdlc-phases): per-story branch, PRD-carrying dispatch, worse-of-both-signals routing`.

### Task 7: Trunk summary — `skills/sdlc/SKILL.md`

**Files:** Modify `skills/sdlc/SKILL.md`.

**Interfaces:** Summary mirror of Task 6 — must not drift from `phases.md`'s authoritative routing.

- [x] Step 5: "Epic loop" → "Story loop"; 5a mentions per-story branch creation and per-story (not per-epic) `sdlc-github-issue` dispatch; 5d routes on the worse of Review/Stress; 5e is "before merge" and states the merge-on-confirm behavior.
- [x] Commit: `docs(sdlc-skill): mirror phases.md's story-loop, worse-of-both routing, and before-merge gate`.

### Task 8: Output-format skeleton — `skills/sdlc/references/output-format.md`

**Files:** Modify `skills/sdlc/references/output-format.md`.

**Interfaces:** None — pure documentation of Task 1's schema.

- [x] Manifest skeleton line: one row per story, `Repo` column always present (`—` when not opted in).
- [x] Commit: `docs(sdlc-output-format): update manifest skeleton to one-row-per-story shape`.

### Task 9: `/sdlc-task` wording parity — `skills/sdlc-task/SKILL.md`, `skills/sdlc-task/references/loop.md`

**Files:** Modify both files.

**Interfaces:** No PRD-passing change needed — `/sdlc-task` deliberately has no PRD; Scrum Master's light-mode branch (Task 2) already covers it.

- [x] `SKILL.md` step 2: "epic-loop" → "story-loop"; "before commit" → "before merge".
- [x] `loop.md`: "epic-loop" → "story-loop" reference; step 4 heading "Tuner routing on Review only" → "routing on the worse of Review/Stress"; step 5 gate "before commit" → "before merge".
- [x] Commit: `docs(sdlc-task): align wording with story-loop and before-merge gate`.

### Task 10: New docs + README pointer

**Files:** Create `docs/superpowers/specs/2026-08-17-p0-orchestrator-fixes-design.md`, create this plan doc, modify `README.md`.

**Interfaces:** None — documentation only, no runtime effect.

- [x] Spec doc: problem-by-problem evidence + fix + rejected alternatives (per repo convention — original `docs/2026-07-29-sdlc-orchestrator-design.md` stays untouched).
- [x] This plan doc.
- [ ] `README.md`'s "Design history": append two bullets pointing at the new spec + plan, matching the existing entries' pattern.
- [ ] Commit: `docs: mark p0-orchestrator-fixes implemented, update design history`.

### Task 11: `/sdlc-bug-fix` parity — found by a broader second-pass review

**Files:** Modify `agents/sdlc-tuner.md`, `skills/sdlc-bug-fix/SKILL.md`, `skills/sdlc-bug-fix/references/dispatch.md`, `README.md`, plus the spec doc (§3.6) and this plan doc.

**Interfaces:** Brings `/sdlc-bug-fix` into line with the contracts Tasks 4 and 6 changed on `sdlc-coder.md` and the routing logic — `sdlc-coder.md` and `sdlc-tuner.md` are shared by `/sdlc`, `/sdlc-task`, and `/sdlc-bug-fix`, but only the first two were checked against the new contracts before this task.

- [x] `sdlc-tuner.md`: Contract Input + frontmatter description name `sdlc-stress.md` alongside `sdlc-qa.md`/`sdlc-reviewer.md` as a valid finding source.
- [x] `sdlc-bug-fix/SKILL.md`: Contract Output adds `stress.md`/`verdict.md`; step 1 creates `bugfix-{slug}-work` before the Investigator dispatch; step 4 becomes Review+Stress in parallel with worse-of-two routing; new step 5 dispatches `sdlc-verdict` and gates the merge; old step 5 (rejoin trunk) renumbers to step 6.
- [x] `sdlc-bug-fix/references/dispatch.md`: branch-creation note before step 1; Investigator's and Coder's prompts state the branch; step 4 becomes a parallel Reviewer+Stress dispatch; new step 5 dispatches Verdict with the merge-gate note; rejoin-trunk renumbers to step 6.
- [x] `README.md`: `/sdlc-bug-fix` entry-point bullet mentions the branch and the stress/verdict path.
- [x] Commit: `fix(sdlc-bug-fix): branch isolation, stress dispatch, and a real merge gate — parity with /sdlc's story loop`.

---

## Verification

1. `grep -rn "before commit\|Review's signal only\|route on Review" agents/ skills/` — must return nothing.
2. `grep -rn "Stories.*Tier\|Epic.*Stories.*Tier" agents/ skills/` — must return nothing; the only manifest shape described anywhere is the new one-row-per-story table.
3. Re-read `phases.md`'s full step 5 block end-to-end as if dispatching it by hand for a 2-story epic — confirm the branch is created once per story (not per epic), the merge happens once per story at its own Gate 4, and manifest-done-marking never touches a row other than the one just verdicted.
4. Cross-check `sdlc-scrum-master.md`'s Input line against `phases.md`'s 5a dispatch prompt — the dispatch prompt must supply everything the contract claims as input.
5. Confirm `task-manifest.md`'s column shape (`sdlc-architect.md` light mode) and `epic-manifest.md`'s shape agree exactly, since `/sdlc-task` treats them as interchangeable.
