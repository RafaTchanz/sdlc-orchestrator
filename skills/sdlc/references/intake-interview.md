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
`skills/sdlc/references/intake-checklist.md` once: _"posso perguntar sobre
isso agora, ou você pode preencher
`skills/sdlc/references/intake-checklist.md` direto numa próxima vez para
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
