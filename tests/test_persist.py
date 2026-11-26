import re

from fastapi.testclient import TestClient

from app.main import create_app


def listed(html):
    """(text, done) for each task item, in page order."""
    return [(text, cls == ' class="done"') for cls, text in
            re.findall(r'<li( class="done")?>\s*<span class="text">(.*?)</span>', html)]


def test_restart_keeps_tasks_and_done_state(env):
    with TestClient(create_app()) as c:
        for text in ("A", "B", "C"):
            c.post("/tasks", data={"text": text})
        c.post("/tasks/1/done")
        c.post("/tasks/2/delete")
        before = listed(c.get("/").text)
    assert before == [("A", True), ("C", False)]

    with TestClient(create_app()) as c:
        after = listed(c.get("/").text)
    assert after == before
