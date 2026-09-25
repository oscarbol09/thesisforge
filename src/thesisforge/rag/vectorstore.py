"""Embedded vector store adapter using ChromaDB with multi-tenant project isolation.

Embedding strategy
------------------
Two implementations of the ``EmbeddingFunction`` protocol are provided:

``FastLocalEmbeddingFunction`` (default)
    Deterministic 384-dim feature-hashing embeddings.  Zero network, zero
    model download — safe for CI, offline use, and resource-constrained machines.
    Semantically weak: good enough for prototype retrieval but not for production
    academic search where synonymy and paraphrasing matter.

``SentenceTransformerEmbeddingFunction``
    Real semantic embeddings via ``sentence-transformers``.  First call downloads
    the model (~90 MB for all-MiniLM-L6-v2).  Produces proper dense vectors that
    capture meaning, not just token identity.  Enable by passing
    ``embedding_provider="sentence_transformer"`` (or a custom model name) to
    ``ChromaVectorStore``.

The ``EmbeddingProvider`` protocol makes it trivial to plug in OpenAI, Cohere,
or any other provider without touching the vector store logic.
"""

import hashlib
import math
import re
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction
from chromadb.config import Settings as ChromaSettings

from thesisforge.core.logging import get_logger
from thesisforge.exceptions import RAGIndexError
from thesisforge.llm.router import LLMRouter
from thesisforge.models import DocumentChunkDTO

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Embedding provider protocol & built-in implementations
# ---------------------------------------------------------------------------


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol that any custom embedding backend must satisfy.

    Satisfying this protocol is sufficient to pass a custom provider to
    ``ChromaVectorStore``.  The provider must also satisfy the ChromaDB
    ``EmbeddingFunction`` interface (i.e. be callable with a list of strings).
    """

    def __call__(self, input: Documents) -> Any:  # noqa: A002
        """Return a list of embedding vectors, one per document."""
        ...

    @classmethod
    def name(cls) -> str:
        """Short identifier used in logging."""
        ...


class FastLocalEmbeddingFunction(EmbeddingFunction[Documents]):
    """Deterministic, zero-network 384-dimensional feature hashing embedding function.

    Runs 100% locally with zero external network downloads, eliminating
    CI/offline timeouts.  Uses an MD5-based feature-hashing trick: each token
    is hashed, mapped to a dimension, and its contribution is sign-flipped
    based on a higher-order bit to reduce collision bias.  The resulting vector
    is L2-normalised.

    Semantic quality: LOW.  Identical tokens → identical contribution regardless
    of context; synonyms and paraphrases are unrelated.  Use only for
    development, CI, or offline scenarios.  Switch to
    ``SentenceTransformerEmbeddingFunction`` for production retrieval.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    @classmethod
    def name(cls) -> str:
        return "fast_local"

    def __call__(self, input: Documents) -> Any:  # noqa: A002
        embeddings: list[list[float]] = []
        for doc in input:
            tokens = re.findall(r"\w+", str(doc).lower())
            vec = [0.0] * self.dimensions
            if not tokens:
                embeddings.append(vec)
                continue

            for token in tokens:
                h = int(hashlib.md5(token.encode("utf-8"), usedforsecurity=False).hexdigest(), 16)
                idx = h % self.dimensions
                sign = 1.0 if (h >> 16) & 1 else -1.0
                vec[idx] += sign

            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings


class SentenceTransformerEmbeddingFunction(EmbeddingFunction[Documents]):
    """Real semantic embeddings via the ``sentence-transformers`` library.

    Produces dense 384-dim vectors that capture meaning, synonymy, and
    paraphrasing — significantly better retrieval quality than
    ``FastLocalEmbeddingFunction``.

    First use downloads the model weights (~90 MB for the default
    ``all-MiniLM-L6-v2``).  Subsequent calls use the local cache.

    Requires ``sentence-transformers`` to be installed::

        pip install sentence-transformers

    It is intentionally NOT in the default ``pyproject.toml`` dependencies so
    that the base install stays lightweight.  Add it to your environment when
    production-quality retrieval is needed.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as err:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers\n"
                "Or keep the default FastLocalEmbeddingFunction for offline/CI use."
            ) from err

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        logger.info(
            "SentenceTransformer embedding model loaded.",
            extra={"model": model_name},
        )

    @classmethod
    def name(cls) -> str:
        return "sentence_transformer"

    def __call__(self, input: Documents) -> Any:  # noqa: A002
        texts = [str(doc) for doc in input]
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()


def build_embedding_function(
    provider: str | EmbeddingProvider | None = None,
) -> EmbeddingProvider:
    """Resolve an embedding provider by name or return the supplied instance.

    Args:
        provider: One of:
            - ``None`` / ``"fast_local"`` → ``FastLocalEmbeddingFunction`` (default)
            - ``"sentence_transformer"`` or ``"sentence_transformer:<model>"``
              → ``SentenceTransformerEmbeddingFunction``
            - Any object satisfying ``EmbeddingProvider`` → used as-is.

    Returns:
        A ready-to-use embedding provider.
    """
    if provider is None or provider == "fast_local":
        return FastLocalEmbeddingFunction()

    if isinstance(provider, str):
        if provider.startswith("sentence_transformer"):
            parts = provider.split(":", 1)
            model_name = parts[1] if len(parts) == 2 else "all-MiniLM-L6-v2"
            return SentenceTransformerEmbeddingFunction(model_name=model_name)
        raise ValueError(
            f"Unknown embedding provider name '{provider}'. "
            "Supported: 'fast_local', 'sentence_transformer', "
            "'sentence_transformer:<model-name>'."
        )

    # Duck-type check: accept any callable that looks like an EmbeddingProvider
    if callable(provider):
        return provider

    raise TypeError(
        f"embedding_provider must be a string or an EmbeddingProvider instance, "
        f"got {type(provider)!r}."
    )


# ---------------------------------------------------------------------------
# ChromaDB vector store
# ---------------------------------------------------------------------------


class ChromaVectorStore:
    """Vector database manager wrapping embedded ChromaDB for local scientific literature search.

    Embedding strategy is configurable via ``embedding_provider``:
    - ``None`` / ``"fast_local"`` — fast deterministic hashing (default, CI-safe)
    - ``"sentence_transformer"`` — real semantic vectors (requires sentence-transformers)
    - Any ``EmbeddingProvider`` instance — bring your own backend
    """

    def __init__(
        self,
        persist_directory: str = "data/chroma",
        llm_router: LLMRouter | None = None,
        is_memory: bool = False,
        embedding_function: Any | None = None,  # kept for back-compat
        embedding_provider: str | EmbeddingProvider | None = None,
    ) -> None:
        self.persist_directory = persist_directory
        self.llm = llm_router
        self.is_memory = is_memory

        # Resolve embedding: new ``embedding_provider`` kwarg takes priority;
        # fall back to legacy ``embedding_function`` for backward compatibility.
        if embedding_provider is not None:
            self.embedding_function: EmbeddingProvider = build_embedding_function(
                embedding_provider
            )
        elif embedding_function is not None:
            self.embedding_function = embedding_function
        else:
            self.embedding_function = FastLocalEmbeddingFunction()

        provider_name = getattr(
            self.embedding_function, "name", lambda: type(self.embedding_function).__name__
        )()
        logger.info(
            "ChromaVectorStore initialized.",
            extra={"embedding_provider": provider_name, "is_memory": is_memory},
        )

        if self.is_memory:
            self._client = chromadb.EphemeralClient(
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        else:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

    def _get_collection_name(self, project_id: str) -> str:
        """Sanitize project_id into a valid Chroma collection identifier (3-63 chars alphanumeric)."""
        clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", project_id).strip("_").lower()
        if not clean_id:
            clean_id = "default"
        return f"proj_{clean_id[:50]}"

    def _get_or_create_collection(self, project_id: str) -> Any:
        """Obtain ChromaDB collection for the given project."""
        col_name = self._get_collection_name(project_id)
        return self._client.get_or_create_collection(
            name=col_name,
            embedding_function=self.embedding_function,  # type: ignore[arg-type]
            metadata={"hnsw:space": "cosine"},
        )

    async def add_chunks(self, project_id: str, chunks: list[DocumentChunkDTO]) -> int:
        """Index a list of document chunks into the project's vector collection."""
        if not chunks:
            return 0

        collection = self._get_or_create_collection(project_id)
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            ids.append(chunk.id)
            documents.append(chunk.text)
            metadatas.append(
                {
                    "project_id": chunk.project_id,
                    "document_id": chunk.document_id,
                    "title": chunk.title or "",
                    "doi": chunk.doi or "",
                    "authors": "; ".join(chunk.authors),
                    "year": chunk.year if chunk.year is not None else 0,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "section_name": chunk.section_name,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                }
            )

        embeddings = self.embedding_function(documents)
        try:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info(
                "Indexed chunks into ChromaDB.",
                extra={"project_id": project_id, "chunk_count": len(chunks)},
            )
            return len(chunks)
        except Exception as err:
            logger.warning("ChromaDB add failed.", extra={"error": str(err)})
            raise RAGIndexError(f"Error indexando fragmentos en ChromaDB: {err}") from err

    async def query_chunks(
        self,
        project_id: str,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        section_filter: str | None = None,
    ) -> list[DocumentChunkDTO]:
        """Perform semantic similarity retrieval over indexed literature for a project."""
        clean_query = query.strip()
        if not clean_query:
            return []

        try:
            collection = self._get_or_create_collection(project_id)
        except Exception:
            return []

        where_clause: dict[str, Any] | None = None
        if section_filter:
            where_clause = {"section_name": section_filter}

        query_embeddings = self.embedding_function([clean_query])
        try:
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=min(top_k, 20),
                where=where_clause,
            )
        except Exception as err:
            logger.warning("ChromaDB query failed.", extra={"error": str(err)})
            return []

        matched_chunks: list[DocumentChunkDTO] = []
        ids_raw = results.get("ids")
        if not ids_raw or not ids_raw[0]:
            return []

        ids_list = ids_raw[0]
        docs_raw = results.get("documents")
        docs_list = docs_raw[0] if docs_raw and len(docs_raw) > 0 else []
        metas_raw = results.get("metadatas")
        metas_list = metas_raw[0] if metas_raw and len(metas_raw) > 0 else []
        dist_raw = results.get("distances")
        distances = dist_raw[0] if dist_raw and len(dist_raw) > 0 else []

        for idx, chunk_id in enumerate(ids_list):
            doc_text = str(docs_list[idx]) if idx < len(docs_list) else ""
            meta_item = metas_list[idx] if idx < len(metas_list) else {}
            meta: dict[str, Any] = dict(meta_item) if isinstance(meta_item, dict) else {}

            # Cosine distance to similarity score: similarity = 1 - distance
            distance = distances[idx] if idx < len(distances) else 0.5
            similarity = max(0.0, min(1.0, 1.0 - float(distance)))

            if similarity < min_score:
                continue

            authors_str = str(meta.get("authors", ""))
            authors = [a.strip() for a in authors_str.split(";") if a.strip()]
            doi_val = meta.get("doi")
            doi_str = str(doi_val) if doi_val else None
            year_val = meta.get("year")
            year_int = int(year_val) if year_val else None

            chunk_dto = DocumentChunkDTO(
                id=chunk_id,
                document_id=str(meta.get("document_id", "")),
                project_id=str(meta.get("project_id", project_id)),
                title=str(meta.get("title", "")),
                doi=doi_str,
                authors=authors,
                year=year_int,
                page_number=int(meta.get("page_number", 1)),
                chunk_index=int(meta.get("chunk_index", 0)),
                section_name=str(meta.get("section_name", "body")),
                text=doc_text,
                char_start=int(meta.get("char_start", 0)),
                char_end=int(meta.get("char_end", 0)),
            )
            matched_chunks.append(chunk_dto)

        return matched_chunks

    async def delete_document(self, project_id: str, document_id: str) -> int:
        """Delete all chunks for a specific document in a project."""
        col_name = self._get_collection_name(project_id)
        try:
            collection = self._client.get_collection(name=col_name)
            collection.delete(where={"document_id": document_id})
            logger.info(
                "Deleted document chunks.",
                extra={"project_id": project_id, "document_id": document_id},
            )
            return 1
        except Exception:
            return 0

    async def delete_project_collection(self, project_id: str) -> None:
        """Delete the entire collection for a project."""
        col_name = self._get_collection_name(project_id)
        try:
            self._client.delete_collection(name=col_name)
            logger.info("Deleted project collection.", extra={"project_id": project_id})
        except Exception as err:
            logger.debug(
                "Project collection not found or already deleted.",
                extra={"project_id": project_id, "error": str(err)},
            )
