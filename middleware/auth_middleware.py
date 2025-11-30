from fastapi import Request, HTTPException
from middleware.security import decode_access_token, verify_admin_token
from Database.dbConnect import SessionLocal
from config.config import settings
import logging

logger = logging.getLogger(__name__)

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
    "/health",
    "/",
    "/login.html",
    "/register.html",
    "/static",
)

ADMIN_ONLY_ROUTES = (
    "/admin/orders",
)


async def auth_middleware(request: Request, call_next):
    # ONLY bypass auth in development with explicit flag
    # This should NEVER be true in production (validated in settings)
    if settings.DISABLE_AUTH and settings.is_development():
        logger.warning(f"⚠️  AUTH DISABLED for {request.url.path} - DEVELOPMENT MODE ONLY")
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