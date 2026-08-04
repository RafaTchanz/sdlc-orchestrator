# Explicit Project Name for Slack Notifications — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a `/sdlc` session give `sdlc-slack-notify` an explicit, optional `project_name` so Canvas titles and channel messages identify which project a notification is about, instead of relying solely on content-scanning.

**Architecture:** `project_name` is asked once at Intake, alongside the existing `channel_id` question, held only in the running session's context (never persisted), and passed straight through in each of the three existing dispatch prompts. `sdlc-slack-notify` uses it verbatim in its Canvas title and message prefix when given, and falls back to its current heuristic/behavior byte-for-byte when it isn't.

**Tech Stack:** Markdown agent/skill definition files only (no application code, no test framework) — this repo's `sdlc-*` agents and `/sdlc` skill are prose contracts read by Claude Code, not executable modules.

## Global Constraints

- No direct commits on `main` — all work happens on `feature/slack-notify-project-name` (already created off up-to-date `main`).
- Branch names must be prefixed `feature/`, `hotfix/`, or `release/`.
- Commit messages must be Conventional Commits.
- `project_name` is session-context-only — never written to any file, exactly like the existing `channel_id` (spec §2, §4).
- When `project_name` is not given, behavior must be byte-identical to current (pre-change) behavior — no regression for sessions that skip it (spec §3, §6).
- No automated test suite exists for these `.md` files — verification is manual/structural plus one live Slack end-to-end check (spec §7).

---

### Task 1: Add optional `project_name` to `sdlc-slack-notify`'s contract and procedure

**Files:**

- Modify: `agents/sdlc-slack-notify.md`

**Interfaces:**

- Consumes: nothing from other tasks.
- Produces: the updated `Input` contract and `Procedure` steps 2 and 4 that Task 2's dispatch-prompt changes rely on (the dispatch prompt gains a `Project: {session project_name}.` clause — this task defines how the agent must read and use that clause).

- [ ] **Step 1: Update the Input line in the Contract section**

Find this line:

```markdown
- **Input**: the artifact's file path (`docs/sdlc/product-brief.md` | `docs/sdlc/PRD.md` | `docs/sdlc/architecture.md`), the one-line hand-off text from the agent that produced it, and a `channel_id`.
```

Replace it with:

```markdown
- **Input**: the artifact's file path (`docs/sdlc/product-brief.md` | `docs/sdlc/PRD.md` | `docs/sdlc/architecture.md`), the one-line hand-off text from the agent that produced it, a `channel_id`, and an optional `project_name`.
```

- [ ] **Step 2: Update Procedure step 2 (Canvas title derivation)**

Find this line:

```markdown
2. Derive a short Canvas title: `"{Artifact label} — {project/feature name if evident from the content}"` (e.g. `"Product Brief — Checkout Redesign"`). Artifact label is `"Product Brief"` for `product-brief.md`, `"PRD"` for `PRD.md`, `"Architecture"` for `architecture.md`. If no project-specific name is evident from the content, use the plain artifact label alone.
```

Replace it with:

```markdown
2. Derive a short Canvas title. If a `project_name` was given in your dispatch, the title is `"{Artifact label} — {project_name}"` directly — do not scan the content. Otherwise, derive it the way you always have: `"{Artifact label} — {project/feature name if evident from the content}"` (e.g. `"Product Brief — Checkout Redesign"`). Artifact label is `"Product Brief"` for `product-brief.md`, `"PRD"` for `PRD.md`, `"Architecture"` for `architecture.md`. If no project-specific name is evident from the content, use the plain artifact label alone.
```

- [ ] **Step 3: Update Procedure step 4 (message body templates)**

Find this whole block (step 4, including both fenced message-body templates):

```markdown
4. Call `slack_send_message` to `channel_id`. If step 3 succeeded, the message body is:
```

📋 {hand-off summary text you were given}
Full artifact: {canvas_url from step 3}

```

If step 3 failed, the message body is:

```

📋 {hand-off summary text you were given}
(Canvas could not be created: {error from step 3} — artifact available at {the file path you were given} in the repo.)

```

```

Replace it with:

```markdown
4. Call `slack_send_message` to `channel_id`. Let `{prefix}` be `[{project_name}] ` if a `project_name` was given in your dispatch, or nothing at all if it wasn't (never a literal empty pair of brackets — the prefix is either present or fully absent). If step 3 succeeded, the message body is:
```

{prefix}📋 {hand-off summary text you were given}
Full artifact: {canvas_url from step 3}

```

If step 3 failed, the message body is:

```

{prefix}📋 {hand-off summary text you were given}
(Canvas could not be created: {error from step 3} — artifact available at {the file path you were given} in the repo.)

```

```

- [ ] **Step 4: Verify the edits landed correctly**

Run:

```bash
grep -n "project_name" agents/sdlc-slack-notify.md
```

Expected: 4 matches — one in the Input line, one in step 2, and two in step 4 (the `{prefix}` definition sentence mentions `project_name` once; if your editor collapses it to one match for step 4, that's fine as long as the `{prefix}` variable is defined once and used in both templates). Also run:

```bash
grep -n "{prefix}" agents/sdlc-slack-notify.md
```

Expected: exactly 2 matches (one per message-body template).

- [ ] **Step 5: Commit**

```bash
git add agents/sdlc-slack-notify.md
git commit -m "feat(sdlc-slack-notify): support optional project_name in Canvas title and message prefix"
```

---

### Task 2: Thread `project_name` through Intake and the three trunk dispatch sites

**Files:**

- Modify: `skills/sdlc/SKILL.md`
- Modify: `skills/sdlc/references/phases.md`

**Interfaces:**

- Consumes: Task 1's contract — `sdlc-slack-notify` now accepts an optional `project_name` and uses it exactly as described there.
- Produces: nothing further downstream — this is the last code-shaped task; Task 3 verifies the whole chain end-to-end.

- [ ] **Step 1: Update the Intake question in `skills/sdlc/SKILL.md`**

Find this line (Step 1 of the Steps list):

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id?"_ Hold the answer (opted in yes/no, and `channel_id` if yes) only in this session's running context — never write it to any file.
```

Replace it with:

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id, e qual o nome do projeto (opcional, para identificar as notificações)?"_ Hold the answer (opted in yes/no, `channel_id` if yes, and `project_name` if given) only in this session's running context — never write it to any file.
```

- [ ] **Step 2: Add the conditional `Project:` clause note after the Step 2 (Gate 1) dispatch block in `skills/sdlc/references/phases.md`**

Find this exact block under `## Step 2 — Analyst`:

```markdown
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/product-brief.md. Hand-off: {sdlc-analyst's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")
```

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning in this session's own narration — never block on it. If the dispatch itself fails or returns no hand-off at all (e.g. the agent type isn't resolvable), treat that identically: log a non-fatal warning and proceed to the gate.

````

Replace it with:

```markdown
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/product-brief.md. Hand-off: {sdlc-analyst's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

````

If this session's `project_name` was given at Intake, insert `Project: {session project_name}.` into the prompt above, between the `Channel:` clause and `Notify per your contract.` — otherwise omit it entirely (not an empty clause).

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning in this session's own narration — never block on it. If the dispatch itself fails or returns no hand-off at all (e.g. the agent type isn't resolvable), treat that identically: log a non-fatal warning and proceed to the gate.

````

- [ ] **Step 3: Add the same conditional-clause note after the Step 3 (Gate 2) dispatch block**

Find this exact block under `## Step 3 — PM`:

```markdown
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/PRD.md. Hand-off: {sdlc-pm's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

````

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it. If the dispatch itself fails or returns no hand-off at all, treat that identically: log a non-fatal warning and proceed to the gate.

````

Replace it with:

```markdown
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/PRD.md. Hand-off: {sdlc-pm's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

````

If this session's `project_name` was given at Intake, insert `Project: {session project_name}.` into the prompt above, between the `Channel:` clause and `Notify per your contract.` — otherwise omit it entirely (not an empty clause).

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it. If the dispatch itself fails or returns no hand-off at all, treat that identically: log a non-fatal warning and proceed to the gate.

````

- [ ] **Step 4: Add the same conditional-clause note after the Step 4 (Gate 3) dispatch block**

Find this exact block under `## Step 4 — Architect + grill-me`:

```markdown
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/architecture.md. Hand-off: {sdlc-architect's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

````

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it. If the dispatch itself fails or returns no hand-off at all, treat that identically: log a non-fatal warning and proceed to the gate.

````

Replace it with:

```markdown
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/architecture.md. Hand-off: {sdlc-architect's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

````

If this session's `project_name` was given at Intake, insert `Project: {session project_name}.` into the prompt above, between the `Channel:` clause and `Notify per your contract.` — otherwise omit it entirely (not an empty clause).

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it. If the dispatch itself fails or returns no hand-off at all, treat that identically: log a non-fatal warning and proceed to the gate.

````

- [ ] **Step 5: Verify the edits landed correctly**

Run:

```bash
grep -n "project_name" skills/sdlc/SKILL.md skills/sdlc/references/phases.md
````

Expected: 1 match in `SKILL.md` (the Intake line), and 3 matches in `phases.md` (one per dispatch-site note). Also confirm the three existing `Agent(subagent_type: "sdlc-slack-notify", ...)` lines themselves are unchanged (still no literal `Project:` text inside them — that clause is instructional, inserted at dispatch time, not baked into the template):

```bash
grep -n 'Agent(subagent_type: "sdlc-slack-notify"' skills/sdlc/references/phases.md
```

Expected: 3 matches, each still ending in `Notify per your contract.")` with no `Project:` text in the line itself.

- [ ] **Step 6: Commit**

```bash
git add skills/sdlc/SKILL.md skills/sdlc/references/phases.md
git commit -m "feat(sdlc): ask optional project_name at Intake and thread it into gate 1/2/3 dispatches"
```

---

### Task 3: Manual end-to-end verification against a real Slack channel

**Files:**

- Create (temporary, not committed): a throwaway fixture artifact, e.g. `/tmp/sdlc-slack-notify-test-brief.md`
- No repo files modified in this task.

**Interfaces:**

- Consumes: Task 1's updated `agents/sdlc-slack-notify.md` procedure and Task 2's updated dispatch-site convention.
- Produces: a pass/fail confirmation that `project_name` actually changes the Canvas title and message prefix in a real Slack channel — nothing downstream depends on this task's artifacts.

- [ ] **Step 1: Create a throwaway fixture artifact**

Write a short markdown file simulating a Product Brief, since this repo has no real `docs/sdlc/product-brief.md` yet (fresh repo, no pipeline run to date):

```bash
cat > /tmp/sdlc-slack-notify-test-brief.md <<'EOF'
# Product Brief (test fixture)

This is a throwaway fixture used only to manually verify the
`project_name`-aware Canvas title and message prefix added to
`agents/sdlc-slack-notify.md`. Not a real product brief.
EOF
```

- [ ] **Step 2: Attempt to dispatch `sdlc-slack-notify` directly via the Agent tool**

Try:

```
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: /tmp/sdlc-slack-notify-test-brief.md. Hand-off: Test brief ready for review. Channel: C0BMZAD3PUJ. Project: Test Project Alpha. Notify per your contract.")
```

If this resolves and runs, skip to Step 4. If the agent type is not resolvable in the running session (this has happened before — see the project memory on this feature's smoke test), proceed to Step 3 instead.

- [ ] **Step 3: Fallback — manually walk the updated procedure**

If Step 2's dispatch didn't resolve, perform the agent's own procedure by hand, exactly as `agents/sdlc-slack-notify.md` now specifies with `project_name = "Test Project Alpha"`:

1. Read `/tmp/sdlc-slack-notify-test-brief.md` in full.
2. Since `project_name` is given, the Canvas title is `"Product Brief — Test Project Alpha"` (no content-scanning).
3. Call `slack_create_canvas` with that title and the fixture's content.
4. Call `slack_send_message` to channel `C0BMZAD3PUJ` with body:

```
[Test Project Alpha] 📋 Test brief ready for review.
Full artifact: {canvas_url from the previous call}
```

- [ ] **Step 4: Verify the result in Slack**

Confirm, from either path above:

- A Canvas was created titled exactly `"Product Brief — Test Project Alpha"`.
- A message landed in `C0BMZAD3PUJ` whose body starts with exactly `[Test Project Alpha] 📋 `.

If either check fails, that's a defect in Task 1 or Task 2's edits — fix the relevant file and re-run this task before proceeding.

- [ ] **Step 5: Clean up the fixture**

```bash
rm /tmp/sdlc-slack-notify-test-brief.md
```

No commit for this task — it produced no repo changes, only a live verification. If you want a record that this check passed, note it in the PR description when Task 2's branch is ready to merge (not as a repo file).
