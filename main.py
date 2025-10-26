"""
Main FastAPI application initialization.

This module:
- Creates the FastAPI app instance
- Configures middleware
- Registers all route handlers
- Sets up CORS, error handling, etc.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.api.auth import router as auth_router
from src.api.events import router as events_router
from src.core.database import engine, Base
from src.core.config import settings

# Rate limiter for API protection
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    print("⚙️  Performing startup checks...")
    print(f"🌍 Environment: {settings.ENVIRONMENT}")
    print(f"🐛 Debug Mode: {settings.DEBUG}")
    print("✅ Startup checks complete")
    
    yield
    
    # Shutdown
    print("⚠️  Performing shutdown cleanup...")
    print("✅ Shutdown cleanup complete")


# ============================================================================
# FastAPI Application Instance
# ============================================================================

app = FastAPI(
    title="Ticket Vendor API",
    description="A comprehensive ticket vendor API for event management and ticket sales",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Attach rate limiter to app
app.state.limiter = limiter


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail)
        }
    )


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """
    API root endpoint.
    
    Returns basic information about the API.
    """
    return {
        "name": "Ticket Vendor API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "api_version": "v1",
        "endpoints": {
            "auth": "/auth",
            "events": "/events",
            "tickets": "/tickets",
            "orders": "/orders",
            "waitlist": "/waitlist"
        }
    }


@app.get("/health", tags=["root"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the API.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_version": "1.0.0",
        "features": {
            "authentication": "active",
            "events": "active",
            "tickets": "pending",
            "orders": "pending",
            "payments": "pending"
        }
    }


# ============================================================================
# Route Registration
# ============================================================================

# Authentication routes
app.include_router(auth_router)

# Event management routes
app.include_router(events_router)

# Other routes will be added here as they're implemented
# app.include_router(tickets_router)
# app.include_router(orders_router)
# app.include_router(waitlist_router)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
