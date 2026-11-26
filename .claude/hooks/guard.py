#!/usr/bin/env python3
"""PreToolUse guard: agents can't approve gates, forge gate answers, or weaken the pipeline.

- Write/Edit to approvals/, hooks, settings, .githooks, bin/sdlc*  -> blocked
- Bash: `sdlc approve|changes|stop`, --no-verify, core.hooksPath, or a write
  verb aimed at a protected path                                    -> blocked
- AskUserQuestion: a [GATE ...] question with pre-filled `answers`  -> blocked
A human can lift the file guards by starting Claude with SDLC_MAINTENANCE=1.
The Bash checks are heuristics (defence in depth), not a sandbox.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bin"))
import sdlc_core as core  # noqa: E402

PROTECTED = [r"sdlc/features/[^/\s]+/approvals", r"\.claude/hooks", r"\.claude/settings",
             r"\.githooks", r"bin/sdlc"]
WRITE_VERBS = (r"(>|\btee\b|\bcp\b|\bmv\b|\brm\b|\btouch\b|\bsed\s+-i|\bpython3?\b|"
               r"\bperl\b|\bchmod\b|\bln\b|\btruncate\b|\bdd\b|\bcat\s*<<)")
HUMAN_ONLY = "Only a human decides gates (gate question, or `! bin/sdlc approve|changes ...`)."


def deny(msg: str) -> None:
    print(f"Blocked by AI-SDLC guard: {msg}", file=sys.stderr)
    sys.exit(2)


def protected(text: str) -> bool:
    return any(re.search(p, text) for p in PROTECTED)


def main() -> int:
    data = json.load(sys.stdin)
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    maintenance = os.environ.get("SDLC_MAINTENANCE") == "1"

    if tool == "AskUserQuestion":
        core.debug_log("pre-AskUserQuestion", data)
        gate_qs = [q for q in inp.get("questions") or []
                   if core.GATE_MARKER.search(q.get("question", ""))]
        if gate_qs and inp.get("answers"):
            deny("gate questions must not pre-fill `answers`. " + HUMAN_ONLY)
        return 0

    if maintenance:
        return 0

    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        if protected(path):
            deny(f"{path} is protected. {HUMAN_ONLY}")
    elif tool == "Bash":
        cmd = inp.get("command", "")
        if re.search(r"sdlc(\.py)?\s+(approve|changes|stop)\b", cmd):
            deny(HUMAN_ONLY)
        if re.search(r"--no-verify|core\.hooksPath|SDLC_MAINTENANCE", cmd):
            deny("bypassing git hooks or the guard is not allowed.")
        # ignore harmless redirections before looking for write verbs
        cleaned = re.sub(r"\d?>&\d|\d?>\s*/dev/null", "", cmd)
        if protected(cleaned) and re.search(WRITE_VERBS, cleaned):
            deny("this command would modify a protected path "
                 "(approvals, hooks, settings, .githooks, bin/sdlc).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
