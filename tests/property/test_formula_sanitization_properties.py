"""Property-based tests for table formula sanitization (CWE-1236) and text cleaning."""

import re

from hypothesis import given
from hypothesis import strategies as st

from thesisforge.drafting.sanitizer import (
    FORMULA_TRIGGERS,
    clean_draft_markup,
    sanitize_cell_value,
    sanitize_table_matrix,
)


@given(st.text(min_size=1, max_size=200))
def test_property_formula_trigger_sanitization_invariant(cell_text: str):
    """Ensure no non-numeric string starts with an unescaped formula trigger after sanitization."""
    sanitized = sanitize_cell_value(cell_text)

    # Empty string is safe
    if not sanitized:
        return

    # If it is a valid signed number, it is safe
    if re.match(r"^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$", sanitized):
        return

    # If the original started with a trigger, the sanitized version MUST start with an apostrophe
    first_char = cell_text.strip()[:1] if cell_text.strip() else ""
    if first_char in FORMULA_TRIGGERS:
        assert sanitized.startswith("'"), f"Cell '{cell_text}' was not escaped with leading apostrophe"


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_property_numeric_values_preserved(number: float):
    """Ensure numeric values (e.g. negative numbers) are not corrupted into string apostrophes."""
    str_num = f"{number:.4f}"
    sanitized = sanitize_cell_value(str_num)
    assert not sanitized.startswith("'")
    assert float(sanitized) == float(str_num)


@given(
    st.lists(
        st.lists(st.text(max_size=50), min_size=1, max_size=5),
        min_size=1,
        max_size=5,
    )
)
def test_property_matrix_dimensions_invariant(matrix: list[list[str]]):
    """Ensure sanitize_table_matrix preserves exact matrix row/col dimensions."""
    sanitized = sanitize_table_matrix(matrix)
    assert len(sanitized) == len(matrix)
    for orig_row, san_row in zip(matrix, sanitized, strict=True):
        assert len(san_row) == len(orig_row)


@given(st.text(min_size=0, max_size=500))
def test_property_clean_draft_markup_never_has_markdown_fences(raw_text: str):
    """Ensure clean_draft_markup strips ```markdown fences."""
    fenced = f"```markdown\n{raw_text}\n```"
    cleaned = clean_draft_markup(fenced)
    assert not cleaned.startswith("```markdown")
    assert not cleaned.endswith("```")
