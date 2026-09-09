# Pipeline Consistency Fixes — Design

**Date**: 2026-08-20
**Status**: Implemented (`agents/sdlc-qa.md`, `agents/sdlc-reviewer.md`, `agents/sdlc-stress.md`, `agents/sdlc-verdict.md`, `agents/sdlc-handoff.md`, `agents/sdlc-devops.md`, `skills/sdlc/references/phases.md`, `skills/sdlc/references/output-format.md`, `README.md`) — see `docs/superpowers/plans/2026-08-20-pipeline-consistency-fixes.md`.

## 1. Motivation

A business-validation audit of the whole `/sdlc` orchestrator — looking for gaps, documentation quality issues, data loss between pipeline steps, and flow inconsistencies, distinct from the prior semantic what/why/limits/decisions/done audit (`docs/superpowers/specs/2026-08-20-epic-context-design.md`) — found 5 substantive findings, each confirmed against exact current file text before being scoped. The user authorized fixing all of them.

## 2. Findings

### Finding 1 — QA/Review/Stress round history is unrecoverable

`qa.md`/`review.md`/`stress.md` are overwritten in place at the same path every round, with no round number in their output templates. Round counters lived only in the orchestrating skill's own ephemeral session context (`phases.md`'s Step 5 preamble) — never written to a file. Two downstream consequences: `sdlc-verdict.md`'s Aggregation rule #1 promised to detect "stale (carryover from a prior round)" inputs with no mechanism to do so; `sdlc-handoff.md`'s Metrics template required `Rounds used: QA {a}/3, Review {b}/3` with nothing in the files it reads carrying that number once round history is overwritten in place.

### Finding 2 — Release dispatch never triggers the IaC half of `sdlc-devops.md`

`sdlc-devops.md`'s Contract Input is two halves sharing one agent: IaC generation (needs `architecture.md`'s Deployment Topology) and release/versioning (needs release branch state). The standalone `/sdlc-release` skill correctly reads and passes the Deployment Topology excerpt before dispatching (`skills/sdlc-release/SKILL.md` step 2). The trunk's `phases.md` Step 8 dispatch passed only "Release half: current release branch state" — Deployment Topology was never supplied, so the IaC half was never actually triggered in the full `/sdlc` pipeline, only in the standalone skill.

### Finding 3 — `epic-manifest.md`'s per-row `Repo` column is silently unused by execution

The manifest schema supports a distinct `Repo` (owner/repo) value per story row for multi-repo epics (`agents/sdlc-architect.md`, `output-format.md`). But every execution dispatch after story-file generation (5b Coder squad, 5c QA, 5d Review+Stress, Step 6 Security+Quality-Gate, Step 7 PR, Step 8 Release) operates on "current branch" with no repo parameter — only the optional `sdlc-github-issue.md` side-channel reads `Repo` at all. A multi-repo epic would silently execute every story against whichever repo the session happens to be checked out in, regardless of what each row's `Repo` column says.

### Finding 4 — Tuner's escalation hand-off is never checked before re-dispatching QA/Review

`sdlc-tuner.md` returns one of two hand-off shapes: a normal fix confirmation, or an escalation ("...reclassifying MAJOR, not applying as a Tuner fix.") when a finding needs full Coder-squad scope. `phases.md`'s 5c and 5d routing dispatched the Tuner then unconditionally re-dispatched QA (5c) or Review+Stress (5d) on the next line, regardless of which shape came back — so an escalated finding got re-audited against unchanged code instead of being routed to the Coder squad.

### Finding 5 — CI config vs. quality-gate command table is a documented, unenforced coupling

`sdlc-devops.md`'s IaC checklist stated CI config "must never drift" from `sdlc-quality-gate.md`'s per-stack gate command table, but nothing made Devops actually read that table when generating CI config — a prose promise with no mechanism, same disposition as the already-deferred 85%-coverage duplication between `sdlc-qa.md` and `sdlc-quality-gate.md`.

## 3. Fix

**Finding 1**: `agents/sdlc-qa.md`, `agents/sdlc-reviewer.md`, `agents/sdlc-stress.md` each gain a `### Round: {n}/3` field in their output templates and a Contract Input note that the round number is stated by the caller. `phases.md`'s 5c/5d dispatch prompts now state the round number being requested (`"Round {n} of 3."`); 5e's Verdict dispatch states the expected final round numbers for each of qa/review/stress. `sdlc-verdict.md`'s Aggregation rule #1 changes from an unenforceable "detect staleness" promise to a concrete check: a present report whose own `Round` field doesn't match the round number the caller stated is treated identically to a missing report, forcing `NOT READY`. `sdlc-handoff.md`'s Procedure gains a line stating `Rounds used` in Metrics is read directly from each touched story's final report's `Round` field — no new dispatch-prompt data needed for Handoff.

**Finding 2**: `phases.md`'s Step 8 now reads `architecture.md`'s Deployment Topology section before the dispatch (mirroring `skills/sdlc-release/SKILL.md`'s step 2 exactly) and passes the excerpt in the prompt alongside the release-half context, with an explicit instruction to generate any missing IaC first.

**Finding 3 (guard rail, not full multi-repo plumbing)**: `phases.md`'s Step 5 gains a check before the per-story loop begins: scan all `pending` rows' `Repo` values; if more than one distinct value appears, stop and surface this to the human — execution dispatches from 5b through Step 8 operate on a single checked-out repo per session, so a multi-repo epic needs a separate `/sdlc` session per distinct `Repo` value. `README.md`'s Global Constraints gains a matching bullet next to "Workspace isolation" documenting this as a stated limit.

**Finding 4**: `phases.md`'s 5c and 5d Tuner-routing bullets now read the Tuner's hand-off before re-dispatching: if it reports the escalation shape, this round's outcome is treated as `MAJOR` directly and falls through to the existing `MAJOR` branch instead of re-dispatching QA/Review. No change to `sdlc-tuner.md` itself — its hand-off already carried the information; only the caller's routing was ignoring it.

**Finding 5**: `agents/sdlc-devops.md`'s CI-pipeline-config checklist bullet gains one line: before writing/updating CI config, read `docs/sdlc/quality-gate.md` if it exists and mirror its actual per-stack command table into the CI config, rather than independently deriving one.

## 4. Rejected / out-of-scope alternatives

- **`/sdlc-pr-review`'s dispatch omitting security-review.md/quality-gate.md status**: not fixed — standalone mode is intentionally for ad-hoc PR review outside the full gated pipeline, unlike the trunk's Step 7. Not a bug in this pass.
- **Machine-checkable enforcement of Finding 5's coupling** (e.g. a static checker diffing the two command tables): deferred — same "documented, needs enforcement, deferred" disposition as the pre-existing coverage-threshold duplication between `sdlc-qa.md` and `sdlc-quality-gate.md`. A natural follow-up, not part of this pass.
- **Full multi-repo execution plumbing** (per-story repo switching, worktrees per repo) for Finding 3: rejected for this pass. The guard rail makes the limit explicit and unmissable; building real multi-repo execution is unscoped work nothing has asked for yet.

## 5. Error handling

No new failure modes introduced. Finding 1's Round-field check degrades safely: a report missing a Round field (e.g. written by a pre-fix agent run) is treated as stale, same as a missing report — never an implicit pass. Finding 3's guard is a stop-and-surface check, not a silent skip — a single-repo session (the common case) never triggers it. Finding 2's Deployment Topology read follows the same "not available" fallback already used by `skills/sdlc-release/SKILL.md`.

## 6. Testing / implementation notes

No executable test suite (Markdown contracts, not code). Verification is static re-reading:

1. Re-read `phases.md`'s 5c/5d/5e dispatch prompts against `sdlc-qa.md`/`sdlc-reviewer.md`/`sdlc-stress.md`/`sdlc-verdict.md`'s updated Contract Inputs — confirmed every claimed input is actually supplied.
2. Re-read `phases.md`'s Step 8 dispatch against `sdlc-devops.md`'s Contract Input — confirmed the IaC half now has what it needs, matching `skills/sdlc-release/SKILL.md`'s existing pattern.
3. `grep -rn "Round:" agents/sdlc-qa.md agents/sdlc-reviewer.md agents/sdlc-stress.md agents/sdlc-verdict.md skills/sdlc/references/phases.md` — confirms the field is threaded consistently end to end.
4. Re-read `phases.md`'s 5c/5d Tuner-routing bullets — confirmed the escalation-shape check is present before every re-dispatch, not just described in prose.
5. Re-read the new Step 5 multi-repo guard against `agents/sdlc-architect.md`'s Repo column description — confirmed the check reads the same field the Architect actually writes.
