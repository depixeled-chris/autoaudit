"""Authentication utilities using Argon2 and JWT."""

import os
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging

logger = logging.getLogger(__name__)

# Initialize Argon2 password hasher
ph = PasswordHasher()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes (short-lived)
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days (long-lived)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        ph.verify(hashed_password, plain_password)
        # Check if hash needs rehashing (Argon2 handles this automatically)
        if ph.check_needs_rehash(hashed_password):
            logger.info("Password hash needs rehashing")
        return True
    except VerifyMismatchError:
        return False


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically user_id and email)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def create_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    Returns:
        A cryptographically secure random token (URL-safe base64)
    """
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token for secure database storage.

    Args:
        token: Plain refresh token

    Returns:
        SHA-256 hash of the token (hex string)
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_token_pair(user_data: Dict) -> Dict:
    """
    Create an access token and refresh token pair.

    Args:
        user_data: User information to encode (user_id, email, etc.)

    Returns:
        Dictionary containing:
        - access_token: Short-lived JWT (15 minutes)
        - refresh_token: Long-lived random token (30 days)
        - token_type: "bearer"
        - expires_in: Access token expiration in seconds
    """
    # Create short-lived access token
    access_token = create_access_token(
        data=user_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Create long-lived refresh token
    refresh_token = create_refresh_token()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }


def get_refresh_token_expiry() -> datetime:
    """
    Get the expiration datetime for a new refresh token.

    Returns:
        Datetime representing when the refresh token should expire
    """
    return datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
