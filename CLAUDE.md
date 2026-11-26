# AI-SDLC Todo App

A todo app built only through an AI-SDLC pipeline: agents draft every artifact,
a human approves every gate. Drive it with `/feature`. Never skip a stage or gate.

## Flow (one feature at a time, on branch `feat/NNN-slug`)
intent → spec → plan → build ⇄ review → merge → release → ops → new intent
Artifacts live in `sdlc/features/NNN-slug/`. Ops reports live in `sdlc/ops/`.

## Gates
- Gates: intent, spec, plan, merge (file: summary.md), release (file: release.md).
- Ops findings come back as a new feature; its intent gate is the triage gate.
- Only a human decides a gate: the in-session gate question (recorded by a hook)
  or `! bin/sdlc approve <id> <gate>` / `! bin/sdlc changes <id> <gate> "notes"`.
- An approval stores the file's sha256. Editing an approved file re-opens the gate.
- Agents never write `approvals/`, never run `bin/sdlc approve|changes`, never edit
  `.claude/hooks/`, `.claude/settings.json`, `.githooks/`, `bin/sdlc*`, never use `--no-verify`.

## The 50-line rule
Every .md file in this repo is ≤ 50 lines; a hook rejects longer writes.
Use the templates in `sdlc/templates/`. If a feature can't fit, propose a split.

## Stack
- Python 3.13 with uv, FastAPI, Jinja2 + HTMX, SQLite via stdlib `sqlite3`.
- Tests: pytest + FastAPI TestClient (httpx). Each test uses a temp DB.
- Code in `app/` (entry point `app.main:app`), tests in `tests/`.
- `GET /health` returns `{"status": "ok"}`.
- DB path from env `TODO_DB` (default `var/todo.db`).
- Log JSON lines to env `TODO_LOG` (default `var/log/app.jsonl`), one per request:
  `ts, level, event, method, path, status, ms`; unhandled errors log
  `level=error, event=unhandled_error, error=<type: message>`.
- Add a dependency only when the approved plan names it.

## Commands
- `make setup` · `make test` · `make run` (dev) · `make prod` (production)
- `make smoke` · `make release-check` · `bin/sdlc status` · `bin/sdlc lines`

## Changing the pipeline itself
Guards block edits to hooks/settings/bin/sdlc. To change them, a human starts
Claude with `SDLC_MAINTENANCE=1 claude` or edits the files by hand.
