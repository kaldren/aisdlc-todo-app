import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.reqlog import RequestLogMiddleware

HERE = Path(__file__).parent
templates = Jinja2Templates(directory=HERE / "templates")
MAX_LEN = 200


def validate(text: str) -> str | None:
    if not text:
        return "Task text is required"
    if len(text) > MAX_LEN:
        return f"Task text must be at most {MAX_LEN} characters"
    return None


def list_response(request: Request, conn):
    """HTMX gets the updated #task-list fragment; plain forms get 303 to /."""
    if request.headers.get("HX-Request") == "true":
        tasks = db.list_tasks(conn)
        return templates.TemplateResponse(request, "_task_list.html", {"tasks": tasks})
    return RedirectResponse("/", status_code=303)


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

    @app.post("/tasks")
    def create_task(request: Request, text: str = Form("")):
        text = text.strip()
        with db.connect(db_path) as conn:
            error = validate(text)
            if error:
                tasks = db.list_tasks(conn)
                return templates.TemplateResponse(
                    request, "index.html", {"tasks": tasks, "error": error}, status_code=422)
            db.add_task(conn, text)
            return list_response(request, conn)

    return app


app = create_app()
