"""Strict Vancouver / NLM citation and bibliography formatter."""

import re

from thesisforge.models import CitationDTO

# Common keywords and acronyms representing corporate or organizational authors
CORPORATE_KEYWORDS = {
    "organization",
    "organizations",
    "organisation",
    "organisations",
    "institute",
    "institutes",
    "institution",
    "institutions",
    "association",
    "associations",
    "group",
    "groups",
    "committee",
    "commission",
    "department",
    "departments",
    "dept",
    "ministry",
    "ministries",
    "university",
    "universities",
    "college",
    "colleges",
    "corporation",
    "corporations",
    "corp",
    "inc",
    "incorporated",
    "ltd",
    "limited",
    "llc",
    "gmbh",
    "center",
    "centers",
    "centre",
    "centres",
    "foundation",
    "foundations",
    "agency",
    "agencies",
    "council",
    "councils",
    "society",
    "societies",
    "academy",
    "academies",
    "laboratory",
    "laboratories",
    "lab",
    "labs",
    "team",
    "consortium",
    "initiative",
    "office",
    "health",
    "who",
    "ieee",
    "acm",
    "nasa",
    "iso",
    "nist",
    "nih",
    "cdc",
    "unesco",
    "fda",
    "unicef",
}

NAME_PARTICLES = {
    "von",
    "van",
    "de",
    "del",
    "der",
    "da",
    "di",
    "della",
    "la",
    "le",
    "dos",
    "das",
}


def _is_corporate_author(author_str: str) -> bool:
    """Determine whether author string represents an institution or corporate entity."""
    cleaned = author_str.strip()
    if not cleaned:
        return False

    if "," in cleaned:
        return False

    if cleaned.isupper() and 2 <= len(cleaned) <= 10:
        return True

    words = set(re.findall(r"\b\w+\b", cleaned.lower()))
    return bool(words & CORPORATE_KEYWORDS)


def _extract_surname(author_str: str) -> str:
    """Extract family/surname or corporate name for in-text / narrative citations."""
    cleaned = author_str.strip()
    if not cleaned:
        return "Anonymous"

    if _is_corporate_author(cleaned):
        return cleaned

    if "," in cleaned:
        return cleaned.split(",", 1)[0].strip()

    parts = cleaned.split()
    if not parts:
        return "Anonymous"
    if len(parts) >= 2 and parts[-2].lower() in NAME_PARTICLES:
        return f"{parts[-2]} {parts[-1]}"
    return parts[-1].strip()


def _parse_vancouver_author(author_str: str) -> str:
    """Parse author string into Vancouver/NLM format: surname followed by initials without punctuation (e.g. 'Smith JK')."""
    cleaned = author_str.strip()
    if not cleaned:
        return "Anonymous"

    if _is_corporate_author(cleaned):
        return cleaned

    if "," in cleaned:
        parts = [p.strip() for p in cleaned.split(",", 1)]
        family = parts[0]
        given = parts[1] if len(parts) > 1 else ""
    else:
        parts = cleaned.split()
        if len(parts) == 1:
            return parts[0]
        if len(parts) >= 2 and parts[-2].lower() in NAME_PARTICLES:
            family = f"{parts[-2]} {parts[-1]}"
            given = " ".join(parts[:-2])
        else:
            family = parts[-1]
            given = " ".join(parts[:-1])

    # Convert given name into consecutive uppercase initials without periods: "John Robert" -> "JR"
    initials_parts: list[str] = []
    tokens = re.findall(r"[A-Za-z]+", given)
    for token in tokens:
        if token:
            initials_parts.append(token[0].upper())

    if initials_parts:
        initials_str = "".join(initials_parts)
        return f"{family} {initials_str}"
    return family


def _clean_doi(doi: str | None) -> str | None:
    """Normalize DOI string by stripping URL schemes and prefixes."""
    if not doi:
        return None
    cleaned = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
    return cleaned.rstrip(".") if cleaned else None


class VancouverFormatter:
    """Formatter adhering strictly to Vancouver / ICMJE / NLM citation guidelines."""

    @classmethod
    def format_in_text(cls, number: int = 1, page: int | str | None = None) -> str:
        """Format Vancouver numerical in-text citation: (1) or (1, p. 25) or (1, pp. 25-26)."""
        if page is not None:
            page_str = str(page).strip()
            if page_str:
                prefix = "pp." if ("-" in page_str or "," in page_str) else "p."
                return f"({number}, {prefix} {page_str})"
        return f"({number})"

    @classmethod
    def format_parenthetical(
        cls,
        citation: CitationDTO | None = None,
        number: int = 1,
        page: int | str | None = None,
    ) -> str:
        """Parenthetical citation in Vancouver style, equivalent to (number)."""
        return cls.format_in_text(number=number, page=page)

    @classmethod
    def format_narrative(cls, citation: CitationDTO, number: int = 1) -> str:
        """Format narrative in-text citation in Vancouver style: Author (1) or Author et al. (1)."""
        authors = citation.authors
        if not authors:
            title_str = citation.title or "Sin título"
            lead = title_str[:30] + ("..." if len(title_str) > 30 else "")
            return f'"{lead}" ({number})'

        if len(authors) == 1:
            surname = _extract_surname(authors[0])
            return f"{surname} ({number})"
        elif len(authors) == 2:
            s1 = _extract_surname(authors[0])
            s2 = _extract_surname(authors[1])
            return f"{s1} and {s2} ({number})"
        else:
            s1 = _extract_surname(authors[0])
            return f"{s1} et al. ({number})"

    @classmethod
    def format_reference_entry(cls, citation: CitationDTO, number: int | None = None) -> str:
        """Format complete bibliography entry according to Vancouver / NLM rules.

        Format:
        1. Smith JK, Jones AB. Title of article. Journal Name. 2023. doi: 10.xxxx/yyyy.
        """
        authors = citation.authors

        # 1. Author formatting (1 to 6 authors all listed; >6 authors: first 6, et al.)
        if not authors:
            author_text = ""
        elif len(authors) <= 6:
            formatted = [_parse_vancouver_author(a) for a in authors]
            author_text = ", ".join(formatted) + "."
        else:
            first_six = [_parse_vancouver_author(a) for a in authors[:6]]
            author_text = ", ".join(first_six) + ", et al."

        # 2. Title formatting (Sentence case ending with period)
        raw_title = (citation.title or "").strip()
        title_core = raw_title.rstrip("., ")
        title_part = f"{title_core}." if title_core else ""

        # 3. Journal formatting (plain text ending with period)
        journal_part = ""
        if citation.journal:
            journal_clean = citation.journal.strip().rstrip("., ")
            journal_part = f"{journal_clean}."

        # 4. Year formatting
        year_str = f"{citation.year}." if citation.year else "n.d."

        # 5. DOI or URL formatting
        doi_clean = _clean_doi(citation.doi)
        doi_url_part = ""
        if doi_clean:
            doi_url_part = f"doi: {doi_clean}."
        elif citation.url:
            doi_url_part = f"Available from: {citation.url.strip()}."

        # Assemble elements
        elements: list[str] = []
        if author_text:
            elements.append(author_text)
        if title_part:
            elements.append(title_part)
        if journal_part:
            elements.append(journal_part)
        elements.append(year_str)
        if doi_url_part:
            elements.append(doi_url_part)

        ref_body = " ".join(elements)

        if number is not None:
            return f"{number}. {ref_body}"
        return ref_body

    @classmethod
    def sort_references(cls, citations: list[CitationDTO]) -> list[CitationDTO]:
        """Sort and deduplicate references in order of appearance."""
        seen: set[str] = set()
        result: list[CitationDTO] = []
        for cit in citations:
            key = cit.doi or cit.title or cit.id
            if key not in seen:
                seen.add(key)
                result.append(cit)
        return result
