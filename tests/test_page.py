import os
import re

from app import db


def add(text):
    with db.connect(os.environ["TODO_DB"]) as conn:
        return db.add_task(conn, text)


def test_empty_page_has_form_and_hint(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert '<form class="add" method="post" action="/tasks">' in r.text
    assert 'name="text"' in r.text
    assert "No tasks yet" in r.text


def test_viewport_meta(client):
    r = client.get("/")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in r.text


def test_actions_are_buttons_in_forms(client):
    task_id = add("Buy milk")
    html = client.get("/").text
    forms = re.findall(r"<form\b[^>]*>.*?</form>", html, re.S)
    by_action = {re.search(r'action="([^"]+)"', f).group(1): f for f in forms}
    for action, label in [("/tasks", "Add"), (f"/tasks/{task_id}/done", "Done"),
                          (f"/tasks/{task_id}/delete", "Delete")]:
        form = by_action[action]
        assert 'method="post"' in form
        assert re.search(rf"<button\b[^>]*>{label}</button>", form)
