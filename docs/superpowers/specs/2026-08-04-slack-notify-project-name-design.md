# Explicit Project Name for Slack Notifications — Design

**Date**: 2026-08-04
**Status**: Approved by user, pending implementation plan.

## 1. Motivation

`agents/sdlc-slack-notify.md` (shipped in PR #4) already tries to guess a
project/feature name for its Canvas title by scanning the artifact's
content, falling back to a plain artifact label ("Product Brief") when
nothing is evident. That heuristic is unreliable — a squad running `/sdlc`
across several repos into the same Slack channel has no dependable way to
tell which project a given notification is about.

## 2. Scope

- **In scope**: an optional, explicit `project_name` threaded from the
  Intake question through to `sdlc-slack-notify`'s Canvas title and channel
  message.
- **Out of scope**: any change to the current content-scanning fallback
  (kept as-is for the case the user leaves the name blank); any persisted
  storage of the name (same zero-on-disk-footprint rule as `channel_id`);
  any change to which gates notify (still only gates 1/2/3, per PR #4).

## 3. Decisions and rationale

| Decision                  | Choice                                                                                        | Why                                                                                                                                |
| ------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Where the name comes from | Asked once at Intake, bundled into the existing Slack opt-in question, alongside `channel_id` | Matches the existing session-scoped, never-persisted pattern for `channel_id` — no new question flow, no new persistence mechanism |
| Required or optional      | Optional — blank falls back to the existing content-scanning heuristic                        | Zero regression for sessions that don't care to name the project; never blocks or breaks an existing flow                          |
| Where it appears          | Both the Canvas title and the channel message                                                 | Maximizes clarity everywhere the squad sees the notification, per user's explicit choice over Canvas-only or message-only          |

## 4. Components

### `agents/sdlc-slack-notify.md` changes

- **Input**: gains one optional field, `project_name` — a short string
  handed to it directly in the dispatch prompt, exactly like `channel_id`.
  Never read from a file, never inferred by this agent when explicitly given.
- **Procedure step 2** (Canvas title): if `project_name` was given in the
  dispatch, the title is `"{Artifact label} — {project_name}"` directly —
  no content-scanning. If it was not given (omitted from the dispatch
  prompt), behavior is unchanged: fall back to scanning the artifact's
  content for an evident name, else the plain artifact label alone.
- **Procedure step 4** (channel message): if `project_name` was given, both
  message-body shapes (Canvas succeeded / Canvas failed) gain a
  `[{project_name}] ` prefix immediately before the `📋` line. If it was not
  given, both message bodies are byte-identical to today's PR #4 behavior.
- **Boundary**: unchanged — this is additive input, not a new failure mode
  or a new blocking condition.

### `skills/sdlc/SKILL.md` + `skills/sdlc/references/phases.md` changes

- **Step 1 (Intake)**: the existing session-scoped question gains a second,
  optional field. Updated question text: _"Quer notificar o squad no Slack
  a cada gate de planejamento nesta sessão? Se sim, qual o channel_id, e
  qual o nome do projeto (opcional, para identificar as notificações)?"_
  Both the opt-in answer and (if given) the `channel_id` and `project_name`
  live only in the running session's context — never written to disk, same
  rule as today.
- **Steps 2, 3, 4 (the three dispatch sites)**: each currently dispatches
  `sdlc-slack-notify` with a fixed-shape prompt ending in
  `Channel: {session channel_id}. Notify per your contract.` Each site now
  branches on whether the session provided a `project_name`:
  - If yes: the prompt gains a `Project: {session project_name}.` clause
    between `Channel:` and `Notify per your contract.`
  - If no: the prompt is emitted exactly as it is today — no `Project:`
    clause at all (not an empty one — the clause is absent).

No new persisted state, no new file format — same zero-on-disk-footprint
guarantee as PR #4.

## 5. Rejected alternatives

- **Infer automatically from the target repo** (directory name or git
  remote): rejected — a directory name is not reliably the project's real
  name, and this would add inference logic with its own failure mode for a
  problem an explicit, optional question solves more simply.
- **Infer with an override prompt**: rejected in favor of a plain question
  — the extra confirm/override step adds friction for a field that's
  already optional and cheap to type at Intake.
- **Making the name mandatory when opting into Slack**: rejected — would
  break existing sessions relying on the current fallback with no benefit
  proportional to the friction added.

## 6. Error handling

Unchanged from PR #4: `sdlc-slack-notify` never blocks the pipeline for any
reason, and a missing/blank `project_name` is not an error condition at
all — it's the expected default that reuses the existing fallback.

## 7. Testing / implementation notes

No automated test suite covers agent/skill `.md` prose (same limitation as
PR #4). Implementation should include one manual end-to-end run with a real
`project_name` against a test channel (reusing `C0BMZAD3PUJ`), confirming:
the Canvas title reads `"{label} — {project_name}"`, and the channel
message starts with `[{project_name}] 📋 ...`.
