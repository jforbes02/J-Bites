from fastapi import Request, HTTPException
from middleware.security import decode_access_token, verify_admin_token
from Database.dbConnect import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

PUBLIC_ROUTES = (
    "/docs",
    "/openapi.json",
    "/login",
    "/register",
    "/items",
    "/items/",
    "/admin/login",
    "/payment-success",
    "/payment-cancelled",
    "/stripe-webhook",
    "/",  # Home page
    "/login.html",  # Login page
    "/register.html",  # Register page
    "/static",  # Static files (CSS, JS, images)
)

ADMIN_ONLY_ROUTES = (
    "/admin/orders",
)


async def auth_middleware(request: Request, call_next):
    # Dev mode bypass
    if os.getenv("DEV_MODE") == "True":
        return await call_next(request)

    path = request.url.path

    # Allow public routes
    if path.startswith(PUBLIC_ROUTES):
        return await call_next(request)

    # Check for admin-only routes
    if any(path.startswith(route) for route in ADMIN_ONLY_ROUTES):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")

        token = auth_header.split(" ")[1]

        # Verify admin token
        db = SessionLocal()
        try:
            if not verify_admin_token(token, db):
                raise HTTPException(
                    status_code=403,
                    detail="Admin access required"
                )
        finally:
            db.close()

        return await call_next(request)

    # Regular authentication for all other routes
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return await call_next(request)