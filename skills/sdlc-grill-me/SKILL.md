---
name: sdlc-grill-me
description: Adversarially reads a plan or design document, generates the hardest questions a skeptical reviewer would ask, resolves what it can from context already available, and escalates the rest. Use when the user asks to stress-test/grill a plan or design, or is invoked against docs/sdlc/architecture.md as part of the /sdlc Architecture gate. Fully self-contained — no runtime dependency on any other installed plugin.
---

# /sdlc-grill-me

## Contract

- **Input**: a plan or design document — a path, or inline text if the user pastes it directly.
- **Output**: the target document edited in place with resolved gaps folded back in; a short list of unresolved open questions escalated to the human.
- **Boundary**: adversarial reading only — never edits the document's actual decisions, only flags gaps and, where resolvable from context already in the document/repo, fills them in with a note on where the answer came from. Never invents an answer that isn't grounded in the document or the repo.

## Steps

1. Resolve the target document's path (ask if given only inline text and no obvious save location, or if the path is ambiguous).
2. Dispatch:

```

Agent(subagent_type: "general-purpose", prompt: "Adversarially review {path}. Read it in full, plus any repo context it references. Generate the hardest, most skeptical questions a reviewer would ask about gaps, contradictions, or unstated assumptions. For each question: try to resolve it from context already available in the document or repo — if resolved, edit the document in place to fold the answer back in (with a brief inline note on where the answer came from), if not resolvable, list it as an open question. Never invent an answer not grounded in the document or repo. Return: the full list of questions generated, which were resolved (and how), and which remain open.")

```

3. Present the agent's returned list to the user: resolved items as a summary of what changed in the document, open items as questions needing a human answer.
4. If any open items exist and this call originated from `/sdlc`'s Architecture gate (Task 19 step 4), those open items get folded into that gate's own `[GATE 3]` prompt rather than presented as a second, separate gate.

**Done when**: every generated question is either resolved-and-folded-in or explicitly listed as open for the human.
