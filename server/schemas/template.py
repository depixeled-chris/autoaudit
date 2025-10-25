"""Template-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class TemplateRuleUpdate(BaseModel):
    """Request model for updating a template rule."""
    status: str = Field(..., description="Rule status (compliant, non_compliant)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    verification_method: str = Field(..., description="Verification method (text, visual, human)")
    notes: Optional[str] = Field(None, description="Notes about this rule")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "compliant",
                    "confidence": 0.95,
                    "verification_method": "visual",
                    "notes": "Vehicle ID always displayed in heading above price"
                }
            ]
        }
    }


class TemplateRuleResponse(BaseModel):
    """Response model for template rule data."""
    id: int = Field(..., description="Rule ID")
    template_id: str = Field(..., description="Template ID")
    rule_key: str = Field(..., description="Rule key")
    status: str = Field(..., description="Status")
    confidence: float = Field(..., description="Confidence score")
    verification_method: Optional[str] = Field(None, description="Verification method")
    notes: Optional[str] = Field(None, description="Notes")
    verified_date: str = Field(..., description="Verification timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "template_id": "dealer.com_vdp",
                    "rule_key": "vehicle_id_adjacent",
                    "status": "compliant",
                    "confidence": 0.95,
                    "verification_method": "visual",
                    "notes": "Vehicle ID prominently displayed above price",
                    "verified_date": "2025-10-24T18:12:27"
                }
            ]
        }
    }


class TemplateResponse(BaseModel):
    """Response model for template data."""
    id: int = Field(..., description="Template ID")
    template_id: str = Field(..., description="Template identifier")
    platform: str = Field(..., description="Platform name")
    template_type: str = Field(..., description="Template type")
    config: Optional[Dict] = Field(None, description="Template configuration")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Update timestamp")
    rules: Optional[list[TemplateRuleResponse]] = Field(None, description="Cached rules")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "template_id": "dealer.com_vdp",
                    "platform": "dealer.com",
                    "template_type": "compliance",
                    "config": {},
                    "created_at": "2025-10-24T18:00:00",
                    "updated_at": "2025-10-24T18:30:00",
                    "rules": []
                }
            ]
        }
    }
