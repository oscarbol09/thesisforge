"""Dependency injection providers for FastAPI endpoints."""

from functools import lru_cache

from fastapi import Depends

from thesisforge.advisor.service import AdvisorService
from thesisforge.config import AppSettings, get_settings
from thesisforge.core.security import LocalKeyVault
from thesisforge.drafting.service import DraftService
from thesisforge.export.bundle import ProjectBundleService
from thesisforge.export.service import ExportService
from thesisforge.jury.service import JuryService
from thesisforge.llm.router import LLMRouter
from thesisforge.rag.service import RAGService
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.jury_repository import JuryRepository
from thesisforge.repository.keystore_repository import SecureKeyStoreRepository
from thesisforge.repository.project_repository import ProjectRepository


@lru_cache(maxsize=1)
def get_db_manager() -> DatabaseManager:
    """Singleton database manager dependency."""
    settings = get_settings()
    return DatabaseManager(settings.database_url)


@lru_cache(maxsize=1)
def get_key_vault() -> LocalKeyVault:
    """Singleton key vault dependency."""
    settings = get_settings()
    return LocalKeyVault(settings.master_key)


def get_project_repository(
    db: DatabaseManager = Depends(get_db_manager),
) -> ProjectRepository:
    """Project repository dependency."""
    return ProjectRepository(db)


def get_keystore_repository(
    db: DatabaseManager = Depends(get_db_manager),
    vault: LocalKeyVault = Depends(get_key_vault),
) -> SecureKeyStoreRepository:
    """Secure key store repository dependency."""
    return SecureKeyStoreRepository(db, vault)


def get_llm_router(
    settings: AppSettings = Depends(get_settings),
    keystore: SecureKeyStoreRepository = Depends(get_keystore_repository),
) -> LLMRouter:
    """LLM Router dependency."""
    return LLMRouter(settings=settings, keystore_repo=keystore)


def get_advisor_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    llm_router: LLMRouter = Depends(get_llm_router),
) -> AdvisorService:
    """Advisor service dependency."""
    return AdvisorService(project_repo=project_repo, llm_router=llm_router)


def get_rag_service(
    db: DatabaseManager = Depends(get_db_manager),
    project_repo: ProjectRepository = Depends(get_project_repository),
    llm_router: LLMRouter = Depends(get_llm_router),
    settings: AppSettings = Depends(get_settings),
) -> RAGService:
    """RAG and literature service dependency."""
    return RAGService(
        db_manager=db,
        project_repo=project_repo,
        llm_router=llm_router,
        persist_dir=settings.rag.chroma_dir,
        candidate_threshold=settings.rag.evidence_candidate_threshold,
        support_threshold=settings.rag.evidence_support_threshold,
    )


def get_draft_service(
    db: DatabaseManager = Depends(get_db_manager),
    project_repo: ProjectRepository = Depends(get_project_repository),
    llm_router: LLMRouter = Depends(get_llm_router),
    rag_service: RAGService = Depends(get_rag_service),
) -> DraftService:
    """Drafting service dependency for section generation and memory."""
    return DraftService(
        db_manager=db,
        project_repo=project_repo,
        llm_router=llm_router,
        rag_service=rag_service,
    )


def get_export_service(
    db: DatabaseManager = Depends(get_db_manager),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> ExportService:
    """Export service dependency for APA 7 document compilation."""
    return ExportService(db_manager=db, project_repo=project_repo)


def get_jury_repository(
    db: DatabaseManager = Depends(get_db_manager),
) -> JuryRepository:
    """Jury repository dependency."""
    return JuryRepository(db)


def get_jury_service(
    db: DatabaseManager = Depends(get_db_manager),
    project_repo: ProjectRepository = Depends(get_project_repository),
    jury_repo: JuryRepository = Depends(get_jury_repository),
    llm_router: LLMRouter = Depends(get_llm_router),
) -> JuryService:
    """Jury service dependency for project audits and oral defense simulations."""
    return JuryService(
        db_manager=db,
        project_repo=project_repo,
        jury_repo=jury_repo,
        llm_router=llm_router,
    )


def get_project_bundle_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> ProjectBundleService:
    """Project bundle service dependency for .thesisforge archives."""
    return ProjectBundleService(project_repo=project_repo)
