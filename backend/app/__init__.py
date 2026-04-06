"""
Main FastAPI application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path
from typing import AsyncIterator

from config import config
from app.database import Base, engine, get_db
from app.services.page_ocr_job_service import PageOcrJobService

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# NOTE: Do NOT create tables here. Use `python scripts/init_db.py` instead.
# This prevents database connection attempts during app import.


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle resources."""
    try:
        yield
    finally:
        PageOcrJobService.shutdown()

# Create FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="RESTful API for NLF Database Management",
    terms_of_service=config.API_TERMS_OF_SERVICE_URL,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "authentication", "description": "Authentication and user management"},
        {"name": "users", "description": "User management and profile"},
        {"name": "roles", "description": "Role and permission management"},
        {"name": "records", "description": "Record and object management"},
        {"name": "pages", "description": "Page management and OCR processing"},
        {"name": "admin-record-import", "description": "Admin-only record import routes"},
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Trusted Host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com"],
)

# Mount static files for uploaded documents
# Ensure upload directory exists
config.ensure_upload_directory()
if config.UPLOAD_DIRECTORY.exists():
    app.mount("/uploads", StaticFiles(directory=str(config.UPLOAD_DIRECTORY)), name="uploads")
    logger.info(f"Static files (uploads) mounted at /uploads from {config.UPLOAD_DIRECTORY}")

# Mount assets for logo and other static assets
assets_dir = Path(__file__).parent.parent / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    logger.info(f"Static files (assets) mounted at /assets from {assets_dir}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": config.APP_NAME
    }


# NOTE: Router imports are deferred to avoid circular imports and schema
# resolution issues during module initialization. They are loaded only
# when the app is actually run (see app/main.py).

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
    )
