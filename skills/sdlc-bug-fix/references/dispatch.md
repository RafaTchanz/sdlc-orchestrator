# Dispatch reference — `/sdlc-bug-fix`

## Slug derivation

Kebab-case the bug's short title: lowercase, spaces/punctuation → `-`, strip anything not `[a-z0-9-]`, collapse repeated `-`. Example: `"Login button double-submits on slow network"` → `login-button-double-submits-on-slow-network`. If a `docs/sdlc/bugs/{slug}/` already exists for a materially different bug, append `-2`, `-3`, etc.

## Step 1 — Investigator

```

Agent(subagent_type: "sdlc-bug-investigator", prompt: "Bug: {description}. Repro steps: {steps}. Diagnose and write docs/sdlc/bugs/{slug}/investigation.md, then commit a failing RED test, per your contract.")

```

## Step 2 — Coder squad

```

Agent(subagent_type: "sdlc-coder", prompt: "Root cause + RED test: docs/sdlc/bugs/{slug}/investigation.md. Tier overlay: {inferred from affected surface area}. Fix per your TDD contract — RED is already written, drive it to GREEN with the minimum change.")

```

## Step 3 — QA

```

Agent(subagent_type: "sdlc-qa", prompt: "Bug fix for '{slug}', just implemented. Audit per your contract. Write docs/sdlc/bugs/{slug}/qa.md.")

```

Routing identical to the `/sdlc` skill's step 5c (`references/phases.md` in the `sdlc` skill) — reuse that logic, this file doesn't repeat it.

## Step 4 — Reviewer

```

Agent(subagent_type: "sdlc-reviewer", prompt: "Bug fix for '{slug}'. Review per your contract. Write docs/sdlc/bugs/{slug}/review.md.")

```

## Step 5 — Rejoin trunk

Invoke `/sdlc`'s own step 6 onward (Security + Quality Gate → PR gate → Release gate → Handoff), pointing it at this bug-fix branch/diff instead of an epic's diff.
