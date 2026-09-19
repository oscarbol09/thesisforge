"""Citation Guard ensuring DOI validity and claim-evidence grounding."""

import re

from thesisforge.core.logging import get_logger
from thesisforge.llm.prompts import EVIDENCE_VERIFICATION_PROMPT
from thesisforge.llm.router import LLMRouter
from thesisforge.models import (
    CitationDTO,
    DocumentChunkDTO,
    EvidenceVerdictDTO,
)
from thesisforge.rag.apa_formatter import APA7Formatter
from thesisforge.rag.clients.crossref import CrossRefClient

logger = get_logger(__name__)


class CitationGuard:
    """Validator ensuring that cited papers have valid DOIs and actually support scientific claims."""

    def __init__(
        self,
        crossref_client: CrossRefClient,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self.crossref = crossref_client
        self.llm = llm_router

    async def verify_doi(self, doi: str) -> bool:
        """Query official CrossRef registry to verify DOI existence."""
        if not doi or not doi.strip():
            return False
        result = await self.crossref.resolve_doi(doi)
        return result is not None and result.doi is not None

    @staticmethod
    def _compute_lexical_grounding(claim: str, chunk_text: str) -> float:
        """Calculate word overlap and key term presence between claim and source passage."""
        claim_words = set(re.findall(r"\b\w{4,}\b", claim.lower()))
        chunk_words = set(re.findall(r"\b\w{4,}\b", chunk_text.lower()))

        if not claim_words:
            return 0.0

        intersection = claim_words.intersection(chunk_words)
        return len(intersection) / len(claim_words)

    async def verify_claim_evidence(
        self,
        claim: str,
        retrieved_chunks: list[DocumentChunkDTO],
    ) -> EvidenceVerdictDTO:
        """Verify whether candidate text chunks substantiate the scientific claim."""
        clean_claim = claim.strip()
        if not clean_claim:
            return EvidenceVerdictDTO(
                claim=claim,
                is_supported=False,
                confidence_score=0.0,
                refuting_or_missing_reason="Afirmación vacía proporcionada.",
            )

        if not retrieved_chunks:
            return EvidenceVerdictDTO(
                claim=clean_claim,
                is_supported=False,
                confidence_score=0.0,
                refuting_or_missing_reason="No se encontraron fragmentos de literatura relacionados.",
            )

        # 1. Deterministic heuristic scoring
        matching_citations: list[CitationDTO] = []
        max_score = 0.0

        for chunk in retrieved_chunks:
            score = self._compute_lexical_grounding(clean_claim, chunk.text)
            if score > max_score:
                max_score = score

            if score >= 0.25:  # Overlap threshold for candidate relevance
                cit = CitationDTO(
                    doi=chunk.doi,
                    title=chunk.title or f"Documento {chunk.document_id}",
                    authors=chunk.authors,
                    year=chunk.year or 2024,
                    abstract=chunk.text[:500],
                    chunk_id=chunk.id,
                    section_name=chunk.section_name,
                    page_number=chunk.page_number,
                    relevance_score=round(score, 3),
                    supports_claim=score >= 0.40,
                    evidence_text=chunk.text[:1000],
                )
                cit.apa_formatted = APA7Formatter.format_reference_entry(cit)
                matching_citations.append(cit)

        # 2. LLM-assisted verification if router is configured
        if self.llm and matching_citations:
            evidence_context = "\n\n".join(
                f"[Fragmento #{idx + 1} | Página {c.page_number} | Sección: {c.section_name}]\n{c.evidence_text}"
                for idx, c in enumerate(matching_citations[:3])
            )
            prompt = EVIDENCE_VERIFICATION_PROMPT.format(
                claim=clean_claim,
                evidence_passages=evidence_context,
            )
            try:
                llm_verdict = await self.llm.complete_json(prompt)
                is_supported = bool(llm_verdict.get("is_supported", False))
                confidence = float(llm_verdict.get("confidence_score", max_score))
                reason = str(llm_verdict.get("reasoning", ""))

                for cit in matching_citations:
                    cit.supports_claim = is_supported

                return EvidenceVerdictDTO(
                    claim=clean_claim,
                    is_supported=is_supported,
                    confidence_score=round(confidence, 3),
                    supporting_chunks=matching_citations,
                    refuting_or_missing_reason=reason if not is_supported else "",
                )
            except Exception as e:
                logger.warning(
                    "LLM evidence verification fallback to heuristic.",
                    extra={"error": str(e)},
                )

        is_supported = max_score >= 0.40
        return EvidenceVerdictDTO(
            claim=clean_claim,
            is_supported=is_supported,
            confidence_score=round(max_score, 3),
            supporting_chunks=matching_citations,
            refuting_or_missing_reason=""
            if is_supported
            else "La evidencia disponible no respalda suficientemente los términos clave de la afirmación.",
        )
