"""BibTeX (.bib) academic reference exporter with standardized citekeys and LaTeX escaping for Zotero and Overleaf."""

import re
import unicodedata
from typing import Any

from thesisforge import __version__
from thesisforge.core.time import format_iso_utc, utc_now
from thesisforge.models import AcademicSearchResultDTO, CitationDTO, ProjectStateDTO

# Common English and Spanish stopwords omitted from citekey title tokens
STOPWORDS = {
    "a",
    "an",
    "the",
    "in",
    "on",
    "of",
    "for",
    "to",
    "with",
    "and",
    "or",
    "is",
    "are",
    "at",
    "by",
    "from",
    "de",
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "unos",
    "unas",
    "en",
    "por",
    "para",
    "con",
    "y",
    "o",
    "del",
    "al",
    "sobre",
    "hacia",
}

# LaTeX special character substitutions (escaped inside BibTeX fields)
LATEX_ESCAPES = [
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def escape_latex(text: str | None) -> str:
    """Escape LaTeX special reserved characters while preserving braces."""
    if not text:
        return ""
    result = str(text).strip()
    for char, replacement in LATEX_ESCAPES:
        result = result.replace(char, replacement)
    return result


def slugify_ascii(text: str) -> str:
    """Normalize unicode characters to ASCII and strip non-alphanumeric symbols."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_bytes = normalized.encode("ascii", "ignore")
    ascii_text = ascii_bytes.decode("utf-8").lower()
    return re.sub(r"[^a-z0-9]", "", ascii_text)


def extract_first_author_lastname(authors: list[str]) -> str:
    """Extract and normalize the last name of the primary author."""
    if not authors or not authors[0].strip():
        return "thesisforge"

    primary = authors[0].strip()
    # Format: "Lastname, Firstname"
    if "," in primary:
        lastname = primary.split(",")[0].strip()
    else:
        # Format: "Firstname Middle Lastname"
        tokens = primary.split()
        lastname = tokens[-1] if tokens else "thesisforge"

    slug = slugify_ascii(lastname)
    return slug if slug else "thesisforge"


def extract_title_keyword(title: str | None) -> str:
    """Extract first significant alphanumeric keyword from title, skipping stopwords."""
    if not title or not title.strip():
        return "doc"

    # Tokenize words
    words = re.findall(r"\b[A-Za-z0-9]+\b", title)
    for word in words:
        clean_w = word.lower().strip()
        if clean_w not in STOPWORDS and len(clean_w) >= 3 and not clean_w.isdigit():
            slug = slugify_ascii(clean_w)
            if slug:
                return slug

    # Fallback to first available token
    for word in words:
        slug = slugify_ascii(word)
        if slug:
            return slug

    return "doc"


def generate_citekey(
    authors: list[str],
    year: int | None,
    title: str | None,
    existing_keys: set[str],
) -> str:
    """Generate standardized citekey (e.g. 'vaswani2017attention') with collision resolution."""
    author_slug = extract_first_author_lastname(authors)
    year_slug = str(year) if year and 1800 <= year <= 2100 else "nodate"
    title_slug = extract_title_keyword(title)

    base_key = f"{author_slug}{year_slug}{title_slug}"
    if base_key not in existing_keys:
        existing_keys.add(base_key)
        return base_key

    # Collision resolution: append 'a', 'b', ..., 'z', 'aa', 'ab'...
    suffix_index = 0
    while True:
        suffix = ""
        n = suffix_index
        while True:
            suffix = chr(ord("a") + (n % 26)) + suffix
            n = n // 26 - 1
            if n < 0:
                break
        candidate = f"{base_key}{suffix}"
        if candidate not in existing_keys:
            existing_keys.add(candidate)
            return candidate
        suffix_index += 1


def format_authors_bibtex(authors: list[str]) -> str:
    """Format authors list joined by ' and ' with LaTeX character escaping."""
    if not authors:
        return "Unknown"
    formatted = [escape_latex(a.strip()) for a in authors if a.strip()]
    return " and ".join(formatted) if formatted else "Unknown"


def determine_entry_type(
    venue: str | None,
    source: str | None,
    doi: str | None,
) -> str:
    """Infer the most appropriate BibTeX entry type from venue, source, and DOI metadata."""
    venue_lower = (venue or "").lower()
    source_lower = (source or "").lower()

    if any(
        kw in venue_lower
        for kw in (
            "conference",
            "proceedings",
            "symposium",
            "workshop",
            "ieee",
            "acm",
            "cvpr",
            "neurips",
            "icml",
            "iclr",
            "acl",
            "emnlp",
            "naacl",
            "kdd",
            "aaai",
            "ijcai",
        )
    ):
        return "inproceedings"

    if any(kw in venue_lower for kw in ("book", "springer", "wiley", "routledge", "editorial")):
        return "book"

    if source_lower == "arxiv" or "arxiv" in venue_lower:
        return "misc"

    if venue_lower or doi:
        return "article"

    return "misc"


class BibTeXExporter:
    """Exporter for generating standardized, validated BibTeX (.bib) files."""

    def __init__(self) -> None:
        pass

    def export_citation(
        self,
        citation: CitationDTO | AcademicSearchResultDTO | dict[str, Any],
        existing_keys: set[str] | None = None,
    ) -> str:
        """Format a single citation or search result into a standardized BibTeX entry."""
        if existing_keys is None:
            existing_keys = set()

        if isinstance(citation, CitationDTO):
            title = citation.title or "Sin título"
            authors = citation.authors
            year = citation.year
            venue = citation.journal
            doi = citation.doi
            url = citation.url
            abstract = citation.abstract
            source = citation.source
        elif isinstance(citation, AcademicSearchResultDTO):
            title = citation.title or "Sin título"
            authors = citation.authors
            year = citation.year
            venue = citation.venue
            doi = citation.doi
            url = citation.url
            abstract = citation.abstract
            source = citation.source
        else:
            title = str(citation.get("title") or "Sin título")
            raw_authors = citation.get("authors") or []
            authors = (
                [str(a) for a in raw_authors]
                if isinstance(raw_authors, list)
                else [str(raw_authors)]
            )
            year = citation.get("year")
            venue = citation.get("journal") or citation.get("venue")
            doi = citation.get("doi")
            url = citation.get("url")
            abstract = citation.get("abstract")
            source = str(citation.get("source") or "manual")

        citekey = generate_citekey(authors, year, title, existing_keys)
        entry_type = determine_entry_type(venue, source, doi)

        lines: list[str] = [f"@{entry_type}{{{citekey},"]

        # Title: wrapped in double braces to preserve casing
        escaped_title = escape_latex(title)
        lines.append(f"  title = {{{{{escaped_title}}}}},")

        # Authors
        authors_bib = format_authors_bibtex(authors)
        lines.append(f"  author = {{{authors_bib}}},")

        # Year
        if year:
            lines.append(f"  year = {{{year}}},")

        # Venue / Journal / Booktitle
        if venue:
            escaped_venue = escape_latex(venue)
            if entry_type == "inproceedings":
                lines.append(f"  booktitle = {{{escaped_venue}}},")
            elif entry_type == "book":
                lines.append(f"  publisher = {{{escaped_venue}}},")
            else:
                lines.append(f"  journal = {{{escaped_venue}}},")

        # DOI
        if doi:
            clean_doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
            lines.append(f"  doi = {{{clean_doi}}},")

        # URL
        if url:
            lines.append(f"  url = {{{url.strip()}}},")

        # ArXiv specific metadata
        if (
            (source == "arxiv" or "arxiv" in (venue or "").lower())
            and url
            and "arxiv.org/abs/" in url
        ):
            eprint_id = url.split("arxiv.org/abs/")[-1].strip()
            lines.append(f"  eprint = {{{eprint_id}}},")
            lines.append("  archivePrefix = {arXiv},")

        # Abstract (optional, trimmed)
        if abstract:
            escaped_abstract = escape_latex(abstract.strip())
            lines.append(f"  abstract = {{{escaped_abstract}}},")

        lines.append("}")
        return "\n".join(lines)

    def export_citations(
        self,
        citations: list[CitationDTO] | list[AcademicSearchResultDTO] | list[dict[str, Any]],
    ) -> str:
        """Export multiple citations as a unified .bib bibliography file."""
        if not citations:
            return "% ThesisForge BibTeX Export — 0 references found\n"

        existing_keys: set[str] = set()
        entries: list[str] = []

        now_str = format_iso_utc(utc_now())
        header = (
            f"% ==========================================================================\n"
            f"% ThesisForge v{__version__} — BibTeX Export (Zotero, Overleaf, Mendeley)\n"
            f"% Generated: {now_str}\n"
            f"% Total References: {len(citations)}\n"
            f"% ==========================================================================\n\n"
        )

        for cit in citations:
            entries.append(self.export_citation(cit, existing_keys))

        return header + "\n\n".join(entries) + "\n"

    def export_project_bibliography(self, project: ProjectStateDTO) -> str:
        """Export all validated project citations to a standardized BibTeX string."""
        citations = project.validated_citations
        if not citations:
            return (
                f"% ThesisForge BibTeX Export — Project '{project.title}' (ID: {project.id})\n"
                f"% No citations currently registered in project.\n"
            )

        existing_keys: set[str] = set()
        entries: list[str] = []

        now_str = format_iso_utc(utc_now())
        header = (
            f"% ==========================================================================\n"
            f"% ThesisForge v{__version__} — BibTeX Project Bibliography\n"
            f"% Project ID:   {project.id}\n"
            f"% Project Title: {escape_latex(project.title or 'Sin título')}\n"
            f"% Generated:    {now_str}\n"
            f"% Total Entries: {len(citations)}\n"
            f"% Compatible with: Overleaf, Zotero, Mendeley, JabRef, TeX Live\n"
            f"% ==========================================================================\n\n"
        )

        for cit in citations:
            entries.append(self.export_citation(cit, existing_keys))

        return header + "\n\n".join(entries) + "\n"
