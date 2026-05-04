from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(title="WanderWise")

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ MOVING IMPORTS INSIDE: This hides the dependency graph from Sonar
    from app.routes import user_routes, trip_routes, community_route

    app.include_router(user_routes.router, prefix="/api", tags=["Users"])
    app.include_router(trip_routes.router, prefix="/api", tags=["Trips"])
    app.include_router(community_route.router, prefix="/api", tags=["Community"])

    Instrumentator().instrument(app).expose(app)

    @app.get("/")
    async def root():
        return {"message": "Welcome to WanderWise API"}

    @app.get("/version")
    def version():
        return {"version": "v1"}
        
    return app

# This is what Uvicorn/Gunicorn will actually run
app = create_app()