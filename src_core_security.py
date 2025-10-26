"""
Security utilities for password hashing and JWT token management.

This module provides:
- Password hashing with bcrypt
- JWT token creation and verification
- Token payload management
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# ============================================================================
# Configuration
# ============================================================================

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor for bcrypt - security vs performance trade-off
)

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


# ============================================================================
# Token Models
# ============================================================================

class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # Subject (user_id)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at time
    type: str  # Token type: 'access' or 'refresh'
    scopes: list[str] = []  # Permissions/scopes


class TokenResponse(BaseModel):
    """Token response for API returns."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration


# ============================================================================
# Password Functions
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password hashing fails
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Return False on any verification error (e.g., invalid hash format)
        return False


# ============================================================================
# JWT Token Functions
# ============================================================================

def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[list[str]] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: User ID or identifier to encode in token
        expires_delta: Custom expiration time (default: ACCESS_TOKEN_EXPIRE_MINUTES)
        scopes: Optional list of permission scopes
        
    Returns:
        Encoded JWT token string
        
    Raises:
        ValueError: If token creation fails
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    now = datetime.utcnow()
    expire = now + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "access",
        "scopes": scopes or []
    }
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Token creation failed: {str(e)}")


def create_refresh_token(subject: str) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: User ID or identifier to encode in token
        
    Returns:
        Encoded JWT refresh token string
    """
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    now = datetime.utcnow()
    expire = now + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "scopes": []
    }
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Refresh token creation failed: {str(e)}")


def verify_token(token: str) -> Optional[TokenPayload]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        TokenPayload if token is valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        # Extract required fields
        subject = payload.get("sub")
        if subject is None:
            return None
        
        token_payload = TokenPayload(
            sub=subject,
            exp=datetime.fromtimestamp(payload.get("exp")),
            iat=datetime.fromtimestamp(payload.get("iat")),
            type=payload.get("type", "access"),
            scopes=payload.get("scopes", [])
        )
        return token_payload
        
    except JWTError:
        # Token is invalid or expired
        return None
    except Exception:
        return None


def decode_token_unsafe(token: str) -> Optional[dict]:
    """
    Decode a JWT token WITHOUT verification (for debugging only).
    
    WARNING: This should only be used for development/debugging.
    Never trust the data from an unverified token in production!
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded payload dictionary if successful, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": False}
        )
        return payload
    except Exception:
        return None


# ============================================================================
# Token Response Helpers
# ============================================================================

def create_token_response(
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_in: Optional[int] = None
) -> TokenResponse:
    """
    Create a standardized token response.
    
    Args:
        access_token: Access token string
        refresh_token: Optional refresh token string
        expires_in: Token expiration time in seconds
        
    Returns:
        TokenResponse object
    """
    if expires_in is None:
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )


# ============================================================================
# Utility Functions
# ============================================================================

def is_token_expired(token_payload: TokenPayload) -> bool:
    """
    Check if a token payload is expired.
    
    Args:
        token_payload: TokenPayload to check
        
    Returns:
        True if expired, False otherwise
    """
    return datetime.utcnow() > token_payload.exp


def get_token_from_header(auth_header: Optional[str]) -> Optional[str]:
    """
    Extract bearer token from Authorization header.
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer token_value")
        
    Returns:
        Token string if valid format, None otherwise
    """
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]
