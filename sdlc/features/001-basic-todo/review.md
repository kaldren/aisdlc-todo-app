# Review 001 — round 2
Verdict: PASS
Diff: main...feat/001-basic-todo · Tests: 24 passed, 0 failed

## Findings (≤ 25 lines, one per line; "None." if none)
- [minor] app/main.py:34-39 — HTMX 404 on done/delete (task removed in another tab) swaps only `#form-error`, so the stale item stays listed next to "Task not found" → optional: also return the current `_task_list.html` with `hx-swap-oob="true"` in the 404 partial. Spec only requires 404; fine to defer.

## Checks
- SQL: all queries parameterised (app/db.py:36-52). XSS: Jinja2 autoescape; `{{ error }}` in _error.html escaped too; test_html_escaped.
- Logging: unchanged since round 1, meets CLAUDE.md (app/reqlog.py:32-46); lifespan scope passes through (reqlog.py:20).
- htmx 2.0.4 matches `responseHandling` codes with an unanchored RegExp: `[23]..` does not match 404/422/500, `404|422` swaps, other 4xx/5xx do not. Checked against the vendored source.
- Lifespan `db.init` (main.py:49-52): every test uses `with TestClient(...)`, so startup runs; uvicorn runs lifespan by default. test_import proves import creates no files.
- Unreachable from the UI: non-int id (e.g. `/tasks/abc/done`) gives FastAPI JSON 422, which htmx would swap into `#task-list`. Only crafted requests hit it; not a finding.
- Scope: error partial, htmx-config meta, `pattern`/`title` and test_import all serve spec edge cases or round-1 findings; no new deps. Commit 9ec2ff0 changes only pipeline files (.claude/agents/reviewer.md, .claude/skills/feature/SKILL.md), was requested by a human, and is not app scope.
- Phone layout: CSS unchanged except `.error`; round-1 notes still apply. Still needs a manual 375px check.

## Spec coverage (one line per AC)
- AC1: tests/test_page.py::test_empty_page_has_form_and_hint
- AC2: tests/test_add.py::test_add_redirects_and_lists
- AC3: tests/test_add.py::test_add_htmx_returns_fragment
- AC4: tests/test_add.py::test_oldest_first
- AC5: tests/test_done_delete.py::test_done_sets_class
- AC6: tests/test_done_delete.py::test_done_button_only_on_open_and_css
- AC7: tests/test_done_delete.py::test_delete_removes, tests/test_persist.py::test_restart_keeps_tasks_and_done_state
- AC8: tests/test_persist.py::test_restart_keeps_tasks_and_done_state
- AC9: tests/test_done_delete.py::test_htmx_vs_redirect
- AC10: tests/test_page.py::test_viewport_meta
- AC11: tests/test_page.py::test_actions_are_buttons_in_forms
- Edge cases: test_blank_rejected(+_htmx_gets_error_partial), test_too_long_rejected, test_text_trimmed, test_html_escaped, test_unknown_id_404, test_done_twice_idempotent, test_page_gives_feedback_for_blank_text

## Previous round (≤ 5 lines; omit in round 1)
- index.html whitespace-only text silently ignored → fixed (`pattern` + `title`, HTMX 422 partial swapped; tests in test_add.py)
- main.py HTMX 422 returned the full page → fixed (`_error.html` partial via HX-Retarget; test asserts no `<html`)
- main.py 404 was raw JSON → fixed (HTML page for forms, partial for HTMX; test_unknown_id_404)
- main.py import created var/ files → fixed (db.init in lifespan; tests/test_import.py)
