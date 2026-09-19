"""Unit tests for academic literature clients and aggregator with respx mocking."""

import pytest
import respx

from thesisforge.models import AcademicSearchResultDTO
from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient
from thesisforge.repository.database import DatabaseManager


@pytest.mark.asyncio
@respx.mock
async def test_semantic_scholar_search_and_cache(in_memory_db: DatabaseManager):
    """Verify Semantic Scholar search returns normalized results and uses cache."""
    cache = LiteratureCache(in_memory_db)
    client = SemanticScholarClient(cache=cache)

    mock_response = {
        "total": 1,
        "data": [
            {
                "paperId": "s2_paper_123",
                "title": "Retrieval-Augmented Generation for NLP",
                "authors": [{"name": "Patrick Lewis"}, {"name": "Ethan Perez"}],
                "year": 2020,
                "venue": "NeurIPS",
                "abstract": "RAG models combine parametric and non-parametric memory.",
                "externalIds": {"DOI": "10.5555/rag2020"},
                "openAccessPdf": {"url": "https://arxiv.org/pdf/2005.11401.pdf"},
                "citationCount": 1250,
            }
        ],
    }

    route = respx.get("https://api.semanticscholar.org/graph/v1/paper/search").respond(
        status_code=200, json=mock_response
    )

    # First call: hits network
    results = await client.search("Retrieval-Augmented Generation", limit=5)
    assert len(results) == 1
    assert results[0].paper_id == "s2_paper_123"
    assert results[0].doi == "10.5555/rag2020"
    assert results[0].authors == ["Patrick Lewis", "Ethan Perez"]
    assert route.call_count == 1

    # Second call: hits cache without network call
    cached_results = await client.search("Retrieval-Augmented Generation", limit=5)
    assert len(cached_results) == 1
    assert cached_results[0].title == "Retrieval-Augmented Generation for NLP"
    assert route.call_count == 1

    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_arxiv_search_atom_xml(in_memory_db: DatabaseManager):
    """Verify ArXiv client parses Atom XML feeds safely."""
    cache = LiteratureCache(in_memory_db)
    client = ArxivClient(cache=cache)

    atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2305.14314v1</id>
        <title> QLoRA: Efficient Finetuning of Quantized LLMs </title>
        <summary> We present QLoRA, an efficient finetuning approach... </summary>
        <published>2023-05-23T17:59:00Z</published>
        <arxiv:doi>10.48550/arXiv.2305.14314</arxiv:doi>
        <author><name>Tim Dettmers</name></author>
        <author><name>Artidoro Pagnoni</name></author>
        <link title="pdf" href="http://arxiv.org/pdf/2305.14314v1" type="application/pdf"/>
      </entry>
    </feed>
    """

    respx.get("https://export.arxiv.org/api/query").respond(
        status_code=200, text=atom_xml, headers={"Content-Type": "application/atom+xml"}
    )

    results = await client.search("QLoRA", limit=2)
    assert len(results) == 1
    assert results[0].paper_id == "arxiv:2305.14314v1"
    assert results[0].title == "QLoRA: Efficient Finetuning of Quantized LLMs"
    assert results[0].year == 2023
    assert results[0].doi == "10.48550/arXiv.2305.14314"
    assert "Tim Dettmers" in results[0].authors
    assert results[0].open_access_pdf == "http://arxiv.org/pdf/2305.14314v1"

    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_crossref_resolve_doi(in_memory_db: DatabaseManager):
    """Verify CrossRef DOI metadata resolution."""
    cache = LiteratureCache(in_memory_db)
    client = CrossRefClient(cache=cache)

    crossref_data = {
        "message": {
            "DOI": "10.1038/s41586-020-2649-2",
            "title": ["Language Models are Few-Shot Learners"],
            "author": [
                {"given": "Tom", "family": "Brown"},
                {"given": "Benjamin", "family": "Mann"},
            ],
            "container-title": ["Nature Machine Intelligence"],
            "published-print": {"date-parts": [[2020, 7, 22]]},
            "is-referenced-by-count": 4500,
        }
    }

    respx.get("https://api.crossref.org/works/10.1038%2Fs41586-020-2649-2").respond(
        status_code=200, json=crossref_data
    )

    result = await client.resolve_doi("10.1038/s41586-020-2649-2")
    assert result is not None
    assert result.doi == "10.1038/s41586-020-2649-2"
    assert result.title == "Language Models are Few-Shot Learners"
    assert result.year == 2020
    assert result.venue == "Nature Machine Intelligence"
    assert result.authors == ["Brown, Tom", "Mann, Benjamin"]

    await client.close()


@pytest.mark.asyncio
async def test_aggregator_deduplication():
    """Verify aggregator eliminates duplicates based on normalized DOI and title signature."""
    ss_client = SemanticScholarClient()
    arxiv_client = ArxivClient()
    cr_client = CrossRefClient()
    aggregator = AcademicSearchAggregator(ss_client, arxiv_client, cr_client)

    papers = [
        AcademicSearchResultDTO(
            paper_id="s2_1",
            title="Deep Residual Learning for Image Recognition",
            authors=["He, Kaiming", "Zhang, Xiangyu"],
            year=2016,
            doi="10.1109/CVPR.2016.90",
            source="semantic_scholar",
        ),
        AcademicSearchResultDTO(
            paper_id="cr_1",
            title="Deep Residual Learning for Image Recognition.",
            authors=["He, Kaiming"],
            year=2016,
            doi="https://doi.org/10.1109/cvpr.2016.90",  # Same DOI normalized
            source="crossref",
        ),
        AcademicSearchResultDTO(
            paper_id="arxiv_1",
            title="Attention Is All You Need",
            authors=["Vaswani, Ashish"],
            year=2017,
            doi=None,
            source="arxiv",
        ),
        AcademicSearchResultDTO(
            paper_id="s2_2",
            title="Attention is All You Need!",
            authors=["Vaswani, Ashish", "Shazeer, Noam"],
            year=2017,
            doi=None,  # Same Title + Year + First Author signature
            source="semantic_scholar",
        ),
    ]

    deduped = aggregator.deduplicate(papers)
    assert len(deduped) == 2
    assert deduped[0].title.startswith("Deep Residual Learning")
    assert deduped[1].title.startswith("Attention")


@pytest.mark.asyncio
@respx.mock
async def test_semantic_scholar_get_paper(in_memory_db: DatabaseManager):
    """Verify Semantic Scholar get_paper fetching by ID or DOI."""
    cache = LiteratureCache(in_memory_db)
    client = SemanticScholarClient(cache=cache)

    mock_paper = {
        "paperId": "s2_paper_999",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers",
        "authors": [{"name": "Jacob Devlin"}, {"name": "Ming-Wei Chang"}],
        "year": 2018,
        "venue": "NAACL",
        "abstract": "We introduce a new language representation model called BERT.",
        "externalIds": {"DOI": "10.18653/v1/N19-1423"},
        "citationCount": 50000,
    }

    respx.get("https://api.semanticscholar.org/graph/v1/paper/s2_paper_999").respond(
        status_code=200, json=mock_paper
    )

    paper = await client.get_paper("s2_paper_999")
    assert paper is not None
    assert paper.title == "BERT: Pre-training of Deep Bidirectional Transformers"
    assert paper.doi == "10.18653/v1/N19-1423"
    assert len(paper.authors) == 2

    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_crossref_search(in_memory_db: DatabaseManager):
    """Verify CrossRef catalog search with query parameters."""
    cache = LiteratureCache(in_memory_db)
    client = CrossRefClient(cache=cache)

    mock_crossref_search = {
        "message": {
            "items": [
                {
                    "DOI": "10.1145/3397271.3401075",
                    "title": ["Retrieval-Augmented Generation for NLP"],
                    "author": [{"given": "Patrick", "family": "Lewis"}],
                    "container-title": ["NeurIPS 2020"],
                    "published-print": {"date-parts": [[2020]]},
                }
            ]
        }
    }

    respx.get("https://api.crossref.org/works").respond(status_code=200, json=mock_crossref_search)

    results = await client.search("Retrieval Augmented Generation", limit=1)
    assert len(results) == 1
    assert results[0].doi == "10.1145/3397271.3401075"
    assert results[0].authors == ["Lewis, Patrick"]

    await client.close()


@pytest.mark.asyncio
async def test_literature_cache_cleanup(in_memory_db: DatabaseManager):
    """Verify literature cache operations including TTL expiration and prune_expired."""
    cache = LiteratureCache(in_memory_db, default_ttl_hours=1)

    # Set and get expired entry
    await cache.set("arxiv", "query:123", {"title": "Test Paper"}, ttl_hours=-1)
    expired = await cache.get("arxiv", "query:123")
    assert expired is None

    # Valid entry
    await cache.set("crossref", "doi:10.1234/test", {"title": "Valid DOI"}, ttl_hours=24)
    valid = await cache.get("crossref", "doi:10.1234/test")
    assert valid == {"title": "Valid DOI"}

    # Prune expired entries
    pruned_count = await cache.prune_expired()
    assert pruned_count >= 1
