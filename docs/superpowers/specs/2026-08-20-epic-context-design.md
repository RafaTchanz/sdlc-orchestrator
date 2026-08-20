# Epic-level Context — Design

**Date**: 2026-08-20
**Status**: Implemented (`agents/sdlc-pm.md`, `agents/sdlc-architect.md`, `agents/sdlc-scrum-master.md`, `skills/sdlc/references/output-format.md`, `skills/sdlc/references/phases.md`, `README.md`) — see `docs/superpowers/plans/2026-08-20-epic-context.md`.

## 1. Motivation

Following the P0 orchestrator fixes (`docs/superpowers/plans/2026-08-17-p0-orchestrator-fixes.md`, merged) and the separate mechanical contract-consistency pass (`a92c28f`, static-checker-driven: stale wording, missing branch clauses, cross-references), this pass ran a _semantic_ audit of every artifact `/sdlc` produces, against five questions any planning artifact should answer for a reader who has nothing else open:

1. **What** is this describing?
2. **Why** does it exist?
3. What are its **limits/boundaries**?
4. What **decisions** were made, and why (rationale, alternatives)?
5. How do you know you're **done**?

## 2. Audit

| Artifact                            | What                                 | Why                                | Limits                                                               | Decisions                                                                 | Done                                                                                   | Verdict                                                  |
| ----------------------------------- | ------------------------------------ | ---------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `product-brief.md`                  | Problem Statement                    | Problem Statement                  | Scope, Constraints                                                   | Competitive/Existing-Solution Scan                                        | Success Metrics                                                                        | 5/5                                                      |
| `PRD.md`                            | Functional Requirements (Epic/Story) | Overview                           | Goals/Non-goals                                                      | Priority (MoSCoW) per story                                               | Release Criteria                                                                       | 4/5 — no epic-level "why" beyond the story list (see §3) |
| `architecture.md`                   | Component/Service Boundaries         | Context & Constraints              | Component/Service Boundaries                                         | Tech Stack Decision (choice + rationale + rejected alternative, required) | Definition of Done is per-story, not stated here — inherited from PRD Release Criteria | 4/5                                                      |
| **`epic-manifest.md`**              | Story table                          | —                                  | —                                                                    | —                                                                         | "every row `done`" (implicit, never written)                                           | **0/5 — the gap**                                        |
| `task-manifest.md`                  | Technical Approach note + single row | Technical Approach note            | Technical Approach note (implicitly, single task)                    | Technical Approach note                                                   | Story's own Definition of Done (once written)                                          | 3/5 — acceptable; see §4 for why this is out of scope    |
| `story-{n.m}.md`                    | Title                                | Context                            | Acceptance Criteria (bounds what's required)                         | Technical Notes (architecture excerpts + concrete paths)                  | Definition of Done                                                                     | 5/5                                                      |
| `qa.md` / `review.md` / `stress.md` | Findings                             | Findings rationale                 | Findings scope (`file:line` evidence required)                       | Signal + rationale                                                        | Signal itself (`APPROVE`+)                                                             | 5/5                                                      |
| `verdict.md`                        | Aggregate verdict                    | Rationale citing specific findings | Aggregation rule (worst-of, `CRITICAL`/`BLOCKED` forces `NOT READY`) | Aggregation rule                                                          | Verdict (READY/READY WITH NOTES/NOT READY)                                             | 5/5                                                      |
| `security-review.md`                | Severity-tagged findings             | Findings (`file:line`)             | `CRITICAL` always blocks, no exceptions                              | OWASP coverage tables (what was checked, what wasn't)                     | Overall pass/fail by severity                                                          | 5/5                                                      |
| `quality-gate.md`                   | Per-gate PASS/FAIL                   | Per-gate rationale (tool output)   | "gate can't run → FAIL with a note, never skipped"                   | Per-gate table                                                            | Overall verdict line                                                                   | 5/5                                                      |
| `pr-review.md`                      | PR title/body                        | PR body (context for reviewers)    | Never merges, never opens without confirmation                       | Action taken                                                              | PR opened/comments posted                                                              | 5/5                                                      |
| `release.md`                        | Added/Fixed/Breaking                 | Changelog                          | No live-infra access (IaC files + tag only)                          | Version-bump rationale                                                    | Tag/publish completed                                                                  | 5/5                                                      |

13 of 14 artifacts already satisfy at least 3 of the 5 questions, because each already has a section built for it. The one exception is `epic-manifest.md`: a pure routing table (`Epic | Story | Title | Tier | Repo | Language/Stack | Depends-on | Status`, prior to this fix) with no narrative field at all. Nothing in the pipeline stated _why_ an epic exists, what it's bounded to, which architectural decisions govern it, or what "this epic is done" means beyond "every row below it says `done`" — true, but never written down anywhere a reader could find without reconstructing it from the PRD + `architecture.md` + the row-by-row `Status` column.

This is a narrow, specific gap, not a systemic pattern: Epic is the one layer that sits between the product-wide PRD narrative and the individually self-contained story, and no agent currently owns writing its what/why/limits/decisions as its own unit. The PM writes Epics as a grouping label for Stories, not as a thing with its own stated purpose; the Architect turns that grouping into manifest rows without adding narrative either.

## 3. Fix

`agents/sdlc-pm.md` — the PRD's Functional Requirements section gains one field per Epic, written before that epic's Stories list: **Epic Goal** — one sentence stating why the epic exists as a unit and what capability it delivers as a whole, distinct from any single story's `Description` (which is that one story's user-facing slice). Boundary addition, same shape as the existing AC-ownership line: the PM is the sole author of an Epic Goal's _meaning_ — the Architect may add technical framing when carrying it into the manifest, but any change to what the epic is meant to deliver must come back through the PM.

`agents/sdlc-architect.md` — `epic-manifest.md`'s full-mode Procedure step 4 gains a short **Epic Summary** block written once per epic, directly above that epic's story rows (the row shape itself is unchanged from the P0 fix's one-row-per-story flattening):

- **Goal** — carried from the PRD's Epic Goal, technical framing allowed, meaning not.
- **Boundaries** — what this epic explicitly excludes: a pointer plus a one-line excerpt from `architecture.md`'s own Component/Service Boundaries section relevant to this epic.
- **Key decisions** — a pointer plus an inline statement of the specific Tech Stack Decision entries that govern this epic, not just a "see Tech Stack Decision" link.
- **Definition of Done** — epic-level completion criteria beyond the sum of its stories, if any (e.g. a cross-story/E2E behavior); otherwise state explicitly "every story below reaches `Status: done`, with no cross-story criteria beyond that."

Per-story columns drop the `Epic` column — now redundant with the header, since `Story` IDs already carry the epic number as their leading digit (`1.1`, `1.2`). Confirmed clean before making this change: nothing downstream reads a manifest row's `Epic` column value — every `epic-{n}` file-path reference in `phases.md`/`SKILL.md` (e.g. `docs/sdlc/epics/epic-{n}/stories/story-{n.m}.md`) derives `{n}` from the story ID's own leading digit, never from a per-row `Epic` field.

`agents/sdlc-scrum-master.md` — Contract Input gains this epic's Epic Summary block (read straight out of `epic-manifest.md`, alongside the row already read), so the Context section it writes can ground "why this story exists" in the epic's stated Goal instead of re-deriving it from the PRD alone. No change to the story file's own section list — Context already asks for "why this story exists, what it enables"; this gives it a real source instead of requiring the Scrum Master to infer epic-level intent from scattered story descriptions.

`skills/sdlc/references/output-format.md` — the `epic-manifest.md` skeleton line now mentions the per-epic header block above the table (`task-manifest.md`'s line is unchanged).

`skills/sdlc/references/phases.md` — 5a's Scrum Master dispatch prompt gains one clause: pass this story's containing Epic Summary excerpt alongside the manifest row and PRD story excerpt it already passes.

## 4. Rejected alternatives

- **Also add an Epic-style header to `task-manifest.md`**: rejected. A `/sdlc-task` session is a single task/single story by construction, and light mode already has a 2-3 sentence Technical Approach note above its one row, and the Scrum Master's resulting story file is already fully self-contained (Context + Definition of Done). Adding an Epic-style header to a manifest with exactly one row would restate the Technical Approach note under a new label, not close a real gap.
- **Give the epic a dedicated file (`docs/sdlc/epics/epic-{n}/epic.md`) instead of a header block in `epic-manifest.md`**: rejected. The manifest is already the one place a reader looks for "what epics exist and their status" — splitting the narrative into per-epic files would mean cross-referencing two locations for something that fits in a few lines, and would need its own dispatch/hand-off wiring for no proportionate benefit.
- **Machine-checkable enforcement now** (extend `scripts/check_contracts.py` to flag a manifest epic-header missing a `Goal:` line): deferred — this pass is a content/contract fix; a static checker for it is a natural follow-up, not a blocker for this one.

## 5. Error handling

No new failure modes. The Epic Summary block is prose written once per epic by the Architect, consumed read-only by the Scrum Master; a missing or thin Epic Summary (e.g. an Architect run that predates this fix) degrades to the Scrum Master's prior behavior — infer from the PRD's Functional Requirements and story descriptions — never a hard failure.

## 6. Testing / implementation notes

No executable test suite (Markdown contracts, not code). Verification is static re-reading:

1. Re-read `sdlc-pm.md`'s new Epic Goal field against `sdlc-architect.md`'s Epic Summary block — confirmed the Architect's `Goal` line has a concrete source to carry from, not an invented one.
2. Re-read `phases.md`'s 5a dispatch prompt against `sdlc-scrum-master.md`'s updated Contract Input — the dispatch supplies everything the contract now claims as input.
3. `grep -rn "Epic | Story\|Epic.*Story.*Tier" agents/ skills/` — no stale copy of the old manifest shape (with an `Epic` row column) survives anywhere; the only remaining "Epic/Task ... Story ... Tier" text describes `task-manifest.md`'s intentionally unchanged single-row shape.
4. Confirmed no downstream file-path or dispatch logic reads a manifest row's `Epic` column value directly — every `epic-{n}` reference derives `{n}` from the story ID's leading digit — before dropping that column from the per-story table.
