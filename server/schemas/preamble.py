"""Preamble management schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Preamble Templates
class PreambleTemplateBase(BaseModel):
    """Base preamble template schema."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = None
    template_structure: str = Field(..., description="Jinja2 template structure")
    is_default: bool = Field(default=False)


class PreambleTemplateCreate(PreambleTemplateBase):
    """Schema for creating a preamble template."""
    pass


class PreambleTemplateResponse(PreambleTemplateBase):
    """Preamble template response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Preambles
class PreambleBase(BaseModel):
    """Base preamble schema."""
    name: str = Field(..., description="Human-readable name")
    scope: str = Field(..., pattern="^(universal|state|page_type|project)$")
    page_type_code: Optional[str] = None
    state_code: Optional[str] = None
    project_id: Optional[int] = None


class PreambleCreate(PreambleBase):
    """Schema for creating a preamble."""
    created_via: str = Field(..., pattern="^(config|project_override)$")
    created_by: Optional[int] = None
    initial_text: str = Field(..., description="Initial preamble text for version 1")


class PreambleResponse(PreambleBase):
    """Preamble response schema."""
    id: int
    machine_name: str
    created_via: str
    created_at: datetime
    created_by: Optional[int]
    active_version: Optional['PreambleVersionResponse'] = None

    class Config:
        from_attributes = True


# Preamble Versions
class PreambleVersionBase(BaseModel):
    """Base preamble version schema."""
    preamble_text: str = Field(..., description="The preamble content")
    change_summary: Optional[str] = None


class PreambleVersionCreate(PreambleVersionBase):
    """Schema for creating a preamble version."""
    preamble_id: int
    created_by: Optional[int] = None


class PreambleVersionUpdate(BaseModel):
    """Schema for updating a preamble version."""
    status: str = Field(..., pattern="^(draft|active|retired)$")


class PreambleVersionResponse(PreambleVersionBase):
    """Preamble version response schema."""
    id: int
    preamble_id: int
    version_number: int
    status: str
    created_at: datetime
    created_by: Optional[int]
    performance: Optional['PreambleVersionPerformanceResponse'] = None

    class Config:
        from_attributes = True


# Preamble Version Performance
class PreambleVersionPerformanceResponse(BaseModel):
    """Preamble version performance metrics."""
    id: int
    preamble_version_id: int
    test_runs_count: int
    avg_score: Optional[float]
    score_stddev: Optional[float]
    avg_confidence: Optional[float]
    false_positive_rate: Optional[float]
    false_negative_rate: Optional[float]
    avg_cost: Optional[float]
    avg_duration_seconds: Optional[float]
    last_tested_at: Optional[datetime]

    class Config:
        from_attributes = True


# Preamble Test Runs
class PreambleTestRunCreate(BaseModel):
    """Schema for creating a test run."""
    preamble_version_id: int
    url_id: int
    score_achieved: Optional[float]
    violations_found: Optional[str]
    confidence_score: Optional[float]
    token_count: Optional[int]
    cost: Optional[float]
    duration_seconds: Optional[float]
    model_used: str
    false_positive: Optional[bool]
    false_negative: Optional[bool]


class PreambleTestRunResponse(PreambleTestRunCreate):
    """Preamble test run response schema."""
    id: int
    run_date: datetime

    class Config:
        from_attributes = True


# Default Page Type Preamble Assignments
class DefaultPageTypePreambleBase(BaseModel):
    """Base schema for default page type preamble assignment."""
    page_type_code: str
    preamble_id: int
    active_version_id: int


class DefaultPageTypePreambleCreate(DefaultPageTypePreambleBase):
    """Schema for creating default page type preamble."""
    pass


class DefaultPageTypePreambleResponse(DefaultPageTypePreambleBase):
    """Default page type preamble response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Project Page Type Preamble Overrides
class ProjectPageTypePreambleBase(BaseModel):
    """Base schema for project page type preamble override."""
    project_id: int
    page_type_code: str
    preamble_id: int
    active_version_id: int
    override_reason: Optional[str] = None


class ProjectPageTypePreambleCreate(ProjectPageTypePreambleBase):
    """Schema for creating project page type preamble override."""
    pass


class ProjectPageTypePreambleResponse(ProjectPageTypePreambleBase):
    """Project page type preamble override response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List responses
class PreambleTemplatesListResponse(BaseModel):
    """Response for list of preamble templates."""
    templates: List[PreambleTemplateResponse]
    total: int


class PreamblesListResponse(BaseModel):
    """Response for list of preambles."""
    preambles: List[PreambleResponse]
    total: int


class PreambleVersionsListResponse(BaseModel):
    """Response for list of preamble versions."""
    versions: List[PreambleVersionResponse]
    total: int


class PreambleTestRunsListResponse(BaseModel):
    """Response for list of test runs."""
    test_runs: List[PreambleTestRunResponse]
    total: int


# Composition
class PreambleCompositionRequest(BaseModel):
    """Request to compose a preamble."""
    project_id: int
    page_type_code: str
    state_code: Optional[str] = None


class PreambleCompositionResponse(BaseModel):
    """Response with composed preamble."""
    composed_text: str
    cached: bool
    components: dict = Field(
        description="Components used in composition",
        example={
            "universal_version_id": 1,
            "state_version_id": 2,
            "page_type_version_id": 3,
            "project_version_id": None
        }
    )


# Update forward references
PreambleResponse.model_rebuild()
PreambleVersionResponse.model_rebuild()
