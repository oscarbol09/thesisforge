"""FastAPI application factory with security middleware and domain error handlers."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from thesisforge import __version__
from thesisforge.api.deps import get_db_manager
from thesisforge.api.routes_advisor import router as advisor_router
from thesisforge.api.routes_defense import router as defense_router
from thesisforge.api.routes_drafting import router as drafting_router
from thesisforge.api.routes_export import router as export_router
from thesisforge.api.routes_jury import router as jury_router
from thesisforge.api.routes_literature import router as literature_router
from thesisforge.api.routes_project import router as project_router
from thesisforge.config import get_settings
from thesisforge.core.logging import get_logger
from thesisforge.exceptions import (
    DefenseSessionError,
    DefenseTurnNotFoundError,
    ExportError,
    InvalidPhaseTransitionError,
    JuryEvaluationError,
    LLMProviderError,
    MethodologyValidationError,
    ProjectNotFoundError,
    SectionNotFoundError,
    SecurityError,
    ThesisForgeError,
)
from thesisforge.rag.cache import LiteratureCache

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject strict security headers into all HTTP responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' ws: wss: https:;"
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database and resources on startup, release on shutdown."""
    db_manager = get_db_manager()
    await db_manager.initialize()

    # Automatically purge expired literature cache entries on startup
    try:
        cache = LiteratureCache(db_manager)
        pruned_count = await cache.prune_expired()
        if pruned_count > 0:
            logger.info(
                "Pruned expired literature cache entries on startup.",
                extra={"pruned_count": pruned_count},
            )
    except Exception as exc:
        logger.warning(
            "Could not prune literature cache during startup.",
            extra={"error": str(exc)},
        )

    logger.info("Application startup complete. Database initialized.")
    yield
    await db_manager.close()
    logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """Application factory configuring routes, error handlers, and middleware."""
    settings = get_settings()

    app = FastAPI(
        title="ThesisForge API",
        description="Asistente y forjador de investigación académica con IA.",
        version=__version__,
        lifespan=lifespan,
    )

    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS Configuration compliant with W3C Fetch / browser specs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID", "Accept"],
    )

    # Exception Handlers
    @app.exception_handler(ProjectNotFoundError)
    async def project_not_found_handler(
        request: Request, exc: ProjectNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "PROJECT_NOT_FOUND", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(SectionNotFoundError)
    async def section_not_found_handler(
        request: Request, exc: SectionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "SECTION_NOT_FOUND", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(ExportError)
    async def export_error_handler(request: Request, exc: ExportError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "EXPORT_ERROR", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(MethodologyValidationError)
    async def methodology_validation_handler(
        request: Request, exc: MethodologyValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "METHODOLOGY_VALIDATION_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(InvalidPhaseTransitionError)
    async def phase_transition_handler(
        request: Request, exc: InvalidPhaseTransitionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "INVALID_PHASE_TRANSITION",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(SecurityError)
    async def security_error_handler(request: Request, exc: SecurityError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "SECURITY_VIOLATION", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(LLMProviderError)
    async def llm_error_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": "LLM_PROVIDER_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(JuryEvaluationError)
    async def jury_evaluation_handler(request: Request, exc: JuryEvaluationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND
            if "no se encontró" in exc.message.lower()
            else status.HTTP_400_BAD_REQUEST,
            content={
                "error": "JURY_EVALUATION_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(DefenseTurnNotFoundError)
    async def defense_turn_not_found_handler(
        request: Request, exc: DefenseTurnNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "DEFENSE_TURN_NOT_FOUND",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(DefenseSessionError)
    async def defense_session_handler(request: Request, exc: DefenseSessionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND
            if "no se encontró" in exc.message.lower()
            else status.HTTP_400_BAD_REQUEST,
            content={
                "error": "DEFENSE_SESSION_ERROR",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(ThesisForgeError)
    async def general_domain_error_handler(request: Request, exc: ThesisForgeError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "DOMAIN_ERROR", "message": exc.message, "details": exc.details},
        )

    # Routers
    app.include_router(project_router)
    app.include_router(advisor_router)
    app.include_router(literature_router)
    app.include_router(drafting_router)
    app.include_router(export_router)
    app.include_router(jury_router)
    app.include_router(defense_router)

    # Health check & system metadata
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "version": __version__}

    @app.get("/api/version", tags=["system"])
    async def get_version() -> dict[str, str]:
        return {"version": __version__}

    # Web SPA Static Files Mounting
    gui_path = Path(settings.gui_dir)
    if gui_path.is_dir():
        app.mount("/", StaticFiles(directory=str(gui_path), html=True), name="gui")

    return app


app = create_app()
