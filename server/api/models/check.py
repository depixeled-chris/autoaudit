"""Compliance check-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CheckRequest(BaseModel):
    """Request model for initiating a compliance check."""
    url: str = Field(..., description="URL to check")
    state_code: str = Field(..., min_length=2, max_length=2, description="State code")
    skip_visual: bool = Field(default=False, description="Skip visual verification")
    save_formats: List[str] = Field(default=["markdown"], description="Report formats to save")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
                    "state_code": "OK",
                    "skip_visual": False,
                    "save_formats": ["markdown", "json"]
                }
            ]
        }
    }


class ViolationResponse(BaseModel):
    """Response model for violation data."""
    id: int = Field(..., description="Violation ID")
    check_id: int = Field(..., description="Check ID")
    category: str = Field(..., description="Violation category")
    severity: str = Field(..., description="Severity level")
    rule_violated: str = Field(..., description="Rule that was violated")
    rule_key: Optional[str] = Field(None, description="Rule key")
    confidence: Optional[float] = Field(None, description="Confidence score")
    needs_visual_verification: bool = Field(..., description="Needs visual verification")
    explanation: Optional[str] = Field(None, description="Explanation")
    evidence: Optional[str] = Field(None, description="Evidence")
    created_at: str = Field(..., description="Creation timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "check_id": 1,
                    "category": "pricing",
                    "severity": "high",
                    "rule_violated": "Price must include all fees",
                    "rule_key": "full_price_disclosure",
                    "confidence": 0.85,
                    "needs_visual_verification": True,
                    "explanation": "Price shown without fee disclosure",
                    "evidence": "Price: $35,411 (no disclaimer visible)",
                    "created_at": "2025-10-24T18:30:00"
                }
            ]
        }
    }


class VisualVerificationResponse(BaseModel):
    """Response model for visual verification data."""
    id: int = Field(..., description="Verification ID")
    check_id: int = Field(..., description="Check ID")
    rule_key: str = Field(..., description="Rule key")
    rule_text: str = Field(..., description="Rule text")
    is_compliant: bool = Field(..., description="Compliance status")
    confidence: float = Field(..., description="Confidence score")
    verification_method: str = Field(..., description="Verification method")
    visual_evidence: Optional[str] = Field(None, description="Visual evidence description")
    proximity_description: Optional[str] = Field(None, description="Proximity description")
    screenshot_path: Optional[str] = Field(None, description="Screenshot file path")
    cached: bool = Field(..., description="Whether result was cached")
    created_at: str = Field(..., description="Creation timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "check_id": 1,
                    "rule_key": "vehicle_id_adjacent",
                    "rule_text": "Vehicle ID must be adjacent to price",
                    "is_compliant": True,
                    "confidence": 0.95,
                    "verification_method": "visual",
                    "visual_evidence": "Vehicle heading displayed directly above price",
                    "proximity_description": "20px separation, same visual module",
                    "screenshot_path": "screenshots/visual_123.png",
                    "cached": False,
                    "created_at": "2025-10-24T18:30:00"
                }
            ]
        }
    }


class CheckResponse(BaseModel):
    """Response model for compliance check data."""
    id: int = Field(..., description="Check ID")
    url_id: int = Field(..., description="URL ID")
    url: str = Field(..., description="URL checked")
    state_code: str = Field(..., description="State code")
    template_id: Optional[str] = Field(None, description="Template ID used")
    overall_score: int = Field(..., ge=0, le=100, description="Overall compliance score")
    compliance_status: str = Field(..., description="Compliance status")
    summary: str = Field(..., description="Summary of findings")
    llm_input_path: Optional[str] = Field(None, description="LLM input file path")
    report_path: Optional[str] = Field(None, description="Report file path")
    checked_at: str = Field(..., description="Check timestamp")
    violations: Optional[List[ViolationResponse]] = Field(None, description="Violations found")
    visual_verifications: Optional[List[VisualVerificationResponse]] = Field(None, description="Visual verifications")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "url_id": 1,
                    "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
                    "state_code": "OK",
                    "template_id": "dealer.com_vdp",
                    "overall_score": 70,
                    "compliance_status": "NEEDS_REVIEW",
                    "summary": "Found 4 violations, 1 visually verified as compliant",
                    "llm_input_path": "llm_inputs/input_20251024_183000.md",
                    "report_path": "reports/report_20251024_183000.md",
                    "checked_at": "2025-10-24T18:30:00",
                    "violations": [],
                    "visual_verifications": []
                }
            ]
        }
    }
