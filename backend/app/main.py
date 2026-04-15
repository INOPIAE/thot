"""
Main application entry point.
This module is responsible for loading routes and starting the FastAPI app.
"""

from app import create_app
from app.routes.api import api_router

app = create_app()

# Router registrieren
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    from config import config

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
    )
