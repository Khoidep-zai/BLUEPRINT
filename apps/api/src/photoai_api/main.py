"""Main FastAPI application."""
from fastapi import FastAPI

app = FastAPI(title="Photo AI API", version="0.1.0")


@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return {"status": "ok"}
