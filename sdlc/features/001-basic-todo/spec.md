# Spec 001: Basic todo list
Intent: intent.md (approved)

## Summary (≤ 3 lines)
One web page at `/` lists all tasks, with a form to add a task by short text and,
per task, a button to mark it done and one to delete it. Done tasks look different.
Tasks are kept in SQLite, survive restarts, and the page works by touch on a phone.

## Acceptance criteria (≤ 15 lines, one per line)
- AC1: Given an empty DB, when GET `/`, then 200 HTML with an add-task form and the text "No tasks yet".
- AC2: Given any DB, when POST `/tasks` with form `text=Buy milk` (no HX-Request), then 303 to `/` and GET `/` lists "Buy milk" as open.
- AC3: Given any DB, when POST `/tasks` with `text=Buy milk` and header `HX-Request: true`, then 200 with the `#task-list` fragment (no `<html>`) containing "Buy milk".
- AC4: Given tasks "A" then "B" were added, when GET `/`, then both are listed, "A" before "B".
- AC5: Given an open task, when POST `/tasks/{id}/done`, then it is stored as done and its list item in GET `/` has class `done` (open items do not).
- AC6: Given one done and one open task, when GET `/`, then only the open task has a "Done" button; the page CSS styles `.done` items (e.g. struck through).
- AC7: Given a task, when POST `/tasks/{id}/delete`, then it is removed from the DB and absent from GET `/`, also after a restart.
- AC8: Given tasks (some done) in the DB file at `TODO_DB`, when the app is started again on that file, then GET `/` shows the same tasks with the same done state.
- AC9: Given HX-Request on done/delete, then 200 with the updated `#task-list` fragment; without it, 303 to `/`.
- AC10: Given GET `/`, then the page has `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- AC11: Given GET `/`, then add, done and delete are `<button>` elements inside forms (work by tap, no hover needed).

## Edge cases (≤ 8 lines)
- Empty or whitespace-only text → 422 with "Task text is required"; nothing stored.
- Text over 200 chars (after trimming) → 422 with "Task text must be at most 200 characters"; nothing stored.
- Leading/trailing spaces in text → trimmed before storing.
- Text with HTML, e.g. `<b>x</b>` → shown literally (escaped), not rendered.
- Done or delete on an unknown id → 404; no data changes.
- Done on an already-done task → same response as AC5/AC9; stays done.
- Input field has `required` and `maxlength="200"` so browsers block bad input early.

## Surface (≤ 8 lines)
- GET `/`: full HTML page (form + `#task-list`).
- POST `/tasks` (form field `text`): create open task.
- POST `/tasks/{id}/done`: mark task done.
- POST `/tasks/{id}/delete`: delete task.
- Storage: SQLite at `TODO_DB`, table `tasks` (id, text, done, created_at).

## Out of scope (≤ 4 lines)
- Editing text, un-marking done, bulk actions (per intent).
- Due dates, priorities, tags, custom ordering, search, filtering, accounts.
- A JSON API; only the HTML/HTMX routes above.

## Open questions (≤ 4 lines; "None." if none)
- Max task length? Default: 200 characters.
- List order? Default: oldest first (creation order); done tasks stay in place.
- Phone fit (no zoom, no sideways scroll, ≥ 44px tap targets)? Default: CSS does it; checked by hand at 375px width in review.
- `/health` and JSON request logging (CLAUDE.md baseline)? Default: plan adds them; not ACs here.
