import os
import re
import sqlite3

from app import db

HX = {"HX-Request": "true"}


def add(text):
    with db.connect(os.environ["TODO_DB"]) as conn:
        return db.add_task(conn, text)


def rows():
    with sqlite3.connect(os.environ["TODO_DB"]) as conn:
        return conn.execute("SELECT id, text, done FROM tasks ORDER BY id").fetchall()


def items(html):
    """Map task text -> its <li ...>...</li> markup."""
    lis = re.findall(r"<li\b[^>]*>.*?</li>", html, re.S)
    return {re.search(r'<span class="text">(.*?)</span>', li).group(1): li
            for li in lis if 'class="text"' in li}


def test_done_sets_class(client):
    a, _ = add("A"), add("B")
    r = client.post(f"/tasks/{a}/done", follow_redirects=False)
    assert r.status_code == 303
    assert rows() == [(1, "A", 1), (2, "B", 0)]
    li = items(client.get("/").text)
    assert li["A"].startswith('<li class="done">')
    assert "done" not in li["B"].split(">")[0]


def test_done_button_only_on_open_and_css(client):
    a, _ = add("A"), add("B")
    client.post(f"/tasks/{a}/done")
    html = client.get("/").text
    li = items(html)
    assert ">Done</button>" not in li["A"]
    assert ">Done</button>" in li["B"]
    assert '<link rel="stylesheet" href="/static/style.css">' in html
    css = client.get("/static/style.css").text
    assert re.search(r"\.done[^{]*\{[^}]*text-decoration:\s*line-through", css)


def test_delete_removes(client):
    a, _ = add("A"), add("B")
    r = client.post(f"/tasks/{a}/delete", follow_redirects=False)
    assert r.status_code == 303
    assert rows() == [(2, "B", 0)]
    assert list(items(client.get("/").text)) == ["B"]


def test_htmx_vs_redirect(client):
    a, b = add("A"), add("B")
    for path in (f"/tasks/{a}/done", f"/tasks/{b}/delete"):
        r = client.post(path, headers=HX)
        assert r.status_code == 200
        assert "<html" not in r.text
        assert r.text.lstrip().startswith('<ul id="task-list">')
    li = items(r.text)
    assert list(li) == ["A"] and li["A"].startswith('<li class="done">')
    c = add("C")
    for path in (f"/tasks/{c}/done", f"/tasks/{c}/delete"):
        r = client.post(path, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/"


def test_unknown_id_404(client):
    add("A")
    for path in ("/tasks/999/done", "/tasks/999/delete"):
        assert client.post(path, follow_redirects=False).status_code == 404
        assert client.post(path, headers=HX).status_code == 404
    assert rows() == [(1, "A", 0)]


def test_done_twice_idempotent(client):
    a = add("A")
    first = client.post(f"/tasks/{a}/done", headers=HX)
    second = client.post(f"/tasks/{a}/done", headers=HX)
    assert second.status_code == 200 and second.text == first.text
    r = client.post(f"/tasks/{a}/done", follow_redirects=False)
    assert r.status_code == 303
    assert rows() == [(1, "A", 1)]
