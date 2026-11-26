import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("TODO_DB", str(tmp_path / "todo.db"))
    monkeypatch.setenv("TODO_LOG", str(tmp_path / "log" / "app.jsonl"))
    return tmp_path


@pytest.fixture
def client(env):
    with TestClient(create_app()) as c:
        yield c
