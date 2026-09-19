"""Async client for ArXiv API using defusedxml for safe Atom feed parsing."""

import re
from typing import Any

import defusedxml.ElementTree as ET
import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from thesisforge.core.logging import get_logger
from thesisforge.core.security import assert_safe_academic_url_async
from thesisforge.models import AcademicSearchResultDTO
from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.clients.base import BaseAcademicClient, _is_retryable_http_error

logger = get_logger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivClient(BaseAcademicClient):
    """Client for ArXiv query API."""

    def __init__(
        self,
        cache: LiteratureCache | None = None,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = "https://export.arxiv.org/api/query"
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.cache = cache
        self.user_agent = "ThesisForge/0.1.0 (https://github.com/oscarbol09/thesisforge; mailto:thesisforge@academic.org)"
        self._client: httpx.AsyncClient | None = None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        limit: int = 10,
        category: str | None = None,
        **kwargs: Any,
    ) -> list[AcademicSearchResultDTO]:
        """Search ArXiv preprints using keywords or category filters."""
        clean_query = query.strip()
        if not clean_query:
            return []

        cache_key = f"arxiv:{clean_query}:{limit}:{category}"
        if self.cache:
            cached = await self.cache.get("arxiv", cache_key)
            if cached is not None and isinstance(cached, list):
                return [AcademicSearchResultDTO.model_validate(item) for item in cached]

        search_expr = f"all:{clean_query}"
        if category:
            search_expr = f"cat:{category} AND all:{clean_query}"

        params: dict[str, str | int] = {
            "search_query": search_expr,
            "start": 0,
            "max_results": min(limit, 50),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        await assert_safe_academic_url_async(self.base_url)

        retrier = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential_jitter(initial=1.0, max=10.0),
            retry=retry_if_exception(_is_retryable_http_error),
            reraise=True,
        )

        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )

        xml_text = ""
        try:
            async for attempt in retrier:
                with attempt:
                    resp = await self._client.get(self.base_url, params=params)
                    resp.raise_for_status()
                    xml_text = resp.text
        except Exception as e:
            logger.warning(
                "ArXiv search request failed.",
                extra={"query": clean_query, "error": str(e)},
            )
            return []

        results = self._parse_atom_feed(xml_text)
        if self.cache and results:
            await self.cache.set("arxiv", cache_key, [r.model_dump() for r in results])

        return results

    def _parse_atom_feed(self, xml_content: str) -> list[AcademicSearchResultDTO]:
        """Safely parse Atom XML using defusedxml."""
        if not xml_content.strip():
            return []

        try:
            root = ET.fromstring(xml_content)
        except Exception as err:
            logger.warning("Failed to parse ArXiv XML feed.", extra={"error": str(err)})
            return []

        results: list[AcademicSearchResultDTO] = []
        entries = root.findall("atom:entry", ATOM_NS)

        for entry in entries:
            id_elem = entry.find("atom:id", ATOM_NS)
            title_elem = entry.find("atom:title", ATOM_NS)
            summary_elem = entry.find("atom:summary", ATOM_NS)
            published_elem = entry.find("atom:published", ATOM_NS)
            doi_elem = entry.find("arxiv:doi", ATOM_NS)

            if id_elem is None or title_elem is None or not title_elem.text:
                continue

            raw_id = id_elem.text.strip() if id_elem.text else ""
            paper_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
            title = " ".join(title_elem.text.split())
            abstract = (
                " ".join(summary_elem.text.split())
                if (summary_elem is not None and summary_elem.text)
                else None
            )

            year: int | None = None
            if published_elem is not None and published_elem.text:
                year_match = re.match(r"^(\d{4})", published_elem.text.strip())
                if year_match:
                    year = int(year_match.group(1))

            doi: str | None = None
            if doi_elem is not None and doi_elem.text:
                doi = doi_elem.text.strip()

            authors: list[str] = []
            for author_elem in entry.findall("atom:author", ATOM_NS):
                name_elem = author_elem.find("atom:name", ATOM_NS)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            pdf_url: str | None = None
            for link_elem in entry.findall("atom:link", ATOM_NS):
                if (
                    link_elem.attrib.get("title") == "pdf"
                    or link_elem.attrib.get("type") == "application/pdf"
                ):
                    pdf_url = link_elem.attrib.get("href")

            results.append(
                AcademicSearchResultDTO(
                    paper_id=f"arxiv:{paper_id}",
                    title=title,
                    authors=authors,
                    year=year,
                    venue="arXiv",
                    abstract=abstract,
                    doi=doi,
                    url=raw_id or f"https://arxiv.org/abs/{paper_id}",
                    open_access_pdf=pdf_url,
                    source="arxiv",
                )
            )

        return results
