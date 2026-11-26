# Merge summary 001: Basic todo list
Branch: feat/001-basic-todo · Review: PASS after 2 rounds

## What changed (≤ 8 lines, user terms first)
- The page at `/` lists tasks oldest first and shows "No tasks yet" when the list is empty.
- Add a task by short text (trimmed, 1-200 chars). Mark a task done (struck through, no Done button) or delete it.
- With htmx (vendored 2.0.4), the list updates in place. Without JS, forms POST and get a 303 back to `/`.
- Bad input (blank, too long) and unknown ids show a readable message: a small inline error for HTMX, the full page for plain forms (422/404).
- Tasks live in SQLite at `TODO_DB` and survive restarts. Phone-friendly: viewport meta, 44px tap targets, no fixed widths.
- Baseline: `GET /health`, one JSON log line per request to `TODO_LOG`, unhandled errors logged and returned as 500.
- Pipeline (not app): reviewer.md and feature SKILL.md now relay summary.md when the write is blocked (9ec2ff0, human-requested).

## Files (≤ 12 lines, from `git diff --stat main...HEAD`)
- app/main.py (+95/-0), app/db.py (+52/-0), app/reqlog.py (+46/-0), app/__init__.py (+0/-0)
- app/templates/index.html (+28/-0), _task_list.html (+19/-0), _error.html (+1/-0)
- app/static/style.css (+15/-0), app/static/htmx.min.js (+1/-0, vendored htmx 2.0.4)
- tests/conftest.py (+17), test_add.py (+88), test_done_delete.py (+94), test_page.py (+46)
- tests/test_baseline.py (+47), test_persist.py (+25), test_import.py (+15)
- .claude/agents/reviewer.md (+2), .claude/skills/feature/SKILL.md (+3), sdlc/features/001-basic-todo/* (docs, approvals)

## Tests (≤ 4 lines)
- `make test` → 24 passed, 0 failed (1 Starlette httpx deprecation warning, harmless)
- Every AC1-AC11 and every spec edge case has a named test (see review.md).

## Where to look (≤ 6 lines)
- Phone at 375px width (open `make run` in a browser or devtools): no zoom, no sideways scroll, easy taps. Not automated.
- app/templates/index.html:6-8 — htmx-config `responseHandling` swaps 404/422 responses; inline `hx-on` JS clears the error.
- app/main.py:34-42 — error_response: HX-Retarget to `#form-error` for HTMX, full page for plain forms.
- app/main.py:49-52 — DB schema is created in the app lifespan, not at import.
- app/reqlog.py:19-46 — hand-written ASGI log middleware; check that the fields match the ops needs.

## Open findings / known limits (≤ 4 lines; "None." if none)
- [minor] An HTMX 404 (task already removed in another tab) shows "Task not found" but leaves the stale item listed. Optional fix: an OOB list swap.
- A non-integer id in a crafted URL returns FastAPI's JSON 422. The UI can't send one.
- `make smoke` and the 375px phone check were not run by the reviewer.
