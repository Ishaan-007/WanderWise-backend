from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import community_route, user_routes, trip_routes

app = FastAPI(title="WanderWise")

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can later restrict this to your frontend domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Routes
app.include_router(user_routes.router, prefix="/api", tags=["Users"])
app.include_router(trip_routes.router, prefix="/api", tags=["Trips"])
#app.include_router(trip_routes_2.router, prefix="/api", tags=["Trips_2"])
app.include_router(community_route.router, prefix="/api", tags=["Community"])

@app.get("/")
async def root():
    return {"message": "Welcome to WanderWise API"}

@app.get("/version")
def version():
    return {"version": "v1"}
