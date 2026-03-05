"""
FastAPI application factory and main entry point.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.admin_routes import router as admin_router
from backend.api.agent_routes import router as agent_router
from backend.api.auth_routes import router as auth_router
from backend.api.chat_routes import router as chat_router
from backend.api.widget_routes import router as widget_router
from backend.config import get_settings
from backend.db.session import close_db, init_db
from backend.logging_config import setup_logging
from backend.middleware.error_handlers import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from backend.middleware.logging_middleware import RequestLoggingMiddleware
from backend.middleware.rate_limiter import limiter
from backend.middleware.request_id import RequestIDMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown events."""
    # Startup
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    if not settings.is_production:
        await init_db()

    yield

    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Chatbot API",
        description="Production-grade AI chatbot powered by Google Gemini",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ── Rate Limiter ─────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Middleware (order matters — executed bottom to top) ───────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else settings.app_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Error Handlers ───────────────────────────────────────────────────
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # ── API Routes ───────────────────────────────────────────────────────
    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(chat_router, prefix=api_prefix)
    app.include_router(widget_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)
    app.include_router(agent_router, prefix=api_prefix)

    # ── Health Check Endpoints ───────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.app_env,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        """Check if the application is ready to serve requests."""
        checks = {"database": True, "gemini": bool(settings.gemini_api_key)}
        all_ready = all(checks.values())
        return {
            "ready": all_ready,
            "checks": checks,
        }

    # ── Serve demo page ─────────────────────────────────────────────────
    import os
    project_root = os.path.dirname(os.path.dirname(__file__))

    @app.get("/", tags=["Demo"], response_class=HTMLResponse)
    async def demo_page():
        """Serve the demo HTML page."""
        demo_path = os.path.join(project_root, "demo.html")
        if os.path.exists(demo_path):
            return FileResponse(demo_path, media_type="text/html")
        return HTMLResponse("<h1>Chatbot API</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>")

    @app.get("/agent", tags=["Agent Dashboard"], response_class=HTMLResponse)
    async def agent_dashboard():
        """Serve the agent dashboard HTML page."""
        dashboard_path = os.path.join(project_root, "agent_dashboard.html")
        if os.path.exists(dashboard_path):
            return FileResponse(dashboard_path, media_type="text/html")
        return HTMLResponse("<h1>Agent Dashboard</h1><p>Dashboard file not found.</p>")

    # ── Serve static assets (images, etc.) ────────────────────────────────
    static_dir = os.path.join(project_root, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # ── Serve widget static files ────────────────────────────────────────
    widget_dist = os.path.join(project_root, "widget", "dist")
    if os.path.exists(widget_dist):
        app.mount("/widget", StaticFiles(directory=widget_dist), name="widget")

    return app


app = create_app()
