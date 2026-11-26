import os

from fastapi import FastAPI

from app.reqlog import RequestLogMiddleware


def create_app() -> FastAPI:
    log_path = os.environ.get("TODO_LOG", "var/log/app.jsonl")
    app = FastAPI()
    app.add_middleware(RequestLogMiddleware, log_path=log_path)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
