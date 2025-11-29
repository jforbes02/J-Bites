from fastapi import Request, HTTPException
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET", "secret_jbites")

async def auth_middleware(request: Request, call_next):
    # Public routes do not require login
    public_routes = [
        "/items",
        "/login",
        "/register",
        "/docs",
        "/openapi.json"
    ]

    if not any(request.url.path.startswith(route) for route in public_routes):
        token = request.headers.get("Authorization")

        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")

        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid or expired token")

    response = await call_next(request)
    return response
