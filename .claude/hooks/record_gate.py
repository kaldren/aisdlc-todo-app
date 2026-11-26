#!/usr/bin/env python3
"""PostToolUse(AskUserQuestion): record the human's answer to a [GATE <id> <gate>] question.

Runs outside the model, so the approval file is written by this script, never by
an agent. Reports what it recorded back to Claude as additionalContext.
Raw payloads go to var/hooks/ for debugging.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bin"))
import sdlc_core as core  # noqa: E402


def main() -> int:
    data = json.load(sys.stdin)
    core.debug_log("post-AskUserQuestion", data)
    inp = data.get("tool_input") or {}
    resp = data.get("tool_response")
    gates = [(q.get("question", ""), core.GATE_MARKER.search(q.get("question", "")))
             for q in inp.get("questions") or []]
    gates = [(q, m) for q, m in gates if m]
    if not gates:
        return 0

    answers = (core.find_key(resp, "answers") or core.find_key(inp, "answers")
               or core.answers_from_text(json.dumps(resp) if resp else ""))
    annotations = core.find_key(resp, "annotations") or core.find_key(inp, "annotations") or {}
    msgs = []
    for question, m in gates:
        fid, gate = m.group(1), m.group(2)
        answer = answers.get(question)
        if answer is None:  # keys may be normalised; fall back to the marker
            answer = next((v for k, v in answers.items() if m.group(0) in k), None)
        if answer is None:
            msgs.append(f"Gate {fid} {gate}: NOT recorded (no answer found in tool result). "
                        f"Ask the human to type `! bin/sdlc approve {fid} {gate}` "
                        f"or `! bin/sdlc changes {fid} {gate} \"<notes>\"`.")
            continue
        decision, notes = core.decide(str(answer))
        extra = (annotations.get(question) or {}).get("notes", "")
        notes = "; ".join(x for x in (notes, extra) if x)
        try:
            e = core.record(fid, gate, decision, notes, via="session")
            msg = f"Gate {fid} {gate}: recorded '{decision}' by {e['by']}"
            if decision == "approve":
                msg += f" (sha256 {e['sha256'][:12]})"
            if notes:
                msg += f". Notes: {notes}"
            msgs.append(msg + ".")
        except core.SdlcError as err:
            msgs.append(f"Gate {fid} {gate}: NOT recorded ({err}).")

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": " ".join(msgs),
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
