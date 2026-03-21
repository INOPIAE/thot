"""
API Routes initialization
"""

from fastapi import APIRouter
from app.routes import auth, users, config, records, pages, roles, legal_content, public_links

# Create main router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(config.router)
api_router.include_router(legal_content.router)
api_router.include_router(records.router)
api_router.include_router(pages.router)
api_router.include_router(roles.router)
api_router.include_router(public_links.router)

# Export
__all__ = ["api_router"]
