# sdlc-orchestrator

A self-contained Claude Code plugin that runs a full software delivery lifecycle — idea → brief → PRD → architecture → epics/stories → TDD implementation → QA → review → stress test → verdict → security review → quality gate → PR → release → handoff — as a chain of 18 single-purpose agent personas, driven by 9 skills.

Built from scratch. No runtime dependency on any other installed plugin (content inspiration only, all prose original).

## Entry points

Three ways in, all converging on a common trunk (security review → quality gate → PR → release → handoff):

- **`/sdlc`** — greenfield: full brief → PRD → architecture → epics/stories → coding loop.
- **`/sdlc-bug-fix`** — root-cause investigation (failing test first) → fix → same QA/review path, joins the trunk at security review.
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

## Layout

```
agents/    18 persona files (sdlc-analyst, sdlc-pm, sdlc-architect, sdlc-coder(+overlays), ...)
skills/    9 skills (sdlc, sdlc-bug-fix, sdlc-task, sdlc-security-review, sdlc-quality-gate,
           sdlc-pr-review, sdlc-release, sdlc-grill-me, sdlc-handoff)
docs/      design doc + implementation plan this was built from
```

## Install

Copy (or symlink) the contents of `agents/` into `~/.claude/agents/` and `skills/` into `~/.claude/skills/`, or install as a plugin pointing at this repo.

## Design history

- [`docs/2026-07-29-sdlc-orchestrator-design.md`](docs/2026-07-29-sdlc-orchestrator-design.md) — the approved design.
- [`docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md`](docs/superpowers/plans/2026-07-30-sdlc-orchestrator.md) — the 27-task implementation plan executed to build it.
