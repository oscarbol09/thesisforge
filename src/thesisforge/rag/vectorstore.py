"""Embedded vector store adapter using ChromaDB with multi-tenant project isolation."""

import hashlib
import math
import re
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction
from chromadb.config import Settings as ChromaSettings

from thesisforge.core.logging import get_logger
from thesisforge.exceptions import RAGIndexError
from thesisforge.llm.router import LLMRouter
from thesisforge.models import DocumentChunkDTO

logger = get_logger(__name__)


class FastLocalEmbeddingFunction(EmbeddingFunction[Documents]):
    """Deterministic, zero-network 384-dimensional feature hashing embedding function.

    Runs 100% locally with zero external network downloads, eliminating CI/offline timeouts.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    @classmethod
    def name(cls) -> str:
        return "default"

    def __call__(self, input: Documents) -> Any:

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


class ChromaVectorStore:
    """Vector database manager wrapping embedded ChromaDB for local scientific literature search."""

    def __init__(
        self,
        persist_directory: str = "data/chroma",
        llm_router: LLMRouter | None = None,
        is_memory: bool = False,
        embedding_function: Any | None = None,
    ) -> None:
        self.persist_directory = persist_directory
        self.llm = llm_router
        self.is_memory = is_memory
        self.embedding_function = embedding_function or FastLocalEmbeddingFunction()

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
        """Sanitize project_id into a valid Chroma collection identifier."""
        clean_id = project_id.replace("-", "_").lower()
        return f"proj_{clean_id}"

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
