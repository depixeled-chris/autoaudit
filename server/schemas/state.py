"""State and legislation schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# States
class StateBase(BaseModel):
    """Base state schema."""
    code: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    name: str = Field(..., min_length=1, description="State name")
    active: bool = Field(default=True, description="Whether state is active")


class StateCreate(StateBase):
    """Schema for creating a state."""
    pass


class StateUpdate(BaseModel):
    """Schema for updating a state."""
    name: Optional[str] = None
    active: Optional[bool] = None


class StateResponse(StateBase):
    """State response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Legislation Sources
class LegislationSourceBase(BaseModel):
    """Base legislation source schema."""
    state_code: str = Field(..., min_length=2, max_length=2)
    statute_number: str = Field(..., description="Statute or regulation number")
    title: str = Field(..., description="Title of the legislation")
    full_text: str = Field(..., description="Complete undoctored text of the statute")
    source_url: Optional[str] = None
    effective_date: Optional[date] = None
    sunset_date: Optional[date] = None
    last_verified_date: Optional[date] = None
    applies_to_page_types: Optional[str] = Field(
        None,
        description="Comma-separated page type codes this applies to"
    )


class LegislationSourceCreate(LegislationSourceBase):
    """Schema for creating a legislation source."""
    pass


class LegislationSourceUpdate(BaseModel):
    """Schema for updating a legislation source."""
    statute_number: Optional[str] = None
    title: Optional[str] = None
    full_text: Optional[str] = None
    source_url: Optional[str] = None
    effective_date: Optional[date] = None
    sunset_date: Optional[date] = None
    last_verified_date: Optional[date] = None
    applies_to_page_types: Optional[str] = None


class LegislationSourceResponse(LegislationSourceBase):
    """Legislation source response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Legislation Digests
class LegislationDigestBase(BaseModel):
    """Base legislation digest schema."""
    legislation_source_id: int
    interpreted_requirements: str = Field(..., description="Plain language interpretation")
    approved: bool = Field(default=False)


class LegislationDigestCreate(LegislationDigestBase):
    """Schema for creating a legislation digest."""
    created_by: Optional[int] = None


class LegislationDigestUpdate(BaseModel):
    """Schema for updating a legislation digest."""
    interpreted_requirements: Optional[str] = None
    approved: Optional[bool] = None
    reviewed_by: Optional[int] = None


class LegislationDigestResponse(LegislationDigestBase):
    """Legislation digest response schema."""
    id: int
    created_by: Optional[int]
    reviewed_by: Optional[int]
    last_review_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List responses
class StatesListResponse(BaseModel):
    """Response for list of states."""
    states: List[StateResponse]
    total: int


class LegislationSourcesListResponse(BaseModel):
    """Response for list of legislation sources."""
    sources: List[LegislationSourceResponse]
    total: int


class LegislationDigestsListResponse(BaseModel):
    """Response for list of legislation digests."""
    digests: List[LegislationDigestResponse]
    total: int
