from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import (
    RequestValidationError,
    HTTPException as StarletteHTTPException,
)
from fastapi.middleware.cors import CORSMiddleware # Added CORS
import logging  # Moved import to the top

from app.core.logging import setup_logging  #  Import logging setup

# Call logging setup at the application's entry point
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME, # Use project name from settings
    version=settings.PROJECT_VERSION, # Use project version from settings
    description="API for the Pai Nai Dee travel planning application.",
    # openapi_url=f"{settings.API_V1_STR}/openapi.json" # Optional: customize openapi json url
)

# CORS Middleware
# Should be placed before routers and error handlers if possible,
# or at least early in the middleware stack.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def root():
    return {"message": "Welcome to Pai Nai Dee API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Import the main API router
from app.api.api_v1.api import router as api_v1_router  # noqa: E402
from app.core.config import settings  # noqa: E402

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Placeholder for future top-level routers or other versions
# e.g., app.include_router(api_v2_router, prefix="/api/v2")

# --- Custom Error Handlers ---
# import logging # Moved to top

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
    logger.exception(
        f"Unhandled exception: {exc}"
    )  # logger.exception includes stack trace
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )


# --- End Custom Error Handlers ---

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
