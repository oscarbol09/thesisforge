"""Scholarly text audit, AI-writing detoxifier, and L3 locator anchor verifier.

Eliminates AI clichés, formulaic transition soup, passive abstraction fog,
and enforces authentic academic registers and citation anchor depth.
"""

from __future__ import annotations

import math
import re
from typing import NamedTuple

from pydantic import BaseModel, ConfigDict, Field

# High-frequency synthetic AI markers and boilerplate formulas (Spanish & English)
AI_SLOP_RULES: list[tuple[str, str, str]] = [
    # (regex_pattern, category, explanation/replacement)
    (
        r"\b(?:crucial facet|pivotal role|beacon of|testament to|delve(?:s|d|ing)? into|tapestry of|vital role|ever-evolving landscape|foster a deeper|stark reminder|paramount importance)\b",
        "ai_cliche_en",
        "Cliché de IA en inglés: Reemplazar por formulaciones empíricas precisas.",
    ),
    (
        r"\b(?:un papel fundamental|un rol crucial|pieza fundamental|tapiz de|un faro de|testimonio de|un recordatorio contundente|paisaje en constante evolución|fomentar una comprensión más profunda|de vital importancia|crucial para entender)\b",
        "ai_cliche_es",
        "Cliché de IA en español: Frase inflada sin contenido empírico. Eliminar o especificar el mecanismo concreto.",
    ),
    (
        r"\b(?:cabe destacar que|es importante resaltar que|es imperativo señalar que|vale la pena mencionar que|resulta imprescindible subrayar que|no se puede subestimar la importancia de)\b",
        "boilerplate_filler",
        "Relleno de transición inflado: Ir directo a la evidencia empírica sin muletillas meta-discursivas.",
    ),
    (
        r"\b(?:en resumen,|en conclusión,|a modo de conclusión,|para concluir,)\b",
        "formulaic_closure",
        "Cierre formulaico redundante: Integrar la conclusión como síntesis conceptual argumentativa.",
    ),
    (
        r"\b(?:game changer|paradigma transformador|a la vanguardia|en el corazón de|revolucionar el campo)\b",
        "hyperbole",
        "Hipérbole comercial/periodística: Inadecuada para registro académico riguroso.",
    ),
    (
        r"\b(?:se podría argumentar que potencialmente|uno podría considerar la posibilidad de que)\b",
        "hedging_fog",
        "Niebla de ambigüedad protectora: Formular afirmaciones con el grado epistémico exacto según la evidencia.",
    ),
]

# Regex detecting L3 Citation Anchors with explicit locators (e.g., p. 12, págs. 34-36, párr. 4, sec. 2.1)
L3_LOCATOR_PATTERN = re.compile(
    r"\((?:[A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+et\s+al\.)?,\s*\d{4}[^)]*?(?:p\.|pp\.|pág\.|págs\.|párr\.|par\.|sec\.|sección|tabla|figura)\s*\d+[^)]*)\)",
    re.IGNORECASE,
)

# Standard in-text citation pattern (e.g., (González, 2023) or (Smith et al., 2024))
STANDARD_CITATION_PATTERN = re.compile(
    r"\((?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+et\s+al\.)?,\s*\d{4})\)",
)


class SlopOccurrence(BaseModel):
    """An identified synthetic writing pattern or cliché."""

    model_config = ConfigDict(frozen=True)

    matched_text: str
    category: str
    explanation: str
    start_pos: int
    end_pos: int


class SentenceRhythmStats(NamedTuple):
    """Statistical metrics of sentence length variability."""

    total_sentences: int
    mean_length: float
    std_dev: float
    monotonous_clusters_count: int


class DraftQualityAuditResult(BaseModel):
    """Comprehensive diagnostic report on academic prose quality and AI-slop density."""

    model_config = ConfigDict(extra="ignore")

    score: float = Field(ge=0.0, le=100.0, description="Overall prose quality score (0-100)")
    word_count: int = Field(ge=0)
    slop_count: int = Field(ge=0)
    slop_density_per_1k: float = Field(ge=0.0)
    slop_occurrences: list[SlopOccurrence] = Field(default_factory=list)
    sentence_count: int = Field(ge=0)
    mean_sentence_length: float = Field(ge=0.0)
    sentence_length_std_dev: float = Field(ge=0.0)
    is_rhythm_monotonous: bool = False
    standard_citations_count: int = Field(ge=0)
    l3_locator_citations_count: int = Field(ge=0)
    l3_coverage_ratio: float = Field(ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences while respecting common academic abbreviations."""
    # Protect common abbreviations like et al., e.g., i.e., pág., etc.
    cleaned = re.sub(r"\b(et al|e\.g|i\.e|pág|págs|vol|núm|art|cap)\.", r"\1<DOT>", text)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return [s.replace("<DOT>", ".").strip() for s in sentences if len(s.strip()) > 3]


def compute_sentence_rhythm(sentences: list[str]) -> SentenceRhythmStats:
    """Analyze sentence length variation to detect formulaic AI cadence."""
    if not sentences:
        return SentenceRhythmStats(0, 0.0, 0.0, 0)

    lengths = [len(s.split()) for s in sentences]
    n = len(lengths)
    mean_len = sum(lengths) / n

    if n < 2:
        return SentenceRhythmStats(n, mean_len, 0.0, 0)

    variance = sum((x - mean_len) ** 2 for x in lengths) / (n - 1)
    std_dev = math.sqrt(variance)

    # Detect monotonous clusters: 4 or more consecutive sentences within +/- 3 words
    monotonous_clusters = 0
    consecutive_similar = 1
    for i in range(1, n):
        if abs(lengths[i] - lengths[i - 1]) <= 3:
            consecutive_similar += 1
            if consecutive_similar == 4:
                monotonous_clusters += 1
        else:
            consecutive_similar = 1

    return SentenceRhythmStats(n, round(mean_len, 2), round(std_dev, 2), monotonous_clusters)


def audit_scholarly_draft(text: str) -> DraftQualityAuditResult:
    """Audit academic draft for AI-slop density, syntactic rhythm, and L3 locator coverage."""
    if not text or not text.strip():
        return DraftQualityAuditResult(
            score=100.0,
            word_count=0,
            slop_count=0,
            slop_density_per_1k=0.0,
            sentence_count=0,
            mean_sentence_length=0.0,
            sentence_length_std_dev=0.0,
            standard_citations_count=0,
            l3_locator_citations_count=0,
            l3_coverage_ratio=1.0,
            recommendations=[],
        )

    words = text.split()
    word_count = len(words)

    # 1. Search AI Slop patterns
    occurrences: list[SlopOccurrence] = []
    for pattern, cat, explanation in AI_SLOP_RULES:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            occurrences.append(
                SlopOccurrence(
                    matched_text=match.group(0),
                    category=cat,
                    explanation=explanation,
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
            )

    slop_count = len(occurrences)
    slop_density = (slop_count / word_count * 1000.0) if word_count > 0 else 0.0

    # 2. Analyze Sentence Rhythm
    sentences = split_into_sentences(text)
    rhythm = compute_sentence_rhythm(sentences)
    is_monotonous = rhythm.monotonous_clusters_count > 0 or (
        rhythm.total_sentences >= 5 and rhythm.std_dev < 4.0
    )

    # 3. Citation Depth (Standard vs L3 Locators)
    standard_cits = STANDARD_CITATION_PATTERN.findall(text)
    l3_cits = L3_LOCATOR_PATTERN.findall(text)
    total_cits = len(standard_cits) + len(l3_cits)
    l3_coverage = (len(l3_cits) / total_cits) if total_cits > 0 else 1.0

    # 4. Compute overall score
    score = 100.0
    # Deduct for slop density (up to -40 pts)
    score -= min(40.0, slop_density * 8.0)
    # Deduct for monotonous rhythm (up to -15 pts)
    if is_monotonous:
        score -= 15.0
    # Deduct if citations exist but lack L3 locators (up to -20 pts)
    if total_cits > 2 and l3_coverage < 0.3:
        score -= 20.0 * (1.0 - l3_coverage)

    score = max(0.0, min(100.0, round(score, 1)))

    # 5. Build actionable recommendations
    recommendations: list[str] = []
    if slop_count > 0:
        recommendations.append(
            f"Se detectaron {slop_count} instancias de lenguaje sintético/clichés de IA. "
            "Reemplace muletillas como 'cabe destacar' o 'un papel fundamental' por evidencia empírica directa."
        )
    if is_monotonous:
        recommendations.append(
            "El ritmo sintáctico es monótono (oraciones de longitud casi idéntica). "
            "Varíe la cadencia combinando oraciones compuestas con sentencias breves y directas."
        )
    if total_cits > 0 and l3_coverage < 0.5:
        recommendations.append(
            "Mejore el anclaje de citas a nivel L3: incluya localizadores específicos (pág., párr. o sección) "
            "para afirmaciones empíricas clave en lugar de citas globales únicamente."
        )

    return DraftQualityAuditResult(
        score=score,
        word_count=word_count,
        slop_count=slop_count,
        slop_density_per_1k=round(slop_density, 2),
        slop_occurrences=occurrences,
        sentence_count=rhythm.total_sentences,
        mean_sentence_length=rhythm.mean_length,
        sentence_length_std_dev=rhythm.std_dev,
        is_rhythm_monotonous=is_monotonous,
        standard_citations_count=len(standard_cits),
        l3_locator_citations_count=len(l3_cits),
        l3_coverage_ratio=round(l3_coverage, 2),
        recommendations=recommendations,
    )


def detoxify_text(raw_text: str) -> str:
    """Perform deterministic sanitization and removal of common AI meta-discursive filler."""
    if not raw_text:
        return ""

    text = raw_text

    # Replace boilerplate preambles and meta-commentary phrases
    replacements = [
        (r"\b[Cc]abe destacar que\s+", ""),
        (r"\b[Ee]s importante (?:resaltar|señalar|mencionar) que\s+", ""),
        (r"\b[Vv]ale la pena mencionar que\s+", ""),
        (r"\b[Ee]s imperativo subrayar que\s+", ""),
        (r"\b[Ee]n resumen,\s+", ""),
        (r"\b[Ee]n conclusión,\s+", ""),
        (r"\b[Aa] modo de conclusión,\s+", ""),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    # Capitalize first letter of sentences if stripped phrase was at beginning
    sentences = split_into_sentences(text)
    capitalized = []
    for s in sentences:
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        capitalized.append(s)

    cleaned = " ".join(capitalized)
    return cleaned.strip()
