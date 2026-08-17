# Phase dispatch reference — `/sdlc`

Each dispatch below is a call shape: `Agent(subagent_type: "sdlc-...", prompt: "...")`. The orchestrating skill reads back only the sub-agent's one-line hand-off (per each agent's own "Hand-off" section) — never the full artifact — then reads the artifact file directly if it needs specific content for the next dispatch prompt.

## Step 2 — Analyst

```

Agent(subagent_type: "sdlc-analyst", prompt: "Idea: {original input, gap-filled with any interview answers}. Assumptions still open: {any dimension left unresolved after its cap, phrased as 'user did not specify X' — omit this sentence entirely if no gap went unresolved}. Existing repo context: {summary if any}. Write docs/sdlc/product-brief.md per your contract.")

```

On return: read `docs/sdlc/product-brief.md`, present it to the user.

If this session opted into Slack notifications during Intake, dispatch `sdlc-slack-notify` now — before the human gate, so the squad reviews concurrently with the coordinator:

```

Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/product-brief.md. Hand-off: {sdlc-analyst's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

```

If this session's `project_name` was given at Intake, insert `Project: {session project_name}.` into the prompt above, between the `Channel:` clause and `Notify per your contract.` — otherwise omit it entirely (not an empty clause).

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning in this session's own narration — never block on it. If the dispatch itself fails or returns no hand-off at all (e.g. the agent type isn't resolvable), treat that identically: log a non-fatal warning and proceed to the gate.

**[GATE 1]** — explicit confirmation before continuing.

## Step 3 — PM

```

Agent(subagent_type: "sdlc-pm", prompt: "Approved brief at docs/sdlc/product-brief.md. Write docs/sdlc/PRD.md per your contract.")

```

If this session opted into Slack notifications during Intake, dispatch `sdlc-slack-notify` now, same pattern as Step 2:

```

Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/PRD.md. Hand-off: {sdlc-pm's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

```

If this session's `project_name` was given at Intake, insert `Project: {session project_name}.` into the prompt above, between the `Channel:` clause and `Notify per your contract.` — otherwise omit it entirely (not an empty clause).

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it. If the dispatch itself fails or returns no hand-off at all, treat that identically: log a non-fatal warning and proceed to the gate.

**[GATE 2]** on the PRD, same confirmation pattern as Step 2.

## Step 4 — Architect + grill-me

```

Agent(subagent_type: "sdlc-architect", prompt: "Approved brief (docs/sdlc/product-brief.md) and PRD (docs/sdlc/PRD.md). Full mode. Write docs/sdlc/architecture.md and docs/sdlc/epic-manifest.md per your contract.")

```

Then invoke the `sdlc-grill-me` skill against `docs/sdlc/architecture.md` before the gate.

If this session opted into Slack notifications during Intake, dispatch `sdlc-slack-notify` now, after `grill-me` has resolved:

```

Agent(subagent_type: "sdlc-slack-notify", prompt: "Artifact: docs/sdlc/architecture.md. Hand-off: {sdlc-architect's one-line hand-off}. Channel: {session channel_id}. Notify per your contract.")

```

If this session's `project_name` was given at Intake, insert `Project: {session project_name}.` into the prompt above, between the `Channel:` clause and `Notify per your contract.` — otherwise omit it entirely (not an empty clause).

Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block on it. If the dispatch itself fails or returns no hand-off at all, treat that identically: log a non-fatal warning and proceed to the gate.

**[GATE 3]** on architecture + manifest together.

## Step 5 — Story loop

For each `pending` row in `epic-manifest.md`, in row order (respecting `Depends-on`) — each row is exactly one story:

Before 5a begins, create a dedicated branch for this story off the session's base branch: `git checkout -b story-{n.m}-work`. Every dispatch for this story (5a's Coder squad through 5e's gate) operates on this branch. This is the default for every story, single-epic or multi-epic alike.

If this session is additionally working multiple epics that could touch overlapping files (per Global Constraints' workspace-isolation rule), create an isolated `git worktree` for this epic in the target repo now too, before the first story's branch is created — e.g. `git worktree add ../epic-{n} -b epic-{n}-work` — and create each story's `story-{n.m}-work` branch inside that worktree rather than the main checkout. A single-epic session skips this; the per-story branch above still applies. Track each story's own QA-loop and Review-loop round counters here too — both reset to 0 at the start of every new story, per the Loop cap & escalation rule in Global Constraints.

**5a — Scrum Master**

```

Agent(subagent_type: "sdlc-scrum-master", prompt: "Epic manifest row: {row}. PRD story {n.m}: {this story's ID/Title/Description/ACs/Priority excerpt from docs/sdlc/PRD.md — full-mode sessions only, omit this clause in light mode}. Architecture: docs/sdlc/architecture.md. Write the story file at docs/sdlc/epics/epic-{n}/stories/story-{n.m}.md.")

```

If this session opted into GitHub issue creation during Intake, dispatch `sdlc-github-issue` now, once for this story, right after this story's Scrum Master dispatch:

```

Agent(subagent_type: "sdlc-github-issue", prompt: "Epic {n} story directory: docs/sdlc/epics/epic-{n}/stories/. Target repo: {this row's manifest Repo value}. Board: {session board owner}/{session board number}. Tribo: {session tribo}. Squad: {session squad}. Project: {session project_name, if given}. Create issues per your contract.")

```

`sdlc-github-issue` dedups per-story via each story file's own `**GitHub Issue**:` marker line, so calling it once per story against the same epic directory is safe — it only ever creates the one new Issue for the story just written. Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block 5b on its outcome. If the dispatch itself fails or returns no hand-off at all (e.g. the agent type isn't resolvable), treat that identically: log a non-fatal warning and continue to 5b.

**5b — Coder squad** (per story; tier overlay chosen from the row's `Tier` column — `backend`→`sdlc-coder-backend`, `frontend`→`sdlc-coder-frontend`, `fullstack`→ dispatch both overlays' guidance in one prompt alongside the core)

```

Agent(subagent_type: "sdlc-coder", prompt: "Story: docs/sdlc/epics/epic-{n}/stories/story-{n.m}.md. Tier overlay: {sdlc-coder-backend|sdlc-coder-frontend|both}. Implement per your TDD contract.")

```

Note: Claude Code loads exactly one `subagent_type` per `Agent` call — for a `fullstack`-tier story, dispatch `sdlc-coder` with both overlay files' content concatenated into the prompt (read them with `Read` first), since the overlays are prose guidance, not separate runtime agents that can be composed automatically. Every Coder-squad, Tuner, and gate-merge action for this story happens on its `story-{n.m}-work` branch (see the note before 5a) — dispatch prompts should state that branch so the sub-agent operates there, never on the base branch. If this epic also has an isolated worktree for the multi-epic-concurrency case, that branch lives inside the worktree; state the worktree path too so the sub-agent operates there, not on the main checkout.

**5c — QA, with Tuner routing (round-capped at 3, this story's own QA counter)**

```

Agent(subagent_type: "sdlc-qa", prompt: "Story {n.m}, just implemented. Audit per your contract. Write docs/sdlc/epics/epic-{n}/story-{n.m}/qa.md.")

```

Read the signal from `qa.md`, and increment this story's QA-round counter each time this step runs after round 1:

- `APPROVE` → go to 5d.
- `NIT` or `MINOR`, round < 3 → `Agent(subagent_type: "sdlc-tuner", prompt: "Finding: {exact finding line from qa.md}. Apply the fix per your contract.")`, then re-dispatch `sdlc-qa` on the same story (round + 1).
- `NIT` or `MINOR`, round = 3 and still open → reclassify `MAJOR` (per Global Constraints' loop-cap rule) and fall through to the `MAJOR` branch below instead of dispatching `sdlc-tuner` again.
- `MAJOR`, round < 3 → re-dispatch the Coder squad (5b) with the finding included in the prompt, then re-run 5c (round + 1).
- `MAJOR`, round = 3 and still open, or `CRITICAL`/`BLOCKED` at any round → stop, escalate to the human with the finding, **[GATE]** (unscheduled — this is the "escalate" gate from design §3, distinct from the six numbered gates).

**5d — Review + Stress in parallel, with Tuner routing on the worse of the two signals (round-capped at 3, this story's own Review/Stress counter — independent of 5c's QA counter)**

```

parallel:
Agent(subagent_type: "sdlc-reviewer", prompt: "Story {n.m}. Review per your contract. Write docs/sdlc/epics/epic-{n}/story-{n.m}/review.md.")
Agent(subagent_type: "sdlc-stress", prompt: "Story {n.m}. Stress-test per your contract. Write docs/sdlc/epics/epic-{n}/story-{n.m}/stress.md.")

```

Read both Review's and Stress's signals and take the worse of the two (`CRITICAL`/`BLOCKED` > `MAJOR` > `MINOR`/`NIT` > `APPROVE`), incrementing this story's Review/Stress-round counter each time this step runs after round 1:

- Worse-of-the-two is `APPROVE`, or `NIT`/`MINOR` only, round < 3 → if any `NIT`/`MINOR` present (in either report), dispatch `sdlc-tuner` on each, then re-run **both** `sdlc-reviewer` and `sdlc-stress` (round + 1).
- Worse-of-the-two is `NIT`/`MINOR` only, round = 3 and still open → reclassify `MAJOR` and fall through to the branch below instead of dispatching `sdlc-tuner` again.
- Worse-of-the-two is `MAJOR`/`CRITICAL`, round < 3 → back to the Coder squad (5b), then re-run 5c and 5d from the top for this story (round + 1).
- Worse-of-the-two is `MAJOR`/`CRITICAL`, round = 3 and still open → reclassify `CRITICAL`/`BLOCKED` (if not already) and stop, escalate to the human, **[GATE]** (unscheduled — same escalation gate as 5c's).

**5e — Verdict**

```

Agent(subagent_type: "sdlc-verdict", prompt: "Story {n.m}. Aggregate docs/sdlc/epics/epic-{n}/story-{n.m}/{qa,review,stress}.md per your contract.")

```

**[GATE 4]** — present the verdict to the human before merge. On confirmation, merge `story-{n.m}-work` into the session's base branch, then delete the branch. On rejection/rework, stay on `story-{n.m}-work` — no merge — and loop back to whichever step the human directs.

Update the manifest row's `Status` to `done` once the story's verdict gate clears and the merge lands; move to the next `pending` row.

## Step 6 — Security + Quality Gate (parallel, independent)

```

parallel:
Agent(subagent_type: "sdlc-security", prompt: "Target: current branch, full diff since main. Write docs/sdlc/epics/epic-{n}/security-review.md.")
Agent(subagent_type: "sdlc-quality-gate", prompt: "Target: current branch. Write docs/sdlc/epics/epic-{n}/quality-gate.md.")

```

Any `CRITICAL` from Security, or `FAIL` overall from Quality Gate, stops the trunk here — route back to the Coder squad for the specific finding, don't proceed to step 7.

## Step 7 — PR

**[GATE 5]** — confirm with the human before dispatching:

```

Agent(subagent_type: "sdlc-pr", prompt: "Diff ready — security-review.md and quality-gate.md both clean. Open the PR per your contract.")

```

## Step 8 — Release

**[GATE 6]** — confirm with the human before dispatching:

```

Agent(subagent_type: "sdlc-devops", prompt: "Release half: current release branch state. Write docs/sdlc/release.md and tag/publish per your contract once confirmed.")

```

## Step 9 — Handoff

```

Agent(subagent_type: "sdlc-handoff", prompt: "Session covered: {list of phases/stories touched}. Append PROGRESS.md per your contract.")

```
