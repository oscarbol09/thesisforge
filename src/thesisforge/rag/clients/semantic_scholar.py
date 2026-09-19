"""Async client for Semantic Scholar Graph API."""

from typing import Any

from thesisforge.core.logging import get_logger
from thesisforge.models import AcademicSearchResultDTO
from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.clients.base import BaseAcademicClient

logger = get_logger(__name__)

DEFAULT_PAPER_FIELDS = (
    "paperId,title,authors,year,venue,abstract,openAccessPdf,citationCount,externalIds,url"
)


class SemanticScholarClient(BaseAcademicClient):
    """Client for Semantic Scholar Graph API v1."""

    def __init__(
        self,
        api_key: str | None = None,
        cache: LiteratureCache | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            base_url="https://api.semanticscholar.org",
            timeout_seconds=timeout_seconds,
        )
        self.api_key = api_key
        self.cache = cache

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def search(
        self,
        query: str,
        limit: int = 10,
        year_start: int | None = None,
        year_end: int | None = None,
        **kwargs: Any,
    ) -> list[AcademicSearchResultDTO]:
        """Search academic papers by query string with optional year filtering."""
        clean_query = query.strip()
        if not clean_query:
            return []

        cache_key = f"search:{clean_query}:{limit}:{year_start}:{year_end}"
        if self.cache:
            cached = await self.cache.get("semantic_scholar", cache_key)
            if cached is not None and isinstance(cached, list):
                return [AcademicSearchResultDTO.model_validate(item) for item in cached]

        params: dict[str, Any] = {
            "query": clean_query,
            "limit": min(limit, 100),
            "fields": DEFAULT_PAPER_FIELDS,
        }
        if year_start or year_end:
            y_start = year_start or 1900
            y_end = year_end or 2100
            params["year"] = f"{y_start}-{y_end}"

        try:
            data = await self.request_json(
                method="GET",
                endpoint="/graph/v1/paper/search",
                params=params,
                headers=self._get_headers(),
            )
        except Exception as e:
            logger.warning(
                "Semantic Scholar search failed.",
                extra={"query": clean_query, "error": str(e)},
            )
            return []

        results: list[AcademicSearchResultDTO] = []
        for item in data.get("data", []):
            if not item.get("title"):
                continue

            authors = [
                author.get("name", "").strip()
                for author in item.get("authors", [])
                if author.get("name")
            ]
            external_ids = item.get("externalIds", {}) or {}
            doi = external_ids.get("DOI")
            pdf_info = item.get("openAccessPdf") or {}
            pdf_url = pdf_info.get("url") if isinstance(pdf_info, dict) else None

            result = AcademicSearchResultDTO(
                paper_id=item.get("paperId", ""),
                title=item.get("title", ""),
                authors=authors,
                year=item.get("year"),
                venue=item.get("venue"),
                abstract=item.get("abstract"),
                doi=doi,
                url=item.get("url") or (f"https://doi.org/{doi}" if doi else None),
                citation_count=item.get("citationCount"),
                open_access_pdf=pdf_url,
                source="semantic_scholar",
            )
            results.append(result)

        if self.cache and results:
            await self.cache.set(
                "semantic_scholar",
                cache_key,
                [r.model_dump() for r in results],
            )

        return results

    async def get_paper(self, paper_id: str) -> AcademicSearchResultDTO | None:
        """Fetch full details for a paper by Semantic Scholar ID or DOI (e.g. 'DOI:10.1038/...')."""
        clean_id = paper_id.strip()
        if not clean_id:
            return None

        cache_key = f"paper:{clean_id}"
        if self.cache:
            cached = await self.cache.get("semantic_scholar", cache_key)
            if cached is not None and isinstance(cached, dict):
                return AcademicSearchResultDTO.model_validate(cached)

        try:
            item = await self.request_json(
                method="GET",
                endpoint=f"/graph/v1/paper/{clean_id}",
                params={"fields": DEFAULT_PAPER_FIELDS},
                headers=self._get_headers(),
            )
        except Exception as e:
            logger.warning(
                "Semantic Scholar paper lookup failed.",
                extra={"paper_id": clean_id, "error": str(e)},
            )
            return None

        if not item or not item.get("title"):
            return None

        authors = [
            author.get("name", "").strip()
            for author in item.get("authors", [])
            if author.get("name")
        ]
        external_ids = item.get("externalIds", {}) or {}
        doi = external_ids.get("DOI")
        pdf_info = item.get("openAccessPdf") or {}
        pdf_url = pdf_info.get("url") if isinstance(pdf_info, dict) else None

        result = AcademicSearchResultDTO(
            paper_id=item.get("paperId", clean_id),
            title=item.get("title", ""),
            authors=authors,
            year=item.get("year"),
            venue=item.get("venue"),
            abstract=item.get("abstract"),
            doi=doi,
            url=item.get("url") or (f"https://doi.org/{doi}" if doi else None),
            citation_count=item.get("citationCount"),
            open_access_pdf=pdf_url,
            source="semantic_scholar",
        )

        if self.cache:
            await self.cache.set("semantic_scholar", cache_key, result.model_dump())

        return result
