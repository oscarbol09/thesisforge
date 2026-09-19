"""Academic literature search and metadata resolution clients."""

from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.base import BaseAcademicClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient

__all__ = [
    "AcademicSearchAggregator",
    "ArxivClient",
    "BaseAcademicClient",
    "CrossRefClient",
    "SemanticScholarClient",
]
