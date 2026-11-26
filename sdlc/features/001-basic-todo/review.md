# Review 001 — round 1
Verdict: PASS
Diff: main...feat/001-basic-todo · Tests: 21 passed, 0 failed

## Findings (≤ 25 lines, one per line; "None." if none)
- [minor] app/templates/index.html:17 — `required` lets whitespace-only text through; on the HTMX path the server's 422 is not swapped, so tapping Add with "   " silently does nothing (plan risk assumed the browser blocks it) → add `pattern=".*\S.*"` (plus a `title`) to the input, or show the 422 message via an `hx-on::response-error` handler.
- [minor] app/main.py:58 — 422 on an HTMX request returns the full index.html page; if 4xx swapping is ever enabled it would nest a whole page inside `#task-list` → for `HX-Request: true` return the fragment or a small error partial.
- [minor] app/main.py:67,74 — 404 body is FastAPI JSON `{"detail": ...}`; a plain-form user on a stale page sees raw JSON, an HTMX user sees nothing → acceptable per spec (404 only); consider an HTML 404 in a later feature.
- [minor] app/main.py:80 — module-level `app = create_app()` runs at test import with default env, so `make test` creates `var/todo.db` and `var/log/` in the repo (gitignored, schema only, no data written) → optional: build the app lazily or set env in conftest before import.

## Checks
- SQL: all queries parameterised (app/db.py:36-52). XSS: Jinja2 autoescape on .html; tests/test_add.py::test_html_escaped.
- Logging: one JSON line per request with ts, level, event, method, path, status, ms; unhandled errors log level=error, event=unhandled_error, error="Type: msg" and return 500 (app/reqlog.py).
- Scope: no deps added; htmx 2.0.4 vendored per plan; no JSON API, no extra features. Extra test test_htmx_vendored is in scope.
- `make smoke` not run by reviewer (read-only rule); script only checks /health.

## Phone layout (manual AC, assessed from CSS/templates only)
- Verified in code: viewport meta (AC10); `box-sizing: border-box`; no fixed widths (main max-width 40rem + 1rem padding); add input `flex:1; min-width:0`; task text `min-width:0; overflow-wrap:anywhere` so long words wrap; buttons and input `min-height:44px`, buttons `min-width:44px`; input font-size 1rem (16px) avoids iOS focus zoom.
- Not verified: actual render at 375px in a real browser/device, touch behaviour, and spacing between Done/Delete (8px gap). Human should open the page at 375px width before merge.

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
- Edge cases: test_blank_rejected, test_too_long_rejected, test_text_trimmed, test_html_escaped, test_unknown_id_404, test_done_twice_idempotent, input attrs in test_empty_page_has_form_and_hint
