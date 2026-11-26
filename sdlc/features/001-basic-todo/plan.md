# Plan 001: Basic todo list
Spec: spec.md (approved)

## Approach (≤ 4 lines)
`create_app()` factory in app/main.py (`app = create_app()`), env read at create time so tests and restarts get a fresh DB/log.
stdlib sqlite3, one connection per request, `CREATE TABLE IF NOT EXISTS` on startup; parent dirs auto-created.
Jinja2 page; `#task-list` is a partial template, returned alone when `HX-Request: true`, else 303 to `/`.
Pure-ASGI middleware writes one JSON line per request to TODO_LOG and catches unhandled errors (500).

## Files (≤ 10 lines)
- app/__init__.py: new (empty)
- app/main.py: new: create_app, /health, routes `/`, `/tasks`, `/tasks/{id}/done`, `/tasks/{id}/delete`
- app/db.py: new: connect(path), init schema, list/add/mark_done/delete (parameterised SQL)
- app/reqlog.py: new: JSON request-log middleware (named to avoid clashing with stdlib `logging`)
- app/templates/index.html, app/templates/_task_list.html: new: page and list fragment (autoescape on)
- app/static/style.css: new: `.done` struck through, ≥ 44px buttons, no fixed widths
- app/static/htmx.min.js: new: vendored htmx 2.0.x, served by FastAPI StaticFiles at `/static`
- tests/conftest.py: new: fixture sets TODO_DB/TODO_LOG to tmp_path, yields TestClient(create_app())

## Steps (≤ 10 lines; each leaves `make test` green)
1. conftest + app/main.py with `GET /health` and test_health_ok (pytest needs ≥ 1 test to pass) → baseline
2. app/reqlog.py middleware + log tests (normal request, unhandled error) → baseline
3. app/db.py schema + CRUD; GET `/` renders index + empty list → AC1, AC10, AC11
4. POST `/tasks`: `text: str = Form("")`, trim, 422 checks, 303 or fragment → AC2, AC3, AC4
5. POST done/delete with 404 on unknown id, HTMX vs 303 split; style.css `.done` → AC5, AC6, AC7, AC9
6. Vendor htmx, wire `hx-post`/`hx-target="#task-list"`/`hx-swap="outerHTML"`; restart test; `make smoke` → AC8

## Tests (≤ 10 lines; every AC appears at least once)
- tests/test_baseline.py::test_health_ok, ::test_request_logged_as_json, ::test_unhandled_error_logged → baseline
- tests/test_page.py::test_empty_page_has_form_and_hint → AC1; ::test_viewport_meta → AC10; ::test_actions_are_buttons_in_forms → AC11
- tests/test_add.py::test_add_redirects_and_lists → AC2; ::test_add_htmx_returns_fragment → AC3; ::test_oldest_first → AC4
- tests/test_add.py::test_blank_rejected, ::test_too_long_rejected, ::test_text_trimmed, ::test_html_escaped → edge cases
- tests/test_done_delete.py::test_done_sets_class → AC5; ::test_done_button_only_on_open_and_css → AC6
- tests/test_done_delete.py::test_delete_removes → AC7; ::test_htmx_vs_redirect → AC9
- tests/test_done_delete.py::test_unknown_id_404, ::test_done_twice_idempotent → edge cases
- tests/test_persist.py::test_restart_keeps_tasks_and_done_state (second create_app() on same TODO_DB) → AC7, AC8

## Data / dependencies (≤ 3 lines; "None." if none)
- Table `tasks(id INTEGER PRIMARY KEY, text TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)`; order by id.
- No new Python packages (fastapi, jinja2, python-multipart, pytest, httpx already in pyproject.toml).
- New front-end asset: htmx 2.0.x, vendored as one static file (no CDN at runtime).

## Risks (≤ 3 lines)
- A missing `text` field would give FastAPI's JSON 422 without our message → default `Form("")`, validate ourselves.
- Middleware may miss errors or the 500 status → pure ASGI wrapper, tested via a route that raises, added in the test.
- htmx skips swapping 4xx responses → fine: `required`/`maxlength` block bad input; non-HTMX POST still shows the 422 message.
