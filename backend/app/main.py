import uuid as uuid_lib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app import models  # noqa: F401 - imported so metadata contains all models
from app.api import auth, contracts, portal, reviews, users
from app.api.catalogs import (
    clauses_router,
    comparisons_router,
    knowledge_router,
    recommendations_router,
    risks_router,
    rules_router,
)
from app.core.config import get_settings
from app.core.database import Base, engine


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="2.0.0-fastapi",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.media_root.mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url, StaticFiles(directory=str(settings.media_root)), name="media")


def ensure_schema_compatibility() -> None:
    inspector = inspect(engine)
    if "portal_file_review_record" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("portal_file_review_record")}
    with engine.begin() as connection:
        if "duration_seconds" not in columns:
            connection.execute(
                text("ALTER TABLE portal_file_review_record ADD COLUMN duration_seconds INTEGER NOT NULL DEFAULT 0")
            )
        if "task_id" not in columns:
            connection.execute(text("ALTER TABLE portal_file_review_record ADD COLUMN task_id VARCHAR(36) NULL"))
        if "task_status" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE portal_file_review_record "
                    "ADD COLUMN task_status VARCHAR(20) NOT NULL DEFAULT 'succeeded'"
                )
            )
            connection.execute(
                text(
                    "UPDATE portal_file_review_record "
                    "SET task_status = CASE "
                    "WHEN status = 'failed' THEN 'failed' "
                    "WHEN status = 'processing' THEN 'running' "
                    "ELSE 'succeeded' END"
                )
            )
        rows = list(connection.execute(
            text("SELECT id FROM portal_file_review_record WHERE task_id IS NULL OR task_id = ''")
        ).mappings())
        for row in rows:
            connection.execute(
                text("UPDATE portal_file_review_record SET task_id = :task_id WHERE id = :id"),
                {"task_id": str(uuid_lib.uuid4()), "id": row["id"]},
            )


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()


@app.get("/")
def root():
    return {"message": "AI智能合同审核系统 FastAPI backend", "docs": "/api/docs"}


@app.get("/api/health/")
def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(portal.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(clauses_router, prefix="/api")
app.include_router(risks_router, prefix="/api")
app.include_router(comparisons_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
