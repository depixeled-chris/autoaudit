"""FastAPI application for Auto Dealership Compliance Checker."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import sys
from pathlib import Path
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routes import projects, urls, checks, templates, reports, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Auto Dealership Compliance API",
    description="""
    API for checking automotive dealership website compliance with state advertising regulations.

    ## Features

    * **Multi-project management** - Organize URLs by dealership/client
    * **Template caching** - Reuse compliance decisions for known templates
    * **Visual verification** - GPT-4V screenshot analysis for spatial rules
    * **Historical tracking** - Complete audit trail of all checks
    * **Automated checks** - Schedule recurring compliance checks

    ## Workflow

    1. Create a **project** for your dealership
    2. Add **URLs** to monitor
    3. Run **compliance checks** (text + visual analysis)
    4. View **reports** and violation details
    5. Track compliance over time

    ## States Supported

    Currently supporting: **CA, TX, NY, OK**
    """,
    version="1.0.0",
    contact={
        "name": "AutoAudit Support",
        "email": "support@autoaudit.example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for screenshots
screenshots_dir = Path(__file__).parent.parent / "screenshots"
screenshots_dir.mkdir(parents=True, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")

# Include routers
app.include_router(auth.router)  # Auth routes (already has /api/auth prefix)
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(urls.router, prefix="/api/urls", tags=["URLs"])
app.include_router(checks.router, prefix="/api/checks", tags=["Compliance Checks"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Auto Dealership Compliance API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
