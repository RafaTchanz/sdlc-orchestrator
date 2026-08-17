# P0 Orchestrator Fixes — Design

**Date**: 2026-08-17
**Status**: Implemented (`agents/sdlc-architect.md`, `agents/sdlc-scrum-master.md`, `agents/sdlc-pm.md`, `agents/sdlc-coder.md`, `agents/sdlc-verdict.md`, `agents/sdlc-tuner.md`, `skills/sdlc/SKILL.md`, `skills/sdlc/references/phases.md`, `skills/sdlc/references/output-format.md`, `skills/sdlc-task/SKILL.md`, `skills/sdlc-task/references/loop.md`, `skills/sdlc-bug-fix/SKILL.md`, `skills/sdlc-bug-fix/references/dispatch.md`, `README.md`) — see `docs/superpowers/plans/2026-08-17-p0-orchestrator-fixes.md`.

## 1. Motivation

A dry-run of `/sdlc` against a personal project shipped every feature
broken. A static audit — using the `sdlc-grill-me` skill as an adversarial
lens against the orchestrator's own agent/skill files, not against any
generated artifact — found four load-bearing bugs and two smaller
consistency gaps in the pipeline itself, verified directly against this
repo's `.md` contracts (re-checked again after a mid-session pull of 21
commits — GitHub issue creation and the Intake interview — neither of
which fixes any of these bugs, but both touch files this change also
edits).

After that first pass shipped, a second, deliberately broader pass — every
one of the 20 agent files and 9 skills, not just the 11 files the first
pass touched — checked whether fixing a _shared_ agent's contract (§3.3's
Stress routing, §3.4's per-story branch) had left any of that agent's
_other_ callers inconsistent with the new contract. It had:
`/sdlc-bug-fix` also dispatches `sdlc-coder` and `sdlc-tuner`, and had
neither the branch isolation §3.4 now assumes nor the Stress dispatch
§3.3 now routes on. See §3.6.

## 2. Scope

- **In scope**: the four bugs and two gaps in §3.1–3.5, plus one more found
  by the broader second-pass review in §3.6 — fixed with the smallest
  structural change that closes each one.
- **Out of scope** (deferred — a separate, larger effort): stable
  IDs/`derived_from` traceability graph, `traceability.yaml`/`run-state.yaml`/gate
  hash files, a dedicated `sdlc-trace-reviewer` agent, contract/journey
  tests, a Godot/unknown-stack adapter for `sdlc-quality-gate.md`,
  AC-level test-traceability proof in QA (vs. plain coverage %), a
  negative-fixture test suite for the orchestrator itself.

## 3. Problems found and fixes

### 3.1 Scrum Master never receives the PRD

**Evidence**: `agents/sdlc-scrum-master.md`'s old Contract Input was "one
epic-manifest.md (or task-manifest.md) row + `architecture.md` if it
exists" — no PRD — yet its own Acceptance Criteria step said to "carry
over and refined from the PRD story of the same ID." It ends up inventing
ACs instead of inheriting them, since it was never given the PRD to
inherit from.

**Fix**: Contract Input now explicitly includes "that story's own entry
... in `docs/sdlc/PRD.md` (full-mode `/sdlc` sessions only)", and
`phases.md`'s 5a dispatch prompt now passes that story's exact PRD excerpt
alongside the manifest row and architecture.md. The Acceptance Criteria
rule now says: carry the PRD story's ACs as the baseline verbatim; wording
refinement is fine; any refinement that changes an AC's _meaning_ must be
flagged in the hand-off as a "PRD deviation" naming the AC.

### 3.2 An epic could be marked `done` after just its first story

**Evidence**: `epic-manifest.md` listed a comma-separated set of story IDs
per epic _row_ (`Stories: 1.1, 1.2, ...`), and `phases.md` marked that
whole row `done` right after _one_ story's Gate 4 cleared. The rest of the
epic's stories were silently never implemented.

**Fix**: restructured `epic-manifest.md` (and `task-manifest.md`, which
already had this shape) to **one row per story**:
`Epic | Story | Title | Tier | Repo | Language/Stack | Depends-on | Status`.
`sdlc-architect.md` already reads every story's ID/title straight from the
PRD's Functional Requirements in full mode — this is a different
projection of data it already has, not new invention. `Depends-on` now
names specific story IDs instead of epic numbers. Since a manifest row now
_is_ one story, the `Status → done` update in `phases.md`'s Gate 4 is
correct by construction — it can no longer close an epic on one story's
verdict, because there is no more per-epic row to close.

This also fixes 3.1 for free: a one-story row can carry that exact story's
PRD excerpt in its own dispatch, rather than a whole epic's worth at once.

### 3.3 Stress findings didn't drive routing

**Evidence**: step 5d dispatched `sdlc-reviewer` and `sdlc-stress` in
parallel, but the routing logic read only Review's signal
(`skills/sdlc/SKILL.md`'s old step 5d bullet, `phases.md`'s old 5d
routing). A `MAJOR`/`CRITICAL` from Stress alone never sent the story back
to the Coder squad.

**Fix**: 5d now reads both signals and routes on the worse of the two
(`CRITICAL`/`BLOCKED` > `MAJOR` > `MINOR`/`NIT` > `APPROVE`), across all
four routing branches in `phases.md` and the summary bullet in `SKILL.md`.

### 3.4 The Coder committed before QA/Review/Stress/Verdict ran

**Evidence**: Gate 4 was named "before commit," but `sdlc-coder.md`
committed during 5b — implementation — long before QA (5c), Review+Stress
(5d), and Verdict (5e) had run. A rework loop (5c/5d routing back to 5b)
left broken intermediate commits on whatever branch was checked out, and
the "gate before commit" framing was already false by the time a human saw
it.

**Fix**: a lightweight dedicated branch per story, `story-{n.m}-work`
(`git checkout -b`, no `git worktree`), created before the Coder squad
starts. `sdlc-coder.md` now works and commits there by default, never
directly on the base branch. Gate 4 is renamed "before merge" everywhere
(`sdlc-verdict.md`, `SKILL.md`, `phases.md`, and both `/sdlc-task` files)
and now actually gates a merge: on confirmation, `story-{n.m}-work` merges
into the base branch and is deleted; on rejection/rework, the branch stays
and no merge happens. This is real isolation without a full `git
worktree`'s disk/dependency cost — worktrees stay reserved for the
existing "concurrent epics touching overlapping files" case, which nests
a per-story branch inside the epic's worktree rather than replacing it.

### 3.5 Two smaller consistency gaps

- Nothing stated PM as the sole owner of an AC's _meaning_, so Scrum
  Master's "refine" step had no line it couldn't cross. **Fix**: one-line
  Boundary addition to `agents/sdlc-pm.md`.
- `sdlc-verdict.md`'s missing/stale-input handling was Boundary prose, not
  a numbered Aggregation rule, and its `CRITICAL`-only clause didn't
  mention `BLOCKED` even though `BLOCKED` is part of the same signal
  vocabulary used elsewhere (e.g. `sdlc-coder.md`'s own hand-off). **Fix**:
  promoted missing/stale-input handling into its own numbered clause
  (ordered first), and added `BLOCKED` alongside `CRITICAL` in the
  NOT-READY clause.

### 3.6 `/sdlc-bug-fix` left inconsistent by 3.3's and 3.4's own fixes

**Evidence**: found by the broader second-pass review (§1), not the
original static audit. `agents/sdlc-coder.md`'s Contract Input (3.4's fix)
now unconditionally reads "work and commit on the dedicated
`story-{n.m}-work` branch the dispatching skill creates before you start —
never directly on the base branch." `sdlc-coder.md` is shared by three
skills, but only `/sdlc` and `/sdlc-task` were checked against this new
requirement — `/sdlc-bug-fix`'s Coder dispatch (`references/dispatch.md`
step 2) created no branch at all, so its Coder run had no branch matching
its own contract's expectation, and would have fallen back to committing
on the base branch — reintroducing 3.4's exact bug through a skill the
first pass never touched. Separately, `/sdlc-bug-fix` never dispatched
`sdlc-stress` at all (only `sdlc-reviewer`), so 3.3's worse-of-both-signals
routing had nothing to route on for this entry point — a bug fix's
production resilience was never evaluated. With no Stress dispatch, there
was also no `sdlc-verdict` dispatch and no merge gate — QA/Review clearing
just fell through to the trunk directly.

**Fix**: `/sdlc-bug-fix` gets the same shape as `/sdlc`'s story loop, at
bug-fix scale. A dedicated `bugfix-{slug}-work` branch is created before
the Investigator dispatch (earlier than the story loop's equivalent
branch-creation point, since the Investigator also commits a RED test —
committing that on the base branch would be its own smaller version of the
same problem). `sdlc-reviewer` and `sdlc-stress` now dispatch in parallel,
routed on the worse of the two signals exactly like `/sdlc` step 5d.
`sdlc-verdict` now aggregates `qa.md`/`review.md`/`stress.md` into
`verdict.md`, gating the merge of `bugfix-{slug}-work` into the base
branch — the bug-fix equivalent of Gate 4. `agents/sdlc-tuner.md`'s own
Contract Input and frontmatter description are also updated to name
`sdlc-stress.md` as a valid finding source alongside QA/Review, since
3.3's routing (and now this fix) can send it Stress-originated findings
that Tuner's contract text didn't previously acknowledge.

## 4. Decisions and rationale

| Decision                    | Choice                                                                                  | Why                                                                                                                                                                                                                                                     |
| --------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest shape              | One row per story (not an inner loop over a per-epic row)                               | Architect already reads every story's ID/title from the PRD in full mode — a different projection of existing data, not new invention. Matches `task-manifest.md`'s existing one-row-per-story shape, so `/sdlc-task` and `/sdlc` stay interchangeable. |
| Coder isolation             | Lightweight branch per story (`story-{n.m}-work`), not a full `git worktree`            | Real isolation without a worktree's disk/dependency cost. Worktrees stay reserved for the genuinely concurrent multi-epic case.                                                                                                                         |
| `sdlc-github-issue` trigger | Reworded to "once per story" in `phases.md`, no change to `agents/sdlc-github-issue.md` | The agent already dedups per-story via each story file's own `**GitHub Issue**:` marker line — calling it once per story instead of once per epic is safe by its existing contract.                                                                     |

## 5. Rejected alternatives

- **Keep the per-epic manifest row, fix the loop logic to iterate its
  story list**: rejected — the manifest row would still not carry a single
  story's own PRD excerpt cleanly, and the Depends-on/Status semantics
  would need per-story sub-state bolted onto a per-epic row anyway. A
  one-row-per-story table is a strictly simpler data shape for the same
  information.
- **Rename Gate 4 without changing the commit timing**: rejected — the
  gate's name was already a lie about when the commit happened; renaming
  it without moving the commit fixes nothing.
- **Always use full `git worktree` isolation per story**: rejected — too
  heavy for the common single-epic case; a lightweight branch gives the
  same rework-safety without the added disk/dependency cost.
- **The larger "v2" traceability rewrite** (stable IDs/`derived_from`
  graph, `traceability.yaml`/`run-state.yaml`, `sdlc-trace-reviewer`,
  contract/journey tests): real gaps, but a separate, larger effort not
  attempted in this pass.

## 6. Error handling

No new failure modes introduced. The branch-per-story merge at Gate 4 is
the only new mechanical step with a failure surface (merge conflict on
merge); on any git error the session narration stops and surfaces it to
the human at the gate rather than proceeding — consistent with the
existing "never auto-advance past a `[GATE]`" boundary already in
`SKILL.md`.

## 7. Testing / implementation notes

This plugin has no executable test suite of its own — its `.md` files are
prose contracts consumed by Claude Code, not code that runs. Verification
is static consistency, detailed in the plan doc's own verification
section: greps for stale wording ("before commit", "Review's signal
only", the old manifest shape) returning zero hits repo-wide, plus a
manual re-read of `phases.md`'s step 5 block end-to-end as if dispatching
it by hand for a 2-story epic.

§3.6 was found only because that static-consistency check was widened to
every agent/skill file in the repo, not just the 11 the first pass touched
— cross-reading each shared agent's Contract Input against every skill
that dispatches it, not just the skills already known to be in scope. The
same limit applies: this confirms textual consistency between contracts,
not observed runtime dispatch behavior — there is no way to execute
`/sdlc-bug-fix` end-to-end and watch it branch/merge correctly short of an
actual session.
