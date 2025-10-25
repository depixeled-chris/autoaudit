"""Dependency injection for API routes."""

from typing import Generator
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import ComplianceDatabase
from core.config import DATABASE_PATH
from services.project_service import ProjectService


def get_db() -> Generator[ComplianceDatabase, None, None]:
    """
    Get database instance for dependency injection.

    Yields:
        Database instance

    Usage in routes:
        @router.get("/")
        async def list_items(db: ComplianceDatabase = Depends(get_db)):
            ...
    """
    db = ComplianceDatabase(DATABASE_PATH)
    try:
        yield db
    finally:
        db.close()


def get_project_service() -> Generator[ProjectService, None, None]:
    """
    Get project service instance for dependency injection.

    Yields:
        ProjectService instance

    Usage in routes:
        @router.post("/")
        async def create_project(
            project: ProjectCreate,
            service: ProjectService = Depends(get_project_service)
        ):
            return service.create_project(project)
    """
    db = ComplianceDatabase(DATABASE_PATH)
    service = ProjectService(db)
    try:
        yield service
    finally:
        service.close()
