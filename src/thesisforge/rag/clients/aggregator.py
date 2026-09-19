"""Multi-source concurrent academic literature aggregator with intelligent deduplication."""

import asyncio
import re

from thesisforge.core.logging import get_logger
from thesisforge.models import AcademicSearchResultDTO
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient

logger = get_logger(__name__)


def _normalize_doi(doi: str | None) -> str | None:
    """Normalize DOI string for strict comparison."""
    if not doi:
        return None
    cleaned = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if cleaned.startswith(prefix):
            cleaned = cleaned.replace(prefix, "")
    return cleaned.strip()


def _normalize_title(title: str) -> str:
    """Normalize title for fuzzy deduplication."""
    return re.sub(r"[^\w\s]", "", title.lower()).strip()


class AcademicSearchAggregator:
    """Aggregates and deduplicates academic search results across Semantic Scholar, ArXiv, and CrossRef."""

    def __init__(
        self,
        semantic_scholar: SemanticScholarClient,
        arxiv: ArxivClient,
        crossref: CrossRefClient,
    ) -> None:
        self.semantic_scholar = semantic_scholar
        self.arxiv = arxiv
        self.crossref = crossref

    async def search(
        self,
        query: str,
        limit_per_source: int = 10,
        sources: list[str] | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
    ) -> list[AcademicSearchResultDTO]:
        """Query enabled academic sources concurrently and deduplicate the unified result set."""
        clean_query = query.strip()
        if not clean_query:
            return []

        enabled_sources = {
            s.lower() for s in (sources or ["semantic_scholar", "arxiv", "crossref"])
        }

        tasks: list[asyncio.Task[list[AcademicSearchResultDTO]]] = []

        if "semantic_scholar" in enabled_sources:
            tasks.append(
                asyncio.create_task(
                    self.semantic_scholar.search(
                        clean_query,
                        limit=limit_per_source,
                        year_start=year_start,
                        year_end=year_end,
                    )
                )
            )

        if "arxiv" in enabled_sources:
            tasks.append(
                asyncio.create_task(self.arxiv.search(clean_query, limit=limit_per_source))
            )

        if "crossref" in enabled_sources:
            tasks.append(
                asyncio.create_task(self.crossref.search(clean_query, limit=limit_per_source))
            )

        raw_results: list[list[AcademicSearchResultDTO] | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        all_papers: list[AcademicSearchResultDTO] = []
        for res in raw_results:
            if isinstance(res, list):
                all_papers.extend(res)
            elif isinstance(res, Exception):
                logger.warning(
                    "Academic source query encountered an exception during aggregation.",
                    extra={"error": str(res)},
                )

        return self.deduplicate(all_papers)

    @classmethod
    def deduplicate(cls, papers: list[AcademicSearchResultDTO]) -> list[AcademicSearchResultDTO]:
        """Deduplicate papers by DOI or Normalized Title + Year + First Author."""
        seen_dois: set[str] = set()
        seen_signatures: set[str] = set()
        deduped: list[AcademicSearchResultDTO] = []

        for paper in papers:
            norm_doi = _normalize_doi(paper.doi)
            if norm_doi:
                if norm_doi in seen_dois:
                    continue
                seen_dois.add(norm_doi)

            # Fingerprint by title + year + first author
            norm_title = _normalize_title(paper.title)
            first_author = (
                re.sub(r"[^\w]", "", paper.authors[0].lower().split(",")[0])
                if paper.authors
                else ""
            )
            year_str = str(paper.year) if paper.year else ""
            signature = f"{norm_title[:60]}:{year_str}:{first_author}"

            if signature in seen_signatures and norm_title:
                continue

            seen_signatures.add(signature)
            deduped.append(paper)

        return deduped
