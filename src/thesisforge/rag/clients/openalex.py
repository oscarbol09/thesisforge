"""Async client for OpenAlex Works API with inverted index abstract reconstruction and caching."""

from typing import Any

from thesisforge import __version__
from thesisforge.core.logging import get_logger
from thesisforge.models import AcademicSearchResultDTO
from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.clients.base import BaseAcademicClient

logger = get_logger(__name__)


def reconstruct_inverted_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Reconstruct full text abstract from OpenAlex inverted index dictionary."""
    if not inverted_index:
        return None

    pos_to_word: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            if pos >= 0:
                pos_to_word[pos] = word

    if not pos_to_word:
        return None

    max_idx = max(pos_to_word.keys())
    tokens = [pos_to_word.get(i, "") for i in range(max_idx + 1)]
    abstract_text = " ".join(tokens).strip()
    return abstract_text if abstract_text else None


class OpenAlexClient(BaseAcademicClient):
    """Client for OpenAlex Academic Graph Works API (https://api.openalex.org)."""

    def __init__(
        self,
        api_key: str | None = None,
        email: str = "thesisforge@academic.org",
        cache: LiteratureCache | None = None,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        user_agent: str | None = None,
    ) -> None:
        ua = (
            user_agent
            or f"ThesisForge/{__version__} (https://github.com/oscarbol09/thesisforge; mailto:{email})"
        )
        super().__init__(
            base_url="https://api.openalex.org",
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            user_agent=ua,
        )
        self.api_key = api_key
        self.email = email
        self.cache = cache

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["api_key"] = self.api_key
        return headers

    async def search(
        self,
        query: str,
        limit: int = 10,
        year_start: int | None = None,
        year_end: int | None = None,
        **kwargs: Any,
    ) -> list[AcademicSearchResultDTO]:
        """Search OpenAlex catalog for works matching query string with optional year filtering."""
        clean_query = query.strip()
        if not clean_query:
            return []

        cache_key = f"openalex:search:{clean_query}:{limit}:{year_start}:{year_end}"
        if self.cache:
            cached = await self.cache.get("openalex", cache_key)
            if cached is not None and isinstance(cached, list):
                return [AcademicSearchResultDTO.model_validate(item) for item in cached]

        params: dict[str, Any] = {
            "search": clean_query,
            "per_page": min(max(1, limit), 50),
        }
        if self.email:
            params["mailto"] = self.email

        # Publication year filter
        if year_start and year_end:
            params["filter"] = f"publication_year:{year_start}-{year_end}"
        elif year_start:
            params["filter"] = f"from_publication_date:{year_start}-01-01"
        elif year_end:
            params["filter"] = f"to_publication_date:{year_end}-12-31"

        try:
            data = await self.request_json(
                method="GET",
                endpoint="/works",
                params=params,
                headers=self._get_headers(),
            )
        except Exception as e:
            logger.warning(
                "OpenAlex search failed.",
                extra={"query": clean_query, "error": str(e)},
            )
            return []

        results: list[AcademicSearchResultDTO] = []
        for item in data.get("results", []):
            parsed = self._parse_work_item(item)
            if parsed:
                results.append(parsed)

        if self.cache and results:
            await self.cache.set(
                "openalex",
                cache_key,
                [r.model_dump() for r in results],
            )

        return results

    async def get_work(self, work_id: str) -> AcademicSearchResultDTO | None:
        """Fetch full metadata for a specific work by OpenAlex ID or DOI (e.g. 'W2741809807' or '10.1038/...')."""
        clean_id = work_id.strip()
        if not clean_id:
            return None

        if clean_id.startswith("openalex:"):
            clean_id = clean_id.replace("openalex:", "")
        elif clean_id.startswith("https://openalex.org/"):
            clean_id = clean_id.replace("https://openalex.org/", "")

        cache_key = f"openalex:work:{clean_id}"
        if self.cache:
            cached = await self.cache.get("openalex", cache_key)
            if cached is not None and isinstance(cached, dict):
                return AcademicSearchResultDTO.model_validate(cached)

        params: dict[str, Any] = {}
        if self.email:
            params["mailto"] = self.email

        # If it looks like a DOI, OpenAlex supports /works/https://doi.org/...
        endpoint = (
            f"/works/https://doi.org/{clean_id}"
            if (clean_id.startswith("10.") and "/" in clean_id)
            else f"/works/{clean_id}"
        )

        try:
            data = await self.request_json(
                method="GET",
                endpoint=endpoint,
                params=params,
                headers=self._get_headers(),
            )
        except Exception as e:
            logger.warning(
                "OpenAlex work lookup failed.",
                extra={"work_id": clean_id, "error": str(e)},
            )
            return None

        if not data:
            return None

        result = self._parse_work_item(data)
        if self.cache and result:
            await self.cache.set("openalex", cache_key, result.model_dump())

        return result

    def _parse_work_item(self, item: dict[str, Any]) -> AcademicSearchResultDTO | None:
        """Extract standardized AcademicSearchResultDTO from an OpenAlex work JSON object."""
        title = item.get("display_name") or item.get("title") or ""
        if not title:
            return None

        raw_id = item.get("id") or ""
        short_id = raw_id.split("/")[-1] if "/" in raw_id else raw_id
        paper_id = f"openalex:{short_id}" if short_id else f"openalex:{hash(title)}"

        authors: list[str] = []
        for authorship in item.get("authorships", []):
            author_info = authorship.get("author", {}) or {}
            display_name = author_info.get("display_name", "").strip()
            if display_name:
                authors.append(display_name)

        doi_val = item.get("doi")
        doi_clean: str | None = None
        if doi_val:
            doi_clean = (
                doi_val.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
            )

        # Venue / journal resolution
        venue: str | None = None
        primary_location = item.get("primary_location") or {}
        if isinstance(primary_location, dict):
            source_info = primary_location.get("source") or {}
            if isinstance(source_info, dict):
                venue = source_info.get("display_name")

        if not venue:
            host_venue = item.get("host_venue") or {}
            if isinstance(host_venue, dict):
                venue = host_venue.get("name")

        # Open Access PDF
        pdf_url: str | None = None
        oa_info = item.get("open_access") or {}
        if isinstance(oa_info, dict):
            pdf_url = oa_info.get("oa_url")
        if not pdf_url and isinstance(primary_location, dict):
            pdf_url = primary_location.get("pdf_url")

        # Abstract reconstruction
        abstract = reconstruct_inverted_abstract(item.get("abstract_inverted_index"))

        return AcademicSearchResultDTO(
            paper_id=paper_id,
            title=title,
            authors=authors,
            year=item.get("publication_year"),
            venue=venue,
            abstract=abstract,
            doi=doi_clean,
            url=doi_val or raw_id or (f"https://doi.org/{doi_clean}" if doi_clean else None),
            citation_count=item.get("cited_by_count"),
            open_access_pdf=pdf_url,
            source="openalex",
        )
