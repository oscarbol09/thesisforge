"""Hermetic test fixtures for ThesisForge unit and property tests."""

import os
import socket
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from hypothesis import HealthCheck, settings

os.environ["THESISFORGE_ENVIRONMENT"] = "test"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["LITELLM_TELEMETRY"] = "False"

from thesisforge.config import get_settings  # noqa: E402
from thesisforge.core.security import LocalKeyVault  # noqa: E402
from thesisforge.models import (  # noqa: E402
    AcademicLevel,
    CitationDTO,
    MethodologyDTO,
    ProjectPhase,
    ProjectStateDTO,
    ResearchApproach,
    SectionDraftDTO,
    SectionStatus,
)
from thesisforge.repository.database import DatabaseManager  # noqa: E402

# Configure Hypothesis profiles to prevent test timing jitter flakes on Windows / CI runners
settings.register_profile(
    "ci",
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile(
    "default",
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))


@pytest.fixture(autouse=True)
def mock_dns_for_hermetic_testing(monkeypatch: pytest.MonkeyPatch):
    """Ensure hermetic test execution without outbound network DNS dependencies."""
    original_getaddrinfo = socket.getaddrinfo

    def hermetic_getaddrinfo(host, port, *args, **kwargs):
        if not host:
            return original_getaddrinfo(host, port, *args, **kwargs)
        host_str = str(host).lower()
        if host_str in ("localhost", "127.0.0.1", "::1"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port or 0))]
        if host_str.endswith(".local") or host_str.endswith(".internal"):
            raise socket.gaierror(11001, "getaddrinfo failed")
        # For academic APIs and external endpoints in unit tests, return a safe public IP
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 0))]

    monkeypatch.setattr(socket, "getaddrinfo", hermetic_getaddrinfo)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear lru_cache on get_settings before and after every test to guarantee test isolation."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def master_key() -> str:
    """Provide a static, valid Fernet key for predictable testing."""
    return LocalKeyVault.generate_key()


@pytest.fixture
def vault(master_key: str) -> LocalKeyVault:
    """Provide an isolated LocalKeyVault instance."""
    return LocalKeyVault(master_key)


@pytest_asyncio.fixture
async def in_memory_db() -> AsyncGenerator[DatabaseManager, None]:
    """Provide an initialized in-memory SQLite database."""
    manager = DatabaseManager(":memory:")
    await manager.initialize()
    try:
        yield manager
    finally:
        await manager.close()


@pytest.fixture
def sample_project() -> ProjectStateDTO:
    """Provide a rich, valid ProjectStateDTO instance."""
    return ProjectStateDTO(
        id="proj-test-01",
        title="Impacto del RAG en la Redacción de Tesis Universitarias",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.ORIENTATION,
        area_of_study="Ingeniería de Software / Inteligencia Artificial",
        topic="Sistemas RAG para Asistencia Académica",
        research_problem="Los estudiantes sufren de alucinaciones bibliográficas en LLMs comerciales.",
        research_question="¿Cómo influye un pipeline RAG estructurado en la veracidad de las citas bibliográficas?",
        hypothesis="El uso de RAG con literatura indexada reduce a 0% las citas alucinadas.",
        general_objective="Desarrollar y evaluar un sistema de asistencia a la redacción académica con RAG.",
        specific_objectives=[
            "Diseñar un módulo de extracción de metadatos académicos.",
            "Implementar un mecanismo de chunking léxico jerárquico.",
            "Evaluar la coherencia de los capítulos generados.",
        ],
        justification="Garantizar integridad científica y acelerar el tiempo de estructuración de tesis.",
        variables=["Precisión de citas", "Coherencia metodológica", "Tiempo de redacción"],
        methodology=MethodologyDTO(
            approach=ResearchApproach.CUANTITATIVO,
            design="Cuasiexperimental con grupo de control",
            population="Estudiantes de último año de ingeniería",
            sample="40 estudiantes seleccionados aleatoriamente",
            instruments=["Rúbrica de evaluación APA 7", "Cuestionario de usabilidad"],
            analysis_technique="Prueba t de Student para muestras independientes",
        ),
        validated_citations=[
            CitationDTO(
                doi="10.1145/3397271.3401075",
                title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                authors=["Lewis, P.", "Perez, E.", "Piktus, A."],
                year=2020,
                journal="NeurIPS 2020",
                abstract="We build RAG models where the parametric memory is a pre-trained seq2seq model.",
                apa_formatted="Lewis, P., Perez, E., & Piktus, A. (2020). Retrieval-Augmented Generation...",
            )
        ],
        sections=[
            SectionDraftDTO(
                section_id="ch-01-intro",
                title="Capítulo 1: Introducción y Planteamiento del Problema",
                content="El avance acelerado de la inteligencia artificial generativa...",
                summary="Introducción al problema de alucinaciones en LLMs y justificación del estudio.",
                status=SectionStatus.APPROVED,
                word_count=850,
            ),
            SectionDraftDTO(
                section_id="ch-02-state-of-art",
                title="Capítulo 2: Marco Teórico y Estado del Arte",
                content="",
                status=SectionStatus.PENDING,
            ),
        ],
    )
