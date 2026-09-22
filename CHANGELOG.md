# Changelog

## 1.1.0 — 2026-09-22

### Added

- `/sdlc` story loop now writes every pending story in a batch (or a human-named subset) in parallel via `sdlc-scrum-master`, presents the whole batch together, and gates it as GATE 4 before any Coder-squad dispatch begins — previously implementation started right after a single story was written, with no checkpoint in between.
- `sdlc-github-issue` dispatch moves to after GATE 4 and now takes an explicit approved-file list instead of scanning an epic's story directory, so a story sent back for rework never gets a stale GitHub Issue (Issues are never edited once created).
- `/sdlc-task` gets the same single-story validation gate before its Coder dispatch, for consistency with `/sdlc`.

### Fixed

- Renumbered every downstream gate reference after inserting the new batch gate: per-story merge is now GATE 5, PR is GATE 6, release is GATE 7 — updated across `phases.md`, `SKILL.md` summaries, `sdlc-pr.md`, `sdlc-devops.md`, `sdlc-pr-review/SKILL.md`, and `sdlc-release/SKILL.md`, which use the gate number to decide whether the trunk already confirmed before dispatch.

### Breaking

None.
