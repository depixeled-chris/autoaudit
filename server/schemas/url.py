"""URL-related Pydantic models."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class URLCreate(BaseModel):
    """Request model for adding a URL."""
    url: str = Field(..., description="Full URL to monitor")
    project_id: Optional[int] = Field(None, description="Project ID (optional)")
    url_type: str = Field(default="vdp", description="Type of page (vdp, homepage, inventory)")
    template_id: Optional[str] = Field(None, description="Template ID if known")
    platform: Optional[str] = Field(None, description="Platform (dealer.com, DealerOn, etc.)")
    check_frequency_hours: int = Field(default=24, ge=1, le=168, description="Check frequency in hours")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
                    "project_id": 1,
                    "url_type": "vdp",
                    "template_id": "dealer.com_vdp",
                    "platform": "dealer.com",
                    "check_frequency_hours": 24
                }
            ]
        }
    }


class URLUpdate(BaseModel):
    """Request model for updating a URL."""
    active: Optional[bool] = Field(None, description="Active status")
    url_type: Optional[str] = Field(None, description="Type of page (vdp, homepage, inventory)")
    check_frequency_hours: Optional[int] = Field(None, ge=1, le=168, description="Check frequency in hours")
    template_id: Optional[str] = Field(None, description="Template ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "active": False,
                    "check_frequency_hours": 48
                }
            ]
        }
    }


class URLResponse(BaseModel):
    """Response model for URL data."""
    id: int = Field(..., description="URL ID")
    project_id: Optional[int] = Field(None, description="Project ID")
    url: str = Field(..., description="Full URL")
    url_type: str = Field(..., description="Page type")
    template_id: Optional[str] = Field(None, description="Template ID")
    platform: Optional[str] = Field(None, description="Platform")
    active: bool = Field(..., description="Active status")
    check_frequency_hours: int = Field(..., description="Check frequency")
    last_checked: Optional[str] = Field(None, description="Last check timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    check_count: int = Field(0, description="Number of compliance checks performed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "project_id": 1,
                    "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
                    "url_type": "vdp",
                    "template_id": "dealer.com_vdp",
                    "platform": "dealer.com",
                    "active": True,
                    "check_frequency_hours": 24,
                    "last_checked": "2025-10-24T18:30:00",
                    "created_at": "2025-10-24T10:00:00"
                }
            ]
        }
    }
