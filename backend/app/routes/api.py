"""
API Routes initialization
"""

from fastapi import APIRouter
from app.routes import auth, users, config, records, pages

# Create main router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(config.router)
api_router.include_router(records.router)
api_router.include_router(pages.router)

# Export
__all__ = ["api_router"]
