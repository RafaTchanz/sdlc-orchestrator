# Pipeline Consistency Fixes — Implementation Plan

**Goal:** Close all 5 findings from a business-validation audit of the whole `/sdlc` orchestrator (gaps, documentation quality, data loss between pipeline steps, flow inconsistencies), each scoped to the smallest change that closes the actual gap. Full audit, problem statements, and rejected alternatives: `docs/superpowers/specs/2026-08-20-pipeline-consistency-fixes-design.md`.

**Architecture:** `qa.md`/`review.md`/`stress.md` gain a `Round` field so round history survives past the in-place overwrite, closing both the Verdict staleness check and the Handoff Metrics gap with the same field. `phases.md`'s Step 8 dispatch now reads and passes `architecture.md`'s Deployment Topology, mirroring the standalone `/sdlc-release` skill's existing pattern, so the trunk actually triggers the IaC half of `sdlc-devops.md`. `phases.md`'s Step 5 gains a multi-repo guard that stops and surfaces the limitation instead of silently executing every story against one repo. `phases.md`'s 5c/5d Tuner routing now inspects the Tuner's hand-off shape before re-dispatching QA/Review, instead of always re-dispatching regardless of escalation. `sdlc-devops.md`'s CI checklist now reads `quality-gate.md`'s command table before writing CI config, instead of promising a coupling with no mechanism behind it.

**Tech Stack:** Markdown agent/skill definition files only (no application code, no test framework) — prose contracts read by Claude Code, not executable modules.

## Global Constraints

- No direct commits on `main`.
- Branch names prefixed `feature/`, `hotfix/`, or `release/`.
- Commit messages must be Conventional Commits.
- No automated test suite exists for these `.md` files — verification is static (grep + manual re-read), per the design doc §6.
- Out of scope: `/sdlc-pr-review`'s dispatch shape (design doc §4); machine-checkable enforcement of the CI/quality-gate coupling (design doc §4); full multi-repo execution plumbing beyond the guard rail (design doc §4).

---

### Task 1: Round field on QA/Review/Stress — `agents/sdlc-qa.md`, `agents/sdlc-reviewer.md`, `agents/sdlc-stress.md`

**Files:** Modify all three.

**Interfaces:** Produces the `Round` field Task 4's Verdict aggregation rule and Task 5's Handoff Procedure both read; consumes the round number Task 6's `phases.md` dispatch prompts state.

- [x] Contract Input: each gains "+ the round number for this dispatch (stated by the caller)".
- [x] Output format template: each gains `### Round: {n}/3`, between the Signal line and Findings.
- [x] Commit: `feat(sdlc-qa,sdlc-reviewer,sdlc-stress): add a Round field so round history survives past the in-place overwrite`.

### Task 2: Verdict's staleness check becomes concrete — `agents/sdlc-verdict.md`

**Files:** Modify `agents/sdlc-verdict.md`.

**Interfaces:** Consumes Task 1's `Round` field and Task 6's expected-round-numbers dispatch clause.

- [x] Contract Input: gains "+ the round number each report is expected to carry (from the caller)".
- [x] Aggregation rule #1: rewritten from an unenforceable "detect staleness" promise to a concrete check — a present report whose own `Round` field doesn't match the round number the caller stated for it is treated identically to a missing report, forcing `NOT READY`.
- [x] Commit: `fix(sdlc-verdict): replace the unenforceable staleness promise with a concrete Round-field match`.

### Task 3: Handoff derives Rounds-used from the Round field — `agents/sdlc-handoff.md`

**Files:** Modify `agents/sdlc-handoff.md`.

**Interfaces:** Consumes Task 1's `Round` field. No new dispatch-prompt data required.

- [x] Procedure step 1: gains a note that `Rounds used` in Metrics is read directly from each touched story's final `qa.md`/`review.md`/`stress.md` `Round` field.
- [x] Commit: `fix(sdlc-handoff): derive Rounds-used metrics from each report's own Round field`.

### Task 4: IaC half of Release actually triggers — `skills/sdlc/references/phases.md` (Step 8)

**Files:** Modify `skills/sdlc/references/phases.md`.

**Interfaces:** Satisfies `agents/sdlc-devops.md`'s existing Contract Input (unchanged) — mirrors `skills/sdlc-release/SKILL.md`'s existing step 2/3 pattern.

- [x] Step 8 gains a line: read `architecture.md`'s Deployment Topology section before the dispatch, if the file exists.
- [x] Dispatch prompt: passes the Deployment Topology excerpt (or explicit "not available" fallback) alongside the release-half context, with an instruction to generate any missing IaC first.
- [x] Commit: `fix(sdlc-phases): pass Deployment Topology to the Step 8 Release dispatch so the IaC half actually triggers`.

### Task 5: Multi-repo guard rail — `skills/sdlc/references/phases.md` (Step 5), `README.md`

**Files:** Modify both.

**Interfaces:** Reads the `Repo` column `agents/sdlc-architect.md` already writes into `epic-manifest.md`.

- [x] Step 5 preamble: before the per-story loop begins, scan all `pending` rows' `Repo` values; if more than one distinct value appears, stop and surface this to the human — a multi-repo epic needs a separate `/sdlc` session per distinct `Repo` value.
- [x] `README.md`'s Global Constraints: one new bullet next to "Workspace isolation" documenting this as a stated limit.
- [x] Commit: `fix(sdlc-phases): stop and surface a mixed-Repo manifest instead of silently executing against one repo`.

### Task 6: Tuner escalation routing — `skills/sdlc/references/phases.md` (5c, 5d)

**Files:** Modify `skills/sdlc/references/phases.md`.

**Interfaces:** Reads `agents/sdlc-tuner.md`'s existing hand-off shape (unchanged) — only the caller's routing changes.

- [x] 5c dispatch prompt: states the round number being requested.
- [x] 5c Tuner-routing bullet: reads the Tuner's hand-off before re-dispatching QA — an escalation-shape hand-off is treated as `MAJOR` directly, falling through to the existing `MAJOR` branch instead of re-dispatching.
- [x] 5d dispatch prompts (Review + Stress): state the round number being requested.
- [x] 5d Tuner-routing bullet: same escalation-shape check before re-running both Review and Stress.
- [x] 5e dispatch prompt: states the expected final round numbers for qa/review/stress, satisfying Task 2's Verdict Contract Input.
- [x] Commit: `fix(sdlc-phases): route Tuner escalations to MAJOR instead of blindly re-dispatching QA/Review`.

### Task 7: CI config mirrors the quality-gate command table — `agents/sdlc-devops.md`

**Files:** Modify `agents/sdlc-devops.md`.

**Interfaces:** Reads `docs/sdlc/quality-gate.md`, an artifact `agents/sdlc-quality-gate.md` already produces (unchanged).

- [x] CI-pipeline-config checklist bullet: gains a line — before writing/updating CI config, read `docs/sdlc/quality-gate.md` if it exists and mirror its actual per-stack command table into the CI config.
- [x] Commit: `fix(sdlc-devops): read and mirror the quality-gate command table before writing CI config`.

### Task 8: Output-format skeleton + new docs

**Files:** Modify `skills/sdlc/references/output-format.md`, `README.md`; create `docs/superpowers/specs/2026-08-20-pipeline-consistency-fixes-design.md`, this plan doc.

**Interfaces:** None — documentation only, no runtime effect.

- [x] `output-format.md`'s `qa.md`/`review.md`/`stress.md` skeleton line: mentions the `Round` field.
- [x] Spec doc: all 5 findings, fixes, and rejected/out-of-scope alternatives.
- [x] This plan doc.
- [x] `README.md`'s "Design history": append two bullets pointing at the new spec + plan, matching the existing entries' pattern.
- [x] Commit: `docs: mark pipeline-consistency-fixes implemented, update design history`.

---

## Verification

1. Re-read `phases.md`'s 5c/5d/5e dispatch prompts against `sdlc-qa.md`/`sdlc-reviewer.md`/`sdlc-stress.md`/`sdlc-verdict.md`'s updated Contract Inputs — confirm every claimed input is actually supplied.
2. Re-read `phases.md`'s Step 8 dispatch against `sdlc-devops.md`'s Contract Input — confirm the IaC half now has what it needs, matching `skills/sdlc-release/SKILL.md`'s existing pattern.
3. `grep -rn "Round:" agents/sdlc-qa.md agents/sdlc-reviewer.md agents/sdlc-stress.md agents/sdlc-verdict.md skills/sdlc/references/phases.md` — confirm the field is threaded consistently end to end.
4. Re-read `phases.md`'s 5c/5d Tuner-routing bullets — confirm the escalation-shape check is present before every re-dispatch, not just described in prose.
5. Re-read the new Step 5 multi-repo guard against `agents/sdlc-architect.md`'s Repo column description — confirm the check reads the same field the Architect actually writes.
