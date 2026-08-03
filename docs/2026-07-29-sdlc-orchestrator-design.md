# `/sdlc` Orchestrator — Design

**Date**: 2026-07-29
**Status**: Approved by user, pending implementation plan

## 1. Motivation

The user wants an orchestrator that runs a complete software project lifecycle
(idea → brief → PRD → architecture → epics/stories → code → QA → review →
stress → verdict → security review → quality gate → PR → release → handoff),
using the installed `bmad_v6` plugin as **design inspiration only** — harness
model (Guides/Sensors/Memory/Orchestration), the `.md` artifact chain, the
phase/gate structure, model-assignment discipline.

Explicit decision: **no runtime dependency on `bmad_v6` or any sibling plugin**
(`engineering`, `devtools`, `pr-workflow`, `purchase`). Those plugins are
installed via a marketplace and are out of the user's control — editing them
in place would be overwritten on update and would affect every other project
using the same install. Everything here is built from scratch, owned and
maintained by the user going forward.

## 2. Scope

- **In scope**: a new skill family (`/sdlc` + siblings) and a new agent roster
  (18 personas) that together drive a project from idea to release, with
  mandatory human gates and full `.md` persistence of every phase's output.
- **Out of scope**: modifying `bmad_v6` or any other installed plugin;
  reusing `engineering`/`devtools`/`pr-workflow`/`purchase` skills at runtime;
  git/version-control setup for the new orchestrator (explicitly deferred by
  the user — plain files for now).

## 3. Flow

Three entry points converge on a common trunk:

```
Greenfield (/sdlc):
  Intake (routing)
    → Analyst (Vision)                          → [GATE: approve Brief]
    → PM (Nick Fury)                             → [GATE: approve PRD]
    → Architect (Tony Stark) + grill-me → Manifest → [GATE: approve Architecture+Manifest]
    → per epic:
         per story: ScrumMaster (Cap) → Coder squad (TDD) → QA (Demolidor)
                     ↳ MINOR/NIT → Tuner (Gavião Arqueiro) → re-run QA
                     ↳ MAJOR/bug → back to Coder squad
                     → Reviewer (Odin) + Stress (Hulk) in parallel
                     ↳ MINOR/NIT (Odin) → Tuner (Gavião Arqueiro) → re-run Odin+Hulk
                     → Verdict (Doutor Estranho)
                     → [GATE: approve before commit]
    ┴─── common trunk ───┬
  → Security Review (Viúva Negra) → Quality Gate (Heimdall)
  → [GATE: before opening PR] → PR Review/creation (Homem-Aranha)
  → [GATE: before Release] → Release (Homem-Formiga)
  → Handoff (JARVIS)

Bug-fix (/sdlc-bug-fix):
  Bug Investigator (Wolverine) → Coder squad → QA (Demolidor) → Review (Odin)
    → joins common trunk at Security Review

Small task (/sdlc-task):
  Architect (light, Task Manifest only) → single story loop (same as above)
    → joins common trunk at Security Review
```

Human gates (all confirmed mandatory):

1. After Brief
2. After PRD
3. After Architecture + Manifest
4. Per epic/story, before committing code
5. Before opening a PR
6. Before Release

## 4. Skill contracts

Each skill's Input/Output/Boundary + Steps — same shape as `bmad_v6`'s own
`SKILL.md` files, adapted to this roster and the decisions above (isolated
sub-agent per phase, full `.md` persistence, gates per §3).

### `/sdlc` (entry — greenfield)

- **Input**: a project idea/feature description (ask if not provided).
- **Output**: the full artifact chain in `docs/sdlc/` (brief → PRD →
  architecture → manifest → per-story qa/review/stress/verdict →
  security-review → quality-gate → pr-review → release) plus a `PROGRESS.md`
  entry at every checkpoint.
- **Boundary**: orchestration only — never writes code, tests, or artifacts
  itself; every artifact comes from the sub-agent it dispatches. Never
  auto-advances past a gate in §3. Gavião Arqueiro (Tuner) is dispatched only
  for MINOR/NIT fixes flagged by QA or Review — it never reopens
  architecture, story, or test-authoring decisions.
- **Steps**:
  1. Intake — confirm idea/scope; skip to step 2 if `docs/sdlc/product-brief.md` already exists.
  2. Dispatch Vision (Analyst) → `product-brief.md` → **[GATE]**.
  3. Dispatch Nick Fury (PM) with the Brief → `PRD.md` → **[GATE]**.
  4. Dispatch Tony Stark (Architect) with Brief+PRD → `architecture.md`; run `/sdlc-grill-me` against it; produce `epic-manifest.md` → **[GATE]**.
  5. Epic loop (repeat per epic row in the manifest):
     - a. Dispatch Capitão América (Scrum Master) → one `story-{slug}.md` per task.
     - b. Per story, dispatch the Coder squad (Reed Richards core + Shuri or Professor X overlay, chosen by story tier) → TDD implementation.
     - c. Dispatch Demolidor (QA) → `qa.md`; route on signal:
       - approve → continue to (d);
       - MINOR/NIT → dispatch Gavião Arqueiro (Tuner) for a targeted fix, then re-run Demolidor;
       - MAJOR/bug report → back to the Coder squad (b), then re-run Demolidor;
       - CRITICAL/blocked → escalate → **[GATE]**.
     - d. On QA approval, dispatch Odin (Reviewer) and Hulk (Stress) in parallel → `review.md`, `stress.md`; if Odin's findings are MINOR/NIT only, dispatch Gavião Arqueiro (Tuner) and re-run Odin+Hulk; MAJOR/CRITICAL findings go back to the Coder squad (b).
     - e. Dispatch Doutor Estranho (Verdict) → `verdict.md` → **[GATE]** before commit.
  6. Dispatch Viúva Negra (`/sdlc-security-review`) and Heimdall (`/sdlc-quality-gate`) over the full diff.
  7. **[GATE]** → dispatch Homem-Aranha (`/sdlc-pr-review`) to open the PR.
  8. **[GATE]** → dispatch Homem-Formiga (`/sdlc-release`).
  9. Dispatch JARVIS (`/sdlc-handoff`) to close the session.

### `/sdlc-bug-fix` (entry — alternative)

- **Input**: bug description + reproduction steps (ask if not provided).
- **Output**: `docs/sdlc/bugs/{slug}/` with `investigation.md`, `qa.md`,
  `review.md`, plus a RED→GREEN test; then rejoins the common trunk.
- **Boundary**: never weakens/deletes/rewrites an existing test to fit the
  fix; never opens a PR or release itself — hands off to the trunk for that.
- **Steps**:
  1. Dispatch Wolverine (Bug Investigator) → `investigation.md` with a failing RED test.
  2. Dispatch the Coder squad → minimum fix, GREEN.
  3. Dispatch Demolidor (QA) → full gate run → `qa.md`; MINOR/NIT findings go to Gavião Arqueiro (Tuner) for a targeted fix and a re-run, MAJOR findings go back to step 2.
  4. Dispatch Odin (Reviewer) → `review.md`; same Tuner routing as step 3 for MINOR/NIT findings.
  5. Continue at `/sdlc` step 6 (Security Review onward).

### `/sdlc-task` (entry — alternative)

- **Input**: a single small task/feature (ask if not provided).
- **Output**: `docs/sdlc/task-manifest.md` plus one story's worth of
  `qa.md`/`review.md`/`stress.md`/`verdict.md`; then rejoins the common trunk.
- **Boundary**: skips Brief/PRD entirely; Architect runs in "light" mode
  (task-manifest only, no full `architecture.md` sections).
- **Steps**:
  1. Dispatch Tony Stark (Architect, light mode) → `task-manifest.md` → **[GATE]**.
  2. Single-story loop (same as `/sdlc` step 5, one story only) → **[GATE]** before commit.
  3. Continue at `/sdlc` step 6.

### `/sdlc-security-review` (standalone)

- **Input**: a diff, a set of files, or "the current branch" (ask if ambiguous).
- **Output**: `security-review.md` — OWASP Top 10 (+ OWASP LLM Top 10 when
  AI/LLM code is present) threat table and a verdict (CRITICAL found / none).
- **Boundary**: read-only — proposes fixes but never edits code itself.
- **Steps**: dispatch Viúva Negra → scan changed files → threat table → write `security-review.md`.

### `/sdlc-quality-gate` (standalone)

- **Input**: the current repo/stack (auto-detected) or an explicit file set.
- **Output**: `quality-gate.md` — format/lint/type/coverage/race/vuln
  results, pass/fail per gate.
- **Boundary**: runs sensors only — never modifies code to force a gate to pass.
- **Steps**: dispatch Heimdall → detect stack → run every gate for that stack → write `quality-gate.md`.

### `/sdlc-pr-review` (standalone)

- **Input**: a branch/diff ready for review, or an existing open PR.
- **Output**: `pr-review.md` plus, when creating, the PR title/description itself.
- **Boundary**: never merges; never pushes/opens without explicit user
  confirmation — satisfied automatically by the `/sdlc` step 7 gate when
  called from the trunk, asked directly when called standalone.
- **Steps**: dispatch Homem-Aranha → summarize the diff → draft PR body → confirm with user → open PR (or post review comments on an existing one).

### `/sdlc-release` (standalone)

- **Input**: the current state of the release branch.
- **Output**: `release.md` (changelog, version-bump rationale) plus IaC/CI
  artifacts if missing (Dockerfile, compose, CI config).
- **Boundary**: never tags/publishes without explicit user confirmation —
  satisfied automatically by the `/sdlc` step 8 gate when called from the
  trunk, asked directly when called standalone.
- **Steps**: dispatch Homem-Formiga → changelog → version bump → confirm → tag/publish → write `release.md`.

### `/sdlc-grill-me` (standalone)

- **Input**: a plan or design document (path or inline).
- **Output**: resolved gaps folded back into the document; open questions
  escalated to the human.
- **Boundary**: adversarial reading only — never edits the plan's decisions
  itself, only flags gaps for the owning agent or the human to resolve.
- **Steps**: read the target doc → generate the hardest questions a skeptical
  reviewer would ask → attempt to resolve each from context already
  available → escalate what can't be resolved.

### `/sdlc-handoff` (standalone)

- **Input**: none — reads the current `docs/sdlc/` + `PROGRESS.md` state.
- **Output**: an updated `PROGRESS.md` entry (Done / Failed / Current State /
  Next) plus a short recap to the user.
- **Boundary**: never starts new work — purely closes out the current state
  for the next session.
- **Steps**: dispatch JARVIS → read all artifacts touched this session → append `PROGRESS.md` entry → print recap.

## 5. Context isolation

Every phase — including Analyst/PM/Architect/ScrumMaster, not just Coder —
runs as an **isolated sub-agent** via the `Agent` tool. The orchestrator never
loads a persona's full working context inline; it receives back a compact
pointer/summary (e.g. `"Brief written to docs/sdlc/product-brief.md — 3 open
questions"`) and reads the `.md` artifact directly when it needs the content.
This keeps the orchestrator's own context small across a multi-session,
long-running pipeline.

## 6. Persistence

**Every** phase output is persisted to `.md`, not just the primary artifacts —
this includes QA, Review, Stress, and Verdict outputs, which in `bmad_v6`
today only appear in chat. Layout:

```
docs/sdlc/
  product-brief.md
  PRD.md
  architecture.md
  epic-manifest.md            (or task-manifest.md for /sdlc-task)
  epics/
    epic-1/
      stories/
        story-1.1.md
      story-1.1/
        qa.md
        review.md
        stress.md
        verdict.md
      security-review.md
      quality-gate.md
      pr-review.md
  release.md
  bugs/
    {slug}/
      investigation.md
      qa.md
      review.md

PROGRESS.md                    (repo root — same convention as bmad_v6:
                                 Done / Failed / Current State / Next,
                                 appended at each checkpoint, read at
                                 session start)
```

A new session can resume purely by reading these files — no dependency on
chat history.

## 7. Persona roster (Marvel, single universe, 18 roles, no repeats)

| Role                     | Persona                        | Why                                                                                                                                                |
| ------------------------ | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Analyst                  | Vision                         | synthesizes data/probabilities before acting                                                                                                       |
| PM                       | Nick Fury                      | "I'm assembling a team" — builds the initiative, sets priority                                                                                     |
| Architect                | Tony Stark                     | designs and builds the structure, blueprints                                                                                                       |
| Scrum Master             | Capitão América                | "Avengers, assemble" — leads, splits up the mission                                                                                                |
| Coder (core)             | Reed Richards / Mr. Fantástico | genius who builds and adapts to any problem                                                                                                        |
| Coder (backend overlay)  | Shuri                          | Wakandan tech genius — advanced infrastructure, out of the spotlight                                                                               |
| Coder (frontend overlay) | Professor X (Charles Xavier)   | builds Cerebro — an interface to understand anyone's mind; intelligence applied to the user, not visual flash                                      |
| QA                       | Demolidor                      | heightened senses catch what would go unnoticed                                                                                                    |
| Reviewer                 | Odin                           | All-Father's wise judgment, gives feedback (even to his own son)                                                                                   |
| Stress Tester            | Hulk                           | smashes the system to see what holds                                                                                                               |
| Tuner                    | Gavião Arqueiro                | "never misses" — precise, targeted fix                                                                                                             |
| Verdict                  | Doutor Estranho                | sees millions of futures, picks the winning path                                                                                                   |
| Security Review          | Viúva Negra                    | spy, always assumes she's being watched                                                                                                            |
| Quality Gate             | Heimdall                       | the literal guardian — nothing crosses without passing him                                                                                         |
| PR Review/creation       | Homem-Aranha                   | Marvel's most talkative — comments on everything                                                                                                   |
| DevOps + Release         | Homem-Formiga (Scott Lang)     | shrinks a whole building, carries it, deploys it full-size at the destination — closest literal metaphor to packaging an artifact and deploying it |
| Bug Investigator         | Wolverine                      | obsessively tracks one thing and doesn't let go                                                                                                    |
| Handoff                  | JARVIS                         | keeps the records, recaps, preps the next step                                                                                                     |

This mapping is a **display-name / prompt-identity concern only** — it lives
inside each agent's own `.md` file (system-prompt framing), not in the
slug/filename, which stays functional (see §8).

## 8. File layout

```
~/.claude/agents/
  sdlc-analyst.md            (Vision)
  sdlc-pm.md                 (Nick Fury)
  sdlc-architect.md          (Tony Stark)
  sdlc-scrum-master.md       (Capitão América)
  sdlc-coder.md              (Reed Richards — core)
  sdlc-coder-backend.md      (Shuri — overlay)
  sdlc-coder-frontend.md     (Professor X — overlay)
  sdlc-qa.md                 (Demolidor)
  sdlc-reviewer.md           (Odin)
  sdlc-stress.md             (Hulk)
  sdlc-tuner.md               (Gavião Arqueiro)
  sdlc-verdict.md             (Doutor Estranho)
  sdlc-security.md            (Viúva Negra)
  sdlc-quality-gate.md         (Heimdall)
  sdlc-pr.md                   (Homem-Aranha)
  sdlc-devops.md                (Homem-Formiga)
  sdlc-bug-investigator.md       (Wolverine)
  sdlc-handoff.md                 (JARVIS)

~/.claude/skills/
  sdlc/                        (entry — full greenfield flow)
    SKILL.md
    references/{phases,output-format,progress-file}.md
  sdlc-bug-fix/                 (entry — alternative)
    SKILL.md · references/dispatch.md
  sdlc-task/                     (entry — alternative)
    SKILL.md · references/loop.md
  sdlc-security-review/           (standalone)
  sdlc-quality-gate/                (standalone)
  sdlc-pr-review/                     (standalone)
  sdlc-release/                        (standalone)
  sdlc-grill-me/                        (standalone — plan/design stress-test)
  sdlc-handoff/                          (standalone)
```

Agents are **never invoked directly as slash commands** — same rule as
`bmad_v6`: they're loaded exclusively by a skill via `Agent(subagent_type:
"sdlc-...")`. Each `skills/sdlc*/` folder follows a simplified version of
`bmad_v6`'s shape: `SKILL.md` (contract + steps, §4 above) + `references/*.md`
(heavy detail loaded on demand, never pre-loaded). **Deviation from
`bmad_v6`**: we deliberately drop `skill.spec.yml` and `deps.toml`. Audit of
the installed plugin found these referenced by filename inside several
`SKILL.md` bodies (e.g. "Behavior contract: skill.spec.yml · dependency
ledger: deps.toml") but **absent from every actual skill directory on disk**
— dangling links, not a real, implemented format. Inventing a schema for
files the reference implementation itself never shipped would violate YAGNI;
the `SKILL.md` Contract/Rules section (§4) already carries the boundary and
forbids inline, which is all `skill.spec.yml` would have held anyway.

The `sdlc-` prefix on both agents and skills avoids name collisions with the
already-installed `bmad_v6` skills (`architecture`, `planning`, `bug-fix`,
etc.).

## 9. Model assignment

Adopted from `bmad_v6`'s validated table:

| Work                                       | Model    | Agents                                                                                                                                                              |
| ------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Read-only / quick lookups                  | `haiku`  | any ad-hoc Explore/mapping sub-agent spawned mid-phase                                                                                                              |
| Planning · design · reasoning · validation | `sonnet` | Vision, Nick Fury, Tony Stark, Capitão América, Demolidor, Odin, Hulk, Doutor Estranho, Viúva Negra, Heimdall, Homem-Aranha, Wolverine, JARVIS, orchestrator itself |
| Writing/changing code                      | `opus`   | Reed Richards, Shuri, Professor X, Gavião Arqueiro, Homem-Formiga                                                                                                   |

## 10. Versioning

No git repo for this project yet — plain files under `~/sdlc-orchestrator/`
(this design doc) and, once implemented, `~/.claude/agents/sdlc-*.md` +
`~/.claude/skills/sdlc*/`. Explicitly deferred by the user; revisit later if
they want history/rollback.

## 11. Open items for the implementation plan

- Exact agent `.md` prompt for each of the 18 personas — role contract +
  persona framing, modeled on `bmad_v6`'s `agents/*.md` shape (the
  Input/Output/Boundary is now fixed per skill in §4; each agent's own file
  still needs its persona voice/system-prompt written out).
- `references/*.md` content per skill (phase detail, dispatch templates,
  quality-gate command reference per stack, progress-file template).
- Whether `/sdlc-grill-me` needs its own dedicated logic or can be a thin
  "adversarial re-read" prompt reused by whichever agent invokes it.
- Exact routing/detection logic for "story tier" (which Coder overlay —
  Shuri vs. Professor X — a given story gets).
