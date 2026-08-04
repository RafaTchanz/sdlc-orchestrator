# Slack Notifications for Planning Gates — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Exception:** Task 3 performs a real, visible Slack post and requires explicit human confirmation of the target channel before it runs — do not let an autonomous fix loop send that message without that confirmation having happened first.

**Goal:** Add an opt-in Slack notification that fires at each of the 3 planning gates (Brief, PRD, Architecture) — never gating the pipeline, never persisted to disk.

**Architecture:** One new terminal-node agent (`sdlc-slack-notify`, persona "Jarvis Jr.") that reads an artifact, posts it as a Slack Canvas, and messages a channel with a summary + link. The `/sdlc` trunk asks once per session (Intake) whether to opt in and which `channel_id` to use, holds that answer only in the running session's context, and dispatches Jarvis Jr. at the moment each of gates 1/2/3 is presented — before the human approves, so the squad reviews concurrently with the coordinator.

**Tech Stack:** Markdown agent/skill files only (Claude Code's native agent format: YAML frontmatter + prose contract/procedure) plus the `slack` plugin's MCP tools (`mcp__plugin_slack_slack__slack_create_canvas`, `mcp__plugin_slack_slack__slack_send_message`). No new runtime code, no new file format, no persisted state.

## Global Constraints

Reference design doc: `docs/superpowers/specs/2026-08-04-slack-notifications-design.md` (Approved). Every task below implicitly inherits these:

- **Branch:** this repo enforces no direct commits to `main`; branch names must be prefixed `feature/`, `hotfix/`, or `release/`. The design doc for this feature is already committed on `feature/slack-notifications-design`, open as PR #4. Every commit in this plan lands on that same branch — do not create a new branch; this plan's commits extend PR #4 rather than opening a second one.
- **Commit messages:** Conventional Commits (`type(scope): summary`), matching this repo's existing history (`feat(...)`, `fix(...)`, `docs(...)`).
- **MCP tool names in agent `tools:` frontmatter — resolved (was an open verification item in spec §8):** Claude Code's subagent `tools:` field accepts exact MCP tool names (e.g. `mcp__plugin_slack_slack__slack_create_canvas`) directly, the same way it accepts built-in tool names — confirmed against the `sub-agents.md` reference doc, which states server-level patterns (`mcp__<server>`, `mcp__<server>__*`) are accepted "**in addition to** exact tool names," i.e. exact names were already the baseline mechanism. No existing agent in this repo used this pattern yet; Task 1 is the first, and Task 3's live dispatch is the functional confirmation.
- **Notification-only, never a gate:** `sdlc-slack-notify`'s outcome (success, partial, or total failure) is reported only in its one-line hand-off. The dispatching trunk logs a failure as a non-fatal warning in its own narration and proceeds straight to the human gate regardless — no task below may make the trunk stop, retry, or ask the human anything because of a Slack failure.
- **Zero on-disk footprint:** no task may create a persisted config file, a new file format, or a `.gitignore` entry for the opt-in answer or `channel_id`. Both live only in the running session's context for that one `/sdlc` invocation.
- **Which gates:** only gates 1 (Brief), 2 (PRD), 3 (Architecture) per spec §2. Never wire this into gate 4 (per-story verdict), gate 5 (PR), gate 6 (Release), or any per-story loop — those are out of scope by design (spec §2, would flood the channel).
- **Model assignment:** `sdlc-slack-notify` runs on `sonnet` — it's a reporting/side-effect agent, not a code-writing one, consistent with this repo's existing model table (`docs/2026-07-29-sdlc-orchestrator-design.md` §9): `sonnet` for planning/validation/reporting roles, `opus` reserved for `sdlc-coder`(+overlays)/`sdlc-tuner`/`sdlc-devops`.
- **Least privilege:** `sdlc-slack-notify`'s `tools:` line is exactly `Read, mcp__plugin_slack_slack__slack_create_canvas, mcp__plugin_slack_slack__slack_send_message` — no `Write`/`Edit`/`Bash`. It only ever reads the artifact file handed to it; it never touches the filesystem otherwise and never runs a shell command.
- **Agent frontmatter fields, always** (matching every other agent in `agents/`): `name`, `description` (states exactly when/by-what it's dispatched, and that it's never invoked directly), `model`, `tools` (explicit list, never blanket "all tools").
- **Validation style for this repo's prose/config assets:** there is no automated test suite for agent/skill `.md` files. Structural validation is `head`/`grep` checks on frontmatter and section headers (see Task 1 Step 2); the one functional check this feature needs is a real, live dispatch against Slack, which is Task 3 — not automatable, per spec §8.

## File Structure

```
agents/sdlc-slack-notify.md       (new)  — Jarvis Jr., the notify agent
skills/sdlc/SKILL.md              (modified) — Intake opt-in question; gate 1/2/3 steps mention the dispatch
skills/sdlc/references/phases.md (modified) — exact dispatch block + routing at steps 2, 3, 4
README.md                         (modified) — design-history pointers to this spec + plan
docs/superpowers/specs/2026-08-04-slack-notifications-design.md (modified) — Status line only
```

---

## Task 1: `agents/sdlc-slack-notify.md` (Jarvis Jr.) — Slack notify agent

**Files:**

- Create: `agents/sdlc-slack-notify.md`

**Interfaces:**

- Consumes: an artifact file path (`docs/sdlc/product-brief.md` | `docs/sdlc/PRD.md` | `docs/sdlc/architecture.md`), a one-line hand-off string from the agent that produced it, and a `channel_id` — all three passed in the dispatch prompt by the `/sdlc` trunk (Task 2/3 below).
- Produces: a Slack Canvas (via `slack_create_canvas`) and a Slack message (via `slack_send_message`) as side effects; returns exactly one hand-off line back to the trunk, in one of three fixed shapes (success / partial / total failure) — Task 3's dispatch block depends on these exact shapes existing so the trunk can tell success from failure from the hand-off text alone.

- [ ] **Step 1: Write the file**

```markdown
---
name: sdlc-slack-notify
description: Posts a Slack Canvas + channel message for a planning-gate artifact (Brief/PRD/Architecture) so the squad can review async, in parallel with the coordinator's own gate approval. Dispatched only by the /sdlc trunk, and only when the session opted in during Intake — never invoked directly.
model: sonnet
tools: Read, mcp__plugin_slack_slack__slack_create_canvas, mcp__plugin_slack_slack__slack_send_message
---

# Jarvis Jr. — Slack Notify

You are Jarvis Jr.: a junior aide who runs one small, well-defined errand — get today's artifact in front of the squad in Slack — and reports back immediately, without ever holding up the mission.

## Contract

- **Input**: the artifact's file path (`docs/sdlc/product-brief.md` | `docs/sdlc/PRD.md` | `docs/sdlc/architecture.md`), the one-line hand-off text from the agent that produced it, and a `channel_id`.
- **Output**: a standalone Slack Canvas containing the artifact's full content, plus a message posted to `channel_id` with the hand-off summary and a link to that Canvas.
- **Boundary**: you never block the pipeline. Any failure (invalid channel, Slack unreachable, Canvas creation error) is caught and reported in your hand-off — never raised, never retried more than once per call. You never read or write any config file — the channel ID arrives directly in your dispatch prompt, and you never persist it anywhere. You never invoke a Slack tool for anything beyond this one artifact's Canvas + message. You are never invoked directly — only dispatched by the `/sdlc` trunk at the moment a planning gate is presented, and only when the session opted in during Intake.

## Procedure

1. Read the artifact file at the given path in full.
2. Derive a short Canvas title: `"{Artifact label} — {project/feature name if evident from the content}"` (e.g. `"Product Brief — Checkout Redesign"`). Artifact label is `"Product Brief"` for `product-brief.md`, `"PRD"` for `PRD.md`, `"Architecture"` for `architecture.md`. If no project-specific name is evident from the content, use the plain artifact label alone.
3. Call `slack_create_canvas` with that title and the artifact's full content as markdown. If this call fails for any reason, catch it, record the error text, and continue to step 4 with no Canvas link available.
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

5. If step 4 also fails, catch it — do not retry, do not raise, do not attempt any other Slack tool.
6. Hand off exactly one line, in exactly one of these three shapes:
- Both steps 3 and 4 succeeded: `"Slack notified in {channel_id} — canvas: {canvas_url}."`
- Step 3 failed, step 4 succeeded (message sent without a canvas link): `"Slack notification partial — canvas failed ({error}), message sent to {channel_id} without a link."`
- Step 4 failed (regardless of step 3): `"Slack notification failed — {error from step 4}. Pipeline continuing."`

Whatever happens, your hand-off is the only thing the trunk reads. It decides from your one line whether to log a warning — never whether to stop.
```

- [ ] **Step 2: Validate frontmatter and structure**

```bash
head -6 agents/sdlc-slack-notify.md
grep -c '^## ' agents/sdlc-slack-notify.md
grep -n '^tools:' agents/sdlc-slack-notify.md
```

Expected: frontmatter shows `name: sdlc-slack-notify`, `model: sonnet`; the `tools:` line lists exactly `Read, mcp__plugin_slack_slack__slack_create_canvas, mcp__plugin_slack_slack__slack_send_message` (no `Write`/`Edit`/`Bash`, no bare "all tools"); at least 2 `##` sections (Contract, Procedure).

- [ ] **Step 3: Commit**

```bash
git add agents/sdlc-slack-notify.md
git commit -m "feat(agents): add sdlc-slack-notify agent for planning-gate notifications"
```

---

## Task 2: Wire the Slack opt-in and gate dispatch into the `/sdlc` trunk

**Files:**

- Modify: `skills/sdlc/SKILL.md`
- Modify: `skills/sdlc/references/phases.md`

**Interfaces:**

- Consumes: `agents/sdlc-slack-notify.md` from Task 1 (the exact `subagent_type: "sdlc-slack-notify"` and the three hand-off shapes it can return).
- Produces: the session-scoped opt-in question and answer (`notify: yes|no`, `channel_id` if yes) held in the trunk's own running context; the three dispatch call-shapes at gates 1/2/3 that the trunk actually executes.

- [ ] **Step 1: Edit `skills/sdlc/SKILL.md` — Intake step**

Find this line in the `## Steps` section:

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline).
```

Replace it with:

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id?"_ Hold the answer (opted in yes/no, and `channel_id` if yes) only in this session's running context — never write it to any file.
```

- [ ] **Step 2: Edit `skills/sdlc/SKILL.md` — gate steps mention the dispatch**

Find these three lines (still in `## Steps`):

```markdown
2. Dispatch `sdlc-analyst` → `product-brief.md` → **[GATE 1]**.
3. Dispatch `sdlc-pm` with the Brief → `PRD.md` → **[GATE 2]**.
4. Dispatch `sdlc-architect` with Brief+PRD → `architecture.md` + `epic-manifest.md`; run `/sdlc-grill-me` against `architecture.md` → **[GATE 3]**.
```

Replace them with:

```markdown
2. Dispatch `sdlc-analyst` → `product-brief.md` → if this session opted in, dispatch `sdlc-slack-notify` → **[GATE 1]**.
3. Dispatch `sdlc-pm` with the Brief → `PRD.md` → if this session opted in, dispatch `sdlc-slack-notify` → **[GATE 2]**.
4. Dispatch `sdlc-architect` with Brief+PRD → `architecture.md` + `epic-manifest.md`; run `/sdlc-grill-me` against `architecture.md` → if this session opted in, dispatch `sdlc-slack-notify` on `architecture.md` → **[GATE 3]**.
```

- [ ] **Step 3: Edit `skills/sdlc/SKILL.md` — Boundary note**

Find this sentence inside the `## Contract` → `**Boundary**` bullet:

```markdown
- **Boundary**: orchestration only — this skill never writes code, tests, or artifacts itself; every artifact comes from the sub-agent it dispatches via `Agent(subagent_type: "sdlc-...")`. Never auto-advances past a `[GATE]`. `sdlc-tuner` is dispatched only for `NIT`/`MINOR` findings routed by QA or Review — it never reopens architecture, story, or test-authoring decisions.
```

Append one sentence to it so it reads:

```markdown
- **Boundary**: orchestration only — this skill never writes code, tests, or artifacts itself; every artifact comes from the sub-agent it dispatches via `Agent(subagent_type: "sdlc-...")`. Never auto-advances past a `[GATE]`. `sdlc-tuner` is dispatched only for `NIT`/`MINOR` findings routed by QA or Review — it never reopens architecture, story, or test-authoring decisions. `sdlc-slack-notify` is dispatched at gates 1/2/3 only when the session opted in during Intake; it never gates the pipeline — any failure it reports is logged as a non-fatal warning and the trunk proceeds to the gate regardless.
```

- [ ] **Step 4: Edit `skills/sdlc/references/phases.md` — Step 2 (Analyst) dispatch**

Find:

```markdown
On return: read `docs/sdlc/product-brief.md`, present it to the user, **[GATE 1]** — explicit confirmation before continuing.
```

Replace with:

```markdown
On return: read `docs/sdlc/product-brief.md`, present it to the user.

If this session opted into Slack notifications during Intake, dispatch `sdlc-slack-notify` now — before the human gate, so the squad reviews concurrently with the coordinator:

\`\`\`

Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/product-brief.md. Hand-off: {sdlc-analyst's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

\`\`\`

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning in this session's own narration — never block on it.

**[GATE 1]** — explicit confirmation before continuing.
```

- [ ] **Step 5: Edit `skills/sdlc/references/phases.md` — Step 3 (PM) dispatch**

Find:

```markdown
**[GATE 2]** on the PRD, same pattern.
```

Replace with:

```markdown
If this session opted into Slack notifications during Intake, dispatch `sdlc-slack-notify` now, same pattern as Step 2:

\`\`\`

Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/PRD.md. Hand-off: {sdlc-pm's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

\`\`\`

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it.

**[GATE 2]** on the PRD, same confirmation pattern as Step 2.
```

- [ ] **Step 6: Edit `skills/sdlc/references/phases.md` — Step 4 (Architect) dispatch**

Find:

```markdown
Then invoke the `sdlc-grill-me` skill against `docs/sdlc/architecture.md` before the gate. **[GATE 3]** on architecture + manifest together.
```

Replace with:

```markdown
Then invoke the `sdlc-grill-me` skill against `docs/sdlc/architecture.md` before the gate.

If this session opted into Slack notifications during Intake, dispatch `sdlc-slack-notify` now, after `grill-me` has resolved:

\`\`\`

Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/architecture.md. Hand-off: {sdlc-architect's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

\`\`\`

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it.

**[GATE 3]** on architecture + manifest together.
```

- [ ] **Step 7: Validate the edits landed correctly**

```bash
grep -n "sdlc-slack-notify" skills/sdlc/SKILL.md skills/sdlc/references/phases.md
grep -c "sdlc-slack-notify" skills/sdlc/references/phases.md
```

Expected: `SKILL.md` shows 4 matches (Intake sentence + 3 gate-step mentions); `phases.md` shows 3 dispatch blocks (one per gate) — the count command should print `3` or more (each block references the name at least once in the `Agent(subagent_type: ...)` line, some also in surrounding prose).

- [ ] **Step 8: Commit**

```bash
git add skills/sdlc/SKILL.md skills/sdlc/references/phases.md
git commit -m "feat(sdlc): wire Slack opt-in intake and gate notifications into trunk"
```

---

## Task 3: Live end-to-end validation, then close out docs

**Files:**

- No source files modified until Step 5 (docs only).

**Interfaces:**

- Consumes: `agents/sdlc-slack-notify.md` (Task 1) dispatched directly via the `Agent` tool, exactly as `phases.md` (Task 2) now specifies.
- Produces: confirmation that the three hand-off shapes from Task 1 actually occur against a real Slack workspace; updated `Status` line in the spec and updated `README.md` design-history pointers.

**⚠️ Before Step 1:** this task posts a real, visible message to a real Slack channel. Confirm the target `channel_id` with the user first — do not pick one unilaterally, and do not reuse a production/team-facing channel for this test unless the user explicitly says to. The design doc's own validation (spec §6) used a test channel (`C0BMZAD3PUJ`); ask the user whether that channel is still appropriate to reuse, or which one to use instead.

- [ ] **Step 1: Get explicit user confirmation of the test channel**

Ask the user directly (not a shell step): "I'm about to dispatch `sdlc-slack-notify` for real, which will post a Canvas + message to a Slack channel. Which `channel_id` should I use for this test?" Do not proceed to Step 2 until you have an explicit answer.

- [ ] **Step 2: Dispatch the success path**

Using the `Agent` tool directly (this is a live functional test, not a scripted step):

```
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/product-brief.md. Hand-off: 'Product Brief written to docs/sdlc/product-brief.md — 0 open questions.' Channel: {channel_id confirmed in Step 1}. Notify per your contract. Note in the Canvas title that this is a test post from the sdlc-orchestrator implementation plan.")
```

If `docs/sdlc/product-brief.md` does not exist in this checkout (it won't, in the `sdlc-orchestrator` repo itself — that file only exists in a target project `/sdlc` runs against), point the dispatch at `docs/2026-07-29-sdlc-orchestrator-design.md` instead purely as test content — the point of this dispatch is exercising the Canvas + message path, not the specific artifact.

Expected: the returned hand-off matches the first shape from Task 1 Step 6 exactly (`"Slack notified in {channel_id} — canvas: {canvas_url}."`); the Canvas and message both actually appear in the target Slack workspace.

- [ ] **Step 3: Dispatch the failure path**

```
Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/2026-07-29-sdlc-orchestrator-design.md. Hand-off: 'Test hand-off for failure-path validation.' Channel: C000000000. Notify per your contract.")
```

(`C000000000` is a well-formed but non-existent channel ID — expected to make `slack_send_message` fail while `slack_create_canvas` still succeeds, since Canvas creation in this design is user-scoped, not channel-scoped per spec §5/§6.)

Expected: the returned hand-off matches the second shape from Task 1 Step 6 (`"Slack notification partial — canvas failed (...)"` or, if Canvas succeeded and only the message failed, the message-failure branch — whichever actually occurs, confirm it is one of the three fixed shapes, not an unhandled error surfaced to the trunk).

- [ ] **Step 4: Record the result**

If either dispatch produced a hand-off shape not covered by Task 1 Step 6, or crashed instead of returning a hand-off, stop and fix `agents/sdlc-slack-notify.md` before continuing (this is a real gap, not a deferred finding — the whole "never blocks the pipeline" guarantee depends on the hand-off always being one of the three fixed shapes). Otherwise, proceed.

- [ ] **Step 5: Update the spec's Status line**

In `docs/superpowers/specs/2026-08-04-slack-notifications-design.md`, find:

```markdown
**Status**: Approved by user, pending implementation plan
```

Replace with:

```markdown
**Status**: Implemented (`agents/sdlc-slack-notify.md`, `skills/sdlc/SKILL.md`, `skills/sdlc/references/phases.md`) — see `docs/superpowers/plans/2026-08-04-slack-notifications.md`.
```

- [ ] **Step 6: Update `README.md` design history**

Find:

```markdown
## Design history

- [`docs/2026-07-29-sdlc-orchestrator-design.md`](docs/2026-07-29-sdlc-orchestrator-design.md) — the approved design.
- [`docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md`](docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md) — the 27-task implementation plan executed to build it.
```

Replace with:

```markdown
## Design history

- [`docs/2026-07-29-sdlc-orchestrator-design.md`](docs/2026-07-29-sdlc-orchestrator-design.md) — the approved design.
- [`docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md`](docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md) — the 27-task implementation plan executed to build it.
- [`docs/superpowers/specs/2026-08-04-slack-notifications-design.md`](docs/superpowers/specs/2026-08-04-slack-notifications-design.md) — opt-in Slack notifications at the 3 planning gates.
- [`docs/superpowers/plans/2026-08-04-slack-notifications.md`](docs/superpowers/plans/2026-08-04-slack-notifications.md) — the 3-task implementation plan executed to build it.
```

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/2026-08-04-slack-notifications-design.md README.md
git commit -m "docs: mark Slack notifications feature implemented, update design history"
```

- [ ] **Step 8: Push and confirm PR #4 status with the user**

```bash
git push origin feature/slack-notifications-design
```

Then tell the user PR #4 now contains the full spec + plan + implementation, and ask whether they want to merge it now or review first — do not merge without their explicit go-ahead.

---

## Self-Review

- **Spec coverage:** §3 (all 5 decision rows) → Task 1 (agent) + Task 2 (trunk wiring). §4 (agent contract, trunk changes) → Task 1 + Task 2 verbatim. §5 (rejected alternatives) → no task implements them, correctly. §6 (validation) → Task 3 mirrors it with a fresh live dispatch. §7 (error handling) → Task 1's three hand-off shapes + Task 2's "log as non-fatal warning" wiring. §8 (testing/implementation notes) → the MCP-tool-name question is resolved in Global Constraints; the manual E2E run is Task 3.
- **Placeholder scan:** no `TBD`/`TODO`; every code block is complete, copy-pasteable text, not a description of one.
- **Type/name consistency:** `sdlc-slack-notify` (agent name), `channel_id` (dispatch parameter), and the three hand-off string shapes are identical across Task 1 (definition), Task 2 (dispatch sites), and Task 3 (live test expectations).
