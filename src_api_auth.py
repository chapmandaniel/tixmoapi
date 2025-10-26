"""
Authentication API endpoints.

Provides routes for:
- POST /auth/register - Register new user
- POST /auth/login - Login with email/password
- POST /auth/refresh - Get new access token from refresh token
- POST /auth/logout - Logout (optional, mainly for client cleanup)
- GET /auth/me - Get current user profile
- POST /auth/password/change - Change password (requires auth)
- POST /auth/password/reset - Request password reset
- POST /auth/email/verify - Verify email address
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import (
    get_current_user,
    get_refresh_token,
    security
)
from src.models.users import User
from src.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerifyRequest,
    TokenResponse,
)
from src.schemas.users import UserResponse, UserDetailResponse
from src.schemas.common import SuccessResponse, ErrorResponse, ErrorDetail
from src.services.auth_service import AuthService

# Create router with prefix and tags
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        429: {"description": "Too Many Requests - Rate limit exceeded"}
    }
)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password"
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Register a new user account.
    
    **Request Body**:
    - `email`: Valid email address (must be unique)
    - `password`: Min 8 chars, must include uppercase, lowercase, and digit
    - `name`: User's full name
    - `is_promoter`: Whether to register as promoter (default: false)
    
    **Returns**:
    - `access_token`: JWT token for authenticated requests
    - `token_type`: Bearer
    - `expires_in`: Seconds until token expiration
    """
    user, access_token = await AuthService.register(request, db)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60  # 30 minutes
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate with email and password to get tokens"
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Login with email and password.
    
    **Request Body**:
    - `email`: User's registered email
    - `password`: User's password
    
    **Returns**:
    - `access_token`: JWT token for authenticated requests
    - `refresh_token`: Token for getting new access tokens
    - `token_type`: Bearer
    - `expires_in`: Seconds until access token expiration
    """
    user, access_token, refresh_token = await AuthService.login(request, db)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60  # 30 minutes
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using a refresh token"
)
async def refresh(
    db: AsyncSession = Depends(get_db),
    refresh_token: str = Depends(get_refresh_token)
) -> TokenResponse:
    """
    Get a new access token using a refresh token.
    
    **Authorization**:
    - Header: `Authorization: Bearer <refresh_token>`
    
    **Returns**:
    - `access_token`: New JWT token for authenticated requests
    - `token_type`: Bearer
    - `expires_in`: Seconds until token expiration
    """
    new_access_token = await AuthService.refresh_access_token(refresh_token, db)
    
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=30 * 60  # 30 minutes
    )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout the current user (mainly for client-side cleanup)"
)
async def logout(
    current_user: User = Depends(get_current_user)
) -> SuccessResponse:
    """
    Logout the current user.
    
    Note: JWTs are stateless, so this mainly signals to the client
    to delete stored tokens. In production, you might want to:
    - Maintain a token blacklist in Redis
    - Revoke tokens in database
    
    **Returns**:
    - `success`: True
    - `message`: Logout confirmation
    """
    return SuccessResponse(
        success=True,
        message="Successfully logged out"
    )


# ============================================================================
# User Profile Endpoints
# ============================================================================

@router.get(
    "/me",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get the profile of the currently authenticated user"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserDetailResponse:
    """
    Get the current authenticated user's profile.
    
    **Authorization**: Required - Bearer token
    
    **Returns**:
    - Complete user profile including role, email verification status, etc.
    """
    # Convert ORM model to schema
    return UserDetailResponse.from_orm(current_user)


# ============================================================================
# Password Management Endpoints
# ============================================================================

@router.post(
    "/password/change",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change password for the authenticated user"
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Change the password for the current user.
    
    **Request Body**:
    - `old_password`: Current password
    - `new_password`: New password (must be different from old)
    
    **Authorization**: Required - Bearer token
    
    **Returns**:
    - `success`: True
    - `message`: Confirmation message
    """
    await AuthService.change_password(current_user, request, db)
    
    return SuccessResponse(
        success=True,
        message="Password changed successfully"
    )


@router.post(
    "/password/reset",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset email"
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Request a password reset.
    
    **Request Body**:
    - `email`: Email address of account
    
    **Note**: Always returns success to prevent email enumeration.
    Email will only be sent if account exists.
    
    **Returns**:
    - `success`: True
    - `message`: Confirmation message
    """
    await AuthService.request_password_reset(request.email, db)
    
    # Always return success to prevent email enumeration
    return SuccessResponse(
        success=True,
        message="If an account with that email exists, a reset link has been sent"
    )


# ============================================================================
# Email Verification Endpoints
# ============================================================================

@router.post(
    "/email/verify",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Mark email as verified"
)
async def verify_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Verify the current user's email address.
    
    **Authorization**: Required - Bearer token
    
    **Returns**:
    - `success`: True
    - `message`: Verification confirmation
    """
    await AuthService.verify_email(current_user, db)
    
    return SuccessResponse(
        success=True,
        message="Email verified successfully"
    )


# ============================================================================
# Health Check
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Auth service health check",
    description="Check if authentication service is running"
)
async def auth_health() -> dict:
    """
    Quick health check for the authentication service.
    
    **Returns**:
    - `status`: "healthy"
    - `service`: "authentication"
    """
    return {
        "status": "healthy",
        "service": "authentication"
    }
