from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.models import SecuritySchemeType, OAuthFlows as OAuthFlowsModel

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import AppException
from app.db.session import init_db, close_db
from app.core.redis import close_redis
from app.shared.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    setup_logging()
    await init_db()

    from app.features.stats.events import register_stats_handlers

    register_stats_handlers()

    yield

    await close_db()
    await close_redis()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="REST API for tracking reading progress",
        lifespan=lifespan,
        debug=settings.debug,
        openapi_url=f"/api/{settings.app_version}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    from app.middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health_check():
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.utcnow(),
        )

    from app.api.router import api_router

    app.include_router(api_router, prefix=f"/api/{settings.app_version}")

    return app


app = create_app()
