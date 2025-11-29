from fastapi import Request, HTTPException
from security import decode_access_token

PUBLIC_ROUTES = (
    "/docs",
    "/openapi.json",
    "/login",
    "/register",
    "/items",
    "/items/"
)

async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith(PUBLIC_ROUTES):
        return await call_next(request)

        auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return await call_next(request)
