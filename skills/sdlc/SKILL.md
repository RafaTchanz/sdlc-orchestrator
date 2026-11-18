---
name: sdlc
description: Runs a complete software project lifecycle from a raw idea to release — Brief, PRD, Architecture, per-story TDD implementation with QA/Review/Stress/Verdict, Security Review, Quality Gate, PR, and Release, with mandatory human gates. Use when the user asks to build/create a new feature, epic, or greenfield project. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc — Greenfield Orchestrator

Drives a project from idea to release by dispatching one isolated sub-agent per lifecycle phase and persisting every phase's output to `.md`.

## Contract

- **Input**: a project idea/feature description — ask if not provided.
- **Output**: the full artifact chain under `docs/sdlc/` (see `references/output-format.md` for the exact file skeletons) plus a `PROGRESS.md` entry at every checkpoint.
- **Boundary**: orchestration only — this skill never writes code, tests, or artifacts itself; every artifact comes from the sub-agent it dispatches via `Agent(subagent_type: "sdlc-...")`. Never auto-advances past a `[GATE]`. `sdlc-tuner` is dispatched only for `NIT`/`MINOR` findings routed by QA or Review — it never reopens architecture, story, or test-authoring decisions. `sdlc-slack-notify` is dispatched at gates 1/2/3 only when the session opted in during Intake; it never gates the pipeline — any failure, whether reported by the agent itself or from the dispatch failing outright (e.g. the agent is unavailable in the running session), is logged as a non-fatal warning and the trunk proceeds to the gate regardless. `NIT`/`MINOR` and `MAJOR` routing loops are capped at 3 rounds each, tracked independently per audit (see Global Constraints and `references/phases.md`) — a loop still unresolved beyond that escalates to a human gate rather than looping indefinitely.

## Steps

Full phase-by-phase dispatch prompts and routing logic: `references/phases.md`. Summary:

1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). On a fresh start only, before the opt-in questions below, check the received idea/context for gaps and, if any, run the bounded interview — exact mechanics in `references/intake-interview.md`. Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id, e qual o nome do projeto (opcional, para identificar as notificações)?"_ Hold the answer (opted in yes/no, `channel_id` if yes, and `project_name` if given) only in this session's running context — never write it to any file. Also ask once per session, regardless of fresh-start or resume: _"Quer criar issues automaticamente no GitHub para cada story desta sessão? Se sim: qual(is) repositório(s) de destino (`owner/repo`; um por epic, se o projeto tocar mais de um), qual o GitHub Project board (`owner` + número), qual a Tribo, e qual a Squad? Se você ainda não informou um nome de projeto para as notificações no Slack, informe também aqui — essa resposta é compartilhada entre as duas features. Se o board usa o modelo Iniciativa → Épico → História, informe também (tudo opcional — o que faltar eu procuro no board): o repositório da tribo onde ficam iniciativas e épicos (`owner/repo`), a iniciativa e o(s) épico(s) desta entrega (número, link ou parte do título), e, se quiser planejar as datas, o roadmap dos épicos (duração de cada um e data de início, em texto ou o caminho de um documento)."_ Hold the answer (opted in yes/no, `repos` list, `project board` owner+number, `tribo`, `squad`, `project_name` if not already given, and — if given — `tribe_repo`, `iniciativa`, `épicos`, `roadmap`) only in this session's running context — never write it to any file. If the session opted in, run **Step 1a — Board planner** (`references/phases.md`) before step 2: it resolves the board's Iniciativa/Épicos (creating and date-planning the Épicos when a roadmap was given), asks the human once about anything ambiguous or not found, and holds the result as `epic_map` (+ `board_model` on/off) in this session's running context.
2. Dispatch `sdlc-analyst` → `product-brief.md` → if this session opted in, dispatch `sdlc-slack-notify` → **[GATE 1]**.
3. Dispatch `sdlc-pm` with the Brief → `PRD.md` → if this session opted in, dispatch `sdlc-slack-notify` → **[GATE 2]**.
4. Dispatch `sdlc-architect` with Brief+PRD → `architecture.md` + `epic-manifest.md`; run `/sdlc-grill-me` against `architecture.md` → if this session opted in, dispatch `sdlc-slack-notify` on `architecture.md` → **[GATE 3]**.
5. **Story loop** — full routing table in `references/phases.md`:
   - a. Batch: dispatch `sdlc-scrum-master` in parallel for every `pending` manifest row in this batch (default: all pending rows; or a human-named subset) → one story file per row. Present every story in the batch together → **[GATE 4]** before any implementation — the human approves all, a subset, or sends any back for rework. Only then, if this session opted into GitHub issue creation at Intake, dispatch `sdlc-github-issue` per epic touched, passed only the files approved at this gate — never before the gate, since an Issue is never edited once created (non-blocking — full dispatch shape in `references/phases.md`). When `board_model` is on, each epic's dispatch also carries its board Épico from `epic_map` (confirmed with the human at this same gate), so every story lands as a `História` sub-issue of it. Only approved rows proceed below.
   - For each approved row, in manifest order (each row is exactly one story):
     - b. Create the dedicated `story-{n.m}-work` branch, then Coder squad (`sdlc-coder` + tier overlay) → TDD implementation there.
     - c. `sdlc-qa` → route on signal (`APPROVE` → d; `NIT`/`MINOR` → `sdlc-tuner` then re-run `sdlc-qa`; `MAJOR` → back to (b); `CRITICAL`/`BLOCKED` → escalate, **[GATE]**).
     - d. `sdlc-reviewer` + `sdlc-stress` in parallel — unless this row's `Complexity` is `simple`, in which case skip `sdlc-stress` and dispatch `sdlc-reviewer` alone every round → route on the worse of whichever signal(s) ran (`APPROVE`/clean → e; `NIT`/`MINOR`-only on the worse → `sdlc-tuner` then re-run; `MAJOR`/`CRITICAL` on either → back to (b)).
     - e. `sdlc-verdict` → **[GATE 5]** before merge — on confirmation, merge `story-{n.m}-work` into the base branch and delete it.
6. Dispatch `sdlc-security` and `sdlc-quality-gate` over the full diff (can run in parallel — independent, read-only, no shared state).
7. **[GATE 6]** → dispatch `sdlc-pr` to open the PR.
8. **[GATE 7]** → dispatch `sdlc-devops` (release half).
9. Dispatch `sdlc-handoff` to close the session.

**Done when**: `sdlc-handoff` has appended the final `PROGRESS.md` entry for this run, whether the run ended at a gate awaiting the human or completed through release.

## References

- `references/phases.md` — exact dispatch prompts and full routing logic per phase.
- `references/output-format.md` — file skeletons for every artifact this skill's sub-agents produce.
- `references/progress-file.md` — `PROGRESS.md` entry template and the session-start read convention.
- `references/intake-interview.md` — gap-check dimensions, interview mechanics, and fallback rules for Step 1 Intake.
