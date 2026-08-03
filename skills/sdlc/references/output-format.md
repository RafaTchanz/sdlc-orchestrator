# Artifact skeletons — `/sdlc`

These are the section skeletons each agent's contract already specifies in full (see each `sdlc-*.md` agent file's Procedure section for the authoritative version). This reference exists so the orchestrating skill can point a dispatch prompt at a concrete skeleton without re-deriving it:

- `product-brief.md` — Problem Statement, Target Users & JTBD, Success Metrics, Scope, Constraints, Competitive Scan, Risks, Open Questions. (Full spec: `sdlc-analyst.md`.)
- `PRD.md` — Overview, Goals/Non-goals, Personas, Functional Requirements (Epic → Story → ACs), Non-functional Requirements, Release Criteria, Open Questions. (Full spec: `sdlc-pm.md`.)
- `architecture.md` — Context & Constraints, Tech Stack Decision, Component Boundaries, Data Model & Flow, API Contracts, Cross-cutting Concerns, Security Considerations, Deployment Topology, Open Questions. (Full spec: `sdlc-architect.md`.)
- `epic-manifest.md` / `task-manifest.md` — single table: `Epic/Task | Stories | Tier | Language/Stack | Depends-on | Status`. (Full spec: `sdlc-architect.md`.)
- `story-{n.m}.md` — Title, Context, Acceptance Criteria, Technical Notes, Definition of Done. (Full spec: `sdlc-scrum-master.md`.)
- `qa.md` / `review.md` / `stress.md` — Signal + Findings (`file:line` → fix) + Verdict rationale. (Full spec: each of `sdlc-qa.md`, `sdlc-reviewer.md`, `sdlc-stress.md`.)
- `verdict.md` — Verdict (READY/READY WITH NOTES/NOT READY) + Inputs + Rationale. (Full spec: `sdlc-verdict.md`.)
- `security-review.md` — Severity-tagged findings + OWASP Web/LLM coverage tables. (Full spec: `sdlc-security.md`.)
- `quality-gate.md` — Per-gate PASS/FAIL table + overall verdict. (Full spec: `sdlc-quality-gate.md`.)
- `pr-review.md` — PR URL/body used + action taken. (Full spec: `sdlc-pr.md`.)
- `release.md` — Added/Fixed/Breaking + migration notes. (Full spec: `sdlc-devops.md`.)
