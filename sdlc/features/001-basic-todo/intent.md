# Intent 001: Basic todo list
Origin: human · Date: 2026-11-26

## Problem (≤ 5 lines)
A person wants to track the small tasks they need to do.
Today the app gives them nothing: no place to note a task,
no way to see what is still open, and no way to clear finished
or unwanted tasks.

## Desired outcome (≤ 5 lines)
A user can add a task with a short text, see all their tasks in one list,
mark a task as done, and delete a task.
Done tasks are visibly different from open ones.
The list still shows the same tasks after a page reload or app restart.

## Success signals (≤ 5 lines)
- A newly added task appears in the list right away.
- Marking a task done changes how it shows in the list.
- A deleted task is gone from the list and does not come back.
- Tasks are still there after the app restarts.

## Out of scope (≤ 5 lines)
- Editing a task's text, or un-marking a done task.
- Due dates, priorities, tags, ordering, search or filtering.
- User accounts, login, or separate lists per person.
- Bulk actions (e.g. clear all done tasks).

## Size check (1–3 lines)
Fits one small feature.
