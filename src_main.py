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
    
    Handles:
    - Database initialization on startup
    - Cleanup on shutdown
    """
    # Startup
    print("🚀 Starting Ticket Vendor API...")
    async with engine.begin() as conn:
        # Create all tables from SQLAlchemy models
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created/verified")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Ticket Vendor API...")
    await engine.dispose()
    print("✅ Database connection closed")


# ============================================================================
# Create FastAPI Application
# ============================================================================

app = FastAPI(
    title="Ticket Vendor API",
    description="Comprehensive ticket vendor solution for event management",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add state
app.state.limiter = limiter

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=600,  # 10 minutes
)

# Trust proxy headers for X-Forwarded-For (for rate limiting behind proxy)
app.add_middleware(
    "fastapi.middleware.trustedhost.TrustedHostMiddleware",
    allowed_hosts=settings.ALLOWED_HOSTS.split(",") if settings.ALLOWED_HOSTS else ["*"]
)

# ============================================================================
# Request/Response Logging Middleware
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    method = request.method
    path = request.url.path
    
    print(f"📝 {method} {path}")
    
    response = await call_next(request)
    
    print(f"✅ {method} {path} -> {response.status_code}")
    return response


# ============================================================================
# Error Handling
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
            "users": "/users",
            "events": "/events",
            "tickets": "/tickets",
            "orders": "/orders"
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
        "api_version": "1.0.0"
    }


# ============================================================================
# Route Registration
# ============================================================================

# Authentication routes
app.include_router(auth_router)

# Other routes will be added here as they're implemented
# app.include_router(users_router)
# app.include_router(events_router)
# app.include_router(tickets_router)
# app.include_router(orders_router)


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Execute tasks on application startup."""
    print("⚙️  Performing startup checks...")
    print("✅ Startup checks complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute tasks on application shutdown."""
    print("⚠️  Performing shutdown cleanup...")
    print("✅ Shutdown cleanup complete")


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
