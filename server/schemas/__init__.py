"""API schemas (Pydantic models for request/response validation)."""

from .project import ProjectCreate, ProjectResponse, ProjectSummary
from .user import UserCreate, UserLogin, User, Token, TokenData
from .url import URLCreate, URLResponse
from .check import CheckRequest, CheckResponse, ViolationResponse, VisualVerificationResponse
from .template import TemplateResponse, TemplateRuleResponse, TemplateRuleUpdate

__all__ = [
    # Project
    "ProjectCreate",
    "ProjectResponse",
    "ProjectSummary",
    # User
    "UserCreate",
    "UserLogin",
    "User",
    "Token",
    "TokenData",
    # URL
    "URLCreate",
    "URLResponse",
    # Check
    "CheckRequest",
    "CheckResponse",
    "ViolationResponse",
    "VisualVerificationResponse",
    # Template
    "TemplateResponse",
    "TemplateRuleResponse",
    "TemplateRuleUpdate",
]
