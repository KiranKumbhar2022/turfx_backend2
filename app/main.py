
from fastapi import FastAPI
from app.database.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

from app.service.firebase_service import initialize_firebase

from app.client.routes import auth_route
from app.owner.routes import owner_auth_route
from app.admin.routes import admin_owner_route
from app.owner.routes import notification_route
from app.owner.routes import turf_route
from app.client.routes import user_turf_routes
from app.admin.routes import admin_user_route
from app.admin.routes import admin_owner_route

app = FastAPI(
    title="TurfX API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(engine)
initialize_firebase()

app.include_router(auth_route.routes)
app.include_router(owner_auth_route.routes)
app.include_router(admin_owner_route.routes)
app.include_router(notification_route.routes)
app.include_router(turf_route.routes)
app.include_router(user_turf_routes.routes)
app.include_router(admin_user_route.routes)
# app.include_router(admin_owner_route.routes)


@app.get("/")
def root():
    return {
        "message": "Server is created"
    }
