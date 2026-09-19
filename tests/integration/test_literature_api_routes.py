"""Integration tests for FastAPI literature and RAG endpoints."""

import io

import fitz
import pytest
import respx
from httpx import ASGITransport, AsyncClient

from thesisforge.api.app import create_app
from thesisforge.api.deps import get_db_manager, get_key_vault
from thesisforge.core.security import LocalKeyVault
from thesisforge.models import AcademicLevel, ProjectPhase, ProjectStateDTO
from thesisforge.repository.database import DatabaseManager
from thesisforge.repository.project_repository import ProjectRepository


@pytest.mark.asyncio
@respx.mock
async def test_api_search_and_verify_doi(in_memory_db: DatabaseManager, vault: LocalKeyVault):
    """Test /api/literature/search and /api/literature/verify-doi endpoints."""
    app = create_app()
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_key_vault] = lambda: vault

    # Mock Semantic Scholar Search
    s2_data = {
        "total": 1,
        "data": [
            {
                "paperId": "s2_api_01",
                "title": "Attention Is All You Need",
                "authors": [{"name": "Ashish Vaswani"}],
                "year": 2017,
                "externalIds": {"DOI": "10.5555/attention2017"},
                "citationCount": 50000,
            }
        ],
    }
    respx.get("https://api.semanticscholar.org/graph/v1/paper/search").respond(
        status_code=200, json=s2_data
    )

    # Mock CrossRef DOI resolution
    cr_data = {
        "message": {
            "DOI": "10.5555/attention2017",
            "title": ["Attention Is All You Need"],
            "author": [{"given": "Ashish", "family": "Vaswani"}],
            "published-print": {"date-parts": [[2017, 6, 12]]},
        }
    }
    respx.get("https://api.crossref.org/works/10.5555%2Fattention2017").respond(
        status_code=200, json=cr_data
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Search literature
        search_resp = await client.get(
            "/api/literature/search?q=Transformers&source=semantic_scholar&limit=2"
        )
        assert search_resp.status_code == 200
        search_json = search_resp.json()
        assert len(search_json) == 1
        assert search_json[0]["title"] == "Attention Is All You Need"

        # 2. Verify DOI
        doi_resp = await client.post(
            "/api/literature/verify-doi", json={"doi": "10.5555/attention2017"}
        )
        assert doi_resp.status_code == 200
        doi_json = doi_resp.json()
        assert doi_json["is_valid"] is True
        assert doi_json["metadata"]["doi"] == "10.5555/attention2017"

        # 3. Format APA
        cit_payload = {
            "title": "Attention Is All You Need",
            "authors": ["Vaswani, Ashish", "Shazeer, Noam"],
            "year": 2017,
            "journal": "Advances in Neural Information Processing Systems",
            "doi": "10.5555/attention2017",
        }
        apa_resp = await client.post("/api/literature/format-apa", json=cit_payload)
        assert apa_resp.status_code == 200
        apa_json = apa_resp.json()
        assert apa_json["parenthetical"] == "(Vaswani & Shazeer, 2017)"
        assert apa_json["narrative"] == "Vaswani y Shazeer (2017)"
        assert "https://doi.org/10.5555/attention2017" in apa_json["reference_entry"]


@pytest.mark.asyncio
async def test_api_index_pdf_and_query_context(in_memory_db: DatabaseManager, vault: LocalKeyVault):
    """Test /api/literature/index-pdf and /api/literature/query-context endpoints."""
    app = create_app()
    app.dependency_overrides[get_db_manager] = lambda: in_memory_db
    app.dependency_overrides[get_key_vault] = lambda: vault

    repo = ProjectRepository(in_memory_db)
    proj = ProjectStateDTO(
        id="proj-api-rag-01",
        title="Estudio RAG API",
        academic_level=AcademicLevel.PREGRADO,
        phase=ProjectPhase.CONTEXT,
    )
    await repo.create_project(proj)

    # Create dummy PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Introducción\n\nEl procesamiento de lenguaje natural ha avanzado con modelos RAG.",
    )
    pdf_bytes = doc.write()
    doc.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload & Index PDF
        files = {"file": ("paper.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {"project_id": "proj-api-rag-01", "title": "Paper RAG"}
        index_resp = await client.post("/api/literature/index-pdf", data=data, files=files)
        assert index_resp.status_code == 201
        chunks_json = index_resp.json()
        assert len(chunks_json) >= 1

        # Query Context
        query_payload = {
            "project_id": "proj-api-rag-01",
            "query": "modelos RAG",
            "top_k": 3,
        }
        query_resp = await client.post("/api/literature/query-context", json=query_payload)
        assert query_resp.status_code == 200
        query_json = query_resp.json()
        assert len(query_json) >= 1
        assert "lenguaje natural" in query_json[0]["text"]
