---
name: sdlc-pr-review
description: Summarizes a diff, drafts a PR description, and opens the PR (or reviews an existing one) after explicit confirmation. Use when the user asks to open or review a PR outside the full /sdlc pipeline. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-pr-review

## Contract

- **Input**: a branch/diff ready for review, or an existing open PR number — ask if ambiguous.
- **Output**: `pr-review.md`, plus the PR title/description when creating one.
- **Boundary**: never merges; never pushes/opens a PR without explicit user confirmation asked directly in this standalone context (unlike the trunk call, where `/sdlc`'s own gate 5 already covers it).

## Steps

1. Resolve the target: an explicit PR number, or the branch/diff to open a new PR from.
2. Pick the output path: `docs/sdlc/epics/epic-{n}/pr-review.md` if called from within an active `/sdlc` epic loop, otherwise `pr-review.md` at the repo root (or wherever the user specifies).
3. Dispatch:

```

Agent(subagent_type: "sdlc-pr", prompt: "Target: {PR number or branch/diff}. Write the report to {resolved path}. Standalone call — you must ask the dispatching context for explicit confirmation before opening/pushing anything; that confirmation has NOT already been given by a trunk gate.")

```

4. If the agent's response indicates it is waiting on confirmation, relay that request to the user verbatim and re-dispatch once they answer.
5. Report the returned hand-off line back to the user verbatim.

**Done when**: `pr-review.md` exists and, if the user confirmed opening/pushing, the PR is live at the reported URL.
