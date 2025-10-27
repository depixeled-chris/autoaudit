"""API routes for preamble management."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict

from core.database import ComplianceDatabase
from api.dependencies import get_db, get_current_user
from services.preamble_management_service import PreambleManagementService
from services.preamble_service import PreambleService
from schemas.preamble import (
    PreambleCreate, PreambleResponse, PreamblesListResponse,
    PreambleVersionCreate, PreambleVersionUpdate, PreambleVersionResponse,
    PreambleVersionsListResponse,
    PreambleTemplateCreate, PreambleTemplateResponse, PreambleTemplatesListResponse,
    PreambleTestRunCreate, PreambleTestRunResponse, PreambleTestRunsListResponse,
    PreambleVersionPerformanceResponse,
    PreambleCompositionRequest, PreambleCompositionResponse
)

router = APIRouter(prefix="/preambles", tags=["preambles"])


# Templates
@router.post("/templates", response_model=PreambleTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: PreambleTemplateCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new preamble template."""
    service = PreambleManagementService(db)
    try:
        return service.create_template(template_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=PreambleTemplatesListResponse)
async def list_templates(
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List all preamble templates."""
    service = PreambleManagementService(db)
    templates = service.list_templates()
    return PreambleTemplatesListResponse(templates=templates, total=len(templates))


@router.get("/templates/{template_id}", response_model=PreambleTemplateResponse)
async def get_template(
    template_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a preamble template by ID."""
    service = PreambleManagementService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# Preambles
@router.post("", response_model=PreambleResponse, status_code=status.HTTP_201_CREATED)
async def create_preamble(
    preamble_data: PreambleCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new preamble with initial version."""
    service = PreambleManagementService(db)
    try:
        return service.create_preamble(preamble_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PreamblesListResponse)
async def list_preambles(
    scope: Optional[str] = None,
    state_code: Optional[str] = None,
    page_type_code: Optional[str] = None,
    project_id: Optional[int] = None,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List preambles with optional filters."""
    service = PreambleManagementService(db)
    preambles = service.list_preambles(
        scope=scope,
        state_code=state_code,
        page_type_code=page_type_code,
        project_id=project_id
    )
    return PreamblesListResponse(preambles=preambles, total=len(preambles))


@router.get("/{preamble_id}", response_model=PreambleResponse)
async def get_preamble(
    preamble_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a preamble by ID."""
    service = PreambleManagementService(db)
    preamble = service.get_preamble(preamble_id)
    if not preamble:
        raise HTTPException(status_code=404, detail="Preamble not found")
    return preamble


# Versions
@router.post("/{preamble_id}/versions", response_model=PreambleVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    preamble_id: int,
    version_data: PreambleVersionCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new version of a preamble."""
    service = PreambleManagementService(db)

    # Ensure preamble_id matches
    if version_data.preamble_id != preamble_id:
        raise HTTPException(
            status_code=400,
            detail="preamble_id in body must match preamble_id in path"
        )

    try:
        return service.create_version(version_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{preamble_id}/versions", response_model=PreambleVersionsListResponse)
async def list_versions(
    preamble_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List all versions of a preamble."""
    service = PreambleManagementService(db)
    versions = service.list_versions(preamble_id)
    return PreambleVersionsListResponse(versions=versions, total=len(versions))


@router.get("/versions/{version_id}", response_model=PreambleVersionResponse)
async def get_version(
    version_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a preamble version by ID."""
    service = PreambleManagementService(db)
    version = service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.patch("/versions/{version_id}/activate", response_model=PreambleVersionResponse)
async def activate_version(
    version_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Activate a preamble version (retires current active version and invalidates caches)."""
    service = PreambleManagementService(db)
    try:
        return service.activate_version(version_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Test Runs
@router.post("/test-runs", response_model=PreambleTestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_test_run(
    test_data: PreambleTestRunCreate,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new test run record."""
    service = PreambleManagementService(db)
    try:
        return service.create_test_run(test_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/test-runs", response_model=PreambleTestRunsListResponse)
async def list_test_runs(
    preamble_version_id: Optional[int] = None,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """List test runs, optionally filtered by version."""
    service = PreambleManagementService(db)
    test_runs = service.list_test_runs(preamble_version_id=preamble_version_id)
    return PreambleTestRunsListResponse(test_runs=test_runs, total=len(test_runs))


@router.get("/test-runs/{test_id}", response_model=PreambleTestRunResponse)
async def get_test_run(
    test_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a test run by ID."""
    service = PreambleManagementService(db)
    test_run = service.get_test_run(test_id)
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return test_run


@router.get("/versions/{version_id}/performance", response_model=PreambleVersionPerformanceResponse)
async def get_version_performance(
    version_id: int,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get performance metrics for a preamble version."""
    service = PreambleManagementService(db)
    performance = service.get_version_performance(version_id)
    if not performance:
        raise HTTPException(status_code=404, detail="No performance data found for this version")
    return performance


# Composition
@router.post("/compose", response_model=PreambleCompositionResponse)
async def compose_preamble(
    request: PreambleCompositionRequest,
    db: ComplianceDatabase = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Compose a preamble for a specific project and page type."""
    service = PreambleService(db)
    try:
        composed_text = service.compose_preamble(
            project_id=request.project_id,
            page_type_code=request.page_type_code,
            state_code=request.state_code
        )

        # For now, we'll return a simplified response
        # In a future iteration, we could track which components were used
        return PreambleCompositionResponse(
            composed_text=composed_text,
            cached=True,  # We don't track this in current implementation
            components={}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
