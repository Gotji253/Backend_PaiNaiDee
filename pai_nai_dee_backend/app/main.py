from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException as StarletteHTTPException

from app.core.logging import setup_logging # Import logging setup

# Call logging setup at the application's entry point
setup_logging()

app = FastAPI(
    title="Pai Nai Dee API",
    description="API for the Pai Nai Dee travel planning application.",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to Pai Nai Dee API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Import the main API router
from app.api.api_v1.api import router as api_v1_router
from app.core.config import settings

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Placeholder for future top-level routers or other versions
# e.g., app.include_router(api_v2_router, prefix="/api/v2")

# --- Custom Error Handlers ---
import logging
logger = logging.getLogger(__name__)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTPException caught: {exc.status_code} {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the detailed validation errors
    logger.error(f"RequestValidationError: {exc.errors()}")
    # Provide a user-friendly message and the detailed errors
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the full traceback for unexpected errors
    logger.exception(f"Unhandled exception: {exc}") # logger.exception includes stack trace
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

# --- End Custom Error Handlers ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
