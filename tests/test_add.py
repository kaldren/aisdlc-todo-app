import json
import os
import re
import sqlite3

HX = {"HX-Request": "true"}


def stored_texts():
    with sqlite3.connect(os.environ["TODO_DB"]) as conn:
        return [row[0] for row in conn.execute("SELECT text FROM tasks ORDER BY id")]


def test_add_redirects_and_lists(client):
    r = client.post("/tasks", data={"text": "Buy milk"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    html = client.get("/").text
    assert "Buy milk" in html
    assert 'class="done"' not in html
    assert "No tasks yet" not in html


def test_add_htmx_returns_fragment(client):
    r = client.post("/tasks", data={"text": "Buy milk"}, headers=HX)
    assert r.status_code == 200
    assert "<html" not in r.text
    assert r.text.lstrip().startswith('<ul id="task-list">')
    assert "Buy milk" in r.text


def test_oldest_first(client):
    client.post("/tasks", data={"text": "A"})
    client.post("/tasks", data={"text": "B"})
    html = client.get("/").text
    assert ">A</span>" in html and ">B</span>" in html
    assert html.index(">A</span>") < html.index(">B</span>")


def test_blank_rejected(client):
    for data in ({"text": ""}, {"text": "   "}, {}):
        r = client.post("/tasks", data=data, follow_redirects=False)
        assert r.status_code == 422
        assert "Task text is required" in r.text
    assert stored_texts() == []


def test_too_long_rejected(client):
    r = client.post("/tasks", data={"text": "x" * 201}, follow_redirects=False)
    assert r.status_code == 422
    assert "Task text must be at most 200 characters" in r.text
    assert stored_texts() == []
    r = client.post("/tasks", data={"text": "  " + "y" * 200 + "  "}, follow_redirects=False)
    assert r.status_code == 303
    assert stored_texts() == ["y" * 200]


def test_text_trimmed(client):
    client.post("/tasks", data={"text": "  Buy milk  "})
    assert stored_texts() == ["Buy milk"]


def test_html_escaped(client):
    client.post("/tasks", data={"text": "<b>x</b>"})
    html = client.get("/").text
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert "<b>x</b>" not in html


def test_blank_rejected_htmx_gets_error_partial(client):
    r = client.post("/tasks", data={"text": "   "}, headers=HX)
    assert r.status_code == 422
    assert "<html" not in r.text and "task-list" not in r.text
    assert r.text.strip() == '<p id="form-error" class="error" role="alert">Task text is required</p>'
    assert r.headers["HX-Retarget"] == "#form-error"
    assert r.headers["HX-Reswap"] == "outerHTML"
    assert stored_texts() == []


def test_page_gives_feedback_for_blank_text(client):
    html = client.get("/").text
    assert re.search(r'<input [^>]*pattern="\.\*\\S\.\*"[^>]*title="Task text is required"', html)
    assert '<p id="form-error" class="error" role="alert"></p>' in html
    config = json.loads(re.search(r"<meta name=\"htmx-config\" content='(.*?)'>", html, re.S).group(1))
    rule = next(h for h in config["responseHandling"] if re.search(h["code"], "422"))
    assert rule["swap"] is True and rule["error"] is True
    assert next(h for h in config["responseHandling"] if re.search(h["code"], "404")) == rule
    assert next(h for h in config["responseHandling"] if re.search(h["code"], "500"))["swap"] is False
