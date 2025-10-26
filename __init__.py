"""
Schemas package initialization.

Imports all schemas for easy access and documentation.

Usage:
    from src.schemas import (
        LoginRequest, TokenResponse,
        EventCreate, EventResponse,
        CreateOrderRequest, OrderResponse,
        JoinWaitlistRequest, WaitlistResponse,
        # ... etc
    )
"""

# Common schemas
from src.schemas.common import (
    PaginationParams,
    PagedResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    MetadataResponse,
    SuccessResponse,
    MessageResponse,
)

# Authentication schemas
from src.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    UserTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    AuthResponse,
)

# User schemas
from src.schemas.users import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    PromoterDetailResponse,
    BecomePromoterRequest,
    PromoterResponse,
    UserListResponse,
    UserPreferencesUpdate,
)

# Event schemas
from src.schemas.events import (
    EventStatus,
    EventCreate,
    EventUpdate,
    EventResponse,
    EventDetailResponse,
    PromoterSummary,
    TicketTierSummary,
    PublishEventRequest,
    CancelEventRequest,
    EventListResponse,
)

# Ticket schemas
from src.schemas.tickets import (
    TicketStatus,
    CreateTicketTierRequest,
    UpdateTicketTierRequest,
    TicketTierResponse,
    TicketTierAvailabilityResponse,
    TicketResponse,
    TicketDetailResponse,
    EventTicketInfo,
    SetAttendeeRequest,
    TransferTicketRequest,
    ValidateTicketRequest,
    ValidateTicketResponse,
)

# Order schemas
from src.schemas.orders import (
    OrderStatus,
    PaymentStatus,
    OrderItemRequest,
    CreateOrderRequest,
    BillingAddress,
    CreateOrderWithBillingRequest,
    OrderItemResponse,
    OrderResponse,
    OrderDetailResponse,
    EventOrderInfo,
    ConfirmOrderRequest,
    CancelOrderRequest,
    RefundOrderRequest,
    PaymentIntentResponse,
    OrderListResponse,
    CreateOrderResponse,
)

# Waitlist schemas
from src.schemas.waitlist import (
    JoinWaitlistRequest,
    WaitlistResponse,
    WaitlistDetailResponse,
    EventWaitlistInfo,
    TierWaitlistInfo,
    LeaveWaitlistRequest,
    WaitlistNotificationResponse,
    RespondToWaitlistRequest,
    WaitlistListResponse,
    JoinWaitlistResponse,
    WaitlistMetricsResponse,
    BulkNotifyWaitlistRequest,
    BulkNotifyResponse,
)

__all__ = [
    # Common
    "PaginationParams",
    "PagedResponse",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "MetadataResponse",
    "SuccessResponse",
    "MessageResponse",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "LogoutRequest",
    "UserTokenResponse",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    "AuthResponse",
    # Users
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserDetailResponse",
    "PromoterDetailResponse",
    "BecomePromoterRequest",
    "PromoterResponse",
    "UserListResponse",
    "UserPreferencesUpdate",
    # Events
    "EventStatus",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "EventDetailResponse",
    "PromoterSummary",
    "TicketTierSummary",
    "PublishEventRequest",
    "CancelEventRequest",
    "EventListResponse",
    # Tickets
    "TicketStatus",
    "CreateTicketTierRequest",
    "UpdateTicketTierRequest",
    "TicketTierResponse",
    "TicketTierAvailabilityResponse",
    "TicketResponse",
    "TicketDetailResponse",
    "EventTicketInfo",
    "SetAttendeeRequest",
    "TransferTicketRequest",
    "ValidateTicketRequest",
    "ValidateTicketResponse",
    # Orders
    "OrderStatus",
    "PaymentStatus",
    "OrderItemRequest",
    "CreateOrderRequest",
    "BillingAddress",
    "CreateOrderWithBillingRequest",
    "OrderItemResponse",
    "OrderResponse",
    "OrderDetailResponse",
    "EventOrderInfo",
    "ConfirmOrderRequest",
    "CancelOrderRequest",
    "RefundOrderRequest",
    "PaymentIntentResponse",
    "OrderListResponse",
    "CreateOrderResponse",
    # Waitlist
    "JoinWaitlistRequest",
    "WaitlistResponse",
    "WaitlistDetailResponse",
    "EventWaitlistInfo",
    "TierWaitlistInfo",
    "LeaveWaitlistRequest",
    "WaitlistNotificationResponse",
    "RespondToWaitlistRequest",
    "WaitlistListResponse",
    "JoinWaitlistResponse",
    "WaitlistMetricsResponse",
    "BulkNotifyWaitlistRequest",
    "BulkNotifyResponse",
]
