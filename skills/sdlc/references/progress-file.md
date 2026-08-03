# PROGRESS.md convention

Lives at the **target repo's root** (not inside `docs/sdlc/`). Read at the start of every `sdlc*` skill invocation (if present) to resume context without depending on chat history; appended to by `sdlc-handoff` at the end of every session — never overwritten, never truncated.

## Entry template

```

## {date} — {phase/story identifier}

### Done

- {artifact}: {one-line outcome}

### Failed

- {anything that didn't complete, with why}

### Current State

{where the pipeline is right now — which gate it's sitting at, if any, and if a story is mid-loop, which round it's on, e.g. "story 2.3, QA round 2/3 after a MINOR Tuner fix"}

### Next

{the single next action whoever resumes should take}

### Metrics

{lightweight signals, not prose — e.g.:}
- Rounds used: QA {a}/3, Review {b}/3 (omit either that didn't run this session)
- Findings by severity: {n} NIT, {n} MINOR, {n} MAJOR, {n} CRITICAL/BLOCKED
- Gates: cleared {list}; escalated {list, or "none"}

```

## Resume convention

A new session's first `sdlc*` skill dispatch should read the last entry's **Current State** and **Next** sections before doing anything else — this is what lets a multi-session, long-running pipeline resume purely from files, per design §5/§6.
