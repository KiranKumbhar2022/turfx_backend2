from app.admin.schemas.admin_auth_schema import AdminLoginRequest
from app.core.security import createAccessToken
from fastapi import APIRouter, HTTPException

routes = APIRouter(
    prefix="/admin/auth",
    tags=["Admin Authentication"]
)

# Static admin credentials
ADMIN_EMAIL = "admin@123gmail.com"
ADMIN_PASSWORD = "admin@123"


@routes.post("/login")
def admin_login(request: AdminLoginRequest):

    if (
        request.email != ADMIN_EMAIL
        or request.password != ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = createAccessToken({
        "sub": "1",
        "role": "admin"
    })

    return {
        "statusCode": 200,
        "message": "Admin login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {
            "id": 1,
            "name": "Admin",
            "email": ADMIN_EMAIL
        }
    }
