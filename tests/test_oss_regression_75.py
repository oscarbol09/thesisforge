from thesisforge.drafting.detox import (
    STANDARD_CITATION_PATTERN,
    detoxify_text,
    split_into_sentences,
)


def test_detox_preserves_spanish_academic_markdown() -> None:
    heading = "## Métodos: cabe destacar que se conservan"
    draft = (
        f"{heading}\r\n"
        "\r\n"
        "Cabe destacar que este estudio\r\n"
        "incluye tres casos.  Es importante señalar que los datos se conservan.  \r\n"
        "    - Vale la pena mencionar que hoy hay dos casos.\n"
        "    * No.\n"
        "\n"
        "Sí."
    )
    expected_draft = (
        f"{heading}\r\n"
        "\r\n"
        "Este estudio\r\n"
        "incluye tres casos.  Los datos se conservan.  \r\n"
        "    - Hoy hay dos casos.\n"
        "    * No.\n"
        "\n"
        "Sí."
    )
    sentence = "El Dr. Núñez y la Dra. Ruiz contrastan A vs. B (cfr. pp. 3-5, p. 8)."
    citations = [
        "(Pérez & López, 2023)",
        "(García-Márquez, 1982)",
        "(de la Cruz y Peña del Río, 2020)",
        "(Muñoz et al., 2024)",
        "(García Márquez, 1981)",
        "(Nu\u0301ñez, 2021)",
    ]
    cited_text = f"Según {', '.join(citations)}. Véase (Pérez, 2023, p. 8) y (métodos, 2020)."

    assert (
        detoxify_text(draft),
        split_into_sentences(f"{sentence} No."),
        STANDARD_CITATION_PATTERN.findall(cited_text),
    ) == (expected_draft, [sentence, "No."], citations)
