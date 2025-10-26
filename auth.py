"""
Authentication schemas for login, register, and token management.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(
        min_length=6,
        max_length=128,
        description="User password (6-128 characters)"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(description="Email address for new account")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password (8-128 characters, should include numbers and special chars)"
    )
    password_confirm: str = Field(description="Password confirmation")
    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="Last name"
    )

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

    @validator("password_confirm")
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(description="JWT access token (15 min expiration)")
    refresh_token: str = Field(description="JWT refresh token (7 day expiration)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Access token expiration time in seconds (900)")
    user: "UserTokenResponse" = Field(description="User information")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "user"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(description="Valid refresh token")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class LogoutRequest(BaseModel):
    """Logout request schema."""

    refresh_token: Optional[str] = Field(
        default=None,
        description="Refresh token to invalidate (optional)"
    )


class UserTokenResponse(BaseModel):
    """User info in token response."""

    id: int = Field(description="User ID")
    email: str = Field(description="User email")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    role: str = Field(description="User role (user, promoter, admin)")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    current_password: str = Field(description="Current password")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password (must be different from current)"
    )
    new_password_confirm: str = Field(description="New password confirmation")

    @validator("new_password")
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

    @validator("new_password_confirm")
    def passwords_match(cls, v, values):
        """Validate that new passwords match."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""

    email: EmailStr = Field(description="Email address for password reset")


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""

    token: str = Field(description="Password reset token from email")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New password"
    )
    new_password_confirm: str = Field(description="Password confirmation")

    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

    @validator("new_password_confirm")
    def passwords_match(cls, v, values):
        """Validate passwords match."""
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class VerifyEmailRequest(BaseModel):
    """Verify email request schema."""

    token: str = Field(description="Email verification token from email")


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema."""

    email: EmailStr = Field(description="Email address to resend verification to")


class AuthResponse(BaseModel):
    """Generic authentication response."""

    message: str = Field(description="Response message")
    token: Optional[TokenResponse] = Field(default=None, description="Token data if applicable")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "message": "Login successful",
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 900,
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "role": "user"
                    }
                }
            }
        }
