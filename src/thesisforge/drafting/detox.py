"""Scholarly text audit, AI-writing detoxifier, and L3 locator anchor verifier.

Eliminates AI clichés, formulaic transition soup, passive abstraction fog,
and enforces authentic academic registers and citation anchor depth.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, NamedTuple

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Iterator

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
    (
        r"\b(?:altamente significativo|muy significativo|significancia extrema)\b",
        "statistical_inflation",
        "Inflación inferencial: La significancia estadística es binaria (decisión sobre H₀), no tiene grados. Emplear el tamaño del efecto (d, η², r) para reportar la magnitud.",
    ),
    (
        r"\bp\s*=\s*(?:0\.000|\.000)\b",
        "apa_statistical_zero",
        "Error de reporte APA 7: Un valor p nunca puede ser cero. Reportar como 'p < .001'.",
    ),
    (
        r"\b(?:la hip[oó]tesis (?:se confirma|es verdadera|qued[oó] demostrada) al \d+%|(?:confirmar|verificar) la hip[oó]tesis con un \d+%)",
        "frequentist_misconception",
        "Error epistemológico frecuentista: El p-valor no mide la probabilidad de verdad de la hipótesis, sino la probabilidad de los datos bajo H₀.",
    ),
    (
        r"\b(?:se recomienda mejorar la calidad(?: educativa)?|es necesario concientizar a la (?:comunidad|población|sociedad)|sería interesante (?:seguir|continuar) investigando este tema|los docentes deberían reflexionar más sobre su práctica)\b",
        "vacuous_recommendation",
        "Recomendación vacua o genérica: Toda recomendación debe estructurarse con destinatario explícito, acción en infinitivo, hallazgo de origen e indicador de seguimiento.",
    ),
    (
        r"\b(?:se encontr[oó] evidencia que podr[ií]a sugerir una posible mejora|parece haber indicios de que posiblemente)\b",
        "conclusions_evasion_fog",
        "Evasiva sintáctica en conclusión: Exprese la inferencia de manera afirmativa y directa, modulando la certeza a través del estatus epistémico declarado.",
    ),
]

# Regex detecting L3 Citation Anchors with explicit locators (e.g., p. 12, págs. 34-36, párr. 4, sec. 2.1)
L3_LOCATOR_PATTERN = re.compile(
    r"\((?:[A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+et\s+al\.)?,\s*\d{4}[^)]*?(?:p\.|pp\.|pág\.|págs\.|párr\.|par\.|sec\.|sección|tabla|figura)\s*\d+[^)]*)\)",
    re.IGNORECASE,
)

# Capitalized surnames may contain diacritics, hyphens, and lowercase particles.
_AUTHOR_LETTER = r"(?:[^\W\d_]|[\u0300-\u036f])"
_SURNAME_WORD = rf"[A-ZÀ-ÖØ-Þ]{_AUTHOR_LETTER}*(?:-[^\W\d_]{_AUTHOR_LETTER}*)*"
_NAME_PARTICLES = r"(?:(?:de|del|la|las|los)\s+)*"
_SURNAME = rf"{_NAME_PARTICLES}{_SURNAME_WORD}(?:\s+{_NAME_PARTICLES}{_SURNAME_WORD})*"
STANDARD_CITATION_PATTERN = re.compile(
    rf"\({_SURNAME}"
    rf"(?:\s+et\s+al\.|(?:(?:\s*&\s*|\s+y\s+){_SURNAME})+)?"
    r",\s*\d{4}\)",
)

# Consume whitespace after abbreviations before it can be matched as a sentence separator.
_SENTENCE_BOUNDARY = re.compile(
    r"\b(?:et[ \t]+al|e\.g|i\.e|pp?|págs?|párr|par|sec|vol|núm|art|cap|dra?|vs|cfr)\.\s+"
    r"|(?<=[.!?])(?P<separator>\s+)",
    re.IGNORECASE,
)

# Retain blank lines, ATX headings and list prefixes as separators between prose blocks.
_MARKDOWN_BOUNDARY = re.compile(
    r"((?:\A|(?<=\n)|(?<=\r)(?!\n))[ \t]*(?:"
    r"#{1,6}(?:[ \t][^\r\n]*)?(?=[\r\n]|\Z)"
    r"|(?:[-+*]|\d+[.)])[ \t]+"
    r"|\r\n?|\n))"
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


def _sentence_parts(text: str) -> Iterator[tuple[str, str]]:
    """Yield sentence text with its original separator."""
    start = 0
    for boundary in _SENTENCE_BOUNDARY.finditer(text):
        if boundary.lastgroup == "separator":
            yield text[start : boundary.start()], boundary[0]
            start = boundary.end()
    yield text[start:], ""


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences while respecting common academic abbreviations."""
    return [stripped for sentence, _ in _sentence_parts(text) if (stripped := sentence.strip())]


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
            score=0.0,
            word_count=0,
            slop_count=0,
            slop_density_per_1k=0.0,
            sentence_count=0,
            mean_sentence_length=0.0,
            sentence_length_std_dev=0.0,
            standard_citations_count=0,
            l3_locator_citations_count=0,
            l3_coverage_ratio=0.0,
            recommendations=[
                "El borrador está vacío. Redacta o genera contenido para comenzar la auditoría de calidad científica."
            ],
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
    """Remove common boilerplate phrases while preserving Markdown structure."""
    if not raw_text:
        return ""

    filler = re.compile(
        r"\b(?:[Cc]abe destacar que|[Ee]s importante (?:resaltar|señalar|mencionar) que"
        r"|[Vv]ale la pena mencionar que|[Ee]s imperativo subrayar que"
        r"|[Ee]n resumen,|[Ee]n conclusión,|[Aa] modo de conclusión,)"
        r"(?:[^\S\r\n]+(?=\S)|(?=[^\S\r\n]*[\r\n]))"
    )

    def clean_prose(prose: str) -> str:
        return "".join(
            re.sub(r"^(\s*)(\w)", lambda match: match[1] + match[2].upper(), sentence) + separator
            for sentence, separator in _sentence_parts(filler.sub("", prose))
        )

    parts = _MARKDOWN_BOUNDARY.split(raw_text)
    for i in range(0, len(parts), 2):
        parts[i] = clean_prose(parts[i])
    return "".join(parts)
