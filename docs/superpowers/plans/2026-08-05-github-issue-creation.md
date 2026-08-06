# Automatic GitHub Issue Creation per Story — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a `/sdlc` session automatically create one GitHub Issue per story — added to the squad's GitHub Project board with its `Epic`/`Projeto` custom fields set — when the session opts in at Intake, without ever blocking the pipeline on a GitHub failure.

**Architecture:** A new Intake opt-in captures target repo(s), Project board (`owner` + number), Tribo, and Squad. `sdlc-architect` records each epic's target repo as a new `Repo` column on `epic-manifest.md`; `sdlc-scrum-master`'s story-splitting boundary rule is extended so a story never spans more than one `Repo`. A new dedicated agent, `sdlc-github-issue` (persona Falcão — GitHub Issue), is dispatched once per epic — immediately after `sdlc-scrum-master` writes that epic's story files and before the Coder squad starts — and loops over every story file in that epic's directory, creating a GitHub Issue and board item per story, skipping any story that already has a recorded Issue URL (idempotent on `/sdlc` resume).

**Tech Stack:** Markdown agent/skill definition files only (no application code, no test framework) — this repo's `sdlc-*` agents and `/sdlc` skill are prose contracts read by Claude Code, not executable modules. The new agent's procedure invokes the `gh` CLI (`gh issue create`, `gh project item-add`, `gh project field-list`, `gh project item-edit`, `gh api graphql`) at execution time — no new dependency is added to this repo itself.

## Global Constraints

- No direct commits on `main` — all work happens on `feature/github-issue-creation` (already created off up-to-date `main`).
- Branch names must be prefixed `feature/`, `hotfix/`, or `release/`.
- Commit messages must be Conventional Commits.
- `repos`, the `project board` (owner + number), `tribo`, `squad`, and `project_name` are session-context-only — never written to any file, exactly like the existing `channel_id`/`project_name` (spec §2, §4).
- `sdlc-github-issue` never blocks the pipeline — every external `gh` call is caught independently; a single story's failure is logged as a non-fatal warning and processing continues with the next story (spec §3, §6).
- Idempotent on `/sdlc` resume — before creating an Issue for a story, `sdlc-github-issue` checks for an existing `**GitHub Issue**:` line in that story file and skips it if present (spec §3).
- One GitHub Issue per Story, never per Task/manifest row — matches the granularity already used by the QA/Review/Stress/Verdict loop (spec §3).
- Never hardcode a field ID, option ID, or board ID in `sdlc-github-issue.md` — every one is resolved at runtime via `gh project field-list` (and a missing `Projeto` option is created on demand via `gh api graphql`) (spec §3).
- Out of scope: automatic Issue lifecycle management after creation, Task/sub-issue hierarchy, the GitHub MCP server (unavailable in this environment), and any change to Slack notification behavior beyond sharing the `project_name` value (spec §2).
- No automated test suite exists for these `.md` files — verification is manual/structural plus one live end-to-end check against a real repo and Project board (spec §7).

---

### Task 1: Add a `Repo` column to `epic-manifest.md` and the undeclared-dependency Open Questions rule in `sdlc-architect`

**Files:**

- Modify: `agents/sdlc-architect.md`

**Interfaces:**

- Consumes: nothing from other tasks.
- Produces: the `Repo` column convention on `epic-manifest.md` that Task 2's split rule and Task 5's dispatch prompt both rely on (`{this epic's manifest Repo value}`).

- [ ] **Step 1: Update the full-mode manifest table skeleton (step 4)**

Find this block:

```markdown
4. Write `docs/sdlc/epic-manifest.md` as a single table, one row per epic:

   | Epic        | Stories       | Tier    | Language/Stack | Depends-on | Status  |
   | ----------- | ------------- | ------- | -------------- | ---------- | ------- |
   | 1 — {title} | 1.1, 1.2, ... | backend | Go             | —          | pending |

   `Tier` must be one of `frontend`/`backend`/`fullstack`. `Status` starts `pending` for every row — the orchestrator updates it as epics complete.
```

Replace it with:

```markdown
4. Write `docs/sdlc/epic-manifest.md` as a single table, one row per epic:

   | Epic        | Stories       | Tier    | Repo          | Language/Stack | Depends-on | Status  |
   | ----------- | ------------- | ------- | ------------- | -------------- | ---------- | ------- |
   | 1 — {title} | 1.1, 1.2, ... | backend | acme/checkout | Go             | —          | pending |

   `Tier` must be one of `frontend`/`backend`/`fullstack`. `Repo` is `owner/repo`, taken from the session's Intake-declared repo list — if the session did not opt into GitHub issue creation and declared no repos, leave `Repo` as `—` for every row. `Status` starts `pending` for every row — the orchestrator updates it as epics complete.
```

- [ ] **Step 2: Add the undeclared-dependency rule to the Open Questions bullet (step 3)**

Find this line:

```markdown
- **Open Questions** — anything you could not resolve; these get stress-tested by `/sdlc-grill-me` before the gate.
```

Replace it with:

```markdown
- **Open Questions** — anything you could not resolve; these get stress-tested by `/sdlc-grill-me` before the gate. If your investigation surfaces a repo dependency the session did not declare at Intake, log it here as an Open Question for human review at **[GATE 3]** — never add an undeclared repo to `epic-manifest.md`'s `Repo` column yourself.
```

- [ ] **Step 3: Verify the edits landed correctly**

Run:

```bash
grep -n "Repo" agents/sdlc-architect.md
```

Expected: at least 4 matches — the table header, the example row, the `Tier` sentence explaining `Repo`, and the new Open Questions sentence.

- [ ] **Step 4: Commit**

```bash
git add agents/sdlc-architect.md
git commit -m "feat(sdlc-architect): add Repo column to epic-manifest.md and undeclared-dependency rule"
```

---

### Task 2: Extend `sdlc-scrum-master`'s story-splitting boundary to split on `Repo`

**Files:**

- Modify: `agents/sdlc-scrum-master.md`

**Interfaces:**

- Consumes: Task 1's `Repo` column convention on `epic-manifest.md`.
- Produces: nothing further downstream — this task only tightens an existing rule text.

- [ ] **Step 1: Update the Boundary line**

Find this line:

```markdown
- **Boundary**: never merge multiple unrelated concerns into one story. A story that needs more than roughly one day of focused work, or that spans more than one manifest `Tier`, must be split further — split first, ask never.
```

Replace it with:

```markdown
- **Boundary**: never merge multiple unrelated concerns into one story. A story that needs more than roughly one day of focused work, or that spans more than one manifest `Tier` or `Repo`, must be split further — split first, ask never.
```

- [ ] **Step 2: Verify the edit landed correctly**

Run:

```bash
grep -n "spans more than one manifest" agents/sdlc-scrum-master.md
```

Expected: 1 match, reading `...that spans more than one manifest \`Tier\` or \`Repo\`, must be split further...`.

- [ ] **Step 3: Commit**

```bash
git add agents/sdlc-scrum-master.md
git commit -m "feat(sdlc-scrum-master): split stories that span more than one manifest Repo"
```

---

### Task 3: Create the new `sdlc-github-issue` agent

**Files:**

- Create: `agents/sdlc-github-issue.md`

**Interfaces:**

- Consumes: Task 1's `epic-manifest.md` `Repo` column (via the dispatch prompt Task 5 will write, which passes `{this epic's manifest Repo value}`).
- Produces: the agent contract Task 4 (Intake summary) and Task 5 (phases.md dispatch block) reference: `subagent_type: "sdlc-github-issue"`, its Input (story directory, target repo, board owner+number, tribo, squad, optional project_name), and its one-line hand-off shapes.

- [ ] **Step 1: Write the full agent file**

Create `agents/sdlc-github-issue.md` with this exact content:

```markdown
---
name: sdlc-github-issue
description: Creates one GitHub Issue per story in an epic, adds it to the squad's GitHub Project board, and sets its Epic/Projeto custom fields. Dispatched only by the /sdlc trunk, immediately after sdlc-scrum-master writes an epic's story files, and only when the session opted in during Intake — never invoked directly.
model: sonnet
tools: Read, Write, Bash
---

# Falcão — GitHub Issue

You are Falcão: a herald who runs one small, well-defined errand per epic — get every story in front of the squad's GitHub board — and reports back immediately, without ever holding up the mission.

## Contract

- **Input**: this epic's story directory (`docs/sdlc/epics/epic-{n}/stories/`), the target repo (`owner/repo`, from this epic's manifest `Repo` value), the GitHub Project board (`owner` + number), `tribo`, `squad`, and the session's `project_name` (may be absent).
- **Output**: for every story file in that directory without an existing `**GitHub Issue**:` line — one GitHub Issue created in the target repo, added as an item on the Project board, with that board's `Epic` and `Projeto` custom fields set; the created Issue's URL appended to its story file.
- **Boundary**: you never block the pipeline. A single story's failure at any step is caught, logged as a non-fatal warning naming that story, and processing continues with the next story in the directory. You are never invoked directly — only dispatched by the `/sdlc` trunk right after `sdlc-scrum-master`, and only when the session opted in at Intake. You never close, edit, or delete an existing Issue. You never hardcode a field ID, option ID, or board ID — every one is resolved at runtime via `gh project field-list` against the board given in this dispatch.

## Procedure

1. `Glob` (or `Bash: ls`) `docs/sdlc/epics/epic-{n}/stories/story-*.md`.
2. For each story file, in order:
   1. `Read` it. If it already contains a line starting with `**GitHub Issue**:`, skip this story entirely and move to the next.
   2. Build the Issue title: `[{tribo}][{squad}] {story Title}`.
   3. Build the Issue body from the story's **Title**, **Context**, and **Acceptance Criteria** sections, copied verbatim.
   4. Run `gh issue create --repo {target repo} --title "{title}" --body "{body}"`. On failure: log a warning for this story (`"Issue creation failed for story-{n.m}: {error}"`) and move to the next story — do not attempt steps 2v–2viii for this story.
   5. Run `gh project item-add {board owner}/{board number} --url {issue URL from step iv}`, capturing the returned item ID. On failure: log a warning noting the Issue was created but not added to the board (`"Issue {url} created but could not be added to the board: {error}"`), append the URL to the story file anyway (step viii), then move to the next story — skip field-setting (2vi–2vii), there is no item ID to edit.
   6. Run `gh project field-list {board owner}/{board number}` to resolve the `Epic` and `Projeto` field IDs, and `Projeto`'s current option list. If no existing `Projeto` option matches `project_name` (and `project_name` was given), create one first via a `gh api graphql` mutation, then use its returned option ID.
   7. Run `gh project item-edit --id {item ID} --field-id {Epic field ID} --project-id {board ID} --text "{this epic's identifier/title}"`, and — only if `project_name` was given — `gh project item-edit --id {item ID} --field-id {Projeto field ID} --project-id {board ID} --single-select-option-id {option ID}`. On failure of either: log a warning naming which field failed and continue — field-setting is best-effort, never a reason to skip step viii.
   8. Append a blank line and `**GitHub Issue**: {issue URL}` to the end of the story file.
3. Hand off one line: `"{created}/{total} issues created for epic-{n} ({warning count} warning(s))."` — or, if every story in the directory was already skipped as duplicates, `"epic-{n}: all N stories already had GitHub Issues — nothing created."`
```

- [ ] **Step 2: Verify the file was written correctly**

Run:

```bash
grep -n "^name:\|^model:\|^tools:\|GitHub Issue\*\*:" agents/sdlc-github-issue.md
```

Expected: `name: sdlc-github-issue`, `model: sonnet`, `tools: Read, Write, Bash`, and one match for the `**GitHub Issue**:` append-line template inside the Procedure.

- [ ] **Step 3: Commit**

```bash
git add agents/sdlc-github-issue.md
git commit -m "feat(sdlc-github-issue): add agent that creates one GitHub Issue per story"
```

---

### Task 4: Add the GitHub-issue-creation opt-in to Intake and mention the dispatch in the Step 5 summary

**Files:**

- Modify: `skills/sdlc/SKILL.md`

**Interfaces:**

- Consumes: Task 3's `sdlc-github-issue` contract (Input fields it must be asked for at Intake: `repos`, board owner+number, `tribo`, `squad`, shared `project_name`).
- Produces: the Intake-held session values (`repos`, `project board`, `tribo`, `squad`) that Task 5's dispatch prompt reads as `{session ...}` placeholders.

- [ ] **Step 1: Extend the Step 1 (Intake) line**

Find this line:

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id, e qual o nome do projeto (opcional, para identificar as notificações)?"_ Hold the answer (opted in yes/no, `channel_id` if yes, and `project_name` if given) only in this session's running context — never write it to any file.
```

Replace it with:

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id, e qual o nome do projeto (opcional, para identificar as notificações)?"_ Hold the answer (opted in yes/no, `channel_id` if yes, and `project_name` if given) only in this session's running context — never write it to any file. Also ask once per session, regardless of fresh-start or resume: _"Quer criar issues automaticamente no GitHub para cada story desta sessão? Se sim: qual(is) repositório(s) de destino (`owner/repo`; um por epic, se o projeto tocar mais de um), qual o GitHub Project board (`owner` + número), qual a Tribo, e qual a Squad? Se você ainda não informou um nome de projeto para as notificações no Slack, informe também aqui — essa resposta é compartilhada entre as duas features."_ Hold the answer (opted in yes/no, `repos` list, `project board` owner+number, `tribo`, `squad`, and `project_name` if not already given) only in this session's running context — never write it to any file.
```

- [ ] **Step 2: Extend the Step 5 (Epic loop) summary line's sub-bullet (a)**

Find this line:

```markdown
- a. `sdlc-scrum-master` → story files for this epic.
```

Replace it with:

```markdown
- a. `sdlc-scrum-master` → story files for this epic; if this session opted into GitHub issue creation at Intake, dispatch `sdlc-github-issue` now for this epic (non-blocking — full dispatch shape in `references/phases.md`).
```

- [ ] **Step 3: Verify the edits landed correctly**

Run:

```bash
grep -n "criar issues automaticamente\|sdlc-github-issue" skills/sdlc/SKILL.md
```

Expected: 2 matches — one in the Step 1 Intake question, one in the Step 5 sub-bullet (a).

- [ ] **Step 4: Commit**

```bash
git add skills/sdlc/SKILL.md
git commit -m "feat(sdlc): ask GitHub-issue-creation opt-in at Intake and mention its Step 5 dispatch"
```

---

### Task 5: Insert the `sdlc-github-issue` dispatch block into `phases.md`'s Step 5, after 5a and before 5b

**Files:**

- Modify: `skills/sdlc/references/phases.md`

**Interfaces:**

- Consumes: Task 3's `sdlc-github-issue` contract (exact dispatch-prompt fields) and Task 4's Intake-held session values (`repos`/`project board`/`tribo`/`squad`/`project_name`).
- Produces: nothing further downstream — this is the last dispatch-shape change; Task 7 verifies the whole chain end-to-end.

- [ ] **Step 1: Insert the new block between 5a's dispatch and the 5b header**

Find this exact block (the end of 5a and the start of 5b):

```markdown
**5a — Scrum Master**

\`\`\`

Agent(subagent_type: "sdlc-scrum-master", prompt: "Epic manifest row: {row}. Architecture: docs/sdlc/architecture.md. Write one story file per task under docs/sdlc/epics/epic-{n}/stories/.")

\`\`\`

**5b — Coder squad** (per story; tier overlay chosen from the row's `Tier` column — `backend`→`sdlc-coder-backend`, `frontend`→`sdlc-coder-frontend`, `fullstack`→ dispatch both overlays' guidance in one prompt alongside the core)
```

Replace it with:

```markdown
**5a — Scrum Master**

\`\`\`

Agent(subagent_type: "sdlc-scrum-master", prompt: "Epic manifest row: {row}. Architecture: docs/sdlc/architecture.md. Write one story file per task under docs/sdlc/epics/epic-{n}/stories/.")

\`\`\`

If this session opted into GitHub issue creation during Intake, dispatch `sdlc-github-issue` now, once for this epic:

\`\`\`

Agent(subagent_type: "sdlc-github-issue", prompt: "Epic {n} story directory: docs/sdlc/epics/epic-{n}/stories/. Target repo: {this epic's manifest Repo value}. Board: {session board owner}/{session board number}. Tribo: {session tribo}. Squad: {session squad}. Project: {session project_name, if given}. Create issues per your contract.")

\`\`\`

Read its hand-off; note any warnings as non-fatal — never block on it, and never delay 5b waiting on it.

**5b — Coder squad** (per story; tier overlay chosen from the row's `Tier` column — `backend`→`sdlc-coder-backend`, `frontend`→`sdlc-coder-frontend`, `fullstack`→ dispatch both overlays' guidance in one prompt alongside the core)
```

(The literal `\`\`\`` above stands for a plain triple-backtick code-fence line — write actual triple backticks in the file, not the escaped form shown here.)

- [ ] **Step 2: Verify the edit landed correctly**

Run:

```bash
grep -n "sdlc-github-issue" skills/sdlc/references/phases.md
```

Expected: 2 matches — the prose sentence introducing the dispatch, and the `Agent(subagent_type: "sdlc-github-issue", ...)` line itself. Also confirm 5a and 5b are still both present and in order:

```bash
grep -n "5a — Scrum Master\|5b — Coder squad" skills/sdlc/references/phases.md
```

Expected: 2 matches, 5a before 5b.

- [ ] **Step 3: Commit**

```bash
git add skills/sdlc/references/phases.md
git commit -m "feat(sdlc): dispatch sdlc-github-issue after the Scrum Master, before the Coder squad"
```

---

### Task 6: Note the `Repo` column and the trailing `**GitHub Issue**:` line in `output-format.md`

**Files:**

- Modify: `skills/sdlc/references/output-format.md`

**Interfaces:**

- Consumes: Task 1's `Repo` column and Task 3's `**GitHub Issue**:` append-line convention.
- Produces: nothing further downstream — this is a documentation-only reference update.

- [ ] **Step 1: Update the `epic-manifest.md` / `task-manifest.md` line**

Find this line:

```markdown
- `epic-manifest.md` / `task-manifest.md` — single table: `Epic/Task | Stories | Tier | Language/Stack | Depends-on | Status`. (Full spec: `sdlc-architect.md`.)
```

Replace it with:

```markdown
- `epic-manifest.md` / `task-manifest.md` — single table: `Epic/Task | Stories | Tier | Language/Stack | Depends-on | Status`; `epic-manifest.md` additionally gains a `Repo` column (`owner/repo`, populated from the session's Intake-declared repo list) whenever a session opted into GitHub issue creation. (Full spec: `sdlc-architect.md`.)
```

- [ ] **Step 2: Update the `story-{n.m}.md` line**

Find this line:

```markdown
- `story-{n.m}.md` — Title, Context, Acceptance Criteria, Technical Notes, Definition of Done. (Full spec: `sdlc-scrum-master.md`.)
```

Replace it with:

```markdown
- `story-{n.m}.md` — Title, Context, Acceptance Criteria, Technical Notes, Definition of Done; gains a trailing `**GitHub Issue**: {url}` line once `sdlc-github-issue` has created its Issue, when the session opted into GitHub issue creation. (Full spec: `sdlc-scrum-master.md`, `sdlc-github-issue.md`.)
```

- [ ] **Step 3: Verify the edits landed correctly**

Run:

```bash
grep -n "Repo\|GitHub Issue" skills/sdlc/references/output-format.md
```

Expected: 2 matches — one in the `epic-manifest.md` line, one in the `story-{n.m}.md` line.

- [ ] **Step 4: Commit**

```bash
git add skills/sdlc/references/output-format.md
git commit -m "docs(sdlc): note the epic-manifest Repo column and story GitHub Issue line"
```

---

### Task 7: Manual end-to-end verification against a real repo and Project board

**Files:**

- Create (temporary, not committed): a throwaway epic/story fixture under `docs/sdlc/epics/epic-99/stories/`
- No repo files under `agents/` or `skills/` are modified in this task.

**Interfaces:**

- Consumes: Task 3's `sdlc-github-issue` procedure, Task 4's Intake convention, and Task 5's dispatch-prompt shape.
- Produces: a pass/fail confirmation that Issue creation, board item creation, field-setting, story-file traceability, and idempotency all work against a real repo and board — nothing downstream depends on this task's fixtures.

- [ ] **Step 1: Ask for a real target repo and Project board**

Before running this task, ask the human partner for a GitHub repo (`owner/repo`) they have write access to via their active `gh` account, and a GitHub Project board they can add items to (`owner` + project number). Do not fabricate these — Issue/board writes are visible to others, and a wrong target could create noise in someone else's repo.

- [ ] **Step 2: Create a throwaway fixture story file**

```bash
mkdir -p docs/sdlc/epics/epic-99/stories
cat > docs/sdlc/epics/epic-99/stories/story-99.1.md <<'EOF'
# Story 99.1 (test fixture)

**Title**

GitHub issue creation smoke test

**Context**

This is a throwaway fixture used only to manually verify the
`sdlc-github-issue` agent added in this plan. Not a real story.

**Acceptance Criteria**

- Given this fixture story, when `sdlc-github-issue` runs against it, then
  a GitHub Issue is created with title `[Test Tribo][Test Squad] GitHub
  issue creation smoke test` and this Acceptance Criteria section copied
  into the Issue body.

**Technical Notes**

None — this fixture exercises no real code path.

**Definition of Done**

- [ ] Issue created and traceable from this file.
EOF
```

- [ ] **Step 3: Attempt to dispatch `sdlc-github-issue` directly via the Agent tool**

Try (substituting the real repo and board from Step 1):

```
Agent(subagent_type: "sdlc-github-issue", prompt: "Epic 99 story directory: docs/sdlc/epics/epic-99/stories/. Target repo: {real owner/repo}. Board: {real board owner}/{real board number}. Tribo: Test Tribo. Squad: Test Squad. Project: GitHub Issue Smoke Test. Create issues per your contract.")
```

If this resolves and runs, skip to Step 5. If the agent type is not resolvable in the running session, proceed to Step 4 instead.

- [ ] **Step 4: Fallback — manually walk the updated procedure**

If Step 3's dispatch didn't resolve, perform `sdlc-github-issue`'s own procedure by hand, exactly as `agents/sdlc-github-issue.md` now specifies:

1. Read `docs/sdlc/epics/epic-99/stories/story-99.1.md`. It has no `**GitHub Issue**:` line yet, so proceed.
2. Title: `[Test Tribo][Test Squad] GitHub issue creation smoke test`.
3. Body: the Title, Context, and Acceptance Criteria sections copied verbatim.
4. `gh issue create --repo {real owner/repo} --title "[Test Tribo][Test Squad] GitHub issue creation smoke test" --body "{body}"` — record the returned Issue URL.
5. `gh project item-add {real board owner}/{real board number} --url {issue URL}` — record the returned item ID.
6. `gh project field-list {real board owner}/{real board number}` — resolve the `Epic` and `Projeto` field IDs and `Projeto`'s option list. If no option matches `GitHub Issue Smoke Test`, create one via `gh api graphql`.
7. `gh project item-edit --id {item ID} --field-id {Epic field ID} --project-id {board ID} --text "Epic 99"`, then `gh project item-edit --id {item ID} --field-id {Projeto field ID} --project-id {board ID} --single-select-option-id {option ID}`.
8. Append `**GitHub Issue**: {issue URL}` to `docs/sdlc/epics/epic-99/stories/story-99.1.md`.

- [ ] **Step 5: Verify the result on GitHub**

Confirm, from either path above:

```bash
gh issue view {issue URL} --json title,body
```

Expected: `title` is exactly `[Test Tribo][Test Squad] GitHub issue creation smoke test`; `body` contains the fixture's Context and Acceptance Criteria text.

```bash
gh project item-list {real board owner}/{real board number} --format json | grep -i "GitHub issue creation smoke test"
```

Expected: one item, with `Epic` and `Projeto` fields set (inspect the JSON output's `fieldValues` for both).

```bash
grep -n "GitHub Issue" docs/sdlc/epics/epic-99/stories/story-99.1.md
```

Expected: 1 match — the appended `**GitHub Issue**: {url}` line.

If any check fails, that's a defect in Task 3's agent contract — fix `agents/sdlc-github-issue.md` and re-run this task before proceeding.

- [ ] **Step 6: Verify idempotency — re-run against the same story directory**

Repeat Step 3 (or Step 4) against the same `docs/sdlc/epics/epic-99/stories/` directory. Expected hand-off: `"epic-99: all 1 stories already had GitHub Issues — nothing created."` Confirm no second Issue was created:

```bash
gh issue list --repo {real owner/repo} --search "GitHub issue creation smoke test" --json number
```

Expected: exactly one Issue number in the result.

- [ ] **Step 7: Clean up the fixture and the real-world artifacts**

```bash
rm -rf docs/sdlc/epics/epic-99
```

Close the throwaway Issue created in Steps 3/4 (`gh issue close {issue URL}`) and remove its item from the Project board, since it was only a smoke test, not real tracked work.

No commit for this task — it produced no repo changes under `agents/`/`skills/`, only a live verification (and the throwaway fixture, now removed). If you want a record that this check passed, note it in the PR description when this branch is ready to merge (not as a repo file).
