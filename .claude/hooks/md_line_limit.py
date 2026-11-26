#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit): reject any .md in the project over 50 lines.

Computes the file as it would look after the write/edit and blocks with exit 2,
so the agent gets the message and must tighten the text.
"""
import json
import os
import sys
from pathlib import Path

MAX = 50
SKIP = {".git", ".venv", "node_modules", "var"}


def resulting_text(tool: str, inp: dict, path: Path) -> str:
    if tool == "Write":
        return inp.get("content", "")
    text = path.read_text(errors="replace") if path.exists() else ""
    for e in inp.get("edits") or [inp]:
        old, new = e.get("old_string", ""), e.get("new_string", "")
        if old and old in text:
            text = text.replace(old, new) if e.get("replace_all") else text.replace(old, new, 1)
    return text


def main() -> int:
    data = json.load(sys.stdin)
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    raw = inp.get("file_path", "")
    if not raw.endswith(".md"):
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
    path = Path(raw) if Path(raw).is_absolute() else root / raw
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        return 0  # outside the project
    if SKIP & set(rel.parts):
        return 0
    n = len(resulting_text(tool, inp, path).splitlines())
    if n > MAX:
        print(f"Blocked: {rel} would be {n} lines; the limit is {MAX}. "
              f"Cut {n - MAX}+ lines: drop filler, merge bullets, keep one idea per line. "
              f"If it truly can't fit, the feature is too big: propose a split.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
