# Epic-level Context — Implementation Plan

**Goal:** Close the one gap found by a semantic what/why/limits/decisions/done audit of every artifact `/sdlc` produces — `epic-manifest.md` was a pure routing table with no narrative field, so nothing in the pipeline stated why an epic exists, what it's bounded to, which decisions govern it, or what "done" means at the epic level. Full audit table, problem statement, and rejected alternatives: `docs/superpowers/specs/2026-08-20-epic-context-design.md`.

**Architecture:** The PM's PRD gains a one-sentence **Epic Goal** per epic. The Architect carries that Goal, plus a Boundaries/Key-decisions/Definition-of-Done narrative it derives from `architecture.md`'s own sections, into a new **Epic Summary** block written once per epic in `epic-manifest.md`, directly above that epic's story rows — the row shape itself stays one-row-per-story (P0 fix), just drops the now-redundant `Epic` column. The Scrum Master reads that Epic Summary alongside the row it already reads, so a story's Context section can ground "why this exists" in the epic's stated Goal instead of re-deriving it from scattered story descriptions.

**Tech Stack:** Markdown agent/skill definition files only (no application code, no test framework) — prose contracts read by Claude Code, not executable modules.

## Global Constraints

- No direct commits on `main`.
- Branch names prefixed `feature/`, `hotfix/`, or `release/`.
- Commit messages must be Conventional Commits.
- No automated test suite exists for these `.md` files — verification is static (grep + manual re-read), per the design doc §6.
- Out of scope: `task-manifest.md`/light mode (design doc §4); any change to per-story artifacts, audit reports, or verdict/gate files (audit confirmed those already satisfy the bar); a machine-checkable version of this audit (design doc §4).

---

### Task 1: PM writes an Epic Goal — `agents/sdlc-pm.md`

**Files:** Modify `agents/sdlc-pm.md`.

**Interfaces:** Produces the Epic Goal sentence Task 2's Architect carries into `epic-manifest.md`'s Epic Summary block.

- [x] Procedure step 2's Functional Requirements bullet: each epic opens with a **Goal** — one sentence, why the epic exists as a unit and what capability it delivers as a whole, distinct from any single story's `Description`.
- [x] Boundary: PM is the sole author of an Epic Goal's meaning — the Architect may add technical framing when carrying it into the manifest, but any change to what the epic is meant to deliver comes back through the PM.
- [x] Commit: `docs(sdlc-pm): PM authors an Epic Goal per epic in the PRD`.

### Task 2: Architect writes the Epic Summary block — `agents/sdlc-architect.md`

**Files:** Modify `agents/sdlc-architect.md`.

**Interfaces:** Consumes Task 1's Epic Goal. Produces the Epic Summary block Task 3's Scrum Master reads and Task 5's dispatch prompt passes along.

- [x] Full-mode Procedure step 4: `epic-manifest.md` becomes one **Epic Summary** block per epic (Goal/Boundaries/Key decisions/Definition of Done) followed by that epic's one-row-per-story table.
- [x] Per-story table columns drop `Epic` (redundant with the header — the epic number is already the leading digit of every `Story` ID).
- [x] Light-mode Procedure step 2 (`task-manifest.md`): explicitly states no Epic Summary block — a task-manifest session is always exactly one task.
- [x] Commit: `feat(sdlc-architect): write a per-epic Epic Summary block above each epic's story table`.

### Task 3: Scrum Master grounds Context in the Epic Summary — `agents/sdlc-scrum-master.md`

**Files:** Modify `agents/sdlc-scrum-master.md`.

**Interfaces:** Consumes Task 2's Epic Summary block. Its new Input line is the contract Task 5's `phases.md` 5a dispatch prompt must satisfy.

- [x] Contract Input: manifest row + that row's containing Epic Summary block (full mode only) + PRD story entry + architecture.md.
- [x] Procedure step 1: read the Epic Summary block (full mode) alongside the row.
- [x] Procedure step 2's Context bullet: ground "why this story exists" in the Epic Summary's Goal where one exists, instead of re-deriving epic-level intent from scattered story descriptions.
- [x] Commit: `feat(sdlc-scrum-master): ground story Context in the epic's Goal`.

### Task 4: Output-format skeleton — `skills/sdlc/references/output-format.md`

**Files:** Modify `skills/sdlc/references/output-format.md`.

**Interfaces:** None — pure documentation of Task 2's schema.

- [x] `epic-manifest.md` skeleton line: mentions the per-epic Epic Summary header block above the table; `task-manifest.md`'s line stays unchanged (no header block).
- [x] Commit: `docs(sdlc-output-format): document the epic-manifest Epic Summary block`.

### Task 5: Dispatch prompt carries the Epic Summary — `skills/sdlc/references/phases.md`

**Files:** Modify `skills/sdlc/references/phases.md`.

**Interfaces:** Satisfies Task 3's new Scrum Master Contract Input.

- [x] 5a dispatch prompt: pass this story's containing Epic Summary excerpt alongside the manifest row and PRD story excerpt already passed (full-mode only, omitted in light mode — same pattern as the existing PRD-excerpt clause).
- [x] Commit: `fix(sdlc-phases): pass the Epic Summary excerpt to the Scrum Master dispatch`.

### Task 6: New docs + README pointer

**Files:** Create `docs/superpowers/specs/2026-08-20-epic-context-design.md`, create this plan doc, modify `README.md`.

**Interfaces:** None — documentation only, no runtime effect.

- [x] Spec doc: the audit table (all 14 artifacts), the gap, the fix, and why `task-manifest.md` is explicitly left out of scope.
- [x] This plan doc.
- [x] `README.md`'s "Design history": append two bullets pointing at the new spec + plan, matching the existing entries' pattern.
- [x] Commit: `docs: mark epic-context implemented, update design history`.

---

## Verification

1. Re-read `sdlc-pm.md`'s new Epic Goal field against `sdlc-architect.md`'s Epic Summary block — the Architect's `Goal` line has a concrete source to carry from, not an invented one.
2. Re-read `phases.md`'s 5a dispatch prompt against `sdlc-scrum-master.md`'s updated Contract Input — the dispatch prompt supplies everything the contract now claims as input.
3. `grep -rn "Epic | Story\|Epic.*Story.*Tier" agents/ skills/` — must return nothing except `task-manifest.md`'s intentionally unchanged single-row shape.
4. Confirmed before dropping the `Epic` column: no downstream file-path or dispatch logic reads a manifest row's `Epic` column value directly — every `epic-{n}` reference in `phases.md`/`SKILL.md` derives `{n}` from the story ID's own leading digit.
