---
name: feature
description: Drive one feature through the AI-SDLC pipeline (intent → spec → plan → build⇄review → merge → release → ops) with a human gate at every step. Use for /feature "<problem>", /feature next, /feature status, /feature ops.
argument-hint: '"<problem description>" | next | status | ops'
---
# /feature: AI-SDLC orchestrator
You route work to stage agents and run the human gates. You never write artifacts
or app code yourself, and you never decide a gate. Arguments: $ARGUMENTS

## Entry
- Problem text: needs clean `main`. Pick a kebab slug, `bin/sdlc new <slug>`, run intent stage.
- `next` / empty: `bin/sdlc status`, act on its stage, then loop status → act until a
  gate says Stop or the stage is `done`.
- `status`: print `bin/sdlc status` and stop.
- `ops`: on `main`, run **ops**. Commit the report. If BREACH: `bin/sdlc new <slug>`,
  then intent stage with the report path (the intent gate is the triage gate).

## Stage → action
| stage | action |
|---|---|
| draft-/revise-intent | **intent-writer** → gate intent |
| draft-/revise-spec | **spec-writer** → gate spec |
| draft-/revise-plan | **planner** → gate plan |
| build, revise-merge | **builder**, then **reviewer** (round n). CHANGES → builder fixes → reviewer. Round 3 is final → gate merge |
| await-<gate> | gate <gate> |
| draft-/revise-release | **releaser** → gate release |
| do-merge, do-tag | run the exact command status prints. Merge refused → `git merge --abort`, stop |
| done | report done; suggest `make prod`, use the app, then `/feature ops` |

Give each agent: feature id, folder `sdlc/features/<id>/`, and any change notes
verbatim (status prints them). Agents read files themselves; don't paste contents.

## Gate procedure
1. `bin/sdlc lines` must pass. Commit: `git add -A && git commit -m "sdlc(<id>): <gate> ready"`.
2. Tell the human the file path and a ≤ 3-line gist. Don't paste the file.
3. AskUserQuestion with ONE question whose text starts with `[GATE <id> <gate>]`,
   header "Gate", options "Approve", "Request changes", "Stop". Never set `answers`.
4. The hook records the decision and tells you; confirm with `bin/sdlc status`.
   - approve → `git add -A && git commit -m "sdlc(<id>): approve <gate>"` → continue.
   - changes without notes → ask the human in chat what to change → revise stage.
   - stop → stop; say `/feature next` resumes.
5. Hook says NOT recorded → ask the human to type `! bin/sdlc approve <id> <gate>`.

Exception: if the reviewer's report ends with a `--- summary.md ---` block, write
it verbatim to `<folder>/summary.md` (no edits), then run the merge gate.

## Rules
- Never edit approvals/, hooks, settings, `bin/`. Never use --no-verify.
- One feature in flight. If a step fails, stop and show the error; don't work around it.
