from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from .core.logging import setup_logging
from .api.api_v1.api import router as api_v1_router
from .core.config import settings

# Setup logging at the application's entry point
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="API for the Pai Nai Dee travel planning application.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- Custom Error Handlers ---
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTPException caught: {exc.status_code} {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"RequestValidationError: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

# --- API Routers ---
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", summary="Root", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health", summary="Health Check", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}

# --- Main execution ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
