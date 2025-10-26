"""Project-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    state_code: str = Field(..., min_length=2, max_length=2, description="Two-letter state code (e.g., OK, TX, CA)")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    base_url: Optional[str] = Field(None, max_length=500, description="Base URL for the project")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "AllStar CDJR Muskogee",
                    "state_code": "OK",
                    "description": "Oklahoma dealership compliance monitoring",
                    "base_url": "https://www.allstarcdjrmuskogee.com"
                }
            ]
        }
    }


class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    state_code: str = Field(..., description="State code")
    description: Optional[str] = Field(None, description="Project description")
    base_url: Optional[str] = Field(None, description="Base URL for the project")
    screenshot_path: Optional[str] = Field(None, description="Path to project screenshot")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "AllStar CDJR Muskogee",
                    "state_code": "OK",
                    "description": "Oklahoma dealership compliance monitoring",
                    "base_url": "https://www.allstarcdjrmuskogee.com",
                    "created_at": "2025-10-24T18:30:00",
                    "updated_at": "2025-10-24T18:30:00"
                }
            ]
        }
    }


class ProjectSummary(BaseModel):
    """Project summary statistics."""
    project_id: int = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    total_urls: int = Field(..., description="Total active URLs")
    total_checks: int = Field(..., description="Total compliance checks performed")
    avg_score: float = Field(..., description="Average compliance score (based on most recent check per URL)")
    compliant_count: int = Field(..., description="Number of compliant checks")
    total_violations: int = Field(..., description="Total violations found")
    total_text_tokens: int = Field(..., description="Total tokens used for text analysis")
    total_visual_tokens: int = Field(..., description="Total tokens used for visual verification")
    total_tokens: int = Field(..., description="Total tokens used across all checks")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_id": 1,
                    "project_name": "AllStar CDJR Muskogee",
                    "total_urls": 25,
                    "total_checks": 150,
                    "avg_score": 82.5,
                    "compliant_count": 120,
                    "total_violations": 45
                }
            ]
        }
    }


class IntelligentSetupRequest(BaseModel):
    """Request model for intelligent project setup."""
    url: str = Field(..., min_length=1, max_length=500, description="Starting URL (homepage or any dealership page)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.allstarcdjrmuskogee.com"
                }
            ]
        }
    }


class IntelligentSetupResponse(BaseModel):
    """Response model for intelligent project setup."""
    project: ProjectResponse = Field(..., description="Created project")
    urls_created: int = Field(..., description="Number of URLs created")
    analysis_summary: str = Field(..., description="Summary of the analysis performed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project": {
                        "id": 1,
                        "name": "AllStar CDJR Muskogee",
                        "state_code": "OK",
                        "description": "Auto-detected dealership (dealer.com platform)",
                        "base_url": "https://www.allstarcdjrmuskogee.com",
                        "created_at": "2025-10-24T18:30:00",
                        "updated_at": "2025-10-24T18:30:00"
                    },
                    "urls_created": 3,
                    "analysis_summary": "Detected AllStar CDJR Muskogee dealership in Oklahoma. Created monitoring for homepage, inventory page, and sample VDP."
                }
            ]
        }
    }
