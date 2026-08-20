# sdlc-orchestrator

A self-contained Claude Code plugin that runs a full software delivery lifecycle — idea → brief → PRD → architecture → epics/stories → TDD implementation → QA → review → stress test → verdict → security review → quality gate → PR → release → handoff — as a chain of 20 single-purpose agent personas, driven by 9 skills.

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

## Global Constraints

Each agent's `.md` file carries its own `## Contract` (Input / Output / Boundary) — the source of truth for what it may read, must produce, and must never touch. This section is the canonical home for the cross-cutting rules every agent inherits — every "see Global Constraints" reference elsewhere in `agents/`/`skills/` points here:

- **Signal vocabulary**: every audit/review agent reports one of `APPROVE`, `NIT`, `MINOR`, `MAJOR`, `CRITICAL`, `BLOCKED` — no synonyms. Not every agent can emit every signal: `BLOCKED` is `sdlc-qa`-only (implementation-blocking test failures); `sdlc-reviewer` and `sdlc-stress` use the other five.
- **Loop cap & escalation**: QA, Review, and Stress each get up to 3 rounds per story, tracked independently (Review and Stress share one counter, since they run in parallel and route on the worse of their two signals). An unresolved `NIT`/`MINOR` at round 3 escalates to `MAJOR` (back to the Coder squad); an unresolved `MAJOR` at round 3 escalates to `CRITICAL`/`BLOCKED` and stops at a human-decision gate. Full routing logic: [`skills/sdlc/references/phases.md`](skills/sdlc/references/phases.md).
- **Coverage threshold**: 85% on changed files is the shared bar for both `sdlc-qa`'s audit and `sdlc-quality-gate`'s automated gate — the two are never allowed to disagree on this number.
- **Workspace isolation**: a session working multiple epics whose stories could touch overlapping files must give each epic its own `git worktree` before that epic's first story branch is created; a single-epic session skips this and just uses the per-story branch.
- **Verification before completion**: a check an agent couldn't actually run (missing dependency, no applicable test, tool unavailable) is reported as a finding — never treated as a silent pass just because nothing contradicted it.
- **State tracking**: no separate state-machine diagram — state lives in the six numbered `[GATE N]` human-approval checkpoints (plus unscheduled escalation gates) combined with `PROGRESS.md`'s `Current State` field, e.g. "story 2.3, QA round 2/3 after a MINOR Tuner fix". Convention, including the lightweight session `Metrics` (rounds used, findings by severity, gates cleared/escalated): [`skills/sdlc/references/progress-file.md`](skills/sdlc/references/progress-file.md).
- **Least privilege**: every agent's `tools:` frontmatter lists only what that role needs (e.g. `sdlc-qa` has no `Edit`; `sdlc-handoff` has no `Bash`).
- **Model assignment**: planning/design/validation agents run on Sonnet; the agents that write code (`sdlc-coder` + overlays, `sdlc-tuner`) and `sdlc-devops` run on Opus.

### Responsibility matrix

One agent, one job — no two agents share a write target, and validation is always independent of the write it's checking.

| Phase           | Agents                                                                                          |
| --------------- | ----------------------------------------------------------------------------------------------- |
| Discover        | `sdlc-analyst`, `sdlc-bug-investigator`                                                         |
| Decide / plan   | `sdlc-pm`, `sdlc-architect`, `sdlc-scrum-master`                                                |
| Write           | `sdlc-coder` (+ `-backend`/`-frontend` overlays), `sdlc-tuner`                                  |
| Validate        | `sdlc-qa`, `sdlc-reviewer`, `sdlc-stress`, `sdlc-verdict`, `sdlc-security`, `sdlc-quality-gate` |
| Publish / close | `sdlc-pr`, `sdlc-devops`, `sdlc-handoff`                                                        |
| Notify          | `sdlc-slack-notify`, `sdlc-github-issue`                                                        |

## Layout

```
agents/    20 persona files (sdlc-analyst, sdlc-pm, sdlc-architect, sdlc-coder(+overlays), ...)
skills/    9 skills (sdlc, sdlc-bug-fix, sdlc-task, sdlc-security-review, sdlc-quality-gate,
           sdlc-pr-review, sdlc-release, sdlc-grill-me, sdlc-handoff)
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
