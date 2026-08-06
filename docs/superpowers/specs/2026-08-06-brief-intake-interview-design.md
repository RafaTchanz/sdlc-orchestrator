# Adaptive Brief Intake (Gap-Interview Mode) — Design

**Date**: 2026-08-06
**Status**: Design — not yet implemented.

## 1. Motivation

`sdlc-analyst` writes `docs/sdlc/product-brief.md` from whatever idea text
the user hands it at Intake — a one-shot dispatch with no back-and-forth.
When the user already arrives with a fleshed-out idea this works well, but
when they arrive with only a rough thought, the agent's only recourse today
is to silently invent a best-effort framing and mark it `(assumption)`,
pushing all correction to the human gate after the Brief is already
written. This feature closes that gap: the orchestrator itself, before ever
dispatching `sdlc-analyst`, checks the idea for the handful of things only
the human can supply and asks about anything missing — turning a vague
one-liner into a Brief dispatch that needs far fewer downstream
assumptions, without asking anything of a user who already gave a complete
picture.

## 2. Scope

- **In scope**: an automatic gap-check run by the `/sdlc` orchestrator
  itself against the user's initial idea/context, during Step 1 (Intake);
  a bounded, one-question-at-a-time interview for any gap found; a
  reusable intake checklist file a user can pre-fill to skip the interview
  next time; folding the (possibly interview-enriched) idea into Step 2's
  existing `sdlc-analyst` dispatch prompt.
- **Out of scope**: any change to `sdlc-analyst.md`'s own contract or
  procedure — it keeps writing the Brief exactly as it does today, from
  whatever idea text it receives; any change to the Brief's own file
  format (`docs/sdlc/product-brief.md`'s sections are unchanged); a
  multi-round subagent dispatch loop (rejected — see §5); an explicit
  yes/no mode toggle at Intake (rejected — see §5); interviewing about
  Success Metrics, Competitive Scan, or Risks (these remain `sdlc-analyst`'s
  own research/judgment, unchanged).

## 3. Decisions and rationale

| Decision                                               | Choice                                                                                                                                                       | Why                                                                                                                                                                                                                                                                                                                            |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Where the interactivity happens                        | The `/sdlc` orchestrator's own turn (main session), never a dispatched subagent                                                                              | `Agent(subagent_type: ...)` dispatches run to completion and return a final result — they cannot pause mid-task to ask the human a question and wait for a reply. Every existing piece of Intake interactivity (the Slack and GitHub-Issue opt-in questions, `/sdlc-grill-me`) already lives at this same orchestrator level.  |
| Mode trigger                                           | Automatic gap-detection — no explicit yes/no toggle                                                                                                          | An explicit toggle would make a user re-confirm a mode even when their initial input is already complete, wasting a question for no benefit. Checking completeness directly is strictly better information than asking the user to self-assess it.                                                                             |
| Gap dimensions checked                                 | Exactly 4: **Problem Statement**, **Target Users & Jobs-to-be-Done**, **Scope**, **Constraints**                                                             | These are the only `product-brief.md` sections only the human can supply. Success Metrics, Competitive/Existing-Solution Scan, and Risks are already `sdlc-analyst`'s own job today (research via `WebSearch`, or explicit `(assumption)` marking) — interviewing about them would duplicate work the agent already does well. |
| Question format                                        | Plain conversational question, one dimension per message, fixed order (Problem → Users → Scope → Constraints)                                                | These are open-ended "what/who" questions about the idea's substance, not a choice among options — a multiple-choice UI doesn't fit. Fixed order keeps the interview predictable across sessions.                                                                                                                              |
| Loop cap                                               | 1 question + 1 follow-up per dimension (4 dimensions × 2 = 8 questions, worst case)                                                                          | A flat 3-round cap (this repo's existing QA/Review convention) was rejected as too tight for a genuinely vague idea; no cap at all risks an unbounded back-and-forth. Capping by the Brief's own finite dimension count is a structural bound, not an arbitrary number, while still bounding the worst case.                   |
| What happens to a gap still open after its cap         | Folded into the Step 2 dispatch prompt as an explicit `Assumptions still open` list                                                                          | Reuses `sdlc-analyst`'s existing contract instruction verbatim ("use your judgment to state your best-effort framing and mark it as an assumption rather than blocking") — no change to that agent's own procedure.                                                                                                            |
| Reusable checklist file                                | New file `docs/sdlc/references/intake-checklist.md`, pointed to (never forced) the first time an interview starts in a session                               | Lets a user who repeats this flow learn the shape of a complete submission and skip the interview entirely on a future run by pre-filling it themselves.                                                                                                                                                                       |
| Where the gap-check/interview mechanics are documented | New reference file `skills/sdlc/references/intake-interview.md`, linked from `SKILL.md`'s References section, same pattern as `phases.md`/`output-format.md` | `SKILL.md`'s Step 1 line is already dense with the two existing opt-in questions; the gap-check logic (4 dimension definitions + cap rule + fallback) is detailed enough to deserve its own file rather than growing that paragraph further.                                                                                   |
| Ordering within Step 1 (Intake)                        | idea/context received → gap-check + interview (if any) → existing Slack opt-in → existing GitHub-Issue opt-in → Step 2 dispatch                              | The interview is about the idea's own content, logically prior to and independent of the two feature opt-ins, which don't depend on how detailed the idea is.                                                                                                                                                                  |
| `sdlc-analyst.md` contract changes                     | None                                                                                                                                                         | Its existing procedure already handles ambiguity via best-effort framing + `(assumption)` marking; only the _input_ it receives gets richer.                                                                                                                                                                                   |

## 4. Components

### `skills/sdlc/SKILL.md` — Step 1 (Intake) changes

Insert one line into Step 1, immediately after the idea/context is
received and before the two existing opt-in questions:

> Before the opt-in questions below, check the received idea/context for
> gaps and, if any, run the bounded interview — exact mechanics in
> `references/intake-interview.md`.

Add `references/intake-interview.md` to the skill's `## References` list.

### New reference file: `skills/sdlc/references/intake-interview.md`

Documents, for the orchestrator to follow directly (no subagent involved):

1. **The 4 checked dimensions**, each with what counts as present vs. a gap:
   - **Problem Statement** — gap if the input names no broken/missing thing
     and no affected party.
   - **Target Users & Jobs-to-be-Done** — gap if no audience is named or
     clearly implied.
   - **Scope** — gap if there's no signal at all of what's in or out (even
     a rough boundary counts as present, not a gap).
   - **Constraints** — gap only if the domain obviously implies one (e.g.
     payments, health data, regulated industries) and none is mentioned;
     absence is not automatically a gap here, since most ideas genuinely
     have none worth stating yet.
2. **The interview procedure**: for each dimension flagged as a gap, in the
   fixed order above, ask one plain conversational question (not a
   multiple-choice menu). If the answer still leaves that dimension unclear,
   ask exactly one follow-up for that same dimension; otherwise move to the
   next flagged dimension. After the follow-up (or a clear first answer),
   the dimension is closed regardless of outcome — never loop back to it.
3. **The reusable checklist pointer**: the first time in a session that any
   gap triggers a question, mention
   `docs/sdlc/references/intake-checklist.md` once, e.g.: _"posso perguntar
   sobre isso agora, ou você pode preencher
   `docs/sdlc/references/intake-checklist.md` direto numa próxima vez para
   pular essa etapa."_ Never repeat this pointer later in the same session.
4. **The fallback**: any dimension still unclear after its cap is recorded
   verbatim (e.g. `"user did not specify target users"`) — never silently
   dropped, never re-asked.
5. **The enriched payload**: by the end of Step 1, the orchestrator holds,
   only in its own running session context (never written to a file, same
   rule as `channel_id`/`project_name` today): the original idea text, any
   interview answers, and any still-open assumptions.

### New reference file: `docs/sdlc/references/intake-checklist.md`

A static, human-facing template — not produced by any agent, authored once
by this feature (same category as `phases.md`/`output-format.md`
themselves: hand-written project documentation, not a pipeline artifact).
Contents: the same 4 dimensions as headings, each with the same one-line
prompt used in the interview, plus a closing note that Success Metrics,
Competitive Scan, and Risks don't need to be pre-filled — `sdlc-analyst`
handles those itself.

### `skills/sdlc/references/phases.md` — Step 2 dispatch prompt change

The existing Step 2 dispatch prompt gains one optional clause:

```

Agent(subagent_type: "sdlc-analyst", prompt: "Idea: {original input,
gap-filled with any interview answers}. Assumptions still open: {any
dimension left unresolved after its cap, phrased as 'user did not specify
X' — omit this sentence entirely if no gap went unresolved}. Existing repo
context: {summary if any}. Write docs/sdlc/product-brief.md per your
contract.")

```

## 5. Rejected alternatives

- **Multi-round `sdlc-analyst` dispatch loop** (agent returns `NEEDS_INPUT`,
  gets re-dispatched per question): rejected — subagents carry no memory
  between dispatches, so every round would need the full prior Q&A
  transcript re-pasted into the prompt, which this repo's own
  `subagent-driven-development` skill explicitly warns against; it also
  costs one subagent spin per question for no benefit over doing the same
  interview in the orchestrator's own turn.
- **Explicit yes/no "modo entrevista?" toggle at Intake**: rejected — asks
  the user to self-assess completeness when the orchestrator can just check
  directly; also risks running a fixed question list even when the initial
  input was already complete.
- **Flat 3-round cap** (matching the QA/Review loop convention exactly):
  rejected as too tight for a genuinely vague idea — see decision table.
- **No cap at all**: rejected — risks an unbounded back-and-forth on an
  idea that stays vague no matter how many questions are asked.
- **Interviewing about Success Metrics / Competitive Scan / Risks too**:
  rejected — these are already `sdlc-analyst`'s own job via research and
  explicit assumption-marking; interviewing about them would duplicate
  work the agent already does well.

## 6. Error handling

There is no dispatch, no external call, and no new subagent in this
feature — it is plain conversation inside the orchestrator's own turn, so
there is no new failure mode to handle. The only bounded outcome is the
per-dimension cap being reached, which is not an error: it is the designed
fallback into `sdlc-analyst`'s existing assumption-marking behavior.

## 7. Testing / implementation notes

No automated test suite covers agent/skill `.md` prose (same limitation as
the Slack-notify and GitHub-Issue features). Implementation should include
one manual verification task with two scenarios:

1. Start `/sdlc` with a deliberately sparse one-line idea (missing at least
   Target Users and Scope). Confirm: the interview asks about the right
   dimensions, in the fixed order, and only about the ones actually
   missing; a dimension where the tester keeps giving a vague answer stops
   after the one follow-up rather than looping; the checklist file is
   mentioned exactly once; the resulting `product-brief.md` reflects the
   interview answers, and any dimension the tester never resolved appears
   flagged as `(assumption)`.
2. Start `/sdlc` again with an already-thorough idea (problem, users,
   scope, and constraints all stated up front). Confirm: zero interview
   questions are asked, and Step 2 dispatches exactly as it does today.
