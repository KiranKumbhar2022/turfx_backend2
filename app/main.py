from fastapi import FastAPI
from app.database.database import engine,Base
from fastapi.middleware.cors import CORSMiddleware
from app.service.firebase_service import initialize_firebase
from app.client.routes import auth_route
from app.owner.routes import owner_auth_route
from app.admin.routes import admin_auth_routes
from app.owner.routes import notification_route

app = FastAPI()
# CORS Configuration for Flutter Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:52841",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:7357",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:7357",
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

@app.get("/")
def root():
    return {
        "message":"Server is created"
    }