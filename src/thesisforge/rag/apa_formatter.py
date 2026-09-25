"""Strict APA 7th Edition citation and bibliography formatter."""

import re

from thesisforge.models import CitationDTO


def _parse_author_name(author_str: str) -> tuple[str, str]:
    """Parse author string into (family_name, initials/given_name)."""
    cleaned = author_str.strip()
    if not cleaned:
        return ("Anónimo", "")

    if "," in cleaned:
        parts = [p.strip() for p in cleaned.split(",", 1)]
        family = parts[0]
        given = parts[1] if len(parts) > 1 else ""
    else:
        parts = cleaned.split()
        if len(parts) == 1:
            family = parts[0]
            given = ""
        else:
            family = parts[-1]
            given = " ".join(parts[:-1])

    # Convert given name to initials if needed (e.g. "John Robert" -> "J. R.")
    initials_parts: list[str] = []
    for word in given.split():
        clean_word = re.sub(r"[^\w]", "", word)
        if clean_word:
            initials_parts.append(f"{clean_word[0].upper()}.")

    initials = " ".join(initials_parts)
    return (family, initials)


class APA7Formatter:
    """Formatter adhering strictly to American Psychological Association (APA) 7th Edition rules."""

    @classmethod
    def format_parenthetical(cls, citation: CitationDTO, page: int | str | None = None) -> str:
        """Format parenthetical in-text citation: (Author, Year) or (Author et al., Year, p. 12)."""
        authors = citation.authors
        year_str = str(citation.year) if citation.year else "s.f."

        if not authors:
            title_str = citation.title or "Sin título"
            lead = title_str[:30] + ("..." if len(title_str) > 30 else "")
            core = f'"{lead}", {year_str}'
        elif len(authors) == 1:
            family, _ = _parse_author_name(authors[0])
            core = f"{family}, {year_str}"
        elif len(authors) == 2:
            fam1, _ = _parse_author_name(authors[0])
            fam2, _ = _parse_author_name(authors[1])
            core = f"{fam1} & {fam2}, {year_str}"
        else:
            fam1, _ = _parse_author_name(authors[0])
            core = f"{fam1} et al., {year_str}"

        if page is not None:
            page_str = str(page).strip()
            if page_str:
                core = f"{core}, p. {page_str}"

        return f"({core})"

    @classmethod
    def format_narrative(cls, citation: CitationDTO, language: str = "es") -> str:
        """Format narrative in-text citation: Author (Year) or Author et al. (Year)."""
        authors = citation.authors
        year_str = str(citation.year) if citation.year else "s.f."
        and_conj = "y" if language == "es" else "and"

        if not authors:
            title_str = citation.title or "Sin título"
            lead = title_str[:30] + ("..." if len(title_str) > 30 else "")
            return f'"{lead}" ({year_str})'
        elif len(authors) == 1:
            family, _ = _parse_author_name(authors[0])
            return f"{family} ({year_str})"
        elif len(authors) == 2:
            fam1, _ = _parse_author_name(authors[0])
            fam2, _ = _parse_author_name(authors[1])
            return f"{fam1} {and_conj} {fam2} ({year_str})"
        else:
            fam1, _ = _parse_author_name(authors[0])
            return f"{fam1} et al. ({year_str})"

    @classmethod
    def format_reference_entry(cls, citation: CitationDTO) -> str:
        """Format complete bibliography entry according to APA 7th edition rules."""
        authors = citation.authors
        year_str = str(citation.year) if citation.year else "s.f."

        # 1. Author list formatting
        if not authors:
            author_text = (citation.title or "Sin título").strip()
        elif len(authors) == 1:
            fam, init = _parse_author_name(authors[0])
            author_text = f"{fam}, {init}" if init else fam
        elif len(authors) <= 20:
            formatted_authors: list[str] = []
            for a in authors:
                fam, init = _parse_author_name(a)
                formatted_authors.append(f"{fam}, {init}" if init else fam)
            author_text = ", ".join(formatted_authors[:-1]) + ", & " + formatted_authors[-1]
        else:
            # 21 or more authors: first 19 + ... + last
            formatted_authors = []
            for a in authors[:19]:
                fam, init = _parse_author_name(a)
                formatted_authors.append(f"{fam}, {init}" if init else fam)
            last_fam, last_init = _parse_author_name(authors[-1])
            last_author = f"{last_fam}, {last_init}" if last_init else last_fam
            author_text = ", ".join(formatted_authors) + ", ... " + last_author

        # 2. Title formatting (Sentence case for article titles)
        raw_title = (citation.title or "").strip()
        title_formatted = raw_title[0].upper() + raw_title[1:] if raw_title else "Sin título."
        if raw_title and not title_formatted.endswith("."):
            title_formatted += "."

        # 3. Source / Journal / Publisher formatting
        source_part = ""
        if citation.journal:
            journal_clean = citation.journal.strip()
            source_part = f" *{journal_clean}*."
        elif citation.url and not citation.doi:
            source_part = f" {citation.url}"

        # 4. DOI formatting
        doi_part = ""
        if citation.doi:
            doi_clean = citation.doi.strip()
            for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
                if doi_clean.lower().startswith(prefix):
                    doi_clean = doi_clean[len(prefix) :].strip()
            doi_part = f" https://doi.org/{doi_clean}"

        # Assemble full entry
        entry = f"{author_text} ({year_str}). {title_formatted}{source_part}{doi_part}".strip()
        return entry
