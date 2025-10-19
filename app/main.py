from fastapi import FastAPI
from app.routes import user_routes

app = FastAPI(title="WanderWise")

app.include_router(user_routes.router, prefix="/api", tags=["Users"])

@app.get("/")
async def root():
    return {"message": "Welcome to WanderWise API"}
