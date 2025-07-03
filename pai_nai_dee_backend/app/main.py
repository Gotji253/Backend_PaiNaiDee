from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
# from .database import engine, Base # Will be used later to create tables
# from .routers import auth_router, places_router, reviews_router # Example, adjust as routers are created

# Base.metadata.create_all(bind=engine) # Initialize database tables (consider Alembic for production)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/api/openapi.json", # Customize OpenAPI docs path
    docs_url="/api/docs", # Customize Swagger UI path
    redoc_url="/api/redoc" # Customize ReDoc path
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Basic Error Handler for HTTPExceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Example of a more generic error handler (optional)
# @app.exception_handler(Exception)
# async def generic_exception_handler(request: Request, exc: Exception):
#     # Log the exception here
#     print(f"Unhandled exception: {exc}") # Basic logging
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "An unexpected error occurred."},
#     )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "project_name": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}

@app.get("/") # Keep a root path for basic checks
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


# Placeholder for including routers
# from .routers import auth, users, places, reviews # etc.
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/api/users", tags=["Users"])
# app.include_router(places.router, prefix="/api/places", tags=["Places"])
# app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])


if __name__ == "__main__":
    import uvicorn
    # Uvicorn expects the app instance as a string 'module:variable'
    # or directly as an app instance if running programmatically.
    # For reload, it's better to run from command line: uvicorn app.main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
