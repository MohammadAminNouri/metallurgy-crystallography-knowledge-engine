"""Publication text importers for Cayron Metallurgy Engine.

The parser is deliberately conservative: it extracts structured records from copied
ResearchGate/EPFL/Scholar text exports without automated scraping.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable, List, Dict

PUB_TYPES = {"Article", "Preprint", "Presentation", "Poster", "Conference Paper", "Book", "Chapter", "Question"}
NOISE_PREFIXES = (
    "Fig.", "Figure", "Table", "SEM", "Typical", "Chemical", "SPS", "Optical", "EBSD", "Pole",
    "Lattices", "Unit cell", "Pseudocode", "Projections", "Examples", "Directional", "Hyperplanar",
    "Similarities", "Schematic", "Phase diagram", "a)", "b)", "Micrograph", "FESEM", "TEMPERATURE",
    "Full-text", "View", "Published:", "Current", "Top", "Join", "Network", "Cited", "About", "Home",
)

@dataclass
class Publication:
    title: str
    publication_type: str = ""
    date: str = ""
    year: str = ""
    venue: str = ""
    authors: str = ""
    abstract: str = ""
    source: str = "manual import"
    full_text_available: bool = False


def _clean_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line.replace("*", " ")).strip()
    line = line.replace("\u200b", "")
    return line


def _is_noise(line: str) -> bool:
    if not line or line in {"View", "Full-text available", "1", "2", "3"}:
        return True
    return any(line.startswith(p) for p in NOISE_PREFIXES)


def parse_copied_profile_text(text: str, source: str = "manual import") -> List[Dict[str, object]]:
    """Parse copied ResearchGate/EPFL/Scholar-like text into publication records.

    Works best when the copied text contains a title line followed by a publication type
    and a date line. It deduplicates by normalized title.
    """
    lines = [_clean_line(x) for x in text.splitlines() if _clean_line(x)]
    records: list[Publication] = []

    for i, line in enumerate(lines):
        if line not in PUB_TYPES:
            continue

        # find title above the type marker
        j = i - 1
        while j >= 0 and _is_noise(lines[j]):
            j -= 1
        if j < 0:
            continue
        title = lines[j]
        if title.lower() in {"publications", "questions", "about"}:
            continue

        k = i + 1
        full_text = False
        if k < len(lines) and lines[k] == "Full-text available":
            full_text = True
            k += 1

        date = lines[k] if k < len(lines) else ""
        year_match = re.search(r"(19|20)\d{2}", date)
        year = year_match.group(0) if year_match else ""

        venue = ""
        authors = ""
        abstract = ""
        a_idx = k + 1
        if k + 1 < len(lines):
            nxt = lines[k + 1]
            looks_like_venue = (
                "Cyril" not in nxt and "Cayron" not in nxt and len(nxt) < 95
                and not nxt.startswith(("The ", "We ", "A ", "An ", "In ", "To "))
                and not _is_noise(nxt)
            )
            if looks_like_venue:
                venue = nxt
                a_idx = k + 2
            if a_idx < len(lines):
                authors = lines[a_idx]

            abs_lines: list[str] = []
            q = a_idx + 1
            while q < len(lines) and lines[q] not in {"View"} and lines[q] not in PUB_TYPES and len(abs_lines) < 4:
                if not _is_noise(lines[q]):
                    abs_lines.append(lines[q])
                q += 1
            abstract = " ".join(abs_lines)[:1200]

        records.append(Publication(
            title=title,
            publication_type=line,
            date=date,
            year=year,
            venue=venue,
            authors=authors,
            abstract=abstract,
            source=source,
            full_text_available=full_text,
        ))

    seen: set[str] = set()
    deduped: list[Dict[str, object]] = []
    for rec in records:
        key = re.sub(r"\W+", "", rec.title.lower())[:180]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(asdict(rec))
    return deduped


def scholar_csv_to_records(rows: Iterable[dict], source: str = "Google Scholar CSV export") -> List[Dict[str, object]]:
    """Normalize common Scholar/BibTeX/Publish-or-Perish CSV fields.

    Expected possible columns: Title, Authors, Year, Source/Venue, Cites, DOI, URL.
    """
    normalized = []
    for row in rows:
        lower = {str(k).lower().strip(): v for k, v in row.items()}
        title = lower.get("title") or lower.get("article title") or lower.get("publication") or ""
        if not str(title).strip():
            continue
        year = str(lower.get("year") or lower.get("publication year") or "")
        normalized.append({
            "title": str(title).strip(),
            "publication_type": str(lower.get("type") or "Publication").strip(),
            "date": year,
            "year": re.search(r"(19|20)\d{2}", year).group(0) if re.search(r"(19|20)\d{2}", year) else "",
            "venue": str(lower.get("source") or lower.get("journal") or lower.get("venue") or "").strip(),
            "authors": str(lower.get("authors") or lower.get("author") or "").strip(),
            "abstract": str(lower.get("abstract") or "").strip(),
            "source": source,
            "full_text_available": False,
            "citations": str(lower.get("cites") or lower.get("citations") or "").strip(),
            "doi": str(lower.get("doi") or "").strip(),
            "url": str(lower.get("url") or lower.get("link") or "").strip(),
        })
    return normalized
