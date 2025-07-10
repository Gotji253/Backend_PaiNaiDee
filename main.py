from fastapi import FastAPI

app = FastAPI(title="Travel Planner API", version="0.1.0")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Travel Planner API"}

# Placeholder for later: DB initialization, middleware, routers
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
