# Release 001 → v0.1.0
Commit: 5054126 (main) · Result: READY

## Checks (≤ 10 lines)
- `make test` → 24 passed, 0 failed (1 harmless Starlette httpx deprecation warning)
- `make smoke` → `GET /health ok`
- AC1: `curl /` on empty DB → 200, add form, "No tasks yet"
- AC2/AC3: `curl -d 'text=Buy milk' /tasks` → 303 to `/`, listed; with `HX-Request: true` → fragment, no `<html>`
- AC5/AC9: `curl -X POST /tasks/1/done` → 303; with HX → 200; item has `class="done"`
- AC7/AC8: delete → 303; after app restart on same `TODO_DB`, tasks and done state kept, deleted task gone
- Edges: blank text → 422; delete unknown id 999 → 404; JSON log has 1 line per request, 0 errors
- Not checked here: phone layout at 375px width (manual; the reviewer did not run it either)

## Changes for users (≤ 5 lines)
- New page at `/`: add short tasks (1-200 chars), mark done (struck through), delete.
- With htmx the list updates in place; without JS, plain forms still work.
- Bad input and unknown tasks show a readable message. Tasks survive restarts.
- Phone-friendly layout (viewport meta, 44px tap targets).

## Rollback (≤ 3 lines)
None (first release; no previous tag). To withdraw: stop `make prod`.
Data in `TODO_DB` (default `var/todo.db`) stays; back it up before any later rollback.

## Watch after release (≤ 4 lines; for the ops agent)
- `level=error, event=unhandled_error` (any path) → any line at all is wrong; read `error`.
- `status` 5xx on `/`, `/tasks`, `/tasks/{id}/*` → should be 0; `/health` not 200 → down.
- `status=422` on POST `/tasks` (logged as info) → a high share means input is rejected too often.
- `status=404` on `/tasks/{id}/*` or `ms` > 200 on `/` → stale lists (known minor) or slow DB.
