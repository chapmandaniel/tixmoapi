"""
FastAPI dependencies for authentication and authorization.

Provides dependency functions that can be used in route handlers:
- get_current_user: Extract and verify current user from JWT token
- get_current_admin: Ensure current user is admin
- get_optional_user: Get user if authenticated, None otherwise
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import verify_token, get_token_from_header
from src.models.users import User
from src.schemas.common import ErrorResponse, ErrorDetail

# HTTP Bearer security scheme for Swagger documentation
security = HTTPBearer(
    description="JWT Bearer token authentication"
)


# ============================================================================
# Current User Dependencies
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    This dependency extracts the JWT token from the Authorization header,
    verifies it, and returns the corresponding User model from the database.
    
    Args:
        credentials: HTTPAuthCredentials from Authorization header
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token
    token_payload = verify_token(token)
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type (should be 'access')
    if token_payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.id == int(token_payload.sub))
    )
    user = result.scalars().first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account has been deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current user and verify they are an admin.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if user is admin
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    
    This is useful for endpoints that work with or without authentication.
    
    Args:
        db: Database session
        credentials: Optional HTTPAuthCredentials
        
    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    token_payload = verify_token(token)
    
    if token_payload is None or token_payload.type != "access":
        return None
    
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.id == int(token_payload.sub))
    )
    user = result.scalars().first()
    
    if user is None or user.deleted_at is not None:
        return None
    
    return user


# ============================================================================
# Token Dependencies
# ============================================================================

async def get_refresh_token(
    credentials: HTTPAuthCredentials = Depends(security)
) -> str:
    """
    Extract and verify a refresh token from Authorization header.
    
    Args:
        credentials: HTTPAuthCredentials from Authorization header
        
    Returns:
        Refresh token string if valid
        
    Raises:
        HTTPException: 401 if token is invalid or not a refresh token
    """
    token = credentials.credentials
    
    token_payload = verify_token(token)
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token_payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This endpoint requires a refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


# ============================================================================
# Rate Limiting Setup (for use with slowapi)
# ============================================================================

def get_client_ip(request) -> str:
    """
    Extract client IP address from request.
    
    Handles X-Forwarded-For header for proxied requests.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address string
    """
    # Check for proxy headers
    if request.headers.get("x-forwarded-for"):
        return request.headers.get("x-forwarded-for").split(",")[0]
    
    # Fallback to direct client address
    return request.client.host if request.client else "unknown"
