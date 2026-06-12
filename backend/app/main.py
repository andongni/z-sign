from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 - imported so metadata contains all models
from app.api import auth, contracts, reviews, users
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


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "AI智能合同审核系统 FastAPI backend", "docs": "/api/docs"}


@app.get("/api/health/")
def health():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(clauses_router, prefix="/api")
app.include_router(risks_router, prefix="/api")
app.include_router(comparisons_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")

