"""Rule schemas for compliance rules management."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Rules
class RuleBase(BaseModel):
    """Base rule schema."""
    state_code: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    legislation_source_id: Optional[int] = Field(None, description="FK to legislation_sources, null for manual rules")
    legislation_digest_id: Optional[int] = Field(None, description="FK to legislation_digests, tracks which digest created this rule")
    rule_text: str = Field(..., min_length=1, description="Plain language compliance requirement")
    applies_to_page_types: Optional[str] = Field(
        None,
        description="Comma-separated page type codes (e.g., 'VDP,INVENTORY,HOMEPAGE')"
    )
    active: bool = Field(default=True, description="Whether rule is active")
    approved: bool = Field(default=False, description="Whether rule has been manually reviewed/approved")
    is_manually_modified: bool = Field(default=False, description="Whether rule text has been manually edited")
    original_rule_text: Optional[str] = Field(None, description="Original AI-generated text before manual edits")
    status: str = Field(default="active", description="Rule lifecycle status: active, pending_review, superseded, merged")
    supersedes_rule_id: Optional[int] = Field(None, description="ID of rule this one replaces")


class RuleCreate(RuleBase):
    """Schema for creating a rule."""
    pass


class RuleUpdate(BaseModel):
    """Schema for updating a rule (all fields optional)."""
    state_code: Optional[str] = Field(None, min_length=2, max_length=2)
    legislation_source_id: Optional[int] = None
    legislation_digest_id: Optional[int] = None
    rule_text: Optional[str] = None
    applies_to_page_types: Optional[str] = None
    active: Optional[bool] = None
    approved: Optional[bool] = None
    is_manually_modified: Optional[bool] = None
    original_rule_text: Optional[str] = None
    status: Optional[str] = None
    supersedes_rule_id: Optional[int] = None


class RuleResponse(RuleBase):
    """Rule response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List responses
class RulesListResponse(BaseModel):
    """Response for list of rules."""
    rules: List[RuleResponse]
    total: int


# Digest operations
class DigestRequest(BaseModel):
    """Request to digest/re-digest legislation into rules."""
    legislation_source_id: int
    force: bool = Field(
        default=False,
        description="If true, delete existing rules before re-digesting"
    )


class DigestResponse(BaseModel):
    """Response from digesting legislation."""
    message: str
    rules_created: int
    rules_deleted: int
    rules: List[RuleResponse]
