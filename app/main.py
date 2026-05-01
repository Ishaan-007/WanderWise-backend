from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.community_route import router as community_router
from app.routes.user_routes import router as user_router

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
app.include_router(user_router, prefix="/api", tags=["Users"])
#app.include_router(trip_routes.router, prefix="/api", tags=["Trips"])
#app.include_router(trip_routes_2.router, prefix="/api", tags=["Trips_2"])
app.include_router(community_router, prefix="/api", tags=["Community"])

@app.get("/")
async def root():
    return {"message": "Welcome to WanderWise API"}

@app.get("/version")
def version():
    return {"version": "v1"}
