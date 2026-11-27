"""Regression coverage for citation metadata and optimistic concurrency."""

import json
from unittest.mock import AsyncMock

import fitz
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from thesisforge.api.app import create_app
from thesisforge.api.deps import get_project_repository, get_rag_service
from thesisforge.core.auth import get_current_owner
from thesisforge.models import AcademicSearchResultDTO, DocumentChunkDTO, ProjectStateDTO
from thesisforge.rag.service import RAGService
from thesisforge.repository.project_repository import ProjectRepository


@pytest.fixture
async def citation_api(in_memory_db):
    repo = ProjectRepository(in_memory_db, "local")
    await repo.create_project(ProjectStateDTO(id="citation-fixture"))
    rag = RAGService(in_memory_db, repo, is_memory=True)
    app = create_app()
    app.dependency_overrides.update(
        {
            get_project_repository: lambda: repo,
            get_rag_service: lambda: rag,
            get_current_owner: lambda: "local",
        }
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client, rag, repo
    finally:
        await rag.close()


POST = "/api/literature/citations/citation-fixture"
GET = "/api/projects/citation-fixture"
CLAIM = "Semantic grounding supports reliable references"


@pytest.mark.parametrize("year_fields", [{}, {"year": None}, {"year": 1781}])
async def test_guard_and_legacy_citation_year(citation_api, year_fields):
    client, rag, repo = citation_api
    legacy_citations = json.dumps([{"title": "Historical work", **year_fields}])
    async with repo.db.get_connection() as conn:
        await conn.execute(
            "UPDATE projects SET state_json = json_set(state_json, '$.validated_citations', json(?)) WHERE id = ?",
            (legacy_citations, "citation-fixture"),
        )
        await conn.commit()
    expected = year_fields.get("year")
    response = await client.get(GET)
    assert response.json()["validated_citations"][0]["year"] == expected
    chunk = DocumentChunkDTO(
        project_id="fixture", document_id="document", text=CLAIM, **year_fields
    )
    verdict = await rag.citation_guard.verify_claim_evidence(CLAIM, [chunk])
    assert verdict.supporting_chunks[0].year == expected
    if expected is None:
        assert "(s.f.)" in verdict.supporting_chunks[0].apa_formatted


@pytest.mark.parametrize("year", [0, 2101])
def test_chunk_year_bounds(year):
    with pytest.raises(ValidationError, match="year"):
        DocumentChunkDTO(project_id="fixture", document_id="document", text=CLAIM, year=year)


@pytest.mark.parametrize("mode", ["multipart", "null", "historical"])
async def test_pdf_citation_year(citation_api, mode):
    client, rag, _ = citation_api
    with fitz.open() as doc:
        doc.new_page().insert_text((50, 72), (CLAIM + ".\n") * 5)
        pdf = doc.tobytes()
    expected = 1781 if mode == "historical" else None
    if mode == "multipart":
        response = await client.post(
            "/api/literature/index-pdf",
            data={"project_id": "citation-fixture"},
            files={"file": ("fixture.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 201
        assert response.json()[0]["year"] is None
    else:
        chunks = await rag.index_pdf_document("citation-fixture", "fixture-doc", pdf, year=expected)
        assert chunks[0].year == expected
    matches = await rag.query_relevant_chunks("citation-fixture", CLAIM, min_score=0)
    assert matches[0].year == expected
    stored = (await client.get(GET)).json()["validated_citations"][0]
    assert stored["year"] == expected
    if expected is None:
        assert "(s.f.)" in stored["apa_formatted"]


async def test_citation_post_roundtrip_and_identity(citation_api):
    client, _, _ = citation_api
    payload = {
        "title": "A  Study",
        "authors": ["A. Author"],
        "url": "https://example.org/work/123",
        "category": "marco_teorico",
        "source": "crossref",
    }
    first = (await client.post(POST, json=payload)).json()
    assert first["url"] == payload["url"]
    assert first["category"] == payload["category"]
    assert first["year"] is None
    repeated = await client.post(
        POST,
        json={
            **payload,
            "title": "a study",
            "authors": ["a. author"],
            "url": "http://EXAMPLE.org/work/123/#details",
            "source": "openalex",
            "year": None,
        },
    )
    assert repeated.json() == first
    other = (
        await client.post(POST, json={**payload, "url": "https://example.org/work/456"})
    ).json()
    known = (await client.post(POST, json={**payload, "year": 1999})).json()
    assert (await client.get(GET)).json()["validated_citations"] == [first, other, known]
    assert len({first["id"], other["id"], known["id"]}) == 3


async def test_doi_priority_and_saved_response(citation_api):
    client, rag, _ = citation_api
    rag.crossref.resolve_doi = AsyncMock(
        side_effect=lambda doi: AcademicSearchResultDTO(
            paper_id=doi, doi=doi, title="Registry title", authors=["Registry Author"], year=1999
        )
    )
    body = {"doi": "10.1234/FIXTURE", "year": 1781, "url": "https://example.org/a"}
    first = (await client.post(POST, json=body)).json()
    second = (await client.post(POST, json={**body, "doi": "10.1234/fixture"})).json()
    other = (await client.post(POST, json={**body, "doi": "10.1234/other"})).json()
    no_doi = (
        await client.post(
            POST,
            json={"title": "Registry title", "authors": ["Registry Author"], "year": 1999},
        )
    ).json()
    assert first["year"] == 1999
    assert first["url"] == body["url"]
    assert second == first
    assert (await client.get(GET)).json()["validated_citations"] == [first, other, no_doi]


async def test_citation_version_conflict_and_retry(citation_api, monkeypatch):
    client, _, repo = citation_api
    payload = {"title": "Concurrent paper", "authors": ["A Author"]}
    unrelated = {"title": "Other paper", "authors": ["B Author"]}
    update = repo.update_project

    async def interleave(stale):
        monkeypatch.setattr(repo, "update_project", update)
        winner = await client.post(POST, json=payload)
        assert winner.status_code == 200
        other = await client.post(POST, json=unrelated)
        assert other.status_code == 200
        return await update(stale)

    monkeypatch.setattr(repo, "update_project", interleave)
    assert (await client.post(POST, json=payload)).status_code == 409
    before = (await client.get(GET)).json()["validated_citations"]
    assert [row["title"] for row in before] == [payload["title"], unrelated["title"]]
    retry = await client.post(POST, json=payload)
    assert retry.json() == before[0]
    assert (await client.get(GET)).json()["validated_citations"] == before
