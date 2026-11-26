import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.reqlog import RequestLogMiddleware

HERE = Path(__file__).parent
templates = Jinja2Templates(directory=HERE / "templates")


def create_app() -> FastAPI:
    db_path = os.environ.get("TODO_DB", "var/todo.db")
    log_path = os.environ.get("TODO_LOG", "var/log/app.jsonl")
    db.init(db_path)
    app = FastAPI()
    app.add_middleware(RequestLogMiddleware, log_path=log_path)
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def index(request: Request):
        with db.connect(db_path) as conn:
            tasks = db.list_tasks(conn)
        return templates.TemplateResponse(request, "index.html", {"tasks": tasks})

    return app


app = create_app()
