"""
Jamaah.in API — Backend Service for Siskopatuh Automation
Slim app factory: middleware, router registration, startup, error handling.
"""
# Load .env FIRST — before any imports that read environment variables
from pathlib import Path
import os
from dotenv import load_dotenv

# Initialize Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

_env_path = Path(__file__).resolve().parent.parent / ".env"  # project root .env
load_dotenv(_env_path)

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # 10% of requests traced
        environment=os.getenv("ENV", "development"),
        release=os.getenv("APP_VERSION", "latest"),
    )

import logging
import traceback

# FastAPI
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Auth & Database
from app.database import init_db
from app.routers import (
    auth_router,
    subscription_router,
    admin_router,
    documents_router,
    excel_router,
    groups_router,
    payment_router,
    inventory_router,
    rooming_router,
    shared_router,
    team_router,
    analytics_router,
    itinerary_router,
    document_router,
    notification_router,
)
from app.services.cache import ocr_cache
from app.error_handlers import (
    app_error_handler,
    validation_error_handler,
    general_exception_handler,
    AppError,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
)
from app.logging_config import configure_logging, get_logger

# Configure structured logging
configure_logging()
logger = get_logger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---- Config ----
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ---- Rate Limiter ----
limiter = Limiter(key_func=get_remote_address)

# ---- App ----
app = FastAPI(
    title="Jamaah.in API",
    description="Backend service for Jamaah.in — Siskopatuh Automation Tool. Modular Architecture.",
    version="4.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register custom error handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
# Note: general_exception_handler replaces the default one below

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# GZIP Compression — reduces transfer size for large JSON responses
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Register Routers
app.include_router(auth_router)
app.include_router(subscription_router)
app.include_router(admin_router)
app.include_router(documents_router)
app.include_router(excel_router)
app.include_router(groups_router)
app.include_router(payment_router)
app.include_router(inventory_router)   # Pro: Inventory/Logistics
app.include_router(rooming_router)     # Pro: Auto-Rooming
app.include_router(shared_router)      # Pro: Mutawwif Manifest Sharing
app.include_router(team_router)        # Pro: Multi-User Teams
app.include_router(analytics_router)   # Pro: Dashboard Analytics
app.include_router(itinerary_router)   # Pro: Itinerary/Schedule
app.include_router(document_router)    # Pro: Document Templates
app.include_router(notification_router) # Smart Notifications


# ---- Startup ----
@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized")


# ---- Global Exception Handler ----
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Global Error: {str(exc)}"
    logger.error(error_msg, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": error_msg, "traceback": traceback.format_exc()},
    )


# ---- Utility Routes ----
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Jamaah.in API",
        "version": "4.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "POST /auth/register": "Register new user",
            "POST /auth/login": "Login and get JWT token",
            "POST /process-documents/": "Process images and return JSON preview",
            "POST /generate-excel/": "Generate Excel from verified data",
            "GET /progress/{session_id}": "SSE progress stream",
            "GET /download/{filename}": "Download generated file",
            "GET /cache-stats": "OCR cache statistics",
            # Pro features
            "GET /inventory/forecast/{group_id}": "(Pro) Inventory forecast",
            "POST /rooming/auto/{group_id}": "(Pro) Auto-rooming",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/cache-stats")
async def cache_stats():
    """Return OCR cache statistics."""
    return ocr_cache.stats


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Modular Backend v4.0.0")
    parent_services = str(Path(__file__).parent.parent / "services")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[".", parent_services],
        log_level="info",
    )
