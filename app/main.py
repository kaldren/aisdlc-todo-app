import os
from contextlib import asynccontextmanager
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


def error_response(request: Request, conn, error: str, status: int):
    """HTMX gets a small #form-error partial swapped in place; plain forms get the page."""
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            request, "_error.html", {"error": error}, status_code=status,
            headers={"HX-Retarget": "#form-error", "HX-Reswap": "outerHTML"})
    tasks = db.list_tasks(conn)
    return templates.TemplateResponse(
        request, "index.html", {"tasks": tasks, "error": error}, status_code=status)


def create_app() -> FastAPI:
    db_path = os.environ.get("TODO_DB", "var/todo.db")
    log_path = os.environ.get("TODO_LOG", "var/log/app.jsonl")

    @asynccontextmanager
    async def lifespan(app):
        db.init(db_path)  # at startup, so importing app.main touches no files
        yield

    app = FastAPI(lifespan=lifespan)
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
                return error_response(request, conn, error, 422)
            db.add_task(conn, text)
            return list_response(request, conn)

    @app.post("/tasks/{task_id}/done")
    def done_task(request: Request, task_id: int):
        with db.connect(db_path) as conn:
            if not db.mark_done(conn, task_id):
                return error_response(request, conn, "Task not found", 404)
            return list_response(request, conn)

    @app.post("/tasks/{task_id}/delete")
    def delete_task(request: Request, task_id: int):
        with db.connect(db_path) as conn:
            if not db.delete_task(conn, task_id):
                return error_response(request, conn, "Task not found", 404)
            return list_response(request, conn)

    return app


app = create_app()
