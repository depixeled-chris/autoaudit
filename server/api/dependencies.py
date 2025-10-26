"""Dependency injection for API routes."""

from typing import Generator, Optional, Dict
import sys
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import ComplianceDatabase
from core.config import DATABASE_PATH
from core.auth import decode_access_token
from services.project_service import ProjectService

security = HTTPBearer()


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


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        User data from token payload

    Raises:
        HTTPException: If token is invalid or expired

    Usage in routes:
        @router.get("/protected")
        async def protected_route(current_user: Dict = Depends(get_current_user)):
            user_id = current_user["user_id"]
            ...
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
