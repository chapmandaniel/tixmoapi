"""
User schemas for user management and CRUD operations.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "user"
    PROMOTER = "promoter"
    ADMIN = "admin"


class UserCreate(BaseModel):
    """Create user request schema."""

    email: EmailStr = Field(description="Email address")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password (8-128 characters)"
    )
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
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Phone number (optional)"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890"
            }
        }


class UserUpdate(BaseModel):
    """Update user request schema."""

    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="First name"
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Last name"
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Phone number"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "first_name": "Jane",
                "phone": "+1234567890"
            }
        }


class UserResponse(BaseModel):
    """User response schema."""

    id: int = Field(description="User ID")
    uuid: str = Field(description="User UUID")
    email: str = Field(description="Email address")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    role: str = Field(description="User role")
    email_verified: bool = Field(description="Email verification status")
    is_active: bool = Field(description="Account active status")
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "role": "user",
                "email_verified": True,
                "is_active": True,
                "created_at": "2025-10-26T10:00:00Z",
                "updated_at": "2025-10-26T10:00:00Z",
                "last_login_at": "2025-10-26T11:30:00Z"
            }
        }


class UserDetailResponse(BaseModel):
    """Detailed user response schema."""

    id: int = Field(description="User ID")
    uuid: str = Field(description="User UUID")
    email: str = Field(description="Email address")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    role: str = Field(description="User role")
    email_verified: bool = Field(description="Email verification status")
    is_active: bool = Field(description="Account active status")
    created_at: datetime = Field(description="Account creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login timestamp")
    promoter: Optional["PromoterDetailResponse"] = Field(
        default=None,
        description="Promoter information if user is a promoter"
    )

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PromoterDetailResponse(BaseModel):
    """Promoter detail response schema."""

    id: int = Field(description="Promoter ID")
    company_name: Optional[str] = Field(default=None, description="Company name")
    company_website: Optional[str] = Field(default=None, description="Company website")
    description: Optional[str] = Field(default=None, description="Company description")
    logo_url: Optional[str] = Field(default=None, description="Company logo URL")
    verification_status: str = Field(description="Verification status (pending, verified, rejected)")
    verified_at: Optional[datetime] = Field(default=None, description="Verification timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class BecomePromoterRequest(BaseModel):
    """Become promoter request schema."""

    company_name: str = Field(
        min_length=1,
        max_length=255,
        description="Company name"
    )
    company_website: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Company website URL"
    )
    description: Optional[str] = Field(
        default=None,
        description="Company description"
    )
    address_line1: str = Field(
        min_length=1,
        max_length=255,
        description="Address line 1"
    )
    address_line2: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Address line 2"
    )
    city: str = Field(
        min_length=1,
        max_length=100,
        description="City"
    )
    state: str = Field(
        min_length=1,
        max_length=100,
        description="State/Province"
    )
    postal_code: str = Field(
        min_length=1,
        max_length=20,
        description="Postal code"
    )
    country: str = Field(
        min_length=2,
        max_length=2,
        description="Country code (ISO 3166-1 alpha-2)"
    )
    tax_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Tax ID"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "company_name": "Amazing Events Inc",
                "company_website": "https://amazingevents.com",
                "description": "We organize amazing events!",
                "address_line1": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "tax_id": "12-3456789"
            }
        }


class PromoterResponse(BaseModel):
    """Promoter response schema."""

    id: int = Field(description="Promoter ID")
    company_name: Optional[str] = Field(default=None, description="Company name")
    company_website: Optional[str] = Field(default=None, description="Company website")
    description: Optional[str] = Field(default=None, description="Company description")
    logo_url: Optional[str] = Field(default=None, description="Company logo URL")
    verification_status: str = Field(description="Verification status")
    verified_at: Optional[datetime] = Field(default=None, description="Verification timestamp")
    user: UserResponse = Field(description="Associated user")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema (minimal info)."""

    id: int = Field(description="User ID")
    uuid: str = Field(description="User UUID")
    email: str = Field(description="Email address")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    role: str = Field(description="User role")
    is_active: bool = Field(description="Account active status")
    created_at: datetime = Field(description="Account creation timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    """User preferences update schema."""

    email_notifications: bool = Field(
        default=True,
        description="Enable email notifications"
    )
    marketing_emails: bool = Field(
        default=True,
        description="Enable marketing emails"
    )
    two_factor_enabled: bool = Field(
        default=False,
        description="Enable two-factor authentication"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "email_notifications": True,
                "marketing_emails": False,
                "two_factor_enabled": True
            }
        }


# Update forward references
UserDetailResponse.model_rebuild()
