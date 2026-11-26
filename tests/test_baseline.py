import json

from fastapi.testclient import TestClient

from app.main import create_app


def read_log(env):
    lines = (env / "log" / "app.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines]


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_request_logged_as_json(client, env):
    client.get("/health")
    records = read_log(env)
    assert len(records) == 1
    rec = records[0]
    assert {"ts", "level", "event", "method", "path", "status", "ms"} <= rec.keys()
    assert rec["level"] == "info"
    assert rec["method"] == "GET"
    assert rec["path"] == "/health"
    assert rec["status"] == 200
    assert isinstance(rec["ms"], (int, float))


def test_unhandled_error_logged(env):
    app = create_app()

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/boom")
    assert r.status_code == 500
    rec = read_log(env)[-1]
    assert rec["level"] == "error"
    assert rec["event"] == "unhandled_error"
    assert rec["error"] == "RuntimeError: kaboom"
    assert rec["status"] == 500
    assert rec["path"] == "/boom"
