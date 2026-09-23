"""Data sanitization utilities for academic tables, formula injection prevention (CWE-1236), and draft text cleaning."""

import re
from typing import Any

# Characters triggering spreadsheet / table formula execution
FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell_value(val: Any) -> str:
    """Sanitize a single table cell string against CSV/Excel Formula Injection (CWE-1236).

    If a text cell starts with an executable formula prefix (=, +, -, @, tab, cr),
    an apostrophe is prepended unless the value is a standard decimal number.
    """
    if val is None:
        return ""

    text = str(val).strip()
    if not text:
        return ""

    # Allow valid negative or signed numeric literals (e.g. "-0.45", "+12", "-1500")
    if re.match(r"^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$", text):
        return text

    # Neutralize internal tab/newline injection across all values
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")

    # Check for formula execution triggers
    if text.startswith(FORMULA_TRIGGERS):
        return f"'{text}"

    return text


def sanitize_table_matrix(rows: list[list[Any]]) -> list[list[str]]:
    """Sanitize an entire 2D matrix representing an academic table."""
    return [[sanitize_cell_value(cell) for cell in row] for row in rows]


def clean_draft_markup(raw_text: str) -> str:
    """Clean generated thesis draft text removing conversational preambles, fences, and AI filler."""
    if not raw_text or not raw_text.strip():
        return ""

    text = raw_text.strip()

    # Strip code fences if wrapped in ```markdown ... ``` or ``` ... ```
    if text.startswith("```markdown"):
        text = text[11:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Remove typical conversational AI preambles in Spanish
    preamble_patterns = [
        r"^(?:A continuación|Aquí tienes|A continuación se presenta|En este capítulo|En la presente sección)[^\n]*:\s*\n*",
        r"^(?:Estimado estudiante|Estimado investigador|Como asesor metodológico)[^\n]*:\s*\n*",
        r"^(?:Claro,? con gusto|Por supuesto)[^\n]*:\s*\n*",
    ]
    for pattern in preamble_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove conversational closers
    closer_patterns = [
        r"\n+(?:Espero que este borrador|Si deseas realizar cambios|Quedo atento a tus comentarios)[^\n]*$",
        r"\n+(?:¿Deseas que profundice|¿Qué opinas de esta sección\?)[^\n]*$",
    ]
    for pattern in closer_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Normalize excessive line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
