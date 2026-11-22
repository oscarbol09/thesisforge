"""Resources shared by request-scoped RAG services."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.openalex import OpenAlexClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient
from thesisforge.rag.vectorstore import ChromaVectorStore

if TYPE_CHECKING:
    from thesisforge.rag.clients.base import BaseAcademicClient
    from thesisforge.repository.database import DatabaseManager


class RAGServiceResources:
    """Own reusable literature clients and the vector store for one app lifetime."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        persist_directory: str,
        is_memory: bool,
        embedding_provider: str | None,
    ) -> None:
        self.db_manager = db_manager
        self.persist_directory = persist_directory
        self.is_memory = is_memory
        self.embedding_provider = embedding_provider
        self.cache = LiteratureCache(db_manager)
        self.semantic_scholar = SemanticScholarClient(cache=self.cache)
        self.arxiv = ArxivClient(cache=self.cache)
        self.crossref = CrossRefClient(cache=self.cache)
        self.openalex = OpenAlexClient(cache=self.cache)
        self.academic_clients: tuple[BaseAcademicClient, ...] = (
            self.semantic_scholar,
            self.arxiv,
            self.crossref,
            self.openalex,
        )
        self.vector_store = ChromaVectorStore(
            persist_directory=persist_directory,
            is_memory=is_memory,
            embedding_provider=embedding_provider,
        )

    def matches(
        self,
        db_manager: DatabaseManager,
        persist_directory: str,
        is_memory: bool,
        embedding_provider: str | None,
    ) -> bool:
        """Check that app resources match the request's database and RAG settings."""
        return (
            self.db_manager is db_manager
            and self.persist_directory == persist_directory
            and self.is_memory == is_memory
            and self.embedding_provider == embedding_provider
        )

    async def close(self) -> None:
        """Close all owned clients, attempting every teardown before reporting errors."""
        errors: list[Exception] = []
        for client in self.academic_clients:
            try:
                await client.close()
            except Exception as exc:
                errors.append(exc)

        try:
            await asyncio.to_thread(self.vector_store.close)
        except Exception as exc:
            errors.append(exc)

        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise ExceptionGroup("Failed to close RAG service resources", errors)
