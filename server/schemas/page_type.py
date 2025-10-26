"""Page type related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional


class PageTypeCreate(BaseModel):
    """Request model for creating a page type."""
    code: str = Field(..., description="Unique code (e.g., VDP, HOMEPAGE)")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Description of the page type")


class PageTypeUpdate(BaseModel):
    """Request model for updating a page type."""
    name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Description")
    active: Optional[bool] = Field(None, description="Active status")
    preamble: Optional[str] = Field(None, description="Preamble text sent with compliance analysis")
    extraction_template: Optional[str] = Field(None, description="Template for extracting important data")
    requires_llm_visual_confirmation: Optional[bool] = Field(None, description="Requires LLM visual analysis")
    requires_human_confirmation: Optional[bool] = Field(None, description="Requires human review")


class PageTypeResponse(BaseModel):
    """Response model for page type data."""
    id: int
    code: str
    name: str
    description: Optional[str]
    active: bool
    preamble: Optional[str]
    extraction_template: Optional[str]
    requires_llm_visual_confirmation: bool
    requires_human_confirmation: bool
    created_at: str
    updated_at: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "code": "VDP",
                    "name": "Vehicle Detail Page",
                    "description": "Individual vehicle listing page",
                    "active": True,
                    "preamble": "Analyze this VDP for compliance...",
                    "extraction_template": None,
                    "requires_llm_visual_confirmation": True,
                    "requires_human_confirmation": False,
                    "created_at": "2025-10-26T10:00:00",
                    "updated_at": "2025-10-26T10:00:00"
                }
            ]
        }
    }
