"""Property-based invariant testing for APA 7th Edition citation formatting."""

from hypothesis import given
from hypothesis import strategies as st

from thesisforge.models import CitationDTO
from thesisforge.rag.apa_formatter import APA7Formatter

# Strategies for generating random academic citations
author_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll"), whitelist_characters=" -'"),
    min_size=2,
    max_size=30,
).filter(lambda s: len(s.strip()) >= 2)

authors_list_strategy = st.lists(author_name_strategy, min_size=1, max_size=25)
title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" ,:;?-"),
    min_size=3,
    max_size=100,
).filter(lambda s: len(s.strip()) >= 3)
year_strategy = st.integers(min_value=1900, max_value=2050)
doi_strategy = st.from_regex(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", fullmatch=True)


@given(
    authors=authors_list_strategy,
    title=title_strategy,
    year=year_strategy,
    doi=st.one_of(st.none(), doi_strategy),
)
def test_property_apa_parenthetical_invariants(
    authors: list[str], title: str, year: int, doi: str | None
):
    """Parenthetical citation invariant: always enclosed in parens, et al. for >=3 authors."""
    cit = CitationDTO(
        title=title,
        authors=authors,
        year=year,
        doi=doi,
    )
    formatted = APA7Formatter.format_parenthetical(cit)

    assert formatted.startswith("(")
    assert formatted.endswith(")")
    assert str(year) in formatted

    if len(authors) >= 3:
        assert "et al." in formatted
    elif len(authors) == 2:
        assert "&" in formatted


@given(
    authors=authors_list_strategy,
    title=title_strategy,
    year=year_strategy,
)
def test_property_apa_narrative_invariants(authors: list[str], title: str, year: int):
    """Narrative citation invariant: Year in parens, et al. for >=3 authors."""
    cit = CitationDTO(
        title=title,
        authors=authors,
        year=year,
    )
    formatted = APA7Formatter.format_narrative(cit, language="es")

    assert f"({year})" in formatted
    if len(authors) >= 3:
        assert "et al." in formatted
    elif len(authors) == 2:
        assert " y " in formatted


@given(
    authors=authors_list_strategy,
    title=title_strategy,
    year=year_strategy,
    journal=st.one_of(st.none(), title_strategy),
    doi=st.one_of(st.none(), doi_strategy),
)
def test_property_apa_reference_entry_invariants(
    authors: list[str], title: str, year: int, journal: str | None, doi: str | None
):
    """Reference entry invariant: Contains year, title, journal markdown formatting, and DOI."""
    cit = CitationDTO(
        title=title,
        authors=authors,
        year=year,
        journal=journal,
        doi=doi,
    )
    entry = APA7Formatter.format_reference_entry(cit)

    assert f"({year})." in entry
    if journal:
        assert f"*{journal.strip()}*" in entry

    if doi:
        clean_doi = doi.strip()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            if clean_doi.lower().startswith(prefix):
                clean_doi = clean_doi[len(prefix) :].strip()
        assert f"https://doi.org/{clean_doi}" in entry

    if len(authors) > 20:
        assert "..." in entry
