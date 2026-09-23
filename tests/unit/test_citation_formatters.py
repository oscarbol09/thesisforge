"""Comprehensive unit and property tests for IEEE and Vancouver citation formatters."""

from hypothesis import given
from hypothesis import strategies as st

from thesisforge.models import CitationDTO
from thesisforge.rag.ieee_formatter import IEEEFormatter, _is_corporate_author, _parse_ieee_author
from thesisforge.rag.vancouver_formatter import (
    VancouverFormatter,
    _parse_vancouver_author,
)

# ---------------------------------------------------------------------------
# Unit Tests: Author Parsing & Corporate Author Detection
# ---------------------------------------------------------------------------


def test_corporate_author_detection() -> None:
    """Verify institutions, agencies, and uppercase acronyms are identified as corporate."""
    assert _is_corporate_author("World Health Organization") is True
    assert _is_corporate_author("IEEE") is True
    assert _is_corporate_author("National Institutes of Health") is True
    assert _is_corporate_author("Department of Computer Science") is True
    assert _is_corporate_author("NASA") is True
    assert _is_corporate_author("Alan Turing") is False
    assert _is_corporate_author("Turing, Alan") is False
    assert _is_corporate_author("") is False


def test_parse_ieee_author_individual() -> None:
    """Verify IEEE individual author parsing produces 'Initials Surname'."""
    assert _parse_ieee_author("Alan Turing") == "A. Turing"
    assert _parse_ieee_author("Turing, Alan") == "A. Turing"
    assert _parse_ieee_author("John Ronald Reuel Tolkien") == "J. R. R. Tolkien"
    assert _parse_ieee_author("J. K. Rowling") == "J. K. Rowling"
    assert _parse_ieee_author("Claude Shannon") == "C. Shannon"
    assert _parse_ieee_author("SingleName") == "SingleName"


def test_parse_ieee_author_corporate() -> None:
    """Verify corporate authors preserve their verbatim identity in IEEE."""
    assert _parse_ieee_author("World Health Organization") == "World Health Organization"
    assert _parse_ieee_author("IEEE") == "IEEE"


def test_parse_vancouver_author_individual() -> None:
    """Verify Vancouver author parsing produces 'Surname Initials' without punctuation."""
    assert _parse_vancouver_author("Alan Turing") == "Turing A"
    assert _parse_vancouver_author("Turing, Alan") == "Turing A"
    assert _parse_vancouver_author("John Ronald Reuel Tolkien") == "Tolkien JRR"
    assert _parse_vancouver_author("J. K. Rowling") == "Rowling JK"
    assert _parse_vancouver_author("Claude Shannon") == "Shannon C"


def test_parse_vancouver_author_corporate() -> None:
    """Verify corporate authors preserve their verbatim identity in Vancouver."""
    assert _parse_vancouver_author("World Health Organization") == "World Health Organization"
    assert _parse_vancouver_author("NASA") == "NASA"


# ---------------------------------------------------------------------------
# Unit Tests: IEEE Formatter
# ---------------------------------------------------------------------------


def test_ieee_in_text_formatting() -> None:
    """Verify IEEE in-text numerical citations with and without pages."""
    assert IEEEFormatter.format_in_text(1) == "[1]"
    assert IEEEFormatter.format_in_text(42) == "[42]"
    assert IEEEFormatter.format_in_text(1, page=15) == "[1, p. 15]"
    assert IEEEFormatter.format_in_text(2, page="15-18") == "[2, pp. 15-18]"
    assert IEEEFormatter.format_parenthetical(number=3, page="20, 25") == "[3, pp. 20, 25]"


def test_ieee_narrative_formatting() -> None:
    """Verify IEEE narrative citations across author counts."""
    # 1 author
    c1 = CitationDTO(title="Computing Machinery", authors=["Alan Turing"], year=1950)
    assert IEEEFormatter.format_narrative(c1, number=1) == "Turing [1]"

    # 2 authors
    c2 = CitationDTO(
        title="Communication Theory",
        authors=["Alan Turing", "Claude Shannon"],
        year=1948,
    )
    assert IEEEFormatter.format_narrative(c2, number=2) == "Turing and Shannon [2]"

    # 3+ authors
    c3 = CitationDTO(
        title="Foundations",
        authors=["Alan Turing", "Claude Shannon", "John von Neumann"],
        year=1952,
    )
    assert IEEEFormatter.format_narrative(c3, number=3) == "Turing et al. [3]"

    # Corporate author
    c_corp = CitationDTO(
        title="Health Report",
        authors=["World Health Organization"],
        year=2020,
    )
    assert IEEEFormatter.format_narrative(c_corp, number=4) == "World Health Organization [4]"

    # No authors fallback
    c_none = CitationDTO(title="Anonymous Scientific Note", authors=[], year=2021)
    assert IEEEFormatter.format_narrative(c_none, number=5) == '"Anonymous Scientific Note" [5]'


def test_ieee_reference_entry_author_rules() -> None:
    """Verify IEEE reference entry author lists (1, 2, 3-6, >6 authors)."""
    # 1 author
    c1 = CitationDTO(
        title="Mathematical Analysis",
        authors=["Alan Turing"],
        year=1936,
        journal="Mind",
    )
    ref1 = IEEEFormatter.format_reference_entry(c1, number=1)
    assert ref1.startswith('[1] A. Turing, "Mathematical Analysis," *Mind*, 1936.')

    # 2 authors
    c2 = CitationDTO(
        title="Information Theory",
        authors=["Alan Turing", "Claude Shannon"],
        year=1948,
        journal="Bell Labs Technical Journal",
    )
    ref2 = IEEEFormatter.format_reference_entry(c2, number=2)
    assert ref2.startswith(
        '[2] A. Turing and C. Shannon, "Information Theory," *Bell Labs Technical Journal*, 1948.'
    )

    # 3 to 6 authors: all listed with oxford comma
    c4 = CitationDTO(
        title="Cybernetics",
        authors=["Alan Turing", "Claude Shannon", "John von Neumann", "Norbert Wiener"],
        year=1955,
        journal="IEEE Trans",
    )
    ref4 = IEEEFormatter.format_reference_entry(c4, number=4)
    assert (
        '[4] A. Turing, C. Shannon, J. von Neumann, and N. Wiener, "Cybernetics," *IEEE Trans*, 1955.'
        in ref4
    )

    # > 6 authors: first author et al.
    seven_authors = [f"Author {i}" for i in range(1, 8)]
    c7 = CitationDTO(
        title="Large Scale Systems",
        authors=seven_authors,
        year=2023,
        journal="Nature",
    )
    ref7 = IEEEFormatter.format_reference_entry(c7, number=7)
    assert '[7] A. 1 et al., "Large Scale Systems," *Nature*, 2023.' in ref7


def test_ieee_reference_entry_doi_and_url() -> None:
    """Verify IEEE reference formatting for DOI and fallback URL."""
    c_doi = CitationDTO(
        title="Quantum Teleportation",
        authors=["Charles Bennett"],
        year=1993,
        journal="Phys. Rev. Lett.",
        doi="https://doi.org/10.1103/PhysRevLett.70.1895",
    )
    ref_doi = IEEEFormatter.format_reference_entry(c_doi, number=1)
    assert "doi: 10.1103/PhysRevLett.70.1895." in ref_doi

    # URL when DOI is absent
    c_url = CitationDTO(
        title="Web Architecture",
        authors=["Tim Berners-Lee"],
        year=1990,
        url="https://www.w3.org/History.html",
    )
    ref_url = IEEEFormatter.format_reference_entry(c_url, number=2)
    assert "[Online]. Available: https://www.w3.org/History.html." in ref_url


def test_ieee_reference_without_number() -> None:
    """Verify IEEE reference entry when number is None."""
    c = CitationDTO(
        title="Computability",
        authors=["Alan Turing"],
        year=1937,
    )
    ref = IEEEFormatter.format_reference_entry(c)
    assert not ref.startswith("[")
    assert ref.startswith('A. Turing, "Computability," 1937.')


# ---------------------------------------------------------------------------
# Unit Tests: Vancouver Formatter
# ---------------------------------------------------------------------------


def test_vancouver_in_text_formatting() -> None:
    """Verify Vancouver in-text numerical citations with and without pages."""
    assert VancouverFormatter.format_in_text(1) == "(1)"
    assert VancouverFormatter.format_in_text(99) == "(99)"
    assert VancouverFormatter.format_in_text(1, page=12) == "(1, p. 12)"
    assert VancouverFormatter.format_in_text(2, page="12-14") == "(2, pp. 12-14)"
    assert VancouverFormatter.format_parenthetical(number=5, page="40, 42") == "(5, pp. 40, 42)"


def test_vancouver_narrative_formatting() -> None:
    """Verify Vancouver narrative citations across author counts."""
    c1 = CitationDTO(title="Genomics Study", authors=["Rosalind Franklin"], year=1953)
    assert VancouverFormatter.format_narrative(c1, number=1) == "Franklin (1)"

    c2 = CitationDTO(
        title="DNA Structure",
        authors=["James Watson", "Francis Crick"],
        year=1953,
    )
    assert VancouverFormatter.format_narrative(c2, number=2) == "Watson and Crick (2)"

    c3 = CitationDTO(
        title="Molecular Biology",
        authors=["James Watson", "Francis Crick", "Maurice Wilkins"],
        year=1953,
    )
    assert VancouverFormatter.format_narrative(c3, number=3) == "Watson et al. (3)"

    c_corp = CitationDTO(
        title="Vaccine Advisory",
        authors=["World Health Organization"],
        year=2021,
    )
    assert VancouverFormatter.format_narrative(c_corp, number=4) == "World Health Organization (4)"


def test_vancouver_reference_entry_author_rules() -> None:
    """Verify Vancouver reference entry author rules (1-6 authors all listed, >6: first 6, et al.)."""
    # 2 authors
    c2 = CitationDTO(
        title="Molecular structure of nucleic acids",
        authors=["James Watson", "Francis Crick"],
        year=1953,
        journal="Nature",
    )
    ref2 = VancouverFormatter.format_reference_entry(c2, number=1)
    assert ref2 == "1. Watson J, Crick F. Molecular structure of nucleic acids. Nature. 1953."

    # 6 authors: all listed
    six_authors = [
        "James Watson",
        "Francis Crick",
        "Maurice Wilkins",
        "Rosalind Franklin",
        "Linus Pauling",
        "Max Perutz",
    ]
    c6 = CitationDTO(
        title="X-ray crystallography",
        authors=six_authors,
        year=1954,
        journal="Science",
    )
    ref6 = VancouverFormatter.format_reference_entry(c6, number=2)
    assert (
        "Watson J, Crick F, Wilkins M, Franklin R, Pauling L, Perutz M. X-ray crystallography. Science. 1954."
        in ref6
    )

    # > 6 authors (e.g. 7 authors): first 6 + , et al.
    seven_authors = six_authors + ["John Kendrew"]
    c7 = CitationDTO(
        title="Protein structures",
        authors=seven_authors,
        year=1958,
        journal="Nature",
    )
    ref7 = VancouverFormatter.format_reference_entry(c7, number=3)
    assert (
        "Watson J, Crick F, Wilkins M, Franklin R, Pauling L, Perutz M, et al. Protein structures. Nature. 1958."
        in ref7
    )


def test_vancouver_reference_entry_doi_and_url() -> None:
    """Verify Vancouver reference formatting for DOI and fallback URL."""
    c_doi = CitationDTO(
        title="Clinical Trial of Drug X",
        authors=["Jane Smith", "Bob Jones"],
        year=2020,
        journal="The Lancet",
        doi="10.1016/S0140-6736(20)30183-5",
    )
    ref_doi = VancouverFormatter.format_reference_entry(c_doi, number=1)
    assert "doi: 10.1016/S0140-6736(20)30183-5." in ref_doi

    # Fallback to URL
    c_url = CitationDTO(
        title="Global Burden of Disease",
        authors=["World Health Organization"],
        year=2022,
        url="https://who.int/data/gho",
    )
    ref_url = VancouverFormatter.format_reference_entry(c_url, number=2)
    assert "Available from: https://who.int/data/gho." in ref_url


def test_vancouver_reference_without_number() -> None:
    """Verify Vancouver reference entry when number is None."""
    c = CitationDTO(
        title="Epidemiological Study",
        authors=["Jane Smith"],
        year=2022,
    )
    ref = VancouverFormatter.format_reference_entry(c)
    assert not ref.startswith("1.")
    assert ref.startswith("Smith J. Epidemiological Study. 2022.")


# ---------------------------------------------------------------------------
# Unit Tests: Reference Sorting & Deduplication
# ---------------------------------------------------------------------------


def test_reference_sorting_order_of_appearance_and_deduplication() -> None:
    """Verify sort_references preserves order of appearance and deduplicates by DOI/ID/title."""
    c1 = CitationDTO(id="id1", title="Paper One", authors=["A"], year=2020, doi="10.1/one")
    c2 = CitationDTO(id="id2", title="Paper Two", authors=["B"], year=2021, doi="10.1/two")
    c1_dup = CitationDTO(
        id="id3", title="Paper One (Dup)", authors=["A"], year=2020, doi="10.1/one"
    )
    c3 = CitationDTO(id="id4", title="Paper Three", authors=["C"], year=2022)

    citations = [c1, c2, c1_dup, c3]

    ieee_sorted = IEEEFormatter.sort_references(citations)
    assert len(ieee_sorted) == 3
    assert [c.id for c in ieee_sorted] == ["id1", "id2", "id4"]

    vancouver_sorted = VancouverFormatter.sort_references(citations)
    assert len(vancouver_sorted) == 3
    assert [c.id for c in vancouver_sorted] == ["id1", "id2", "id4"]


# ---------------------------------------------------------------------------
# Property-Based Invariant Tests (Hypothesis)
# ---------------------------------------------------------------------------

author_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll"), whitelist_characters=" -'"),
    min_size=2,
    max_size=30,
).filter(lambda s: len(s.strip()) >= 2)

authors_list = st.lists(author_strategy, min_size=1, max_size=20)
title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" ,:;?-"),
    min_size=3,
    max_size=100,
).filter(lambda s: len(s.strip()) >= 3)
year_strategy = st.integers(min_value=1900, max_value=2050)
doi_strategy = st.from_regex(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", fullmatch=True)


@given(
    number=st.integers(min_value=1, max_value=1000),
    page=st.one_of(st.none(), st.integers(min_value=1, max_value=500)),
)
def test_property_ieee_in_text_invariants(number: int, page: int | None) -> None:
    """IEEE in-text citations must always be enclosed in square brackets."""
    formatted = IEEEFormatter.format_in_text(number=number, page=page)
    assert formatted.startswith("[")
    assert formatted.endswith("]")
    assert str(number) in formatted
    if page is not None:
        assert f"p. {page}" in formatted


@given(
    number=st.integers(min_value=1, max_value=1000),
    page=st.one_of(st.none(), st.integers(min_value=1, max_value=500)),
)
def test_property_vancouver_in_text_invariants(number: int, page: int | None) -> None:
    """Vancouver in-text citations must always be enclosed in parentheses."""
    formatted = VancouverFormatter.format_in_text(number=number, page=page)
    assert formatted.startswith("(")
    assert formatted.endswith(")")
    assert str(number) in formatted
    if page is not None:
        assert f"p. {page}" in formatted


@given(
    authors=authors_list,
    title=title_strategy,
    year=year_strategy,
    number=st.integers(min_value=1, max_value=500),
    doi=st.one_of(st.none(), doi_strategy),
)
def test_property_ieee_reference_entry_invariants(
    authors: list[str], title: str, year: int, number: int, doi: str | None
) -> None:
    """IEEE reference entries must contain number prefix, year, and correct author truncation."""
    cit = CitationDTO(title=title, authors=authors, year=year, doi=doi)
    entry = IEEEFormatter.format_reference_entry(cit, number=number)

    assert entry.startswith(f"[{number}] ")
    assert str(year) in entry
    if len(authors) > 6:
        assert "et al." in entry


@given(
    authors=authors_list,
    title=title_strategy,
    year=year_strategy,
    number=st.integers(min_value=1, max_value=500),
    doi=st.one_of(st.none(), doi_strategy),
)
def test_property_vancouver_reference_entry_invariants(
    authors: list[str], title: str, year: int, number: int, doi: str | None
) -> None:
    """Vancouver reference entries must contain number prefix, year, and correct author truncation."""
    cit = CitationDTO(title=title, authors=authors, year=year, doi=doi)
    entry = VancouverFormatter.format_reference_entry(cit, number=number)

    assert entry.startswith(f"{number}. ")
    assert str(year) in entry
    if len(authors) > 6:
        assert ", et al." in entry
