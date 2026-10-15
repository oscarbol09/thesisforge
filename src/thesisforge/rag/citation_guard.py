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
        candidate_threshold: float = 0.25,
        support_threshold: float = 0.40,
    ) -> None:
        self.crossref = crossref_client
        self.llm = llm_router
        self.candidate_threshold = candidate_threshold
        self.support_threshold = support_threshold

    async def verify_doi(self, doi: str) -> bool:
        """Query official CrossRef registry to verify DOI existence."""
        if not doi or not doi.strip():
            return False
        result = await self.crossref.resolve_doi(doi)
        return result is not None and result.doi is not None

    NEGATION_TERMS: frozenset[str] = frozenset(
        {
            "no",
            "sin",
            "nunca",
            "jamás",
            "jamas",
            "not",
            "never",
            "neither",
            "none",
            "without",
        }
    )

    @classmethod
    def _check_negation_in_proximity(
        cls, tokens: list[str], keywords: set[str], window: int = 2
    ) -> bool:
        """Check if any negation term immediately precedes (within window tokens) any keyword.

        Negation particles in Spanish and English ('no', 'not', 'never', 'sin', 'without')
        are prepositive and directly modify the following verb or predicate.
        """
        n_tokens = len(tokens)
        for idx, token in enumerate(tokens):
            if token in keywords:
                start = max(0, idx - window)
                for j in range(start, idx):
                    tok = tokens[j]
                    if tok in cls.NEGATION_TERMS:
                        # Exclude Spanish adversative idiom 'sin embargo'
                        if tok == "sin" and j + 1 < n_tokens and tokens[j + 1] == "embargo":
                            continue
                        return True
        return False

    @classmethod
    def _compute_lexical_grounding(cls, claim: str, chunk_text: str) -> float:
        """Calculate word overlap and key term presence between claim and source passage.

        Detects polarity and negation asymmetries to prevent false grounding.
        """
        claim_lower = claim.lower()
        chunk_lower = chunk_text.lower()

        claim_tokens = re.findall(r"\b[\wáéíóúüñ]+\b", claim_lower)
        chunk_tokens = re.findall(r"\b[\wáéíóúüñ]+\b", chunk_lower)

        claim_words = {w for w in claim_tokens if len(w) >= 4 and w not in cls.NEGATION_TERMS}
        chunk_words = {w for w in chunk_tokens if len(w) >= 4 and w not in cls.NEGATION_TERMS}

        if not claim_words:
            return 0.0

        intersection = claim_words.intersection(chunk_words)
        if not intersection:
            return 0.0

        raw_score = len(intersection) / len(claim_words)

        # Polarity & negation asymmetry detection
        claim_has_neg = cls._check_negation_in_proximity(claim_tokens, intersection, window=4)
        chunk_has_neg = cls._check_negation_in_proximity(chunk_tokens, intersection, window=4)

        if claim_has_neg != chunk_has_neg:
            # Asymmetry detected: one negates while the other affirms.
            # Penalize overlap score heavily (0.2x multiplier) to prevent false positives.
            return round(raw_score * 0.2, 3)

        return round(raw_score, 3)

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

            if score >= self.candidate_threshold:  # Overlap threshold for candidate relevance
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
                    supports_claim=score >= self.support_threshold,
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

        is_supported = max_score >= self.support_threshold
        return EvidenceVerdictDTO(
            claim=clean_claim,
            is_supported=is_supported,
            confidence_score=round(max_score, 3),
            supporting_chunks=matching_citations,
            refuting_or_missing_reason=""
            if is_supported
            else "La evidencia disponible no respalda suficientemente los términos clave de la afirmación.",
        )
