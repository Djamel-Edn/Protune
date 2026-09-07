"""Protune API entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import ProtuneError, protune_error_handler
from app.routers import cv, health

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Tailors a CV and drafts a cover letter from a job posting.",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_exception_handler(ProtuneError, protune_error_handler)

app.include_router(health.router, prefix="/api/v1")
app.include_router(cv.router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs", "health": "/api/v1/health"}
