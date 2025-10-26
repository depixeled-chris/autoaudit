"""Authentication routes."""

from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from schemas.user import UserCreate, UserLogin, User, Token, TokenData
from core.database import ComplianceDatabase
from core.config import DATABASE_PATH, COOKIE_SECURE, COOKIE_SAMESITE
from core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_token_pair,
    hash_refresh_token,
    get_refresh_token_expiry
)

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
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: ComplianceDatabase = Depends(get_db)
):
    """
    Register a new user.

    Args:
        user_data: User registration data (email, password, full_name)

    Returns:
        JWT access token and user data (refresh token set as httpOnly cookie)
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

    # Create token pair (access + refresh)
    token_pair = create_token_pair(
        user_data={"user_id": user["id"], "email": user["email"]}
    )

    # Hash and save refresh token to database
    refresh_token_hash = hash_refresh_token(token_pair["refresh_token"])
    refresh_token_expiry = get_refresh_token_expiry()

    # Get device info and IP address
    device_info = request.headers.get("user-agent", "Unknown")
    ip_address = request.client.host if request.client else "Unknown"

    db.save_refresh_token(
        user_id=user["id"],
        token_hash=refresh_token_hash,
        expires_at=refresh_token_expiry,
        device_info=device_info,
        ip_address=ip_address
    )

    # Set refresh token as httpOnly cookie (XSS protection)
    # Security settings configured via ENVIRONMENT variable
    response.set_cookie(
        key="refresh_token",
        value=token_pair["refresh_token"],
        httponly=True,  # JavaScript cannot access (XSS protection)
        secure=COOKIE_SECURE,  # HTTPS only in production
        samesite=COOKIE_SAMESITE,  # CSRF protection
        max_age=30 * 24 * 60 * 60,  # 30 days in seconds
        path="/api/auth"  # Only sent to auth endpoints
    )

    logger.info(f"New user {user['email']} registered from {ip_address}")

    # Return access token and user data (refresh token in cookie)
    return {
        "access_token": token_pair["access_token"],
        "token_type": token_pair["token_type"],
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": user["is_active"],
            "created_at": user["created_at"]
        }
    }


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: ComplianceDatabase = Depends(get_db)
):
    """
    Login with email and password.

    Args:
        credentials: Login credentials (email and password)

    Returns:
        JWT access token and user data (refresh token set as httpOnly cookie)
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

    # Create token pair (access + refresh)
    token_pair = create_token_pair(
        user_data={"user_id": user["id"], "email": user["email"]}
    )

    # Hash and save refresh token to database
    refresh_token_hash = hash_refresh_token(token_pair["refresh_token"])
    refresh_token_expiry = get_refresh_token_expiry()

    # Get device info and IP address
    device_info = request.headers.get("user-agent", "Unknown")
    ip_address = request.client.host if request.client else "Unknown"

    db.save_refresh_token(
        user_id=user["id"],
        token_hash=refresh_token_hash,
        expires_at=refresh_token_expiry,
        device_info=device_info,
        ip_address=ip_address
    )

    # Set refresh token as httpOnly cookie (XSS protection)
    # Security settings configured via ENVIRONMENT variable
    response.set_cookie(
        key="refresh_token",
        value=token_pair["refresh_token"],
        httponly=True,  # JavaScript cannot access (XSS protection)
        secure=COOKIE_SECURE,  # HTTPS only in production
        samesite=COOKIE_SAMESITE,  # CSRF protection
        max_age=30 * 24 * 60 * 60,  # 30 days in seconds
        path="/api/auth"  # Only sent to auth endpoints
    )

    logger.info(f"User {user['email']} logged in from {ip_address}")

    # Return access token and user data (refresh token in cookie)
    return {
        "access_token": token_pair["access_token"],
        "token_type": token_pair["token_type"],
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": user["is_active"],
            "created_at": user["created_at"]
        }
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    db: ComplianceDatabase = Depends(get_db)
):
    """
    Refresh access token using refresh token from httpOnly cookie.

    This endpoint implements token rotation for security:
    1. Validates the refresh token from cookie
    2. Creates a new token pair
    3. Revokes the old refresh token
    4. Saves the new refresh token
    5. Returns new access token (new refresh token in cookie)

    Returns:
        New JWT access token and user data
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    # Hash the token to look it up in database
    token_hash = hash_refresh_token(refresh_token)

    # Get token from database
    stored_token = db.get_refresh_token(token_hash)
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if token is expired
    from datetime import datetime
    expires_at = datetime.fromisoformat(stored_token["expires_at"])
    if expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    # Get user
    user = db.get_user(user_id=stored_token["user_id"])
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

    # Revoke old refresh token (token rotation)
    db.revoke_refresh_token(token_hash)

    # Create new token pair
    new_token_pair = create_token_pair(
        user_data={"user_id": user["id"], "email": user["email"]}
    )

    # Hash and save new refresh token
    new_refresh_token_hash = hash_refresh_token(new_token_pair["refresh_token"])
    new_refresh_token_expiry = get_refresh_token_expiry()

    # Get device info and IP address
    device_info = request.headers.get("user-agent", "Unknown")
    ip_address = request.client.host if request.client else "Unknown"

    db.save_refresh_token(
        user_id=user["id"],
        token_hash=new_refresh_token_hash,
        expires_at=new_refresh_token_expiry,
        device_info=device_info,
        ip_address=ip_address
    )

    # Set new refresh token as httpOnly cookie
    # Security settings configured via ENVIRONMENT variable
    response.set_cookie(
        key="refresh_token",
        value=new_token_pair["refresh_token"],
        httponly=True,
        secure=COOKIE_SECURE,  # HTTPS only in production
        samesite=COOKIE_SAMESITE,  # CSRF protection
        max_age=30 * 24 * 60 * 60,  # 30 days
        path="/api/auth"
    )

    logger.info(f"Token refreshed for user {user['email']}")

    # Return new access token and user data
    return {
        "access_token": new_token_pair["access_token"],
        "token_type": new_token_pair["token_type"],
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": user["is_active"],
            "created_at": user["created_at"]
        }
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: ComplianceDatabase = Depends(get_db)
):
    """
    Logout user by revoking refresh token.

    This endpoint:
    1. Gets the refresh token from cookie
    2. Revokes it in the database
    3. Clears the cookie
    4. Returns success message

    Returns:
        Success message
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        # Hash and revoke the token
        token_hash = hash_refresh_token(refresh_token)
        db.revoke_refresh_token(token_hash)
        logger.info(f"User logged out, token revoked")

    # Clear the refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth"
    )

    return {"message": "Successfully logged out"}


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
