# Phase dispatch reference — `/sdlc`

Each dispatch below is a call shape: `Agent(subagent_type: "sdlc-...", prompt: "...")`. The orchestrating skill reads back only the sub-agent's one-line hand-off (per each agent's own "Hand-off" section) — never the full artifact — then reads the artifact file directly if it needs specific content for the next dispatch prompt.

## Index

Resuming mid-pipeline (e.g. after a context compaction or a new session reading `PROGRESS.md`)? Jump straight to the relevant step below instead of re-reading this file top to bottom.

| Step | Section                                                                         | Dispatches                                                                                                                                                   | Gate                                                                                                    |
| ---- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 2    | [Analyst](#step-2--analyst)                                                     | `sdlc-analyst` (+ `sdlc-slack-notify` if opted in)                                                                                                           | GATE 1                                                                                                  |
| 3    | [PM](#step-3--pm)                                                               | `sdlc-pm` (+ `sdlc-slack-notify` if opted in)                                                                                                                | GATE 2                                                                                                  |
| 4    | [Architect + grill-me](#step-4--architect--grill-me)                            | `sdlc-architect`, `/sdlc-grill-me` (+ `sdlc-slack-notify` if opted in)                                                                                       | GATE 3                                                                                                  |
| 5    | [Story loop](#step-5--story-loop)                                               | `sdlc-scrum-master` (batch), `sdlc-github-issue` (if opted in), Coder squad, `sdlc-qa`, `sdlc-reviewer`+`sdlc-stress`, `sdlc-verdict`, `sdlc-tuner` (routed) | GATE 4 (batch, before implementation) + GATE 5 (per story, before merge) + unscheduled escalation gates |
| 6    | [Security + Quality Gate](#step-6--security--quality-gate-parallel-independent) | `sdlc-security`, `sdlc-quality-gate` (parallel)                                                                                                              | —                                                                                                       |
| 7    | [PR](#step-7--pr)                                                               | `sdlc-pr`                                                                                                                                                    | GATE 6                                                                                                  |
| 8    | [Release](#step-8--release)                                                     | `sdlc-devops`                                                                                                                                                | GATE 7                                                                                                  |
| 9    | [Handoff](#step-9--handoff)                                                     | `sdlc-handoff`                                                                                                                                               | —                                                                                                       |

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

Before entering the loop below, scan every `pending` row's `Repo` value in `epic-manifest.md`. If more than one distinct value appears, stop here and surface this to the human explicitly: every execution dispatch from 5b through Step 8 operates on a single checked-out repo per session, so a multi-repo epic needs a separate `/sdlc` session per distinct `Repo` value — do not enter the loop until the human has decided how to proceed.

Step 5 has two parts: **5a writes every story in the batch up front and gates them all together before any implementation starts**; **5b–5e then implement one story at a time**, same as before.

### 5a — Scrum Master (batch) + batch gate

Determine this batch's rows: by default, every `pending` row in `epic-manifest.md`, in manifest order. If the human named a subset when starting this epic (e.g. "só as stories 1.1 a 1.3"), use that subset instead — respecting `Depends-on` still applies within it.

Dispatch one `sdlc-scrum-master` call per row in the batch, in parallel (they write disjoint files, no shared state):

```

parallel, one per batch row:
Agent(subagent_type: "sdlc-scrum-master", prompt: "Epic manifest row: {row}. Epic Summary: {this row's containing Epic Summary block from docs/sdlc/epic-manifest.md — Goal/Boundaries/Key decisions/Definition of Done — full-mode sessions only, omit this clause in light mode}. PRD story {n.m}: {this story's ID/Title/Description/ACs/Priority excerpt from docs/sdlc/PRD.md — full-mode sessions only, omit this clause in light mode}. Architecture: docs/sdlc/architecture.md. Write the story file at docs/sdlc/epics/epic-{n}/stories/story-{n.m}.md.")

```

Once every row in the batch has its story file written, read all of them back and present the full batch to the human together (not one at a time). Do not dispatch `sdlc-github-issue` yet — a story file can still be sent back for rework at this gate, and an Issue is never edited once created, so Issue creation happens only after a row has cleared the gate below.

**[GATE 4]** — batch validation, before any implementation. The human reviews every story in the batch and may approve all, approve a subset (the rest stay `pending`, revisited in a later batch or edited first), or send one or more back to Scrum Master for rework (re-dispatch 5a for just that row, then re-present it before re-gating). Never auto-advance past this gate.

If this session opted into GitHub issue creation during Intake, dispatch `sdlc-github-issue` now — once per epic touched by this batch, passed the exact list of this epic's approved story files from this gate (never the rest of the directory, and never a row still pending rework):

```

Agent(subagent_type: "sdlc-github-issue", prompt: "Story files: {list of this epic's approved story file paths from this gate}. Epic number: {n}. Target repo: {this row's manifest Repo value}. Board: {session board owner}/{session board number}. Tribo: {session tribo}. Squad: {session squad}. Project: {session project_name, if given}. Create issues per your contract.")

```

`sdlc-github-issue` dedups per-story via each story file's own `**GitHub Issue**:` marker line, so re-dispatching it for a later batch in the same epic is safe — it only ever creates Issues for files in the list that don't already have one. Read its hand-off; if it reports a partial or total failure, note that as a non-fatal warning — never block 5b on its outcome. If the dispatch itself fails or returns no hand-off at all (e.g. the agent type isn't resolvable), treat that identically: log a non-fatal warning and continue to 5b.

Only rows the human approves at this gate proceed to 5b–5e below, in manifest order (respecting `Depends-on`).

For each approved row, in order — each row is exactly one story:

Before 5b begins, create a dedicated branch for this story off the session's base branch: `git checkout -b story-{n.m}-work`. Every dispatch for this story (5b's Coder squad through 5e's gate) operates on this branch. This is the default for every story, single-epic or multi-epic alike.

If this session is additionally working multiple epics that could touch overlapping files (per Global Constraints' workspace-isolation rule), create an isolated `git worktree` for this epic in the target repo now too, before the first approved story's branch is created — e.g. `git worktree add ../epic-{n} -b epic-{n}-work` — and create each story's `story-{n.m}-work` branch inside that worktree rather than the main checkout. A single-epic session skips this; the per-story branch above still applies. Track each story's own QA-loop and Review-loop round counters here too — both reset to 0 at the start of every new story, per the Loop cap & escalation rule in Global Constraints.

**5b — Coder squad** (per story; tier overlay chosen from the row's `Tier` column — `backend`→`sdlc-coder-backend`, `frontend`→`sdlc-coder-frontend`, `fullstack`→ dispatch both overlays' guidance in one prompt alongside the core)

Read this row's `Complexity` column before dispatching: `simple`/`complex` → dispatch with no `model` override (the agent's own Sonnet default applies). `very-complex` → add `model: "opus"` to this `Agent()` call. Reuse the same value on every re-dispatch of this story (5c's `MAJOR` routing, 5d's `MAJOR`/`CRITICAL` routing) — it doesn't change round to round.

```

Agent(subagent_type: "sdlc-coder", model: "opus" (only if this row's Complexity is very-complex — omit otherwise), prompt: "Story: docs/sdlc/epics/epic-{n}/stories/story-{n.m}.md. Tier overlay: {sdlc-coder-backend|sdlc-coder-frontend|both}. Branch: story-{n.m}-work — operate there, not on the base branch. Implement per your TDD contract.")

```

Note: Claude Code loads exactly one `subagent_type` per `Agent` call — for a `fullstack`-tier story, dispatch `sdlc-coder` with both overlay files' content concatenated into the prompt (read them with `Read` first), since the overlays are prose guidance, not separate runtime agents that can be composed automatically. Every Coder-squad, Tuner, and gate-merge action for this story happens on its `story-{n.m}-work` branch (see the note before 5b) — dispatch prompts should state that branch so the sub-agent operates there, never on the base branch. If this epic also has an isolated worktree for the multi-epic-concurrency case, that branch lives inside the worktree; state the worktree path too so the sub-agent operates there, not on the main checkout.

**5c — QA, with Tuner routing (round-capped at 3, this story's own QA counter)**

```

Agent(subagent_type: "sdlc-qa", prompt: "Story {n.m}, just implemented. Branch: story-{n.m}-work — audit the code there, not the base branch. Round {n} of 3. Audit per your contract. Write docs/sdlc/epics/epic-{n}/story-{n.m}/qa.md.")

```

Read the signal from `qa.md`, and increment this story's QA-round counter each time this step runs after round 1:

- `APPROVE` → go to 5d.
- `NIT` or `MINOR`, round < 3 → `Agent(subagent_type: "sdlc-tuner", prompt: "Finding: {exact finding line from qa.md}. Branch: story-{n.m}-work — operate there, not on the base branch. Apply the fix per your contract.")`. Read the Tuner's hand-off: if it reports the escalation shape ("...reclassifying MAJOR, not applying as a Tuner fix."), treat this round's outcome as `MAJOR` directly and fall through to the `MAJOR` branch below instead of re-dispatching `sdlc-qa`. Otherwise, re-dispatch `sdlc-qa` on the same story (round + 1).
- `NIT` or `MINOR`, round = 3 and still open → reclassify `MAJOR` (per Global Constraints' loop-cap rule) and fall through to the `MAJOR` branch below instead of dispatching `sdlc-tuner` again.
- `MAJOR`, round < 3 → re-dispatch the Coder squad (5b) with the finding included in the prompt, then re-run 5c (round + 1).
- `MAJOR`, round = 3 and still open, or `CRITICAL`/`BLOCKED` at any round → stop, escalate to the human with the finding, **[GATE]** (unscheduled — this is the "escalate" gate from design §3, distinct from the seven numbered gates).

**5d — Review (+ Stress, unless this row's Complexity is `simple`), with Tuner routing on the worse of the signal(s) (round-capped at 3, this story's own Review/Stress counter — independent of 5c's QA counter)**

If this row's `Complexity` is `simple`, skip `sdlc-stress` entirely for this story — every round, not just the first — and dispatch `sdlc-reviewer` alone:

```

Agent(subagent_type: "sdlc-reviewer", prompt: "Story {n.m}. Branch: story-{n.m}-work — review the code there, not the base branch. Round {n} of 3. Review per your contract. Write docs/sdlc/epics/epic-{n}/story-{n.m}/review.md.")

```

Otherwise (`complex`/`very-complex`), dispatch both in parallel as before:

```

parallel:
Agent(subagent_type: "sdlc-reviewer", prompt: "Story {n.m}. Branch: story-{n.m}-work — review the code there, not the base branch. Round {n} of 3. Review per your contract. Write docs/sdlc/epics/epic-{n}/story-{n.m}/review.md.")
Agent(subagent_type: "sdlc-stress", prompt: "Story {n.m}. Branch: story-{n.m}-work — stress-test the code there, not the base branch. Round {n} of 3. Stress-test per your contract. Write docs/sdlc/epics/epic-{n}/story-{n.m}/stress.md.")

```

Read Review's signal (and Stress's, when dispatched) and take the worse of however many ran (`CRITICAL`/`BLOCKED` > `MAJOR` > `MINOR`/`NIT` > `APPROVE`; with Stress skipped, this is just Review's own signal), incrementing this story's Review/Stress-round counter each time this step runs after round 1:

- Worse-of-the-ran-signals is `APPROVE`, or `NIT`/`MINOR` only, round < 3 → if any `NIT`/`MINOR` present (in whichever report(s) ran), dispatch `sdlc-tuner` on each (with the finding included in the prompt, same branch clause as 5c's Tuner dispatch). Read each Tuner's hand-off: if any reports the escalation shape ("...reclassifying MAJOR, not applying as a Tuner fix."), treat this round's outcome as `MAJOR` directly and fall through to the `MAJOR`/`CRITICAL` branch below instead of re-running Review(+Stress). Otherwise, re-run Review (and Stress, if this story isn't `simple`) (round + 1).
- Worse-of-the-ran-signals is `NIT`/`MINOR` only, round = 3 and still open → reclassify `MAJOR` and fall through to the branch below instead of dispatching `sdlc-tuner` again.
- Worse-of-the-ran-signals is `MAJOR`/`CRITICAL`, round < 3 → back to the Coder squad (5b) with the finding included in the prompt, then re-run 5c and 5d from the top for this story (round + 1).
- Worse-of-the-ran-signals is `MAJOR`/`CRITICAL`, round = 3 and still open → reclassify `CRITICAL`/`BLOCKED` (if not already) and stop, escalate to the human, **[GATE]** (unscheduled — same escalation gate as 5c's).

**5e — Verdict**

```

Agent(subagent_type: "sdlc-verdict", prompt: "Story {n.m}. Complexity: {row's Complexity}. Expected final rounds — QA: {this story's final QA round}/3, Review: {this story's final Review/Stress round}/3, Stress: {'N/A — skipped, Complexity: simple' if this row's Complexity is simple, else the same Review/Stress round} (Review and Stress share one counter when both run). Aggregate docs/sdlc/epics/epic-{n}/story-{n.m}/{qa,review}.md{ and stress.md, unless Complexity is simple} per your contract.")

```

**[GATE 5]** — present the verdict to the human before merge. On confirmation, merge `story-{n.m}-work` into the session's base branch, then delete the branch. On rejection/rework, stay on `story-{n.m}-work` — no merge — and loop back to whichever step the human directs.

Update the manifest row's `Status` to `done` once the story's verdict gate clears and the merge lands; move to the next approved row.

## Step 6 — Security + Quality Gate (parallel, independent)

```

parallel:
Agent(subagent_type: "sdlc-security", prompt: "Target: current branch, full diff since main. Write docs/sdlc/security-review.md.")
Agent(subagent_type: "sdlc-quality-gate", prompt: "Target: current branch. Write docs/sdlc/quality-gate.md.")

```

Any `CRITICAL` from Security, or `FAIL` overall from Quality Gate, stops the trunk here — route back to the Coder squad for the specific finding, don't proceed to step 7.

## Step 7 — PR

**[GATE 6]** — confirm with the human before dispatching:

```

Agent(subagent_type: "sdlc-pr", prompt: "Diff ready — docs/sdlc/security-review.md and docs/sdlc/quality-gate.md both clean. Gate 6 already confirmed — proceed without asking again. Open the PR per your contract.")

```

## Step 8 — Release

Read `docs/sdlc/architecture.md`'s Deployment Topology section if the file exists — the IaC half of the dispatch below needs it (same pattern as `skills/sdlc-release/SKILL.md`'s step 2).

**[GATE 7]** — confirm with the human before dispatching:

```

Agent(subagent_type: "sdlc-devops", prompt: "Release half: current release branch state. Deployment Topology: {excerpt from architecture.md's Deployment Topology section, or 'not available — architecture.md not found' if it doesn't exist}. Generate any missing IaC first, then proceed with the release half. Gate 7 already confirmed — proceed without asking again. Write docs/sdlc/release.md and tag/publish per your contract.")

```

## Step 9 — Handoff

```

Agent(subagent_type: "sdlc-handoff", prompt: "Session covered: {list of phases/stories touched}. Append PROGRESS.md per your contract.")

```
