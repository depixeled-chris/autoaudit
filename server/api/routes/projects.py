"""Project management API routes."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from schemas.project import ProjectCreate, ProjectResponse, ProjectSummary
from services.project_service import ProjectService
from services.screenshot_service import ScreenshotService
from api.dependencies import get_project_service
from core.database import ComplianceDatabase
from core.config import DATABASE_PATH

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    service: ProjectService = Depends(get_project_service)
):
    """
    Create a new project.

    A project represents a dealership or group of dealerships to monitor.
    """
    try:
        return service.create_project(project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(service: ProjectService = Depends(get_project_service)):
    """
    List all projects.

    Returns all projects ordered by creation date (newest first).
    """
    return service.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service)
):
    """
    Get a specific project by ID.
    """
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/summary", response_model=ProjectSummary)
async def get_project_summary(
    project_id: int,
    service: ProjectService = Depends(get_project_service)
):
    """
    Get project summary statistics.

    Returns aggregate statistics including:
    - Total URLs monitored
    - Total checks performed
    - Average compliance score
    - Number of compliant checks
    - Total violations found
    """
    summary = service.get_project_summary(project_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Project not found")
    return summary


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service)
):
    """
    Delete a project.

    Note: This will not delete associated URLs or checks (foreign key constraints).
    Consider marking as inactive instead.
    """
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        service.delete_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@router.post("/{project_id}/screenshot", response_model=ProjectResponse)
async def capture_project_screenshot(
    project_id: int,
    background_tasks: BackgroundTasks,
    service: ProjectService = Depends(get_project_service)
):
    """
    Capture a screenshot of the project's base URL.

    The screenshot is captured in the background and the project is returned immediately.
    The screenshot will be available once the background task completes.
    """
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.base_url:
        raise HTTPException(status_code=400, detail="Project has no base_url set")

    # Capture screenshot in background
    async def capture_screenshot():
        db = ComplianceDatabase(DATABASE_PATH)
        try:
            screenshot_service = ScreenshotService(db)
            await screenshot_service.capture_project_screenshot(
                project_id=project_id,
                url=project.base_url
            )
        finally:
            db.close()

    background_tasks.add_task(capture_screenshot)

    return project
