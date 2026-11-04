"""Domain types. No I/O here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class BoeDocument:
    id: str
    title: str
    department: str
    published: date | None
    url: str
    paragraphs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SearchHit:
    doc: BoeDocument
    score: int
    snippet: str
