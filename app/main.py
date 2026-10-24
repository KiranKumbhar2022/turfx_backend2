from fastapi import FastAPI
from app.database.database import engine,Base
from fastapi.middleware.cors import CORSMiddleware
from app.service.firebase_service import initialize_firebase
from app.client.routes import auth_route
from app.owner.routes import owner_auth_route
from app.admin.routes import admin_auth_routes
from app.owner.routes import notification_route
from app.owner.routes import turf_route
from app.client.routes import user_turf_routes

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:64082",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(engine)
initialize_firebase()

app.include_router(auth_route.routes)
app.include_router(owner_auth_route.routes)
app.include_router(admin_auth_routes.routes)
app.include_router(notification_route.routes)
app.include_router(turf_route.routes)
app.include_router(user_turf_routes.routes)

@app.get("/")
def root():
    return {
        "message":"Server is created"
    }