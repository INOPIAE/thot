"""
CSRF Middleware for FastAPI
- Issues a CSRF token as a cookie on login/session creation
- Validates CSRF token on protected endpoints (e.g. PDF routes)
- Token is expected in a custom header (e.g. X-CSRF-Token)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status
import secrets

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"

# Allow any prefix before /auth/login etc. (e.g. /api/v1/auth/login)
CSRF_EXEMPT_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/register",
    "/api/v1/auth/register/confirm",
    "/api/v1/auth/confirm",
    "/api/v1/auth/password-reset",
    "/api/v1/auth/password-reset/confirm",
    "/api/v1/auth/request-password-reset",
    "/api/v1/auth/otp-reset",
    "/api/v1/auth/otp-reset/confirm",
    "/api/v1/auth/bootstrap",
    "/api/v1/auth/tos",
    "/auth/login",
    "/auth/logout",
    "/auth/register",
    "/auth/register/confirm",
    "/auth/confirm",
    "/auth/password-reset",
    "/auth/password-reset/confirm",
    "/auth/request-password-reset",
    "/auth/otp-reset",
    "/auth/otp-reset/confirm",
    "/auth/bootstrap",
    "/auth/tos",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/health",
    "/status",
    "/config"
]

class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next):

        # Exempt safe methods and exempt paths (robust)
        path = request.url.path
        if request.method in ("GET", "OPTIONS", "HEAD") or any(path.startswith(p) for p in CSRF_EXEMPT_PATHS):
            return await call_next(request)

        # Get CSRF token from cookie and header
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)
        from fastapi.responses import JSONResponse
        if not cookie_token or not header_token:
            # No token present: treat as not authenticated
            return JSONResponse({"detail": "CSRF token missing"}, status_code=status.HTTP_401_UNAUTHORIZED)
        if cookie_token != header_token:
            # Token present but invalid
            return JSONResponse({"detail": "CSRF token invalid"}, status_code=status.HTTP_403_FORBIDDEN)
        return await call_next(request)

    @staticmethod
    def generate_csrf_token() -> str:
        return secrets.token_urlsafe(32)
