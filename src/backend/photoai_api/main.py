"""Main FastAPI application."""
from . import paths  # noqa: F401  (must run before the worker imports)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .errors import APIError, ErrorCode
from .routers import jobs, recipes

app = FastAPI(title=settings.app_name, version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATUS_BY_CODE = {
    ErrorCode.INVALID_FILE_TYPE: 400,
    ErrorCode.INVALID_PARAMS: 400,
    ErrorCode.IMAGE_TOO_SMALL: 400,
    ErrorCode.IMAGE_TOO_LARGE: 413,
    ErrorCode.OWNERSHIP_REQUIRED: 403,
    ErrorCode.RECIPE_NOT_FOUND: 404,
    ErrorCode.JOB_NOT_FOUND: 404,
    ErrorCode.NO_FACE_DETECTED: 422,
    ErrorCode.NO_CLOSED_EYES: 422,
    ErrorCode.FILTER_REJECTED: 422,
    ErrorCode.QA_FAILED_BEST_EFFORT: 200,
}


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Return a stable ``{"error": {"code", "message"}}`` envelope."""
    code = exc.code if isinstance(exc.code, ErrorCode) else ErrorCode(exc.code)
    status = _STATUS_BY_CODE.get(code, 400)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code.value, "message": exc.message}},
    )


@app.get("/healthz")
def healthz() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(recipes.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")

# Serve the bundled frontend (src/frontend) at the root path. Mounting last
# keeps /api and /healthz routes taking precedence.
if paths.FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(paths.FRONTEND_DIR), html=True), name="frontend")
