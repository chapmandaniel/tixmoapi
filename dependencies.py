"""
FastAPI dependencies for authentication and authorization.

Provides dependency functions that can be used in route handlers:
- get_current_user: Extract and verify current user from JWT token
- get_current_admin: Ensure current user is admin
- get_current_promoter_user: Ensure current user is a promoter
- get_optional_user: Get user if authenticated, None otherwise
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.core.security import verify_token
from src.models.users import User, UserRole
from src.models.promoters import Promoter

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
    
    # Get user from database with promoter relationship
    result = await db.execute(
        select(User)
        .where(User.id == int(token_payload.sub))
        .options(selectinload(User.promoter))
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
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_promoter_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current user and verify they are a promoter or admin.
    
    Ensures the user has a promoter account (or is an admin who can 
    create events on behalf of promoters).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if user is promoter or admin
        
    Raises:
        HTTPException: 403 if user is not a promoter or admin
    """
    # Admins can perform promoter actions
    if current_user.role == UserRole.ADMIN:
        return current_user
    
    # Check if user is a promoter
    if current_user.role != UserRole.PROMOTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Promoter access required. Please create a promoter account."
        )
    
    # Verify promoter relationship exists
    if not current_user.promoter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Promoter account not found. Please create a promoter profile."
        )
    
    return current_user


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get the current user if authenticated, None otherwise.
    
    This is useful for endpoints that work with or without authentication.
    For example, public event listings that may show extra info for logged-in users.
    
    Args:
        db: Database session
        credentials: Optional HTTPAuthCredentials from Authorization header
        
    Returns:
        User object if token is valid, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        token_payload = verify_token(token)
        
        if token_payload is None or token_payload.type != "access":
            return None
        
        result = await db.execute(
            select(User)
            .where(User.id == int(token_payload.sub))
            .options(selectinload(User.promoter))
        )
        user = result.scalars().first()
        
        if user is None or user.deleted_at is not None:
            return None
        
        return user
    except Exception:
        # If any error occurs, just return None (don't fail the request)
        return None


# ============================================================================
# Refresh Token Dependencies
# ============================================================================

async def get_refresh_token(
    credentials: HTTPAuthCredentials = Depends(security)
) -> str:
    """
    Extract and validate refresh token from Authorization header.
    
    Args:
        credentials: HTTPAuthCredentials from Authorization header
        
    Returns:
        Refresh token string if valid
        
    Raises:
        HTTPException: 401 if token is invalid or wrong type
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
    
    # Check token type (should be 'refresh')
    if token_payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Refresh token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token
