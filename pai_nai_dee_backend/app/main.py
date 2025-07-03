from fastapi import FastAPI

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

# Import routers
from .routers import recommendations, reviews, users_router, places_router, auth_router
from .database import Base, engine # For table creation if used
# from .database import create_db_and_tables # If using this function

# Create all tables (alternative to Alembic for quick dev setup)
Base.metadata.create_all(bind=engine)
# Make sure all models are imported in database.py or via models/__init__.py for this to work

app.include_router(recommendations.router)
app.include_router(reviews.router)
app.include_router(users_router.router)
app.include_router(places_router.router)
app.include_router(auth_router.router) # Added auth router

# # Optional: Create tables on startup using the function from database.py
# @app.on_event("startup")
# def on_startup():
#     print("Attempting to create database tables if they don't exist...")
#     create_db_and_tables()
#     print("Database table check/creation complete.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
