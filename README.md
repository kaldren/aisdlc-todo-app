# aisdlc-todo-app

A todo app built only through an AI-SDLC loop. Agents draft every artifact;
a human approves every gate before the next stage starts.

```
intent → spec → plan → build ⇄ review → merge → release → ops ─┐
   ▲                                                         │
   └──────────────── new intent (triage) ◄───────────────────┘
```

## Setup
    make setup          # uv sync + enable git hooks

## Use (Claude Code, opened in this folder)
    /feature "people forget what they need to do"   start a feature
    /feature next                                   continue
    /feature status                                 where are we?
    /feature ops                                    check prod logs

## Your job: the gates
At each gate you get a question: Approve / Request changes / Stop.
Read the file it names (always ≤ 50 lines). Fallback from the prompt:

    ! bin/sdlc approve 001 spec
    ! bin/sdlc changes 001 spec "drop the priority field"

## What enforces what
| Rule | Enforced by |
|---|---|
| ≤ 50 lines per .md | `.claude/hooks/md_line_limit.py`, `bin/sdlc lines` |
| Agents can't approve | `.claude/hooks/guard.py` + settings deny rules |
| Approval = exact file | sha256 stored in `approvals/<gate>.json` |
| No merge without approval | `.githooks/pre-merge-commit` |
| Decisions trail | `sdlc/features/<id>/approvals/log.jsonl` |
