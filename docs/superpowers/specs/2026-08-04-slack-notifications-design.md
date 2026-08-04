# Slack Notifications for Planning Gates — Design

**Date**: 2026-08-04
**Status**: Approved by user, pending implementation plan

## 1. Motivation

`sdlc-orchestrator` today gates every planning phase (Brief, PRD, Architecture)
on approval from whoever is running `/sdlc` in their own interactive session.
When one person on a squad runs the pipeline, the rest of the squad has no
visibility into the artifacts unless they manually open the target repo and
read `docs/sdlc/*.md`.

The squad's coordinator wants the rest of the team notified in Slack when a
planning artifact is ready, so they can review it async — in parallel with,
not instead of, the coordinator's own approval at the gate.

## 2. Scope

- **In scope**: an opt-in Slack notification that fires at each of the 3
  planning gates (Brief, PRD, Architecture), posting a short summary plus a
  link to the full artifact.
- **Out of scope**: gating pipeline progress on any Slack reaction/response
  (notification only — the human gate stays exactly as it is today); notifying
  at any other gate (epic/story commit, PR, release) — those are per-story/
  high-frequency and would flood the channel; persisting the Slack channel
  choice across sessions (see §5 — explicitly rejected).

## 3. Decisions and rationale

| Decision                 | Choice                                                                                                           | Why                                                                                                                                                                                                                         |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Role of the notification | Notification-only, never gates the pipeline                                                                      | The interactive gate already exists; Slack is for team visibility, not a second approval mechanism                                                                                                                          |
| Where it lives           | Built into the `sdlc-orchestrator` plugin itself, opt-in                                                         | Every coordinator who installs the plugin gets it, without a private local hook                                                                                                                                             |
| Which gates              | Only the 3 planning gates (Brief/PRD/Architecture)                                                               | Per-story gates fire far more often — would flood the channel                                                                                                                                                               |
| Message content          | Short summary (the dispatched agent's own one-line hand-off) + link to a Slack Canvas holding the full artifact  | Tested live (§6) — the Slack MCP tools available to this plugin cannot attach a raw file; Canvas is the closest supported equivalent for "open and read the full doc in Slack"                                              |
| Channel targeting        | Asked at the start of every `/sdlc` session, answer kept in memory for that session only — never written to disk | The user reconsidered an earlier "ask once, persist" plan: different projects/repos may want different answers (notify in one, not in another), so a per-session ask fits better than any persisted config, local or global |

## 4. Components

### New agent: `agents/sdlc-slack-notify.md` — persona "Jarvis Jr."

- **Input**: the artifact's file path (`docs/sdlc/product-brief.md` |
  `PRD.md` | `architecture.md`), the one-line hand-off text from the agent
  that produced it, and the `channel_id` given by the user earlier in this
  session.
- **Output**: a standalone Slack Canvas containing the artifact's full
  content, plus a message posted to `channel_id` with the hand-off summary
  and a link to that Canvas.
- **Boundary**: never blocks the pipeline — any failure (invalid channel,
  Slack unreachable, Canvas creation error) is reported in its hand-off and
  otherwise swallowed; the `/sdlc` trunk logs it as a non-fatal warning and
  proceeds to the gate regardless. Never reads or writes any config file —
  the channel ID is handed to it directly by the dispatching skill. Never
  invoked directly — dispatched only by the `/sdlc` trunk right when a
  planning gate is presented.
- **Tools**: `Read`, `mcp__plugin_slack_slack__slack_create_canvas`,
  `mcp__plugin_slack_slack__slack_send_message`.

### Trunk changes: `skills/sdlc/SKILL.md` + `skills/sdlc/references/phases.md`

- **Step 1 (Intake)**: unconditionally, at the start of every session
  (whether starting fresh or resuming mid-pipeline), ask: _"Quer notificar o
  squad no Slack a cada gate de planejamento nesta sessão? Se sim, qual o
  channel_id?"_ Hold the answer only in the running session's context.
- **Steps 2, 3, 4 (Brief/PRD/Architecture)**: at the moment each artifact is
  presented for its gate — not after the human approves it, so the squad
  reviews concurrently with the coordinator — if the session's answer was
  yes, dispatch `sdlc-slack-notify` with that artifact's path, its
  producing agent's hand-off line, and the session's `channel_id`. If the
  session's answer was no, skip the dispatch entirely; no Slack tool is ever
  invoked.

No new persisted state, no new file format, no `.gitignore` change needed —
this feature has zero on-disk footprint.

## 5. Rejected alternatives

- **Channel-scoped Canvas via `conversations.canvases.create`**: confirmed
  to exist (§6) and would give real Slack-enforced channel isolation, but (a)
  is not exposed by the Slack MCP tools this plugin has access to — it would
  require the squad to mint and configure a separate bot token with
  `canvases:write`, and (b) only allows one channel canvas per channel ever,
  which doesn't fit "one artifact, one Canvas" cleanly. Rejected in favor of
  the simpler standalone-Canvas approach already validated live.
- **Direct Slack calls inside the `/sdlc` trunk skill**: rejected — breaks
  the repo's existing convention that the trunk only orchestrates and never
  performs side effects itself; every action is a dispatched, narrowly
  scoped sub-agent.
- **Persisted channel config** (per-repo file or global
  `~/.claude/sdlc-orchestrator/slack-config.json`): both were designed and
  then explicitly rejected by the user — a squad may run `/sdlc` across
  multiple projects with different notification preferences per project, so
  no persistence outlives a single session.
- **Gating the pipeline on a Slack reaction/response**: rejected early —
  adds a second approval mechanism redundant with the existing interactive
  gate, and couples pipeline progress to Slack's availability.

## 6. Validation performed during design

Live-tested against a real channel (`C0BMZAD3PUJ`) using the Slack plugin's
connected MCP tools:

- `slack_create_canvas` (title + markdown content, no channel parameter)
  succeeded, returning a standalone canvas URL
  (`https://dafiti-tech.slack.com/docs/TBHMCN197/F0BMTL376HZ`) — confirming
  this tool maps to the Web API's `canvases.create` (user-scoped, not
  channel-scoped).
- `slack_send_message` to `C0BMZAD3PUJ` with a summary + the Canvas link
  succeeded on the first attempt.
- Checked the Slack Web API reference (`docs.slack.dev`) for a
  channel-scoped alternative: `conversations.canvases.create` exists,
  requires a bot/user token with `canvases:write` (not reachable via this
  plugin's MCP tool surface), and permits only one channel canvas per
  channel (`channel_canvas_already_exists` on a second call) — this ruled
  it out per §5.

## 7. Error handling

- User answers "no" to the session's Slack prompt: `sdlc-slack-notify` is
  never dispatched for the rest of that session.
- `sdlc-slack-notify` fails for any reason (bad channel ID, Slack API error,
  workspace without Canvas enabled): it reports the failure in its one-line
  hand-off; the trunk records it as a non-fatal note (e.g. in the session's
  own narration, not a pipeline-blocking error) and proceeds straight to
  presenting the gate to the human as normal.

## 8. Testing / implementation notes

- Verify at implementation time whether this plugin's subagent `tools:`
  frontmatter can list MCP tool names
  (`mcp__plugin_slack_slack__slack_create_canvas`, `..._slack_send_message`)
  the same way it lists built-in tools (`Read`, `Write`, ...) — no existing
  agent in this repo does this yet, so it needs a live check, not an
  assumption.
- No automated test can cover the real Slack call (external system) — the
  implementation plan should include at least one manual end-to-end run
  against a real test channel, mirroring §6's validation.
