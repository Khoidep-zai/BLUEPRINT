"""FastAPI app factory (S13 Backend API & Job Queue)."""
from __future__ import annotations

from fastapi import FastAPI

from photoai_api.config import settings
from photoai_api.routers import jobs, uploads, recipes, feedback, assets

app = FastAPI(title=settings.app_name, version="0.1.0")

app.include_router(jobs.router)
app.include_router(uploads.router)
app.include_router(recipes.router)
app.include_router(assets.router)
app.include_router(feedback.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "environment": settings.environment}
