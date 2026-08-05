# Automatic GitHub Issue Creation per Story — Design

**Date**: 2026-08-05
**Status**: Design — not yet implemented.

## 1. Motivation

`/sdlc` already produces one self-contained `story-{n.m}.md` file per story
(`sdlc-scrum-master`), but nothing surfaces that work as a trackable unit
outside the orchestrator's own `docs/sdlc/` tree. Squads that manage their
board and sprint tracking in GitHub Issues/Projects today have to do that
by hand, re-typing story content that already exists. This feature closes
that gap: when a session opts in, one GitHub Issue is created per story,
added to the squad's GitHub Project board, and tagged with the fields that
board already uses to organize work (`Epic`, `Projeto`).

## 2. Scope

- **In scope**: a new Intake opt-in; a new `Repo` column on
  `epic-manifest.md`; a story-boundary rule extension on `sdlc-scrum-master`;
  a new dedicated agent that creates one Issue per story, adds it to a
  Project board, sets two custom fields, and records the Issue URL back
  onto the story file; non-fatal failure handling; idempotent behavior on
  `/sdlc` resume.
- **Out of scope**: any automatic Issue lifecycle management after creation
  (no auto-close/auto-move on Verdict READY — that stays a manual,
  human-managed board activity); any Ta[REDACTED]/sub-issue hierarchy (one Issue
  per Story only, matching the granularity QA/Review/Stress/Verdict already
  use); switching the access mechanism to the GitHub MCP server (unavailable
  in this environment — see §3); any change to how Slack notifications work
  (this feature shares one Intake value — `project_name` — with that
  existing feature, and nothing else).

## 3. Decisions and rationale

| Decision                                                       | Choice                                                                                                                                              | Why                                                                                                                                                                                                                                                                                                                                                                                                                     |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Access mechanism                                               | `gh` CLI                                                                                                                                            | Reuses each user's own pre-existing, self-service-refreshable auth — the right fit for an orchestrator used company-wide across tribes with different repo/board access. Validated end-to-end against a real Project board this session. The GitHub MCP server is unavailable (TLS/CA cert failure in this environment); the contract below is written mechanism-agnostic so a future swap wouldn't require a redesign. |
| Issue granularity                                              | One Issue per Story (`story-{n.m}.md`)                                                                                                              | Matches the granularity already used by the QA/Review/Stress/Verdict loop — no new granularity concept to learn.                                                                                                                                                                                                                                                                                                        |
| Who dispatches creation                                        | A new, dedicated agent, same architectural pattern as `sdlc-slack-notify` — independent, conditionally dispatched only if opted into at Intake      | Keeps `sdlc-scrum-master`'s contract focused on splitting stories; issue creation is a separate concern with its own failure mode and its own optionality.                                                                                                                                                                                                                                                              |
| When it's dispatched                                           | Once per epic, immediately after 5a (`sdlc-scrum-master` writes that epic's story files), before 5b (Coder squad)                                   | The earliest point at which every story file for the epic exists and is stable; creating Issues before implementation starts means the squad can track "in progress" against a real Issue from the start.                                                                                                                                                                                                               |
| Failure handling                                               | Logged as a non-fatal warning; never blocks the pipeline — and a single story's failure doesn't stop the rest of the batch                          | Exactly matches `sdlc-slack-notify`'s existing precedent; issue tracking is a convenience layer, not a pipeline gate.                                                                                                                                                                                                                                                                                                   |
| Issue title                                                    | `[{Tribo}][{Squad}] {story title}`                                                                                                                  | Mirrors the existing `[project_name]` Slack message-prefix convention; Tribo/Squad are the two pieces of context a company-wide, multi-tribe board needs to disambiguate at a glance.                                                                                                                                                                                                                                   |
| Issue body                                                     | Full story content (Title, Context, Acceptance Criteria) copied in, not a reference to the story file's path                                        | `docs/sdlc/` lives in the orchestrator's own working checkout, not necessarily inside the target repo where the Issue lives — a bare path reference would be unreadable to anyone without access to that separate tree.                                                                                                                                                                                                 |
| `Tribo`/`Squad` source                                         | Asked explicitly and separately at Intake                                                                                                           | Consistent with the "always ask, never infer" precedent already set for repo targeting; a Project board's title is not a reliable stand-in for the squad's actual name.                                                                                                                                                                                                                                                 |
| `Projeto` field value                                          | Same value as the existing Slack `project_name`                                                                                                     | One shared Intake answer feeds both features whenever either is active — no duplicate question, no second concept to keep in sync.                                                                                                                                                                                                                                                                                      |
| Missing `Projeto` option on the board                          | Auto-created via a `gh api graphql` mutation before selecting it                                                                                    | A single-select field's option list is board-specific and will not already contain every project name a company-wide orchestrator might see; creating on demand keeps the feature working on any board without manual pre-setup.                                                                                                                                                                                        |
| Field/option IDs (`Epic`, `Projeto`, and the `Projeto` option) | Resolved at runtime via `gh project field-list` (and created on demand for the option), never hardcoded                                             | This orchestrator is shared company-wide across tribes and boards; the specific field IDs validated during this session's testing belong to one board only and must never appear as literals in the agent's contract.                                                                                                                                                                                                   |
| Traceability of the created Issue                              | Appended to the story file itself as a `**GitHub Issue**: {url}` line                                                                               | The manifest's granularity is per-Task while Issues are per-Story — no clean 1:1 mapping onto a new `epic-manifest.md` column: the story file is the one artifact already at the right granularity.                                                                                                                                                                                                                     |
| Idempotency on `/sdlc` resume                                  | Before creating, read the story file and check for an existing `**GitHub Issue**:` line; if present, skip                                           | Prevents duplicate Issues when a session resumes mid-epic — the story file itself is the durable record of "already done."                                                                                                                                                                                                                                                                                              |
| Issue lifecycle after creation                                 | Out of scope                                                                                                                                        | No automatic close/update when the story reaches Verdict READY (5e) — kept a manual, human-managed board activity, at least for this iteration.                                                                                                                                                                                                                                                                         |
| Undeclared repo dependency discovered mid-architecture         | Logged as an item in `architecture.md`'s Open Questions for human review at **[GATE 3]** — never auto-added to the manifest                         | Matches this codebase's existing pattern of routing anything uncertain through a human gate rather than silently expanding scope.                                                                                                                                                                                                                                                                                       |
| Story-splitting boundary                                       | `sdlc-scrum-master`'s existing "split if >1 day or spans >1 Tier" rule is extended to also split on `Repo` — a story never spans more than one repo | A GitHub Issue and its board item belong to one repo; a story that touched two repos would need two Issues, breaking the one-Issue-per-story granularity decision above.                                                                                                                                                                                                                                                |

## 4. Components

### `skills/sdlc/SKILL.md` — Step 1 (Intake) changes

A second, independent opt-in question, asked once per session alongside the
existing Slack opt-in (regardless of fresh-start or resume):

> _"Quer criar issues automaticamente no GitHub para cada story desta sessão?
> Se sim: qual(is) repositório(s) de destino (`owner/repo`; um por epic, se o
> projeto tocar mais de um), qual o GitHub Project board (`owner` +
> número), qual a Tribo, e qual a Squad? Se você ainda não informou um nome
> de projeto para as notificações no Slack, informe também aqui — essa
> resposta é compartilhada entre as duas features."_

Held only in this session's running context — `repos` (list), `project
board` (owner + number), `tribo`, `squad`, and (if not already given for
Slack) `project_name` — never written to any file, same rule as
`channel_id`/`project_name` today.

### `agents/sdlc-architect.md` changes

- `epic-manifest.md`'s table gains a `Repo` column, same per-row
  granularity as `Tier`: `Epic | Stories | Tier | Repo | Language/Stack |
Depends-on | Status`. Populated from the session's Intake-declared repo
  list.
- If investigation surfaces a repo dependency the user didn't declare at
  Intake, it is logged as an Open Question in `architecture.md` for human
  review at **[GATE 3]** — never silently added to the manifest.

### `agents/sdlc-scrum-master.md` changes

- Boundary rule extended: a story that spans more than one manifest `Repo`
  must be split further, on top of the existing >1 day / >1 `Tier` triggers.

### New agent: `agents/sdlc-github-issue.md`

Same architectural shape as `sdlc-slack-notify` (Jarvis Jr.) — persona
**Falcão — GitHub Issue**, a herald that runs one small errand per epic and
reports back without ever holding up the mission.

- **Input**: this epic's story directory
  (`docs/sdlc/epics/epic-{n}/stories/`), the target repo (`owner/repo`, from
  this epic's manifest `Repo` value), the GitHub Project board (`owner` +
  number), `tribo`, `squad`, and the session's `project_name` (may be
  absent).
- **Output**: for every story file in that directory without an existing
  `**GitHub Issue**:` line — one GitHub Issue created in the target repo,
  added as an item on the Project board, with that board's `Epic` and
  `Projeto` custom fields set; the created Issue's URL appended to its
  story file.
- **Boundary**: never blocks the pipeline. A single story's failure at any
  step is caught, logged as a non-fatal warning naming that story, and
  processing continues with the next story in the directory. Never
  invoked directly — only dispatched by the `/sdlc` trunk right after 5a,
  and only when the session opted in at Intake. Never closes, edits, or
  deletes an existing Issue. Never hardcodes a field ID, option ID, or
  board ID — every one is resolved at runtime via `gh project field-list`
  against the board given in this dispatch.

**Procedure**:

1. `Glob` `docs/sdlc/epics/epic-{n}/stories/story-*.md`.
2. For each story file, in order:
   1. `Read` it. If it already contains a line starting with `**GitHub
Issue**:`, skip this story entirely and move to the next.
   2. Build the Issue title: `[{tribo}][{squad}] {story Title}`.
   3. Build the Issue body from the story's **Title**, **Context**, and
      **Acceptance Criteria** sections, copied verbatim.
   4. `gh issue create --repo {target repo} --title "{title}" --body
"{body}"`. On failure: log a warning for this story (`"Issue creation
failed for story-{n.m}: {error}"`) and move to the next story — do
      not attempt steps 2v–2viii for this story.
   5. `gh project item-add {board owner}/{board number} --url {issue URL
from step iv}`, capturing the returned item ID. On failure: log a
      warning noting the Issue was created but not added to the board
      (`"Issue {url} created but could not be added to the board: {error}"`),
      append the URL to the story file anyway (step viii), then move to the
      next story — skip field-setting (2vi–2vii), there is no item ID to
      edit.
   6. `gh project field-list {board owner}/{board number}` to resolve the
      `Epic` and `Projeto` field IDs, and `Projeto`'s current option list.
      If no existing `Projeto` option matches `project_name` (and
      `project_name` was given), create one first via a `gh api graphql`
      mutation, then use its returned option ID.
   7. `gh project item-edit --id {item ID} --field-id {Epic field ID}
--project-id {board ID} --text "{this epic's identifier/title}"`, and
      — only if `project_name` was given — `gh project item-edit --id
{item ID} --field-id {Projeto field ID} --project-id {board ID}
--single-select-option-id {option ID}`. On failure of either: log a
      warning naming which field failed and continue — field-setting is
      best-effort, never a reason to skip step viii.
   8. Append a blank line and `**GitHub Issue**: {issue URL}` to the end of
      the story file.
3. Hand off one line: `"{created}/{total} issues created for epic-{n}
({warning count} warning(s))."` — or, if every story in the directory was
   already skipped as duplicates, `"epic-{n}: all N stories already had
GitHub Issues — nothing created."`

### `skills/sdlc/references/phases.md` — Step 5 changes

Immediately after 5a's dispatch block and before 5b begins:

```

If this session opted into GitHub issue creation during Intake, dispatch
`sdlc-github-issue` now, once for this epic:

Agent(subagent_type: "sdlc-github-issue", prompt: "Epic {n} story directory:
docs/sdlc/epics/epic-{n}/stories/. Target repo: {this epic's manifest Repo
value}. Board: {session board owner}/{session board number}. Tribo: {session
tribo}. Squad: {session squad}. Project: {session project_name, if given}.
Create issues per your contract.")

Read its hand-off; note any warnings as non-fatal — never block on it, and
never delay 5b waiting on it.

```

## 5. Rejected alternatives

- **Dispatch once per story instead of once per epic**: rejected — would
  multiply Agent dispatches by story count for no benefit, since the agent
  already loops over every story file internally; batching at the epic
  level is the natural point where 5a hands off a stable, complete set of
  story files.
- **One Issue per Task/manifest row instead of per Story**: rejected —
  breaks from the granularity every other loop (QA/Review/Stress/Verdict)
  already uses, and a manifest row can expand into multiple stories that
  deserve independent tracking.
- **Reference the story file path in the Issue body instead of copying
  content**: rejected — `docs/sdlc/` is the orchestrator's own working tree
  and is not reachable from the target repo where the Issue lives.
- **Infer Tribo/Squad from the Project board's title**: rejected — same
  "always ask, never infer" precedent already applied to repo targeting;
  board titles are not a reliable source for either value.
- **Store the created Issue URL as a new `epic-manifest.md` column**:
  rejected — the manifest is per-Task/per-Epic granularity, Issues are
  per-Story; there's no clean 1:1 row to attach the URL to.
- **Automate Issue lifecycle (close/move on Verdict READY)**: rejected for
  this iteration — adds a second write path into the board with its own
  failure modes, for a convenience the team can just as easily do by hand
  today; can be revisited as a separate, later feature.

## 6. Error handling

Every external call (`gh issue create`, `gh project item-add`, `gh project
field-list`, `gh api graphql` for option creation, `gh project item-edit`)
is caught independently. A failure at any step for a given story is logged
as a non-fatal warning naming that story and that step, and the agent moves
on — to the next step for that story where the failure doesn't block later
steps (e.g. Issue created but board-add failed still gets its URL appended
to the story file), or to the next story entirely where it does (e.g. Issue
creation itself failed). The agent never retries a failed call, never
raises, and never causes the `/sdlc` trunk to stop — exactly the same
contract `sdlc-slack-notify` already has at gates 1/2/3.

## 7. Testing / implementation notes

No automated test suite covers agent/skill `.md` prose (same limitation as
the Slack-notify feature). Implementation should include one manual
end-to-end run against a real repo and a real Project board (reusing the
board validated this session), confirming: an Issue is created with the
correct `[Tribo][Squad]` title and full story body; it appears as an item
on the board with `Epic` and `Projeto` set correctly (creating the
`Projeto` option first if it doesn't yet exist); the story file gains the
`**GitHub Issue**:` line; and re-running the same dispatch against the same
story directory creates zero duplicate Issues.
