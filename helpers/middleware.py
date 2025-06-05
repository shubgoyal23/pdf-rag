from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from helpers.jwt_utils import verify_token

INCLUDE_PATHS = ["/chat", "/user"]

class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path not in INCLUDE_PATHS:
            return await call_next(request)

        # 1. Check cookie
        token = request.cookies.get("access_token")

        if not token:
            return JSONResponse(status_code=401, content={"detail": "user not logged in"})

        payload = verify_token(token)
        if not payload:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        request.state.user = payload
        return await call_next(request)

