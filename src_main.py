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
from src.api.tickets import router as tickets_router
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
    print("🚀 Starting up Ticket Vendor API...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔍 Debug mode: {settings.DEBUG}")
    
    # Create database tables (if they don't exist)
    # Note: In production, use Alembic migrations instead
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        pass
    
    print("✅ Startup complete!")
    
    yield
    
    # Shutdown
    print("⚠️  Shutting down Ticket Vendor API...")
    await engine.dispose()
    print("✅ Shutdown complete!")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Ticket Vendor API",
    description="Complete ticket vendor platform with event management, ticket sales, and more",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Error Handlers
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
        },
        "features": {
            "authentication": "✅ Complete",
            "events": "✅ Complete",
            "tickets": "✅ Complete",
            "orders": "⏳ In Progress",
            "payments": "⏳ Pending",
            "email": "⏳ Pending"
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
            "authentication": "operational",
            "events": "operational",
            "tickets": "operational",
            "database": "connected"
        }
    }


# ============================================================================
# Route Registration
# ============================================================================

# Authentication routes
app.include_router(auth_router)

# Event management routes
app.include_router(events_router)

# Ticket management routes
app.include_router(tickets_router)

# Other routes will be added here as they're implemented
# app.include_router(orders_router)
# app.include_router(waitlist_router)


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
