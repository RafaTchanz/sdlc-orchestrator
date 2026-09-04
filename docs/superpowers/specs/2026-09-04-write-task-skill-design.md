# `/sdlc-write-task` — standalone task-writing skill — Design

**Date**: 2026-09-04
**Status**: Approved, not yet implemented.

## 1. Motivation

The full `/sdlc` pipeline already produces a fully-specified story file per unit of work (`docs/sdlc/epics/epic-{n}/stories/story-{n.m}.md`, written by `sdlc-scrum-master`) — but only as one step inside a pipeline that also requires a Brief, a PRD, and a manifest row to already exist. `/sdlc-task` shortens that to a single-task pipeline, but still runs the full Coder→QA→Review→Stress→Verdict loop — it produces working code, not just a well-specified task document.

There is no entry point for "just write the task document — Context, Definition of Ready, Acceptance Criteria, Technical Notes, Definition of Done — without running architecture-light-mode or any implementation." This gap matches the existing standalone-skill pattern (`sdlc-quality-gate`, `sdlc-release`, `sdlc-pr-review`, `sdlc-security-review`, `sdlc-grill-me`, `sdlc-handoff`): one skill, one dedicated agent, usable independently of the full lifecycle.

A second requirement, orthogonal to the entry point itself: whatever writes these documents — the new standalone agent, and the existing `sdlc-scrum-master` — must ground every field in a real source (task description, PRD story, repo inspection, existing architecture/manifest docs) and never invent a plausible-sounding Acceptance Criterion, dependency, or Done-checklist item. Unconfirmable fields become explicit Open Questions instead of silent gaps or fabricated content. This closes a gap in `sdlc-scrum-master`'s current contract too, not just the new agent's.

## 2. Scope

In scope:

- One new agent, `sdlc-task-writer`, and one new skill, `/sdlc-write-task`.
- A new **Definition of Ready (DoR)** section and a new **Open Questions** section, added identically to both `sdlc-task-writer`'s output and `sdlc-scrum-master`'s existing `story-{n.m}.md` output, so the two document shapes stay in lockstep.
- A grounding rule (no invented content; unconfirmable fields become Open Questions) added to both agents' Boundary.
- A lightweight backlog index (`docs/sdlc/tasks/INDEX.md`) so repeated standalone calls in a repo with many existing tasks don't require re-reading every prior task document in full.
- Optional GitHub Issue creation via the existing `sdlc-github-issue` agent, reused as-is.

Out of scope:

- Any change to `/sdlc-task`'s or `/sdlc`'s pipeline behavior beyond the two section additions to `sdlc-scrum-master`.
- Any change to `sdlc-coder`/QA/Review/Stress/Verdict — the new skill never implements anything.
- A machine-checkable linter for the new sections (matches the precedent set in the epic-context design's §4 — content fix now, static checking is a separate follow-up if ever needed).

## 3. Shared contract: grounding + section parity

Both `sdlc-task-writer` (new) and `sdlc-scrum-master` (existing) write a document with exactly these seven sections, in this order:

1. **Title**
2. **Context** — one paragraph: why this exists, what it enables.
3. **Definition of Ready (DoR)** — new section, fixed checklist plus any repo-specific pre-condition the investigation actually surfaced:
   - Scope is unambiguous.
   - Dependencies (other tasks/stories, APIs, data) are identified — each one either already resolved, or explicitly named as a blocker.
   - Any access/data the work needs is confirmed available.
   - Acceptance Criteria are draftable from the input already gathered.
   - Additional items only when the repo investigation (Grep/Glob/Read) turned up a concrete real pre-condition (e.g. "depends on migration X already applied") — never a generic filler item.
4. **Acceptance Criteria** — Given/When/Then; at least one edge/error-path AC.
5. **Technical Notes** — real file paths and contracts, found by inspecting the repo (and, when they exist, `architecture.md`/`PRD.md`/`epic-manifest.md`) — never guessed paths.
6. **Definition of Done (DoD)** — fixed checklist, unchanged from today: tests written first (Red→Green→Refactor) and passing; coverage ≥85% on changed files; no linter/type errors; QA, Review, and Stress all `APPROVE` or better; Verdict `READY`.
7. **Open Questions** — new section. Every field above that could not be grounded in a real source lists its specific gap here, using the field's own wording — never left blank, never filled with a plausible guess.

**Grounding rule** (added to both agents' Boundary, verbatim intent, referencing each agent's own actual input list):

> Every DoR, Acceptance Criteria, Technical Notes, and DoD item must be traceable to a real source: the task description or PRD story given as input, or something actually read from the repo (`Grep`/`Glob`/`Read`) or from `architecture.md`/`epic-manifest.md`/`PRD.md`. Anything that cannot be confirmed against one of those sources is never filled in by inference — it is written as `— (not confirmed, see Open Questions)` in place, with the specific gap named in Open Questions.

This rule does not block document generation (per the resolved question in brainstorming: unconfirmable items become Open Questions, not a hard stop) — the document is always written, with gaps named rather than guessed.

### Changes to `agents/sdlc-scrum-master.md`

- Contract → Boundary: append the grounding rule above.
- Procedure step 2: insert **Definition of Ready (DoR)** between Context and Acceptance Criteria, and **Open Questions** after Definition of Done, using the fixed checklist in §3.
- Hand-off line: append ` Open questions: {N}.` when N > 0 (existing PRD-deviation/needs-re-split appends are unaffected — this is one more optional trailing clause, same pattern already used for those two).

### Changes to `skills/sdlc/references/output-format.md`

- The `story-{n.m}.md` skeleton line gains the two new sections: `Title, Context, Definition of Ready, Acceptance Criteria, Technical Notes, Definition of Done, Open Questions`.

No change to `skills/sdlc/references/phases.md` — the Scrum Master dispatch's inputs are unchanged; only its output shape gains two sections it already has the source material to fill (or explicitly flag as ungrounded).

## 4. New agent: `sdlc-task-writer`

Persona name: **Mulher-Maravilha — Task Writer** (next unused Marvel/DC-hero-style name in the roster; picked for "truth" framing — a fitting hook for a grounding-first contract).

```markdown
---
name: sdlc-task-writer
description: Writes one fully-specified, grounded task document (Context/DoR/Acceptance Criteria/Technical Notes/DoD/Open Questions) from a free-form task description, for use outside the full /sdlc or /sdlc-task pipeline. Dispatched only by the /sdlc-write-task skill via Agent(subagent_type: "sdlc-task-writer") — never invoked directly.
model: sonnet
tools: Read, Write, Grep, Glob, Bash
---
```

**Contract**

- **Input**: a free-form task description (the dispatching skill asks the user if not given). No PRD/manifest row required.
- **Output**: exactly one file, `docs/sdlc/tasks/task-{slug}.md` (`{slug}` derived from the title, kebab-case), plus an update to `docs/sdlc/tasks/INDEX.md`.
- **Boundary**: the grounding rule from §3, verbatim. Additionally: if the task appears to overlap or conflict in scope with an existing entry in `INDEX.md` (or an existing story in `epic-manifest.md`, when that file exists), never decide unilaterally to merge/split/skip — write the document as asked, and flag the possible overlap by name in the hand-off line for a human to resolve. Never implements code. Never invents an Acceptance Criterion, dependency, or DoD item beyond what the task description, repo inspection, or existing docs actually support.

**Procedure**

1. Read the task description.
2. If `docs/sdlc/tasks/INDEX.md` exists, read it in full (it is intentionally kept small — one line per task: `ID | Title | one-line summary | Status | Depends-on`).
3. If anything in the index suggests overlap or a dependency with the new task, open that specific `docs/sdlc/tasks/task-{id}.md` with `Read` — never open every file in the directory, only the one(s) the index flagged.
4. If `docs/sdlc/architecture.md` exists, read it — it may state Tech Stack Decisions or Component Boundaries the new task must respect (or explicitly flag conflict with, in Open Questions — never silently contradict).
5. If `docs/sdlc/epic-manifest.md` or `docs/sdlc/PRD.md` exist, read them — the task may fit better as a story under an existing epic; if so, say so in the hand-off rather than deciding to file it there yourself.
6. Inspect the actual target repo with `Grep`/`Glob`/`Bash` for real file paths and existing contracts relevant to Technical Notes.
7. Assign the next task ID: `{max existing ID in INDEX.md} + 1`, or `1` if `INDEX.md` doesn't exist yet.
8. Write `docs/sdlc/tasks/task-{slug}.md` with the seven sections from §3, applying the grounding rule throughout.
9. Create `docs/sdlc/tasks/INDEX.md` if it doesn't exist (header row + this one entry), or append one row to it if it does: `{ID} | {Title} | {one-line summary} | pending | {Depends-on, or —}`.
10. Hand off: `"Task written: docs/sdlc/tasks/task-{slug}.md (task {ID})."` — append ` Possible overlap with task-{id}/story-{n.m}: {why}.` if step 3 or 5 surfaced one, and ` Open questions: {N}.` if N > 0.

## 5. New skill: `/sdlc-write-task`

```markdown
---
name: sdlc-write-task
description: Writes one fully-specified, grounded task document (Context/DoR/Acceptance Criteria/Technical Notes/DoD/Open Questions) — no pipeline, no implementation. Use when the user wants a well-documented task/ticket written without running /sdlc-task's full Coder/QA/Review/Stress loop. Fully self-contained — no runtime dependency on any other installed plugin.
---
```

**Contract**

- **Input**: a free-form task description — ask if not provided.
- **Output**: `docs/sdlc/tasks/task-{slug}.md` plus `docs/sdlc/tasks/INDEX.md`; optionally, one GitHub Issue.
- **Boundary**: writes documentation only — never dispatches `sdlc-coder` or any QA/Review/Stress/Verdict agent. Never creates a GitHub Issue without explicit user confirmation.

**Steps**

1. Collect the task description from the user if not already given.
2. Dispatch:

   ```
   Agent(subagent_type: "sdlc-task-writer", prompt: "Task: {description}. Write the task document per your contract.")
   ```

3. Report the returned hand-off line verbatim. If it flags a possible overlap or open questions, surface those directly rather than only pointing at the file.
4. Ask the user: open a GitHub Issue for this task now? If yes, ask for every input `sdlc-github-issue`'s own contract actually requires — target repo (`owner/repo`), the Project board (`owner` + number), `tribo`, `squad` — plus the optional `project_name`. `sdlc-github-issue`'s contract has no fallback path for a missing board/tribo/squad (board resolution and field-setting are load-bearing steps in its Procedure, not best-effort like `project_name`), so don't offer a "just the repo" shortcut — collect all four required values or don't dispatch it.
5. If confirmed, dispatch `sdlc-github-issue` reusing its existing contract, passing this task's own ID in place of an epic number:

   ```
   Agent(subagent_type: "sdlc-github-issue", prompt: "Story directory: docs/sdlc/tasks/ (single file: task-{slug}.md). Epic number: {task ID} (standalone task, not a true epic — the resulting 'Epic' custom field will read 'Epic {task ID}'; tell the user this upfront). Target repo: {repo}. Board: {owner}/{number}. Tribo: {tribo}. Squad: {squad}. Project: {project_name, if given}. Create the issue per your contract.")
   ```

   `sdlc-github-issue`'s existing dedup rule (skip any story/task file that already has a `**GitHub Issue**:` line) applies unchanged — safe to call again later against the same `docs/sdlc/tasks/` directory as new task files are added.

6. Report `sdlc-github-issue`'s hand-off line verbatim.

**Done when**: `task-{slug}.md` and `INDEX.md` exist, and — if the user opted in — the GitHub Issue is created and linked in the task file.

## 6. Rejected alternatives

- **Reuse `sdlc-scrum-master` in a "standalone mode" instead of a new agent**: rejected in brainstorming — `sdlc-scrum-master`'s contract is already anchored to a manifest row + Epic Summary + PRD story; overloading it with a second, manifest-free input shape would blur one-agent-one-job, the pattern every other agent in this roster follows. A dedicated agent keeps `sdlc-scrum-master` unchanged in structure (only the two shared sections are added) and lets `sdlc-task-writer` own the repo-wide backlog-index concern that `sdlc-scrum-master` never needs (it always has exactly one row as input).
- **Store standalone tasks under `docs/sdlc/epics/epic-0/stories/` to reuse the existing story path convention**: rejected — these tasks are explicitly outside any epic; forcing them into the epic directory shape would misrepresent that and complicate `sdlc-github-issue`'s existing epic-numbered dispatch assumptions. A parallel `docs/sdlc/tasks/` directory keeps the two concerns visibly separate.
- **Full re-read of every existing task file on each new call, no index**: rejected per the brainstorming decision — doesn't scale token-wise as the backlog grows, and the lightweight `INDEX.md` (one line per task) gives the same overlap-detection signal at a fraction of the read cost, with full detail loaded on demand only when the index flags a real candidate.
- **Hard-block document generation when a field can't be grounded**: rejected per the brainstorming decision — the document is always produced; gaps are named as Open Questions instead of stopping the flow, consistent with how `sdlc-architect` already treats its own Open Questions (never a blocker to writing `architecture.md`, always surfaced for the human gate).

## 7. Error handling

- Missing `docs/sdlc/tasks/` directory on first call: created implicitly by `Write`.
- Malformed or hand-edited `INDEX.md` (e.g. a row that doesn't parse): treat as if the index doesn't exist for ID-assignment purposes — assign ID `1` — but still attempt to append the new row in the existing format; never fail the whole task-write over an unparseable index.
- `sdlc-github-issue` failure (network, `gh` auth, etc.): its own contract already logs a non-fatal warning and continues; the skill reports that warning to the user rather than treating it as a failure of the whole `/sdlc-write-task` call — the task document itself is already written and valid regardless of Issue-creation outcome.

## 8. Testing / implementation notes

No executable test suite (Markdown contracts, not code). Verification is static re-reading, matching precedent from prior specs in this repo:

1. Re-read `sdlc-task-writer.md`'s Procedure against `sdlc-scrum-master.md`'s updated Procedure — confirm the seven sections and grounding rule are worded consistently (not necessarily identically, since their input shapes differ), so a reader who's seen one document shape recognizes the other.
2. Confirm `skills/sdlc/references/output-format.md`'s `story-{n.m}.md` line and the new skill's own contract both list the same seven section names in the same order.
3. Confirm `sdlc-write-task/SKILL.md`'s GitHub-issue dispatch prompt supplies every input `sdlc-github-issue.md`'s Contract → Input actually requires (repo, board, tribo, squad — only `project_name` is genuinely optional there) — no silent fallback for a missing required value.
4. `grep -rn "docs/sdlc/tasks/"` after implementation — confirm every reference (skill, agent, README) points at the same path shape.
5. Update `README.md`'s "Standalone skills" list and Layout section to include `/sdlc-write-task` and the new agent, following the existing entries' format.
