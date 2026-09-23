"""Academic PDF parsing, prompt injection sanitization, and sentence-aware chunking."""

import re
from pathlib import Path

import pymupdf as fitz

from thesisforge.core.logging import get_logger
from thesisforge.exceptions import DocumentProcessingError
from thesisforge.models import DocumentChunkDTO

logger = get_logger(__name__)

# Known academic section patterns in Spanish and English
SECTION_PATTERNS = [
    (r"^(?:resumen|abstract)\b", "Abstract"),
    (r"^(?:1\.?\s*)?(?:introducci[oó]n|introduction)\b", "Introduction"),
    (
        r"^(?:2\.?\s*)?(?:marco\s+te[oó]rico|estado\s+del\s+arte|literature\s+review|background)\b",
        "Literature Review",
    ),
    (
        r"^(?:3\.?\s*)?(?:metodolog[ií]a|m[eé]todos?|methodology|materials\s+and\s+methods)\b",
        "Methodology",
    ),
    (r"^(?:4\.?\s*)?(?:resultados|results)\b", "Results"),
    (r"^(?:5\.?\s*)?(?:discusi[oó]n|discussion)\b", "Discussion"),
    (r"^(?:6\.?\s*)?(?:conclusiones|conclusions)\b", "Conclusions"),
    (r"^(?:referencias|bibliograf[ií]a|references)\b", "References"),
]

# Patterns for sentence tokenization preserving common scientific abbreviations
ABBREVIATION_PATTERN = re.compile(
    r"\b(?:et\s+al|e\.g|i\.e|dr|prof|fig|vs|p\.ej|vol|no|pp|art|sec|dept)\.$",
    re.IGNORECASE,
)


def sanitize_extracted_text(text: str) -> str:
    """Strip dangerous control characters and neutralize prompt injection delimiters."""
    if not text:
        return ""
    # Strip non-printable ASCII control characters except \n, \t, \r
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Neutralize prompt injection delimiter tokens
    cleaned = re.sub(
        r"</?(?:SYSTEM|RETRIEVED|RESEARCHER|INSTRUCTION)[^>]*>",
        "[DELIMITER_REMOVED]",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(?:ignore\s+previous\s+instructions|system\s+prompt\s+override)",
        "[DISALLOWED_INSTRUCTION_REMOVED]",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Normalize excessive carriage returns
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    return cleaned.strip()


class SentenceAwareChunker:
    """Splits academic text along sentence boundaries preserving context and claims."""

    def __init__(
        self,
        target_chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ) -> None:
        self.target_chunk_size = max(300, target_chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.target_chunk_size // 2))

    @staticmethod
    def split_into_sentences(text: str) -> list[str]:
        """Tokenize text into sentences avoiding breaks on academic abbreviations."""
        raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sentences: list[str] = []

        for paragraph in raw_paragraphs:
            # Tokenize by punctuation followed by whitespace and capital letter
            raw_splits = re.split(r"(?<=[.!?])\s+(?=[A-Z¿¡\"'])", paragraph)
            buffer = ""
            for token in raw_splits:
                token_clean = token.strip()
                if not token_clean:
                    continue
                if buffer:
                    if ABBREVIATION_PATTERN.search(buffer):
                        buffer = f"{buffer} {token_clean}"
                        continue
                    else:
                        sentences.append(buffer)
                        buffer = token_clean
                else:
                    buffer = token_clean
            if buffer:
                sentences.append(buffer)

        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(
        self,
        text: str,
        project_id: str,
        document_id: str,
        page_number: int = 1,
        section_name: str = "body",
        title: str = "",
        doi: str | None = None,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> list[DocumentChunkDTO]:
        """Segment input text into overlapping chunks without splitting sentences."""
        clean_text = sanitize_extracted_text(text)
        if not clean_text:
            return []

        sentences = self.split_into_sentences(clean_text)
        if not sentences:
            return []

        chunks: list[DocumentChunkDTO] = []
        current_chunk_sentences: list[str] = []
        current_len = 0
        chunk_idx = 0
        char_cursor = 0

        for sentence in sentences:
            sentence_len = len(sentence) + 1  # Account for space
            if current_len + sentence_len > self.target_chunk_size and current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences).strip()
                char_start = char_cursor
                char_end = char_cursor + len(chunk_text)

                chunks.append(
                    DocumentChunkDTO(
                        document_id=document_id,
                        project_id=project_id,
                        title=title,
                        doi=doi,
                        authors=authors or [],
                        year=year,
                        page_number=page_number,
                        chunk_index=chunk_idx,
                        section_name=section_name,
                        text=chunk_text,
                        char_start=char_start,
                        char_end=char_end,
                    )
                )
                chunk_idx += 1
                char_cursor = char_end

                # Calculate overlap sentences
                overlap_sentences: list[str] = []
                overlap_len = 0
                for s in reversed(current_chunk_sentences):
                    if overlap_len + len(s) + 1 <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s) + 1
                    else:
                        break

                current_chunk_sentences = list(overlap_sentences)
                current_len = sum(len(s) + 1 for s in current_chunk_sentences)

            current_chunk_sentences.append(sentence)
            current_len += sentence_len

        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences).strip()
            char_start = char_cursor
            char_end = char_cursor + len(chunk_text)
            chunks.append(
                DocumentChunkDTO(
                    document_id=document_id,
                    project_id=project_id,
                    title=title,
                    doi=doi,
                    authors=authors or [],
                    year=year,
                    page_number=page_number,
                    chunk_index=chunk_idx,
                    section_name=section_name,
                    text=chunk_text,
                    char_start=char_start,
                    char_end=char_end,
                )
            )

        return chunks


class PDFDocumentParser:
    """Extracts, cleans, and sections text from PDF documents using PyMuPDF."""

    def __init__(
        self,
        chunker: SentenceAwareChunker | None = None,
    ) -> None:
        self.chunker = chunker or SentenceAwareChunker()

    @staticmethod
    def _detect_section(text: str, current_section: str) -> str:
        """Heuristically identify academic section boundaries from line headings."""
        lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
        for line in lines[:5]:  # Look at the top 5 lines of the page/block
            for pattern, section_name in SECTION_PATTERNS:
                if re.match(pattern, line, re.IGNORECASE):
                    return section_name
        return current_section

    def parse_pdf_bytes(
        self,
        pdf_bytes: bytes,
        project_id: str,
        document_id: str,
        title: str = "",
        doi: str | None = None,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> list[DocumentChunkDTO]:
        """Extract text page-by-page from raw PDF bytes and chunk into DocumentChunkDTOs."""
        if not pdf_bytes:
            raise DocumentProcessingError("El archivo PDF está vacío o no contiene bytes válidos.")

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")  # type: ignore[no-untyped-call]
            if doc.is_encrypted:
                raise DocumentProcessingError(
                    "El archivo PDF está protegido con contraseña y no puede ser indexado."
                )
        except DocumentProcessingError:
            raise
        except Exception as err:
            logger.warning("PyMuPDF failed to open PDF document.", extra={"error": str(err)})
            raise DocumentProcessingError(f"No se pudo procesar el PDF: {err}") from err

        all_chunks: list[DocumentChunkDTO] = []
        current_section = "Introduction"
        global_chunk_idx = 0

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()  # type: ignore[no-untyped-call]
                if not page_text or not page_text.strip():
                    continue

                current_section = self._detect_section(page_text, current_section)
                page_chunks = self.chunker.chunk_text(
                    text=page_text,
                    project_id=project_id,
                    document_id=document_id,
                    page_number=page_num + 1,
                    section_name=current_section,
                    title=title,
                    doi=doi,
                    authors=authors,
                    year=year,
                )

                for chunk in page_chunks:
                    chunk.chunk_index = global_chunk_idx
                    global_chunk_idx += 1
                    all_chunks.append(chunk)

        finally:
            doc.close()  # type: ignore[no-untyped-call]

        logger.info(
            "PDF parsed successfully into sentence-aware chunks.",
            extra={
                "project_id": project_id,
                "document_id": document_id,
                "total_chunks": len(all_chunks),
            },
        )
        return all_chunks

    def parse_pdf_file(
        self,
        file_path: Path | str,
        project_id: str,
        document_id: str,
        title: str = "",
        doi: str | None = None,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> list[DocumentChunkDTO]:
        """Read PDF from file system and parse into structured chunks."""
        path = Path(file_path)
        if not path.is_file():
            raise DocumentProcessingError(f"El archivo '{file_path}' no existe.")
        return self.parse_pdf_bytes(
            pdf_bytes=path.read_bytes(),
            project_id=project_id,
            document_id=document_id,
            title=title or path.stem,
            doi=doi,
            authors=authors,
            year=year,
        )
