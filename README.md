# sdlc-orchestrator

A self-contained Claude Code plugin that runs a full software delivery lifecycle — idea → brief → PRD → architecture → epics/stories → TDD implementation → QA → review → stress test → verdict → security review → quality gate → PR → release → handoff — as a chain of 21 single-purpose agent personas, driven by 10 skills.

Built from scratch. No runtime dependency on any other installed plugin (content inspiration only, all prose original).

## Entry points

Three ways in, all converging on a common trunk (security review → quality gate → PR → release → handoff):

- **`/sdlc`** — greenfield: full brief → PRD → architecture → epics/stories → coding loop.
- **`/sdlc-bug-fix`** — root-cause investigation (failing test first) → fix, on its own `bugfix-{slug}-work` branch → same QA/review/stress/verdict path as `/sdlc`, joins the trunk at security review.
- **`/sdlc-task`** — a single well-scoped task, skipping brief/PRD, with a lightweight architecture pass.

Every phase writes its output as a Markdown artifact under `docs/sdlc/` in the target repo, and every major transition is a human-approval gate (`[GATE]`) that the pipeline never auto-advances past.

## Standalone skills

Usable independently of the full lifecycle, each asking for its own explicit confirmation before any irreversible action:

- `/sdlc-security-review` — OWASP Top 10 (+ OWASP LLM Top 10 when relevant) audit of a diff or branch.
- `/sdlc-quality-gate` — stack-aware format/lint/types/coverage/race/vulnerability gate run.
- `/sdlc-pr-review` — summarizes a diff and opens or comments on a PR.
- `/sdlc-release` — changelog, semver bump, tag, publish.
- `/sdlc-grill-me` — adversarial re-read of a plan or design document.
- `/sdlc-handoff` — closes out a session: appends a `PROGRESS.md` entry and recaps.
- `/sdlc-write-task` — writes one grounded task document (Context/DoR/AC/Technical Notes/DoD/Open Questions) without running the full task pipeline; optional GitHub Issue creation.

## Global Constraints

Each agent's `.md` file carries its own `## Contract` (Input / Output / Boundary) — the source of truth for what it may read, must produce, and must never touch. This section is the canonical home for the cross-cutting rules every agent inherits — every "see Global Constraints" reference elsewhere in `agents/`/`skills/` points here:

- **Signal vocabulary**: every audit/review agent reports one of `APPROVE`, `NIT`, `MINOR`, `MAJOR`, `CRITICAL`, `BLOCKED` — no synonyms. Not every agent can emit every signal: `BLOCKED` is `sdlc-qa`-only (implementation-blocking test failures); `sdlc-reviewer` and `sdlc-stress` use the other five.
- **Loop cap & escalation**: QA, Review, and Stress each get up to 3 rounds per story, tracked independently (Review and Stress share one counter, since they run in parallel and route on the worse of their two signals). An unresolved `NIT`/`MINOR` at round 3 escalates to `MAJOR` (back to the Coder squad); an unresolved `MAJOR` at round 3 escalates to `CRITICAL`/`BLOCKED` and stops at a human-decision gate. Full routing logic: [`skills/sdlc/references/phases.md`](skills/sdlc/references/phases.md).
- **Coverage threshold**: 85% on changed files is the shared bar for both `sdlc-qa`'s audit and `sdlc-quality-gate`'s automated gate — the two are never allowed to disagree on this number.
- **Workspace isolation**: a session working multiple epics whose stories could touch overlapping files must give each epic its own `git worktree` before that epic's first story branch is created; a single-epic session skips this and just uses the per-story branch.
- **Single-repo execution per session**: `epic-manifest.md` rows may declare distinct `Repo` values, but every execution dispatch from Coder squad through Release operates on one checked-out repo per session — a multi-repo epic needs a separate `/sdlc` session per distinct `Repo` value; `/sdlc` stops and surfaces this before Step 5 if a manifest mixes repos.
- **Verification before completion**: a check an agent couldn't actually run (missing dependency, no applicable test, tool unavailable) is reported as a finding — never treated as a silent pass just because nothing contradicted it.
- **State tracking**: no separate state-machine diagram — state lives in the six numbered `[GATE N]` human-approval checkpoints (plus unscheduled escalation gates) combined with `PROGRESS.md`'s `Current State` field, e.g. "story 2.3, QA round 2/3 after a MINOR Tuner fix". Convention, including the lightweight session `Metrics` (rounds used, findings by severity, gates cleared/escalated): [`skills/sdlc/references/progress-file.md`](skills/sdlc/references/progress-file.md).
- **Least privilege**: every agent's `tools:` frontmatter lists only what that role needs (e.g. `sdlc-qa` has no `Edit`; `sdlc-handoff` has no `Bash`).
- **Complexity classification**: `sdlc-architect` assigns each story/task row a `Complexity` value (`simple`, `complex`, or `very-complex`) alongside `Tier`, in `epic-manifest.md`/`task-manifest.md`; `sdlc-bug-investigator` assigns the same value in `investigation.md` (bug-fix has no manifest row to carry it). Default to `complex` whenever genuinely unsure — `very-complex` is reserved, never a lazy fallback:
  - `simple` — single component/file area, no new integration, no new data model, no concurrency/async coordination.
  - `complex` — the default when unsure; touches multiple components, introduces a new integration/data flow, or has non-trivial business logic/edge cases.
  - `very-complex` — cross-cutting architectural change, a new external integration with real failure modes, concurrency/consistency guarantees, or a security-sensitive flow (auth, payments, PII).
- **Model assignment**: planning/design/validation agents (including `sdlc-devops`) run on Sonnet by default. `sdlc-coder` (+ overlays) also defaults to Sonnet — the dispatching skill overrides to Opus for that one dispatch only when the story/task's `Complexity` is `very-complex` (routing logic: [`skills/sdlc/references/phases.md`](skills/sdlc/references/phases.md) step 5b, [`skills/sdlc-task/references/loop.md`](skills/sdlc-task/references/loop.md) step 2, [`skills/sdlc-bug-fix/references/dispatch.md`](skills/sdlc-bug-fix/references/dispatch.md) step 2). `sdlc-tuner` always runs on Sonnet, no override — its Contract already keeps every fix narrow enough (one file, no test-intent change) that a "very-complex Tuner fix" can't occur; anything that big escalates to `sdlc-coder` as `MAJOR` instead.
- **Concise grounding**: when an agent inlines an excerpt from another artifact into a self-contained file (a story's Technical Notes, a task document, a bug investigation's Affected Surface/Proposed Fix), inline the smallest verbatim excerpt that supports the claim, or a `file:line` pointer plus a one-line paraphrase — never the surrounding prose. Self-containment (no "see the architecture doc for details") stays mandatory; verbosity doesn't. This file gets re-read in full by every downstream agent — Coder, QA, Reviewer, Stress, Verdict, and any Tuner round — so unnecessary length multiplies across every one of those reads.

### Responsibility matrix

One agent, one job — no two agents share a write target, and validation is always independent of the write it's checking.

| Phase           | Agents                                                                                          |
| --------------- | ----------------------------------------------------------------------------------------------- |
| Discover        | `sdlc-analyst`, `sdlc-bug-investigator`                                                         |
| Decide / plan   | `sdlc-pm`, `sdlc-architect`, `sdlc-scrum-master`, `sdlc-task-writer`                            |
| Write           | `sdlc-coder` (+ `-backend`/`-frontend` overlays), `sdlc-tuner`                                  |
| Validate        | `sdlc-qa`, `sdlc-reviewer`, `sdlc-stress`, `sdlc-verdict`, `sdlc-security`, `sdlc-quality-gate` |
| Publish / close | `sdlc-pr`, `sdlc-devops`, `sdlc-handoff`                                                        |
| Notify          | `sdlc-slack-notify`, `sdlc-github-issue`                                                        |

## Layout

```
agents/    21 persona files (sdlc-analyst, sdlc-pm, sdlc-architect, sdlc-coder(+overlays), ...)
skills/    10 skills (sdlc, sdlc-bug-fix, sdlc-task, sdlc-security-review, sdlc-quality-gate,
           sdlc-pr-review, sdlc-release, sdlc-grill-me, sdlc-handoff, sdlc-write-task)
docs/      design doc + implementation plan this was built from
```

## Install

Copy (or symlink) the contents of `agents/` into `~/.claude/agents/` and `skills/` into `~/.claude/skills/`, or install as a plugin pointing at this repo.

## Design history

- [`docs/2026-07-29-sdlc-orchestrator-design.md`](docs/2026-07-29-sdlc-orchestrator-design.md) — the approved design.
- [`docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md`](docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md) — the 27-task implementation plan executed to build it.
- [`docs/superpowers/specs/2026-08-04-slack-notifications-design.md`](docs/superpowers/specs/2026-08-04-slack-notifications-design.md) — opt-in Slack notifications at the 3 planning gates.
- [`docs/superpowers/plans/2026-08-04-slack-notifications.md`](docs/superpowers/plans/2026-08-04-slack-notifications.md) — the 3-task implementation plan executed to build it.
- [`docs/superpowers/specs/2026-08-04-slack-notify-project-name-design.md`](docs/superpowers/specs/2026-08-04-slack-notify-project-name-design.md) — optional explicit `project_name` for Slack notifications.
- [`docs/superpowers/plans/2026-08-04-slack-notify-project-name.md`](docs/superpowers/plans/2026-08-04-slack-notify-project-name.md) — the 3-task implementation plan executed to build it.
- [`docs/superpowers/specs/2026-08-17-p0-orchestrator-fixes-design.md`](docs/superpowers/specs/2026-08-17-p0-orchestrator-fixes-design.md) — fixes for the four load-bearing `/sdlc` bugs found by a static, `sdlc-grill-me`-driven audit.
- [`docs/superpowers/plans/2026-08-17-p0-orchestrator-fixes.md`](docs/superpowers/plans/2026-08-17-p0-orchestrator-fixes.md) — the 10-task implementation plan executed to build it.
- [`docs/superpowers/specs/2026-08-20-epic-context-design.md`](docs/superpowers/specs/2026-08-20-epic-context-design.md) — an Epic Summary block (Goal/Boundaries/Key decisions/Definition of Done) for `epic-manifest.md`, the one artifact a semantic what/why/limits/decisions/done audit found lacking narrative.
- [`docs/superpowers/plans/2026-08-20-epic-context.md`](docs/superpowers/plans/2026-08-20-epic-context.md) — the 6-task implementation plan executed to build it.
- [`docs/superpowers/specs/2026-08-20-pipeline-consistency-fixes-design.md`](docs/superpowers/specs/2026-08-20-pipeline-consistency-fixes-design.md) — 5 findings from a business-validation audit of the whole `/sdlc` pipeline (round-history loss, a skipped IaC dispatch, an unenforced multi-repo limit, ignored Tuner escalations, undriven CI/quality-gate coupling).
- [`docs/superpowers/plans/2026-08-20-pipeline-consistency-fixes.md`](docs/superpowers/plans/2026-08-20-pipeline-consistency-fixes.md) — the implementation plan executed to fix all 5.
- [`docs/superpowers/specs/2026-09-04-write-task-skill-design.md`](docs/superpowers/specs/2026-09-04-write-task-skill-design.md) — a standalone `/sdlc-write-task` skill that writes one grounded task document without running the full task pipeline.
- [`docs/superpowers/plans/2026-09-04-write-task-skill.md`](docs/superpowers/plans/2026-09-04-write-task-skill.md) — the 6-task implementation plan executed to build it.
