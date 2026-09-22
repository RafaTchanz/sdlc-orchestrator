---
name: sdlc-bug-fix
description: Investigates a reported bug, writes a failing RED test that reproduces it, fixes it via TDD, and audits the fix — then rejoins the standard /sdlc trunk at Security Review. Use when the user reports a bug, crash, regression, or unexpected behavior. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-bug-fix — Bug-fix Entry Point

## Contract

- **Input**: bug description + reproduction steps — ask if not provided.
- **Output**: `docs/sdlc/bugs/{slug}/` with `investigation.md`, `qa.md`, `review.md`, `verdict.md` — plus `stress.md` unless this bug's `Complexity` is `simple` — and a RED→GREEN test in the target repo; then rejoins the common trunk.
- **Boundary**: never weakens/deletes/rewrites an existing test to fit the fix. Never opens a PR or cuts a release itself — hands off to the trunk (`/sdlc` step 6 onward) for that. Never auto-advances past a `[GATE]`.

## Steps

Exact dispatch prompts: `references/dispatch.md`. Summary:

1. Derive `{slug}` (kebab-case from the bug description). Create a dedicated branch `bugfix-{slug}-work` off the base branch — every step below operates on it, never on the base branch. Dispatch `sdlc-bug-investigator` → `docs/sdlc/bugs/{slug}/investigation.md` + a committed failing RED test.
2. Dispatch the Coder squad (`sdlc-coder` + tier overlay, chosen by which part of the codebase the bug lives in) → minimum fix, GREEN.
3. Dispatch `sdlc-qa` → full gate run → `docs/sdlc/bugs/{slug}/qa.md`. `NIT`/`MINOR` → `sdlc-tuner` then re-run `sdlc-qa`. `MAJOR` → back to step 2. `CRITICAL`/`BLOCKED` → escalate, **[GATE]**.
4. Dispatch `sdlc-reviewer` and `sdlc-stress` in parallel → `docs/sdlc/bugs/{slug}/review.md` + `stress.md` — unless this bug's `Complexity` is `simple`, in which case dispatch `sdlc-reviewer` alone (no `sdlc-stress`, any round). Tuner routing on the worse of whichever signal(s) ran, same as `/sdlc` step 5d: `NIT`/`MINOR` → `sdlc-tuner` then re-run; `MAJOR`/`CRITICAL` → back to step 2.
5. Dispatch `sdlc-verdict` → aggregate `qa.md`/`review.md`, plus `stress.md` unless skipped, → `docs/sdlc/bugs/{slug}/verdict.md`. **[GATE]** before merge. On confirmation, merge `bugfix-{slug}-work` into the base branch and delete it. On rejection/rework, stay on the branch — no merge — and loop back to whichever step the human directs.
6. Continue at the `/sdlc` skill's step 6 (Security Review + Quality Gate onward) — invoke that skill's remaining steps directly rather than duplicating them here.

**Done when**: `verdict.md` reads `READY` (or `READY WITH NOTES` accepted by the human at the gate) and the trunk's remaining steps have been handed off to.

## References

- `references/dispatch.md` — exact `Agent()` call shapes and the slug-derivation rule.
