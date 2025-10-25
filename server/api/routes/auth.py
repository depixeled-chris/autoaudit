"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from schemas.user import UserCreate, UserLogin, User, Token, TokenData
from core.database import ComplianceDatabase
from core.config import DATABASE_PATH
from core.auth import hash_password, verify_password, create_access_token, decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# Dependency to get database instance
def get_db():
    db = ComplianceDatabase(DATABASE_PATH)
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: ComplianceDatabase = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_data: User registration data (email, password, full_name)

    Returns:
        JWT token and user data
    """
    # Check if user already exists
    existing_user = db.get_user(email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create user
    user_id = db.create_user(
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name
    )

    # Get created user
    user = db.get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    # Create access token
    access_token = create_access_token(
        data={"user_id": user["id"], "email": user["email"]}
    )

    # Return token and user data
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": user["is_active"],
            "created_at": user["created_at"]
        }
    }


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: ComplianceDatabase = Depends(get_db)):
    """
    Login with email and password.

    Args:
        credentials: Login credentials (email and password)

    Returns:
        JWT token and user data
    """
    # Get user by email
    user = db.get_user(email=credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    access_token = create_access_token(
        data={"user_id": user["id"], "email": user["email"]}
    )

    # Return token and user data
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": user["is_active"],
            "created_at": user["created_at"]
        }
    }


@router.get("/me", response_model=User)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: ComplianceDatabase = Depends(get_db)
):
    """
    Get current authenticated user.

    Requires: Authorization: Bearer <token> header

    Returns:
        Current user data
    """
    # Decode token
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Get user from database
    user = db.get_user(user_id=token_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "is_active": user["is_active"],
        "created_at": user["created_at"]
    }


# Dependency for protecting routes
async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: ComplianceDatabase = Depends(get_db)
) -> dict:
    """
    Dependency to get current authenticated user.
    Use this to protect routes that require authentication.

    Example:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_active_user)):
            return {"message": f"Hello {user['email']}"}
    """
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get_user(user_id=token_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user
