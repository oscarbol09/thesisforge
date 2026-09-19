"""Academic Retrieval-Augmented Generation (RAG) and literature search module."""

from thesisforge.rag.apa_formatter import APA7Formatter
from thesisforge.rag.cache import LiteratureCache
from thesisforge.rag.citation_guard import CitationGuard
from thesisforge.rag.clients.aggregator import AcademicSearchAggregator
from thesisforge.rag.clients.arxiv import ArxivClient
from thesisforge.rag.clients.base import BaseAcademicClient
from thesisforge.rag.clients.crossref import CrossRefClient
from thesisforge.rag.clients.semantic_scholar import SemanticScholarClient
from thesisforge.rag.parser import PDFDocumentParser, SentenceAwareChunker
from thesisforge.rag.service import RAGService
from thesisforge.rag.vectorstore import ChromaVectorStore

__all__ = [
    "APA7Formatter",
    "AcademicSearchAggregator",
    "ArxivClient",
    "BaseAcademicClient",
    "ChromaVectorStore",
    "CitationGuard",
    "CrossRefClient",
    "LiteratureCache",
    "PDFDocumentParser",
    "RAGService",
    "SemanticScholarClient",
    "SentenceAwareChunker",
]
