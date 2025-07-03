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

# Placeholder for future routers
# from .routes import users, places, trips, reviews
# app.include_router(users.router)
# app.include_router(places.router)
# app.include_router(trips.router)
# app.include_router(reviews.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
