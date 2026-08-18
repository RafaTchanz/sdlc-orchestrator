#!/usr/bin/env python3
"""Static consistency checks for agents/*.md and skills/**/*.md.

Catches the class of bug found in the 2026-08-17 P0 review: a shared agent's
Contract/description changes but not every skill that dispatches it is
updated to match. Checks only textual consistency between the prose
contracts — it cannot verify actual runtime dispatch behavior.

Exit code 0 = all checks passed, 1 = at least one failure.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
SKILLS_DIR = ROOT / "skills"

failures = []


def fail(check, detail):
    failures.append(f"[{check}] {detail}")


def read(path):
    return path.read_text(encoding="utf-8")


def all_skill_files():
    return sorted(SKILLS_DIR.glob("**/*.md"))


def all_agent_files():
    return sorted(AGENTS_DIR.glob("*.md"))


# --- Check 1: known-stale wording must never reappear -----------------
STALE_PATTERNS = [
    r"before commit\b",
    r"Review's signal only",
    r"route on Review\b",
]


def check_stale_wording():
    for path in all_agent_files() + all_skill_files():
        text = read(path)
        for pattern in STALE_PATTERNS:
            if re.search(pattern, text):
                fail("stale-wording", f"{path.relative_to(ROOT)}: matches /{pattern}/")


# --- Check 2: sdlc-coder dispatches must state a work branch ----------
def check_coder_branch_clause():
    for path in all_skill_files():
        text = read(path)
        for m in re.finditer(r'subagent_type:\s*"sdlc-coder(?:-backend|-frontend)?"[^)]*\)', text):
            # look at the enclosing Agent(...) call's prompt string
            start = text.rfind("Agent(", 0, m.start())
            end = text.find(")", m.end())
            call_text = text[start:end] if start != -1 else m.group(0)
            if "-work" not in call_text:
                line_no = text.count("\n", 0, m.start()) + 1
                fail(
                    "coder-branch-clause",
                    f"{path.relative_to(ROOT)}:{line_no}: sdlc-coder dispatch has no "
                    f"'-work' branch reference in its prompt",
                )


# --- Check 3: agent <-> skill caller cross-reference -------------------
DISPATCHED_BY_RE = re.compile(r"Dispatched only by (?:the |)([^.]+?) skill", re.IGNORECASE)
SKILL_NAME_RE = re.compile(r"/[\w-]+")
SUBAGENT_CALL_RE = re.compile(r'subagent_type:\s*"([\w-]+)"')

# Known intentional deferrals this regex-based check can't see through:
# a skill can dispatch an agent purely narratively ("same as /sdlc step 5c"),
# without a literal Agent(subagent_type: ...) block of its own. Each entry
# here is a (skill_dir_name, agent_name) pair verified by hand — not a bug.
DIRECTION_A_ALLOWLIST = {
    # /sdlc-task's loop.md restates /sdlc's routing narratively for these
    # four steps instead of repeating their Agent() calls verbatim.
    ("sdlc-task", "sdlc-architect"),
    ("sdlc-task", "sdlc-qa"),
    ("sdlc-task", "sdlc-reviewer"),
    ("sdlc-task", "sdlc-stress"),
    ("sdlc-task", "sdlc-tuner"),
}


def agent_name(path):
    return path.stem


def check_agent_skill_cross_reference():
    agent_claims = {}  # agent_name -> set(skill_dir_name)
    for path in all_agent_files():
        text = read(path)
        m = DISPATCHED_BY_RE.search(text)
        if not m:
            continue
        skills_mentioned = set(SKILL_NAME_RE.findall(m.group(1)))
        agent_claims[agent_name(path)] = {s.lstrip("/") for s in skills_mentioned}

    skill_calls = {}  # skill_dir_name -> set(agent_name actually dispatched)
    for skill_dir in sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir()):
        called = set()
        for md in skill_dir.glob("**/*.md"):
            called.update(SUBAGENT_CALL_RE.findall(read(md)))
        skill_calls[skill_dir.name] = called

    # Direction A: agent claims a skill dispatches it, but that skill never does.
    for agent, claimed_skills in agent_claims.items():
        if agent.endswith("-backend") or agent.endswith("-frontend"):
            # Coder tier overlays are never dispatched under their own
            # subagent_type — their content is read and concatenated into
            # the core sdlc-coder prompt instead (see phases.md's 5b note).
            continue
        for skill in claimed_skills:
            if skill not in skill_calls:
                continue  # unknown skill name in prose, not this check's job
            if (skill, agent) in DIRECTION_A_ALLOWLIST:
                continue
            actual = skill_calls[skill]
            if agent not in actual:
                fail(
                    "agent-skill-crossref",
                    f"agents/{agent}.md claims '{skill}' dispatches it, but no "
                    f"subagent_type: \"{agent}\" call found under skills/{skill}/",
                )

    # Direction B: a skill dispatches an agent that doesn't list it as a caller.
    for skill, called_agents in skill_calls.items():
        for agent in called_agents:
            base_agent = re.sub(r"-(backend|frontend)$", "", agent)
            claimed = agent_claims.get(base_agent)
            if claimed is None:
                continue  # agent file has no parseable "Dispatched only by" line
            if skill not in claimed:
                fail(
                    "agent-skill-crossref",
                    f"skills/{skill}/ dispatches subagent_type: \"{agent}\", but "
                    f"agents/{base_agent}.md's description doesn't list '/{skill}' as a caller",
                )


def main():
    check_stale_wording()
    check_coder_branch_clause()
    check_agent_skill_cross_reference()

    if failures:
        print(f"FAILED — {len(failures)} issue(s):\n")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("OK — all contract consistency checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
