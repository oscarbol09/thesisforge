"""Async client for CrossRef REST API for DOI verification and metadata retrieval."""

from typing import Any
from urllib.parse import quote

from thesisforge.core.logging import get_logger
from thesisforge.models import AcademicSearchResultDTO
from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.clients.base import BaseAcademicClient

logger = get_logger(__name__)


class CrossRefClient(BaseAcademicClient):
    """Client for CrossRef Works API."""

    def __init__(
        self,
        mailto: str = "thesisforge@academic.org",
        cache: LiteratureCache | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            base_url="https://api.crossref.org",
            timeout_seconds=timeout_seconds,
            user_agent=f"ThesisForge/0.1.0 (https://github.com/oscarbol09/thesisforge; mailto:{mailto})",
        )
        self.mailto = mailto
        self.cache = cache

    async def resolve_doi(self, doi: str) -> AcademicSearchResultDTO | None:
        """Resolve metadata for a single DOI."""
        clean_doi = doi.strip().lower()
        if clean_doi.startswith("https://doi.org/"):
            clean_doi = clean_doi.replace("https://doi.org/", "")
        elif clean_doi.startswith("http://doi.org/"):
            clean_doi = clean_doi.replace("http://doi.org/", "")
        elif clean_doi.startswith("doi:"):
            clean_doi = clean_doi.replace("doi:", "")

        clean_doi = clean_doi.strip()
        if not clean_doi:
            return None

        cache_key = f"crossref:doi:{clean_doi}"
        if self.cache:
            cached = await self.cache.get("crossref", cache_key)
            if cached is not None and isinstance(cached, dict):
                return AcademicSearchResultDTO.model_validate(cached)

        try:
            # quote the DOI to handle slashes and special characters safely
            encoded_doi = quote(clean_doi, safe="")
            data = await self.request_json(
                method="GET",
                endpoint=f"/works/{encoded_doi}",
                params={"mailto": self.mailto},
            )
        except Exception as e:
            logger.warning(
                "CrossRef DOI lookup failed.",
                extra={"doi": clean_doi, "error": str(e)},
            )
            return None

        item = data.get("message", {})
        if not item or not item.get("title"):
            return None

        result = self._parse_crossref_item(item)
        if self.cache and result:
            await self.cache.set("crossref", cache_key, result.model_dump())

        return result

    async def search(
        self,
        query: str,
        limit: int = 10,
        **kwargs: Any,
    ) -> list[AcademicSearchResultDTO]:
        """Search CrossRef catalog by title, keywords or author."""
        clean_query = query.strip()
        if not clean_query:
            return []

        cache_key = f"crossref:search:{clean_query}:{limit}"
        if self.cache:
            cached = await self.cache.get("crossref", cache_key)
            if cached is not None and isinstance(cached, list):
                return [AcademicSearchResultDTO.model_validate(item) for item in cached]

        params = {
            "query": clean_query,
            "rows": min(limit, 50),
            "mailto": self.mailto,
        }

        try:
            data = await self.request_json(
                method="GET",
                endpoint="/works",
                params=params,
            )
        except Exception as e:
            logger.warning(
                "CrossRef search failed.",
                extra={"query": clean_query, "error": str(e)},
            )
            return []

        items = data.get("message", {}).get("items", [])
        results: list[AcademicSearchResultDTO] = []
        for item in items:
            parsed = self._parse_crossref_item(item)
            if parsed:
                results.append(parsed)

        if self.cache and results:
            await self.cache.set(
                "crossref",
                cache_key,
                [r.model_dump() for r in results],
            )

        return results

    def _parse_crossref_item(self, item: dict[str, Any]) -> AcademicSearchResultDTO | None:
        """Extract standardized DTO from CrossRef response item."""
        titles = item.get("title", [])
        title = titles[0] if titles else ""
        if not title:
            return None

        authors: list[str] = []
        for author in item.get("author", []):
            given = author.get("given", "").strip()
            family = author.get("family", "").strip()
            if family and given:
                authors.append(f"{family}, {given}")
            elif family:
                authors.append(family)
            elif author.get("name"):
                authors.append(author["name"].strip())

        year: int | None = None
        for date_key in ("published-print", "published-online", "created", "issued"):
            date_parts = item.get(date_key, {}).get("date-parts", [])
            if date_parts and date_parts[0] and isinstance(date_parts[0][0], int):
                year = date_parts[0][0]
                break

        containers = item.get("container-title", [])
        venue = containers[0] if containers else None
        doi = item.get("DOI")
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
        abstract = item.get("abstract")

        return AcademicSearchResultDTO(
            paper_id=f"crossref:{doi}" if doi else f"crossref:{hash(title)}",
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            abstract=abstract,
            doi=doi,
            url=url,
            citation_count=item.get("is-referenced-by-count"),
            open_access_pdf=None,
            source="crossref",
        )
