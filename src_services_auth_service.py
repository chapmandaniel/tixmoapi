"""
Authentication service layer.

Handles:
- User registration and validation
- User login and credential verification
- Password management (change, reset)
- Token refresh
- Account security operations
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    TokenPayload
)
from src.models.users import User, UserRole
from src.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    TokenResponse
)


class AuthService:
    """Authentication service for user management."""
    
    @staticmethod
    async def register(
        request: RegisterRequest,
        db: AsyncSession
    ) -> Tuple[User, str]:
        """
        Register a new user.
        
        Args:
            request: Registration request with email, password, name
            db: Database session
            
        Returns:
            Tuple of (User object, access_token)
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == request.email.lower())
        )
        existing_user = result.scalars().first()
        
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Determine user role
        role = UserRole.PROMOTER if request.is_promoter else UserRole.USER
        
        # Create new user
        hashed_password = hash_password(request.password)
        new_user = User(
            email=request.email.lower(),
            password_hash=hashed_password,
            name=request.name,
            role=role,
            email_verified_at=datetime.utcnow() if not request.require_email_verification else None
        )
        
        db.add(new_user)
        await db.flush()  # Get the auto-generated ID
        await db.commit()
        
        # Create access token
        access_token = create_access_token(subject=str(new_user.id))
        
        return new_user, access_token
    
    @staticmethod
    async def login(
        request: LoginRequest,
        db: AsyncSession
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and return tokens.
        
        Args:
            request: Login request with email and password
            db: Database session
            
        Returns:
            Tuple of (User object, access_token, refresh_token)
            
        Raises:
            HTTPException: If credentials are invalid or user not found
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == request.email.lower())
        )
        user = result.scalars().first()
        
        if user is None:
            # Prevent email enumeration - return generic error
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is deleted
        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been deleted"
            )
        
        # Create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return user, access_token, refresh_token
    
    @staticmethod
    async def refresh_access_token(
        refresh_token: str,
        db: AsyncSession
    ) -> str:
        """
        Issue a new access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            db: Database session
            
        Returns:
            New access token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        token_payload = verify_token(refresh_token)
        if token_payload is None or token_payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Verify user still exists
        result = await db.execute(
            select(User).where(User.id == int(token_payload.sub))
        )
        user = result.scalars().first()
        
        if user is None or user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        new_access_token = create_access_token(subject=str(user.id))
        return new_access_token
    
    @staticmethod
    async def change_password(
        user: User,
        request: PasswordChangeRequest,
        db: AsyncSession
    ) -> None:
        """
        Change password for authenticated user.
        
        Args:
            user: Current authenticated user
            request: Password change request with old and new passwords
            db: Database session
            
        Raises:
            HTTPException: If old password is incorrect
        """
        # Verify old password
        if not verify_password(request.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Old password is incorrect"
            )
        
        # Check that new password is different
        if verify_password(request.new_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from old password"
            )
        
        # Update password
        user.password_hash = hash_password(request.new_password)
        user.updated_at = datetime.utcnow()
        
        db.add(user)
        await db.commit()
    
    @staticmethod
    async def request_password_reset(
        email: str,
        db: AsyncSession
    ) -> Optional[User]:
        """
        Handle password reset request.
        
        In a real application, this would generate a reset token
        and send an email. For now, we just verify the user exists.
        
        Args:
            email: User email
            db: Database session
            
        Returns:
            User object if found, None otherwise
            
        Note:
            Always returns success to prevent email enumeration
        """
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalars().first()
        
        if user is not None and user.deleted_at is None:
            # In production, generate reset token and send email
            # For now, just mark when reset was requested
            user.updated_at = datetime.utcnow()
            db.add(user)
            await db.commit()
        
        # Always return success to prevent email enumeration
        return user
    
    @staticmethod
    async def verify_email(
        user: User,
        db: AsyncSession
    ) -> None:
        """
        Mark user email as verified.
        
        Args:
            user: User to verify
            db: Database session
        """
        if user.email_verified_at is None:
            user.email_verified_at = datetime.utcnow()
            db.add(user)
            await db.commit()


# ============================================================================
# Helper functions
# ============================================================================

async def get_user_by_id(
    user_id: int,
    db: AsyncSession
) -> Optional[User]:
    """Get user by ID from database."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


async def get_user_by_email(
    email: str,
    db: AsyncSession
) -> Optional[User]:
    """Get user by email from database."""
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    return result.scalars().first()
