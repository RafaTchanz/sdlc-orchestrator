---
name: sdlc-release
description: Generates missing infrastructure-as-code artifacts and cuts a release (changelog, semver bump, tag, publish) after explicit confirmation. Use when the user asks to cut/ship a release outside the full /sdlc pipeline. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-release

## Contract

- **Input**: the current state of the release branch.
- **Output**: `docs/sdlc/release.md` (changelog, version-bump rationale) plus any missing IaC/CI artifacts (Dockerfile, compose, CI config).
- **Boundary**: never tags/publishes without explicit user confirmation asked directly in this standalone context (unlike the trunk call, where `/sdlc`'s own gate 6 already covers it).

## Steps

1. Confirm the release branch/target with the user if not already clear from context.
2. Dispatch:

```

Agent(subagent_type: "sdlc-devops", prompt: "Release branch: {target}. Standalone call — you must ask the dispatching context for explicit confirmation before any git tag/publish step; that confirmation has NOT already been given by a trunk gate.")

```

3. If the agent's response indicates it is waiting on confirmation, relay that request to the user verbatim and re-dispatch once they answer.
4. Report the returned hand-off line back to the user verbatim.

**Done when**: `docs/sdlc/release.md` exists and, if the user confirmed, the release is tagged/published.
