# `/sdlc-write-task` Standalone Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone entry point, `/sdlc-write-task`, that writes one fully-specified, grounded task document (Context/DoR/Acceptance Criteria/Technical Notes/DoD/Open Questions) without running `/sdlc-task`'s full Coder→QA→Review→Stress→Verdict loop — and bring `sdlc-scrum-master`'s existing `story-{n.m}.md` output into lockstep with the same two new sections (Definition of Ready, Open Questions) and the same no-invention grounding rule. Full rationale, audit, and rejected alternatives: `docs/superpowers/specs/2026-09-04-write-task-skill-design.md`.

**Architecture:** One new agent, `sdlc-task-writer`, dispatched only by one new skill, `skills/sdlc-write-task/SKILL.md` — matching the existing standalone-skill pattern (`sdlc-quality-gate`, `sdlc-release`, etc.: one skill, one dedicated agent, no pipeline dependency). The new agent reads a free-form task description plus (when they exist) a lightweight `docs/sdlc/tasks/INDEX.md` backlog index, `architecture.md`, `epic-manifest.md`/`PRD.md`, and the target repo itself, then writes `docs/sdlc/tasks/task-{slug}.md` and updates the index. In parallel, `agents/sdlc-scrum-master.md` gains the same Definition of Ready + Open Questions sections and the same grounding rule, so both document shapes stay identical in structure. The skill optionally hands off to the existing `sdlc-github-issue` agent, unchanged, for Issue creation.

**Tech Stack:** Markdown agent/skill definition files only (no application code, no test framework) — prose contracts read by Claude Code, not executable modules.

**Spec:** `docs/superpowers/specs/2026-09-04-write-task-skill-design.md`

## Global Constraints

- No direct commits on `main`.
- Branch names prefixed `feature/`, `hotfix/`, or `release/`.
- Commit messages must be Conventional Commits.
- No automated test suite exists for these `.md` files — verification is static (grep + manual re-read), per the design doc §8.
- Every DoR/Acceptance-Criteria/Technical-Notes/DoD item in both document shapes must be traceable to a real source (task description/PRD story, or something actually read via `Grep`/`Glob`/`Read`, or `architecture.md`/`epic-manifest.md`/`PRD.md`) — anything unconfirmable is written as `— (not confirmed, see Open Questions)` and named in Open Questions, never invented (design doc §3).
- Out of scope: any change to `/sdlc-task`'s or `/sdlc`'s pipeline behavior beyond the two section additions to `sdlc-scrum-master`; any change to `sdlc-coder`/QA/Review/Stress/Verdict; a machine-checkable linter for the new sections (design doc §2).
- `sdlc-github-issue`'s contract requires repo, board (`owner`+number), `tribo`, and `squad` as load-bearing inputs — only `project_name` is optional. The new skill must collect all four required values before dispatching it, never a "just the repo" shortcut (design doc §5, §8).

---

### Task 1: Add Definition of Ready + Open Questions to `sdlc-scrum-master.md`

**Files:** Modify `agents/sdlc-scrum-master.md`.

**Interfaces:** Produces the seven-section story shape (`Title, Context, Definition of Ready, Acceptance Criteria, Technical Notes, Definition of Done, Open Questions`) that Task 5's `output-format.md` documents and that Task 2's `sdlc-task-writer` must match in structure.

- [ ] Contract → Boundary: append the grounding rule — every DoR/AC/Technical-Notes/DoD item must be traceable to the manifest row, Epic Summary, PRD story, `architecture.md`, or something actually read from the repo; anything unconfirmable is written as `— (not confirmed, see Open Questions)` in place, never inferred.
- [ ] Procedure step 2: insert a new bullet between the existing **Context** and **Acceptance Criteria** bullets:
  ```
  - **Definition of Ready (DoR)** — fixed checklist: scope is unambiguous; dependencies (other stories, APIs, data) are identified — each one either already resolved or explicitly named as a blocker; any access/data the work needs is confirmed available; Acceptance Criteria are draftable from the manifest row/PRD story already read. Add an item only when the architecture.md/repo investigation surfaced a concrete real pre-condition (e.g. "depends on migration X already applied") — never a generic filler item.
  ```
- [ ] Procedure step 2: insert a new bullet after the existing **Definition of Done** bullet:
  ```
  - **Open Questions** — every DoR/AC/Technical-Notes/DoD item above that could not be grounded in the manifest row, Epic Summary, PRD story, architecture.md, or the repo itself. List the specific gap using that item's own wording. Empty is fine — never pad this section with a question you can actually answer from what you already read.
  ```
- [ ] Procedure step 4 (hand-off line): append ` Open questions: {N}.` when N > 0, after the existing PRD-deviation/needs-re-split appends (same trailing-clause pattern already used for those two).
- [ ] Commit: `feat(sdlc-scrum-master): add Definition of Ready and Open Questions, ground story fields`.

### Task 2: Create the `sdlc-task-writer` agent

**Files:** Create `agents/sdlc-task-writer.md`.

**Interfaces:** Consumes: a free-form task description (from the dispatching skill's prompt). Produces: `docs/sdlc/tasks/task-{slug}.md` (seven sections, same names/order as Task 1's `sdlc-scrum-master` output) and `docs/sdlc/tasks/INDEX.md` (columns: `ID | Title | Summary | Status | Depends-on`). Hand-off line format Task 3's skill must relay verbatim: `"Task written: docs/sdlc/tasks/task-{slug}.md (task {ID})."` with optional trailing ` Possible overlap with task-{id}/story-{n.m}: {why}.` and/or ` Open questions: {N}.` clauses.

- [ ] Write the frontmatter:
  ```yaml
  ---
  name: sdlc-task-writer
  description: Writes one fully-specified, grounded task document (Context/DoR/Acceptance Criteria/Technical Notes/DoD/Open Questions) from a free-form task description, for use outside the full /sdlc or /sdlc-task pipeline. Dispatched only by the /sdlc-write-task skill via Agent(subagent_type: "sdlc-task-writer") — never invoked directly.
  model: sonnet
  tools: Read, Write, Grep, Glob, Bash
  ---
  ```
- [ ] Write a one-line persona intro (next unused hero name in the roster — `Mulher-Maravilha — Task Writer`, per the spec's "truth"/grounding framing), matching the tone of the existing agent files (e.g. `agents/sdlc-scrum-master.md`'s opening line).
- [ ] Write the **Contract** section:
  - **Input**: a free-form task description (the dispatching skill asks the user if not given). No PRD/manifest row required.
  - **Output**: exactly one file, `docs/sdlc/tasks/task-{slug}.md` (`{slug}` derived from the title, kebab-case), plus an update to `docs/sdlc/tasks/INDEX.md`.
  - **Boundary**: every DoR/AC/Technical-Notes/DoD item must be traceable to the task description, or something actually read from the repo (`Grep`/`Glob`/`Read`) or from `architecture.md`/`epic-manifest.md`/`PRD.md` when those exist; anything unconfirmable is written as `— (not confirmed, see Open Questions)` in place, never inferred. If the task appears to overlap or conflict in scope with an existing `INDEX.md` entry or an existing `epic-manifest.md` story, never decide unilaterally to merge/split/skip — write the document as asked and flag the possible overlap by name in the hand-off line. Never implements code. Never invents an Acceptance Criterion, dependency, or DoD item beyond what the task description, repo inspection, or existing docs actually support.
- [ ] Write the **Procedure** section, numbered exactly as follows:
  1. Read the task description.
  2. If `docs/sdlc/tasks/INDEX.md` exists, read it in full.
  3. If anything in the index suggests overlap or a dependency with the new task, open that specific `docs/sdlc/tasks/task-{id}.md` with `Read` — never open every file in the directory, only the one(s) the index flagged.
  4. If `docs/sdlc/architecture.md` exists, read it — it may state Tech Stack Decisions or Component Boundaries the new task must respect (or explicitly flag conflict with, in Open Questions — never silently contradict).
  5. If `docs/sdlc/epic-manifest.md` or `docs/sdlc/PRD.md` exist, read them — the task may fit better as a story under an existing epic; if so, say so in the hand-off rather than deciding to file it there yourself.
  6. Inspect the actual target repo with `Grep`/`Glob`/`Bash` for real file paths and existing contracts relevant to Technical Notes.
  7. Assign the next task ID: `{max existing ID in INDEX.md} + 1`, or `1` if `INDEX.md` doesn't exist yet or a row fails to parse (treat a malformed/hand-edited index as absent for ID-assignment purposes only — still attempt to append the new row in the existing format in step 9, never fail the whole task-write over an unparseable index).
  8. Write `docs/sdlc/tasks/task-{slug}.md` with exactly these seven sections:
     - **Title**
     - **Context** — one paragraph: why this exists, what it enables.
     - **Definition of Ready (DoR)** — fixed checklist: scope is unambiguous; dependencies (other tasks, APIs, data) are identified — each one either already resolved or explicitly named as a blocker; any access/data the work needs is confirmed available; Acceptance Criteria are draftable from the task description already read. Add an item only when the repo/architecture.md investigation surfaced a concrete real pre-condition (e.g. "depends on migration X already applied") — never a generic filler item.
     - **Acceptance Criteria** — Given/When/Then, at least one edge/error-path AC.
     - **Technical Notes** — real file paths/contracts found in step 6.
     - **Definition of Done (DoD)** — fixed checklist: tests written first (Red→Green→Refactor) and passing; coverage ≥85% on changed files; no linter/type errors; QA, Review, and Stress all `APPROVE` or better; Verdict `READY`.
     - **Open Questions** — every item above that couldn't be grounded, using that item's own wording. Empty is fine — never pad this section with a question you can actually answer from what you already read.
  9. Create `docs/sdlc/tasks/INDEX.md` if it doesn't exist (header row `| ID | Title | Summary | Status | Depends-on |` plus this one entry), or append one row to it if it does: `{ID} | {Title} | {one-line summary} | pending | {Depends-on, or —}`.
  10. Hand off: `"Task written: docs/sdlc/tasks/task-{slug}.md (task {ID})."` — append ` Possible overlap with task-{id}/story-{n.m}: {why}.` if step 3 or 5 surfaced one, and ` Open questions: {N}.` if N > 0.
- [ ] Commit: `feat(sdlc-task-writer): add standalone grounded task-writing agent`.

### Task 3: Create the `/sdlc-write-task` skill

**Files:** Create `skills/sdlc-write-task/SKILL.md`.

**Interfaces:** Consumes: Task 2's `sdlc-task-writer` hand-off line format, and the existing `agents/sdlc-github-issue.md` contract (Input: story directory, epic number, target repo, board owner+number, tribo, squad, optional project_name). Produces: nothing new downstream — this is a leaf entry point.

- [ ] Write the frontmatter:
  ```yaml
  ---
  name: sdlc-write-task
  description: Writes one fully-specified, grounded task document (Context/DoR/Acceptance Criteria/Technical Notes/DoD/Open Questions) — no pipeline, no implementation. Use when the user wants a well-documented task/ticket written without running /sdlc-task's full Coder/QA/Review/Stress loop. Fully self-contained — no runtime dependency on any other installed plugin.
  ---
  ```
- [ ] Write the **Contract** section:
  - **Input**: a free-form task description — ask if not provided.
  - **Output**: `docs/sdlc/tasks/task-{slug}.md` plus `docs/sdlc/tasks/INDEX.md`; optionally, one GitHub Issue.
  - **Boundary**: writes documentation only — never dispatches `sdlc-coder` or any QA/Review/Stress/Verdict agent. Never creates a GitHub Issue without explicit user confirmation.
- [ ] Write the **Steps** section:
  1. Collect the task description from the user if not already given.
  2. Dispatch:
     ```
     Agent(subagent_type: "sdlc-task-writer", prompt: "Task: {description}. Write the task document per your contract.")
     ```
  3. Report the returned hand-off line verbatim. If it flags a possible overlap or open questions, surface those directly rather than only pointing at the file.
  4. Ask the user: open a GitHub Issue for this task now? If yes, ask for every input `sdlc-github-issue`'s own contract actually requires — target repo (`owner/repo`), the Project board (`owner` + number), `tribo`, `squad` — plus the optional `project_name`. Collect all four required values or don't dispatch it — `sdlc-github-issue` has no fallback for a missing board/tribo/squad.
  5. If confirmed, dispatch `sdlc-github-issue` reusing its existing contract, passing this task's own ID in place of an epic number:
     ```
     Agent(subagent_type: "sdlc-github-issue", prompt: "Story directory: docs/sdlc/tasks/ (single file: task-{slug}.md). Epic number: {task ID} (standalone task, not a true epic — the resulting 'Epic' custom field will read 'Epic {task ID}'; tell the user this upfront). Target repo: {repo}. Board: {owner}/{number}. Tribo: {tribo}. Squad: {squad}. Project: {project_name, if given}. Create the issue per your contract.")
     ```
     `sdlc-github-issue`'s existing dedup rule (skip any file that already has a `**GitHub Issue**:` line) applies unchanged.
  6. Report `sdlc-github-issue`'s hand-off line verbatim. If it reports a non-fatal warning (network/`gh`-auth/board-resolution failure — its own contract already logs these and continues), relay that warning to the user as a partial-success note, not as a failure of the whole `/sdlc-write-task` call — the task document from step 2 is already written and valid regardless of Issue-creation outcome.
- [ ] Write the "**Done when**" line: `docs/sdlc/tasks/task-{slug}.md` and `INDEX.md` exist, and — if the user opted in — the GitHub Issue is created and linked in the task file.
- [ ] Commit: `feat(sdlc-write-task): add standalone task-writing skill`.

### Task 4: Verify `sdlc-github-issue` compatibility with a non-epic dispatch

**Files:** Read-only check against `agents/sdlc-github-issue.md` — no modification expected.

**Interfaces:** None — this is a verification task confirming Task 3's dispatch prompt is compatible with the existing agent's actual Procedure, not a code change.

- [ ] Re-read `agents/sdlc-github-issue.md`'s Procedure steps 1-3 against Task 3's dispatch prompt: confirm step 1 (`Glob .../epic-{n}/stories/story-*.md`) is satisfied by pointing it at `docs/sdlc/tasks/` with the single `task-{slug}.md` file instead — if the Glob pattern is hardcoded to the `epics/epic-{n}/stories/` path shape and cannot resolve a `docs/sdlc/tasks/task-{slug}.md` file, note this as a blocking finding rather than silently assuming compatibility.
- [ ] If the Glob pattern is hardcoded and incompatible: add one narrow adjustment to `agents/sdlc-github-issue.md` step 1 — accept either the existing `docs/sdlc/epics/epic-{n}/stories/story-*.md` glob or an explicitly-passed single file path, without altering any other step (title/body building, `gh issue create`, board field-setting all already operate per-file and are agnostic to the source directory).
- [ ] If no change needed: state so explicitly in the commit message body (this task always produces a commit — either the fix or a documented no-op confirmation) so the verification is traceable in history.
- [ ] Commit: `fix(sdlc-github-issue): accept a single explicit story/task file path` (or `docs(sdlc-github-issue): confirm single-file dispatch compatibility, no change needed` if step 1 already Globs correctly for a lone file).

### Task 5: Document the new section shape — `skills/sdlc/references/output-format.md`

**Files:** Modify `skills/sdlc/references/output-format.md`.

**Interfaces:** None — pure documentation of Task 1 and Task 2's schema.

- [ ] The `story-{n.m}.md` skeleton line: update section list to `Title, Context, Definition of Ready, Acceptance Criteria, Technical Notes, Definition of Done, Open Questions` (adding the two new sections to the existing line, same "Full spec: ..." pointer format).
- [ ] Add one new skeleton line for `task-{slug}.md` (new artifact from Task 2), same format as the existing lines: `Title, Context, Definition of Ready, Acceptance Criteria, Technical Notes, Definition of Done, Open Questions` — full spec pointer to `sdlc-task-writer.md`. Also mention `docs/sdlc/tasks/INDEX.md`'s column shape (`ID | Title | Summary | Status | Depends-on`) in the same line or an adjacent one.
- [ ] Commit: `docs(sdlc-output-format): document task-writer's task/INDEX schema and the story DoR/Open-Questions sections`.

### Task 6: README + plugin metadata updates

**Files:** Modify `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`.

**Interfaces:** None — documentation/metadata only, no runtime effect.

- [ ] `README.md` "Standalone skills" list (currently 6 bullets, `/sdlc-security-review` through `/sdlc-handoff`): append a 7th bullet in the same one-line-per-skill format: ``- `/sdlc-write-task` — writes one grounded task document (Context/DoR/AC/Technical Notes/DoD/Open Questions) without running the full task pipeline; optional GitHub Issue creation.``
- [ ] `README.md` "Layout" code block: bump the skill count from 9 to 10 and list `sdlc-write-task` alongside the existing skill names.
- [ ] `README.md` responsibility matrix table: add `sdlc-task-writer` to the "Decide / plan" row (alongside `sdlc-pm`, `sdlc-architect`, `sdlc-scrum-master`) — it plans/specifies, same category as the Scrum Master it mirrors.
- [ ] `README.md` opening paragraph and top-level plugin description text: bump "20 single-purpose agent personas" to "21", "9 skills" to "10".
- [ ] `README.md` "Design history": append two bullets pointing at `docs/superpowers/specs/2026-09-04-write-task-skill-design.md` and this plan doc, matching the existing entries' pattern (spec bullet first, plan bullet second, one-line description each).
- [ ] `.claude-plugin/plugin.json`: bump `"description"` from `"20-agent SDLC pipeline..."` to `"21-agent SDLC pipeline..."`, appending `write-task` to the standalone-skills list in that same description string (`...standalone security-review/quality-gate/pr-review/release/grill-me/handoff/write-task skills...`).
- [ ] `.claude-plugin/marketplace.json`: it is currently stale independent of this change (its top-level `"description"` reads `"an 19-agent SDLC pipeline..."` — pre-existing drift from `plugin.json`'s `"20-agent"`, not caused by this plan). While touching this file, correct both counts to `21-agent` in one pass: the top-level `"description"` (`"Marketplace for the sdlc-orchestrator plugin — an 19-agent SDLC pipeline for Claude Code."` → `"a 21-agent SDLC pipeline..."`, also fixing the `an`/`a` article) and the nested `plugins[0].description` (currently `"19-agent SDLC pipeline..."` → `"21-agent..."`, plus the same standalone-skills-list append as `plugin.json`).
- [ ] Commit: `docs: register /sdlc-write-task in README and plugin metadata, bump agent/skill counts`.

---

## Verification

1. Re-read `agents/sdlc-task-writer.md`'s Procedure against `agents/sdlc-scrum-master.md`'s updated Procedure — confirm the seven sections and grounding rule are worded consistently (not necessarily identically, since their input shapes differ), so a reader who's seen one document shape recognizes the other.
2. Confirm `skills/sdlc/references/output-format.md`'s `story-{n.m}.md` and `task-{slug}.md` lines both list the same seven section names in the same order.
3. Confirm `skills/sdlc-write-task/SKILL.md`'s GitHub-issue dispatch prompt supplies every input `agents/sdlc-github-issue.md`'s Contract → Input actually requires (repo, board, tribo, squad — only `project_name` is genuinely optional there) — no silent fallback for a missing required value.
4. `grep -rn "docs/sdlc/tasks/"` across `agents/` and `skills/` — confirm every reference points at the same path shape (`docs/sdlc/tasks/task-{slug}.md`, `docs/sdlc/tasks/INDEX.md`).
5. `grep -rn "20-agent\|20 single-purpose\|9 skills" README.md .claude-plugin/` — confirm no stale count survives after Task 6.
6. Confirm Task 4's finding (Glob-compatible or patched) is reflected consistently between `agents/sdlc-github-issue.md`'s actual step 1 and `skills/sdlc-write-task/SKILL.md`'s dispatch-prompt comment about the story directory.
