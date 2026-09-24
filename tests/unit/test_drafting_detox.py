"""Unit tests for scholarly drafting detox, AI-slop auditor, and L3 locator anchor checks."""


from thesisforge.drafting.detox import (
    audit_scholarly_draft,
    compute_sentence_rhythm,
    detoxify_text,
    split_into_sentences,
)


def test_split_into_sentences_handles_academic_abbreviations() -> None:
    text = "Según Hernández et al. (2020), la muestra fue de 150 sujetos. En la pág. 45 se detallan los resultados."
    sentences = split_into_sentences(text)
    assert len(sentences) == 2
    assert "et al." in sentences[0]
    assert "pág. 45" in sentences[1]


def test_compute_sentence_rhythm_identifies_monotony() -> None:
    # 5 sentences with identical length (5 words each)
    monotonous = [
        "El estudio analizó los datos.",
        "Los datos mostraron gran impacto.",
        "El impacto fue muy significativo.",
        "Los autores confirmaron la hipótesis.",
        "La hipótesis quedó totalmente demostrada.",
    ]
    stats = compute_sentence_rhythm(monotonous)
    assert stats.total_sentences == 5
    assert stats.monotonous_clusters_count >= 1


def test_audit_scholarly_draft_detects_ai_slop_and_hedging() -> None:
    slop_text = (
        "Cabe destacar que este estudio juega un papel fundamental en el tapiz de la investigación. "
        "Es importante resaltar que delve into an ever-evolving landscape resulta crucial para entender "
        "el impacto. Se podría argumentar que potencialmente es un game changer."
    )
    result = audit_scholarly_draft(slop_text)
    assert result.slop_count >= 4
    assert result.score < 80.0
    assert len(result.slop_occurrences) >= 4
    assert any(o.category == "ai_cliche_es" for o in result.slop_occurrences)
    assert any(o.category == "ai_cliche_en" for o in result.slop_occurrences)
    assert len(result.recommendations) >= 1


def test_audit_scholarly_draft_rewards_clean_human_text_with_l3_citations() -> None:
    clean_text = (
        "La correlación entre el estrés laboral y el desempeño docente fue evaluada mediante el coeficiente de Spearman. "
        "Los resultados indicaron una asociación inversa moderada (González et al., 2023, p. 45). "
        "Asimismo, se observó que la sobrecarga administrativa constituyó el principal predictor de fatiga (Martínez, 2022, sec. 3.2). "
        "No se encontraron diferencias estadísticamente significativas por género en el grupo evaluado."
    )
    result = audit_scholarly_draft(clean_text)
    assert result.slop_count == 0
    assert result.score >= 85.0
    assert result.l3_locator_citations_count == 2
    assert result.l3_coverage_ratio == 1.0


def test_audit_scholarly_draft_empty_text() -> None:
    result = audit_scholarly_draft("")
    assert result.score == 100.0
    assert result.word_count == 0
    assert result.slop_count == 0


def test_detoxify_text_removes_meta_fillers_and_capitalizes() -> None:
    raw = "cabe destacar que los hallazgos demostraron validez interna. Es importante señalar que el modelo convergió."
    cleaned = detoxify_text(raw)
    assert "cabe destacar que" not in cleaned.lower()
    assert "es importante señalar que" not in cleaned.lower()
    assert cleaned.startswith("Los hallazgos")
