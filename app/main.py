from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator # ✅ Add this

def create_app() -> FastAPI:
    app = FastAPI(title="WanderWise")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routes import user_routes, trip_routes, community_route
    app.include_router(user_routes.router, prefix="/api", tags=["Users"])
    app.include_router(trip_routes.router, prefix="/api", tags=["Trips"])
    app.include_router(community_route.router, prefix="/api", tags=["Community"])

    # ✅ Instrument the app to expose the /metrics endpoint
    Instrumentator().instrument(app).expose(app)

    @app.get("/")
    async def root():
        return {"message": "Welcome to WanderWise API"}

    return app

app = create_app()