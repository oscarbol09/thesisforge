"""Unit tests for OpenAlex academic client and inverted index abstract reconstruction with respx mocking."""

import pytest
import respx

from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.openalex import (
    OpenAlexClient,
    reconstruct_inverted_abstract,
)
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient
from thesisforge.repository.database import DatabaseManager


def test_reconstruct_inverted_abstract():
    """Verify OpenAlex inverted index abstract reconstruction logic."""
    # Standard inverted index
    inverted = {
        "Retrieval-Augmented": [0],
        "Generation": [1],
        "combines": [2],
        "parametric": [3],
        "memory": [4, 7],
        "with": [5],
        "non-parametric": [6],
    }
    reconstructed = reconstruct_inverted_abstract(inverted)
    assert (
        reconstructed
        == "Retrieval-Augmented Generation combines parametric memory with non-parametric memory"
    )

    # None or empty
    assert reconstruct_inverted_abstract(None) is None
    assert reconstruct_inverted_abstract({}) is None

    # Single word
    assert reconstruct_inverted_abstract({"Summary": [0]}) == "Summary"

    # Unordered positions
    unordered = {"World": [1], "Hello": [0]}
    assert reconstruct_inverted_abstract(unordered) == "Hello World"


@pytest.mark.asyncio
@respx.mock
async def test_openalex_search_and_cache(in_memory_db: DatabaseManager):
    """Verify OpenAlex search maps items into AcademicSearchResultDTO and utilizes cache."""
    cache = LiteratureCache(in_memory_db)
    client = OpenAlexClient(cache=cache)

    mock_response = {
        "meta": {"count": 1},
        "results": [
            {
                "id": "https://openalex.org/W2741809807",
                "display_name": "Attention Is All You Need",
                "publication_year": 2017,
                "doi": "https://doi.org/10.48550/arXiv.1706.03762",
                "cited_by_count": 98000,
                "authorships": [
                    {"author": {"id": "https://openalex.org/A1", "display_name": "Ashish Vaswani"}},
                    {"author": {"id": "https://openalex.org/A2", "display_name": "Noam Shazeer"}},
                ],
                "primary_location": {
                    "source": {"display_name": "NeurIPS"},
                    "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
                },
                "open_access": {
                    "is_oa": True,
                    "oa_url": "https://arxiv.org/pdf/1706.03762.pdf",
                },
                "abstract_inverted_index": {
                    "The": [0],
                    "dominant": [1],
                    "sequence": [2],
                    "transduction": [3],
                    "models": [4],
                    "are": [5],
                    "based": [6],
                    "on": [7],
                    "complex": [8],
                    "recurrent": [9],
                    "or": [10],
                    "convolutional": [11],
                    "neural": [12],
                    "networks.": [13],
                },
            }
        ],
    }

    route = respx.get("https://api.openalex.org/works").respond(status_code=200, json=mock_response)

    # First call: hits network
    results = await client.search(
        "Attention Is All You Need", limit=5, year_start=2017, year_end=2018
    )
    assert len(results) == 1
    work = results[0]
    assert work.paper_id == "openalex:W2741809807"
    assert work.title == "Attention Is All You Need"
    assert work.year == 2017
    assert work.doi == "10.48550/arXiv.1706.03762"
    assert work.authors == ["Ashish Vaswani", "Noam Shazeer"]
    assert work.venue == "NeurIPS"
    assert work.citation_count == 98000
    assert work.open_access_pdf == "https://arxiv.org/pdf/1706.03762.pdf"
    assert work.abstract is not None
    assert work.abstract.startswith("The dominant sequence")
    assert work.source == "openalex"
    assert route.call_count == 1

    # Second call: cached
    cached_results = await client.search(
        "Attention Is All You Need", limit=5, year_start=2017, year_end=2018
    )
    assert len(cached_results) == 1
    assert cached_results[0].title == "Attention Is All You Need"
    assert route.call_count == 1

    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_openalex_get_work_by_id_and_doi(in_memory_db: DatabaseManager):
    """Verify OpenAlex work metadata retrieval by OpenAlex ID and DOI."""
    cache = LiteratureCache(in_memory_db)
    client = OpenAlexClient(cache=cache)

    mock_work = {
        "id": "https://openalex.org/W2963403868",
        "display_name": "Deep Residual Learning for Image Recognition",
        "publication_year": 2016,
        "doi": "https://doi.org/10.1109/cvpr.2016.90",
        "cited_by_count": 180000,
        "authorships": [
            {"author": {"display_name": "Kaiming He"}},
            {"author": {"display_name": "Xiangyu Zhang"}},
        ],
        "primary_location": {
            "source": {"display_name": "IEEE Conference on Computer Vision and Pattern Recognition"}
        },
        "abstract_inverted_index": {
            "Deeper": [0],
            "neural": [1],
            "networks": [2],
            "are": [3],
            "more": [4],
            "difficult": [5],
            "to": [6],
            "train.": [7],
        },
    }

    respx.get("https://api.openalex.org/works/W2963403868").respond(status_code=200, json=mock_work)

    work = await client.get_work("W2963403868")
    assert work is not None
    assert work.title == "Deep Residual Learning for Image Recognition"
    assert work.doi == "10.1109/cvpr.2016.90"
    assert work.authors == ["Kaiming He", "Xiangyu Zhang"]
    assert work.abstract == "Deeper neural networks are more difficult to train."

    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_openalex_search_error_handling():
    """Verify OpenAlex client handles API failures gracefully by returning an empty list."""
    client = OpenAlexClient()

    respx.get("https://api.openalex.org/works").respond(status_code=500)

    results = await client.search("Error query", limit=5)
    assert results == []

    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_aggregator_with_openalex():
    """Verify AcademicSearchAggregator queries OpenAlex alongside other sources."""
    ss_client = SemanticScholarClient()
    arxiv_client = ArxivClient()
    cr_client = CrossRefClient()
    oa_client = OpenAlexClient()
    aggregator = AcademicSearchAggregator(
        semantic_scholar=ss_client,
        arxiv=arxiv_client,
        crossref=cr_client,
        openalex=oa_client,
    )

    respx.get("https://api.semanticscholar.org/graph/v1/paper/search").respond(
        status_code=200, json={"data": []}
    )
    respx.get("https://export.arxiv.org/api/query").respond(status_code=200, text="<feed></feed>")
    respx.get("https://api.crossref.org/works").respond(
        status_code=200, json={"message": {"items": []}}
    )
    respx.get("https://api.openalex.org/works").respond(
        status_code=200,
        json={
            "results": [
                {
                    "id": "https://openalex.org/W100",
                    "display_name": "Unified OpenAlex Discovery",
                    "publication_year": 2024,
                    "authorships": [{"author": {"display_name": "Dr. Researcher"}}],
                }
            ]
        },
    )

    results = await aggregator.search("OpenAlex Discovery", limit_per_source=2)
    assert len(results) == 1
    assert results[0].title == "Unified OpenAlex Discovery"
    assert results[0].source == "openalex"

    await ss_client.close()
    await arxiv_client.close()
    await cr_client.close()
    await oa_client.close()
