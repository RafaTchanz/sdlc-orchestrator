# Adaptive Brief Intake (Gap-Interview Mode) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Before `/sdlc` ever dispatches `sdlc-analyst`, have the orchestrator itself check the user's idea/context for gaps in the 4 Brief sections only a human can supply, and run a bounded, one-question-at-a-time interview to fill any it finds — so `sdlc-analyst` receives a richer idea and needs far fewer `(assumption)` fallbacks.

**Architecture:** All new interactivity lives in the `/sdlc` orchestrator's own turn (`skills/sdlc/SKILL.md` Step 1), never in a dispatched sub-agent — a new reference file (`skills/sdlc/references/intake-interview.md`) documents the 4 checked dimensions, the fixed-order/1-follow-up-cap interview procedure, the one-time checklist pointer, and the fallback rule. A new static template (`docs/sdlc/references/intake-checklist.md`) lets a user pre-fill the same 4 dimensions to skip the interview on a future run. Step 2's existing `sdlc-analyst` dispatch prompt (`skills/sdlc/references/phases.md`) gains an optional `Assumptions still open` clause carrying any dimension left unresolved after its cap. `agents/sdlc-analyst.md` itself is unchanged — it already turns unresolved ambiguity into `(assumption)` markers.

**Tech Stack:** Markdown skill/reference definition files only (no application code, no test framework) — this repo's `/sdlc` skill and its `references/*.md` files are prose contracts read by Claude Code, not executable modules.

## Global Constraints

- No direct commits on `main` — all work happens on `feature/brief-intake-interview` (already created off up-to-date `main`).
- Branch names must be prefixed `feature/`, `hotfix/`, or `release/`.
- Commit messages must be Conventional Commits.
- No change to `agents/sdlc-analyst.md`'s own contract or procedure — it keeps writing the Brief exactly as it does today, from whatever idea text it receives; only the _input_ it receives gets richer (spec §2, §3).
- No change to `docs/sdlc/product-brief.md`'s own file format — its sections are unchanged (spec §2).
- All new interactivity happens in the `/sdlc` orchestrator's own turn (main session) — never inside a dispatched `Agent(subagent_type: ...)` call, since subagents cannot pause mid-task to ask the human a question and wait for a reply (spec §3).
- Exactly 4 gap dimensions are checked — Problem Statement, Target Users & Jobs-to-be-Done, Scope, Constraints — never Success Metrics, Competitive/Existing-Solution Scan, or Risks, which stay `sdlc-analyst`'s own research/judgment (spec §2, §3, §5).
- Loop cap: 1 question + 1 optional follow-up per flagged dimension; a dimension closes after its cap regardless of outcome and is never re-asked (spec §3).
- The enriched idea (original text + interview answers + any still-open assumptions) is held only in the session's own running context, never written to any file — same rule as the existing `channel_id`/`project_name` values (spec §4).
- The reusable-checklist pointer (`docs/sdlc/references/intake-checklist.md`) is mentioned at most once per session, the first time any gap triggers a question — never repeated (spec §4).
- No automated test suite covers these `.md` skill/reference files (existing repo convention, confirmed again in spec §7) — verification is manual/structural (`grep`), plus one final manual end-to-end task.

---

### Task 1: Wire the gap-check into `SKILL.md` Step 1 (Intake)

**Files:**

- Modify: `skills/sdlc/SKILL.md`

**Interfaces:**

- Consumes: nothing from other tasks.
- Produces: the pointer to `references/intake-interview.md` that Task 2's file fulfills, and the `## References` entry Task 2 relies on existing.

- [ ] **Step 1: Insert the gap-check pointer into the Step 1 (Intake) line**

Find this block (inside `## Steps`, item 1):

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id, e qual o nome do projeto (opcional, para identificar as notificações)?"_ Hold the answer (opted in yes/no, `channel_id` if yes, and `project_name` if given) only in this session's running context — never write it to any file. Also ask once per session, regardless of fresh-start or resume: _"Quer criar issues automaticamente no GitHub para cada story desta sessão? Se sim: qual(is) repositório(s) de destino (`owner/repo`; um por epic, se o projeto tocar mais de um), qual o GitHub Project board (`owner` + número), qual a Tribo, e qual a Squad? Se você ainda não informou um nome de projeto para as notificações no Slack, informe também aqui — essa resposta é compartilhada entre as duas features."_ Hold the answer (opted in yes/no, `repos` list, `project board` owner+number, `tribo`, `squad`, and `project_name` if not already given) only in this session's running context — never write it to any file.
```

Replace it with (only change: one new sentence inserted right after `(resume mid-pipeline).` and before `Regardless of fresh-start or resume, also ask...`):

```markdown
1. **Intake** — confirm idea/scope with the user; skip to step 2 if `docs/sdlc/product-brief.md` already exists (resume mid-pipeline). Before the opt-in questions below, check the received idea/context for gaps and, if any, run the bounded interview — exact mechanics in `references/intake-interview.md`. Regardless of fresh-start or resume, also ask once per session: _"Quer notificar o squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o channel_id, e qual o nome do projeto (opcional, para identificar as notificações)?"_ Hold the answer (opted in yes/no, `channel_id` if yes, and `project_name` if given) only in this session's running context — never write it to any file. Also ask once per session, regardless of fresh-start or resume: _"Quer criar issues automaticamente no GitHub para cada story desta sessão? Se sim: qual(is) repositório(s) de destino (`owner/repo`; um por epic, se o projeto tocar mais de um), qual o GitHub Project board (`owner` + número), qual a Tribo, e qual a Squad? Se você ainda não informou um nome de projeto para as notificações no Slack, informe também aqui — essa resposta é compartilhada entre as duas features."_ Hold the answer (opted in yes/no, `repos` list, `project board` owner+number, `tribo`, `squad`, and `project_name` if not already given) only in this session's running context — never write it to any file.
```

- [ ] **Step 2: Add `references/intake-interview.md` to the `## References` list**

Find this block:

```markdown
## References

- `references/phases.md` — exact dispatch prompts and full routing logic per phase.
- `references/output-format.md` — file skeletons for every artifact this skill's sub-agents produce.
- `references/progress-file.md` — `PROGRESS.md` entry template and the session-start read convention.
```

Replace it with:

```markdown
## References

- `references/phases.md` — exact dispatch prompts and full routing logic per phase.
- `references/output-format.md` — file skeletons for every artifact this skill's sub-agents produce.
- `references/progress-file.md` — `PROGRESS.md` entry template and the session-start read convention.
- `references/intake-interview.md` — gap-check dimensions, interview mechanics, and fallback rules for Step 1 Intake.
```

- [ ] **Step 3: Verify both edits landed correctly**

Run:

```bash
grep -n "intake-interview.md" skills/sdlc/SKILL.md
```

Expected: 2 matches — the new sentence in Step 1, and the new `## References` bullet.

```bash
grep -n "Before the opt-in questions below" skills/sdlc/SKILL.md
```

Expected: 1 match, positioned between `(resume mid-pipeline).` and `Regardless of fresh-start or resume, also ask...` in Step 1's line.

- [ ] **Step 4: Commit**

```bash
git add skills/sdlc/SKILL.md
git commit -m "feat(sdlc): point Step 1 Intake at the new gap-check interview reference"
```

---

### Task 2: Create `skills/sdlc/references/intake-interview.md`

**Files:**

- Create: `skills/sdlc/references/intake-interview.md`

**Interfaces:**

- Consumes: Task 1's pointer sentence in `SKILL.md` (this file is what that sentence links to).
- Produces: the enriched-payload contract (`{original input, gap-filled with any interview answers}` and `{any dimension left unresolved after its cap}`) that Task 4's `phases.md` dispatch-prompt change consumes; the checklist path (`docs/sdlc/references/intake-checklist.md`) that Task 3 creates.

- [ ] **Step 1: Write the file**

Create `skills/sdlc/references/intake-interview.md` with exactly this content:

```markdown
# Intake Interview — gap-check mechanics for Step 1

This file is read directly by the `/sdlc` orchestrator during Step 1
(Intake) — no sub-agent is dispatched for any of this. It runs once, right
after the idea/context is received and before the two existing opt-in
questions (Slack notifications, GitHub Issue creation).

## The 4 checked dimensions

Check the received idea/context against exactly these 4 dimensions, in
this fixed order. These are the only `docs/sdlc/product-brief.md` sections
only the human can supply — Success Metrics, Competitive/Existing-Solution
Scan, and Risks stay `sdlc-analyst`'s own job (research via `WebSearch`, or
explicit `(assumption)` marking) and are never interviewed about here.

1. **Problem Statement** — gap if the input names no broken/missing thing
   and no affected party.
2. **Target Users & Jobs-to-be-Done** — gap if no audience is named or
   clearly implied.
3. **Scope** — gap if there's no signal at all of what's in or out (even
   a rough boundary counts as present, not a gap).
4. **Constraints** — gap only if the domain obviously implies one (e.g.
   payments, health data, regulated industries) and none is mentioned;
   absence is not automatically a gap here, since most ideas genuinely
   have none worth stating yet.

## Interview procedure

For each dimension flagged as a gap, in the fixed order above:

1. Ask one plain conversational question (not a multiple-choice menu):
   - Problem Statement: _"O que está quebrado ou faltando hoje, e para
     quem?"_
   - Target Users & Jobs-to-be-Done: _"Quem vai usar isso, e qual tarefa
     essa pessoa está tentando resolver?"_
   - Scope: _"O que entra no escopo, e o que fica explicitamente de
     fora?"_
   - Constraints: _"Existe alguma restrição técnica, de negócio ou
     regulatória (residência de dados, acessibilidade, licenciamento,
     etc.) que essa solução precisa respeitar?"_
2. If the answer still leaves that dimension unclear, ask exactly one
   follow-up for that same dimension: _"Pode me dar um exemplo concreto
   ou detalhar isso em uma frase?"_ Otherwise move straight to the next
   flagged dimension.
3. After the follow-up (or a clear first answer), the dimension is closed
   regardless of outcome — never loop back to it.

A dimension not flagged as a gap in the check above is never asked about
at all.

## The reusable checklist pointer

The first time in this session that any gap triggers a question, mention
`docs/sdlc/references/intake-checklist.md` once: _"posso perguntar sobre
isso agora, ou você pode preencher
`docs/sdlc/references/intake-checklist.md` direto numa próxima vez para
pular essa etapa."_ Never repeat this pointer later in the same session,
even if more dimensions go on to get interviewed.

## The fallback

Any dimension still unclear after its cap (its one question plus its one
follow-up) is recorded verbatim, e.g. `"user did not specify target
users"` — never silently dropped, never re-asked.

## The enriched payload

By the end of Step 1, the orchestrator holds, only in its own running
session context (never written to any file, same rule as
`channel_id`/`project_name` today):

- the original idea/context text;
- any interview answers, folded into that idea;
- any dimensions still unresolved after their cap, as a list of
  `"user did not specify X"`-style strings.

This is exactly what Step 2's dispatch prompt (`references/phases.md`)
consumes as `{original input, gap-filled with any interview answers}` and
`{any dimension left unresolved after its cap}`.
```

- [ ] **Step 2: Verify the file's content**

Run:

```bash
grep -c "^## " skills/sdlc/references/intake-interview.md
```

Expected: `5` (the 5 top-level sections: dimensions, procedure, checklist pointer, fallback, enriched payload).

```bash
grep -n "Problem Statement\|Target Users\|^3\. \*\*Scope\*\*\|^4\. \*\*Constraints\*\*" skills/sdlc/references/intake-interview.md
```

Expected: all 4 dimension names present.

```bash
grep -n "intake-checklist.md" skills/sdlc/references/intake-interview.md
```

Expected: 2 matches — the checklist-pointer section's prose and its quoted Portuguese sentence.

- [ ] **Step 3: Commit**

```bash
git add skills/sdlc/references/intake-interview.md
git commit -m "feat(sdlc): add intake-interview reference with the 4-dimension gap-check"
```

---

### Task 3: Create `docs/sdlc/references/intake-checklist.md`

**Files:**

- Create: `docs/sdlc/references/intake-checklist.md`

**Interfaces:**

- Consumes: Task 2's exact Portuguese question wording (this file reuses the same one-line prompt per dimension).
- Produces: the file path `docs/sdlc/references/intake-checklist.md` that Task 2's checklist pointer already references.

- [ ] **Step 1: Write the file**

Create `docs/sdlc/references/intake-checklist.md` with exactly this content:

```markdown
# Intake Checklist — Brief Submission Template

Preencha o que puder antes de iniciar `/sdlc`, e cole o conteúdo abaixo
junto com sua ideia/contexto inicial. Nada aqui é obrigatório — o
orquestrador pergunta sobre qualquer coisa que faltar.

## Problem Statement

O que está quebrado ou faltando hoje, e para quem?

## Target Users & Jobs-to-be-Done

Quem vai usar isso, e qual tarefa essa pessoa está tentando resolver?

## Scope

O que entra no escopo, e o que fica explicitamente de fora?

## Constraints

Existe alguma restrição técnica, de negócio ou regulatória (residência de
dados, acessibilidade, licenciamento, etc.) que essa solução precisa
respeitar?

---

Você não precisa preencher Success Metrics, Competitive/Existing-Solution
Scan, ou Risks — o `sdlc-analyst` cuida disso sozinho, via pesquisa e
julgamento próprio.
```

- [ ] **Step 2: Verify the file's content**

Run:

```bash
grep -c "^## " docs/sdlc/references/intake-checklist.md
```

Expected: `4` (the 4 dimension headings).

```bash
grep -n "Success Metrics" docs/sdlc/references/intake-checklist.md
```

Expected: 1 match — the closing note.

- [ ] **Step 3: Commit**

```bash
git add docs/sdlc/references/intake-checklist.md
git commit -m "docs(sdlc): add reusable intake checklist template"
```

---

### Task 4: Extend the Step 2 `sdlc-analyst` dispatch prompt in `phases.md`

**Files:**

- Modify: `skills/sdlc/references/phases.md`

**Interfaces:**

- Consumes: Task 2's enriched-payload contract (`{original input, gap-filled with any interview answers}`, `{any dimension left unresolved after its cap}`).
- Produces: nothing further downstream — this is the last task that changes pipeline behavior.

- [ ] **Step 1: Replace the Step 2 dispatch block**

Find this block (the outer 4-backtick fence below is just this plan's way of quoting a block that itself contains a 3-backtick fence — the actual content to find in `phases.md` is everything between the outer fences):

````markdown
## Step 2 — Analyst

```

Agent(subagent_type: "sdlc-analyst", prompt: "Idea: {user's raw idea/feature description}. Existing repo context: {summary if any}. Write docs/sdlc/product-brief.md per your contract.")

```
````

Replace it with:

````markdown
## Step 2 — Analyst

```

Agent(subagent_type: "sdlc-analyst", prompt: "Idea: {original input, gap-filled with any interview answers}. Assumptions still open: {any dimension left unresolved after its cap, phrased as 'user did not specify X' — omit this sentence entirely if no gap went unresolved}. Existing repo context: {summary if any}. Write docs/sdlc/product-brief.md per your contract.")

```
````

- [ ] **Step 2: Verify the edit landed correctly**

Run:

```bash
grep -n "Assumptions still open" skills/sdlc/references/phases.md
```

Expected: 1 match, inside the Step 2 dispatch block.

```bash
grep -n "gap-filled with any interview answers" skills/sdlc/references/phases.md
```

Expected: 1 match, in the same block.

- [ ] **Step 3: Commit**

```bash
git add skills/sdlc/references/phases.md
git commit -m "feat(sdlc): fold interview answers and open assumptions into the Analyst dispatch prompt"
```

---

### Task 5: Manual end-to-end verification

**Files:**

- None (no repo changes — this task only exercises the behavior added in Tasks 1-4).

**Interfaces:**

- Consumes: the combined output of Tasks 1-4 (Step 1's gap-check + interview, the checklist pointer, and Step 2's enriched dispatch prompt).
- Produces: nothing downstream.

- [ ] **Step 1: Scenario 1 — deliberately sparse idea**

Start `/sdlc` with a one-line idea that omits Target Users and Scope on purpose, e.g.: `"quero um jeito de exportar relatórios"`.

Confirm, in order:

1. The orchestrator does **not** ask about Problem Statement (the idea does name a broken/missing thing — no way to export reports) or Constraints (no regulated domain implied).
2. It asks about Target Users & Jobs-to-be-Done first, then Scope, in that fixed order — using the exact question wording from `skills/sdlc/references/intake-interview.md`.
3. The first time either question is asked, it mentions `docs/sdlc/references/intake-checklist.md` exactly once — verify it is not mentioned again for the second dimension's question.
4. For one of the two dimensions, give a deliberately vague answer (e.g. "sei não, geral"). Confirm exactly one follow-up question is asked for that dimension, then the orchestrator moves on without looping a third time.
5. Leave that same dimension still vague after the follow-up. Confirm the resulting `docs/sdlc/product-brief.md` (after `sdlc-analyst` runs) reflects the other, clearly-answered dimension correctly, and flags the still-vague one as `(assumption)`.
6. Confirm the two existing opt-in questions (Slack notifications, GitHub Issue creation) are still asked afterward, unchanged.

- [ ] **Step 2: Scenario 2 — already-thorough idea**

Start a fresh `/sdlc` session (or a new idea in a fresh working directory) with a one-line idea that states problem, users, scope, and constraints up front, e.g.: `"Times de suporte perdem tempo buscando o histórico de chamados de um cliente espalhado em 3 sistemas; queremos uma tela única de busca por CPF/CNPJ que agregue chamados dos sistemas A, B e C, sem alterar nenhum desses sistemas de origem, respeitando LGPD (mascarar CPF/CNPJ para quem não tiver a permissão de atendimento)."`

Confirm:

1. Zero interview questions are asked — the gap-check finds all 4 dimensions already present.
2. The checklist pointer is never mentioned (no gap ever triggered).
3. Step 2 dispatches `sdlc-analyst` exactly as it does today — no `Assumptions still open` sentence appears in the resulting `product-brief.md`'s framing (i.e. no artifact of an unresolved gap).

No commit for this task — it produced no repo changes. If you want a record that this check passed, note it in the PR description when this branch is ready to merge.
