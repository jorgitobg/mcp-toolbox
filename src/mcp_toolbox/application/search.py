"""Keyword search over BOE documents: accent-insensitive term counting, no ML."""

from __future__ import annotations

import re
import unicodedata

from mcp_toolbox.domain.models import BoeDocument, SearchHit
from mcp_toolbox.domain.ports import DocumentSource

_TOKEN = re.compile(r"[a-z0-9]{3,}")
_STOP = frozenset(
    [
        "los",
        "las",
        "del",
        "que",
        "con",
        "por",
        "una",
        "para",
        "como",
        "más",
        "sus",
        "este",
        "esta",
        "son",
        "han",
    ]
)
TITLE_WEIGHT = 3
SNIPPET_LEN = 240


def fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(fold(text)) if t not in _STOP]


def _snippet(doc: BoeDocument, terms: set[str]) -> str:
    for para in doc.paragraphs:
        if terms & set(tokens(para)):
            return para[:SNIPPET_LEN]
    return (doc.paragraphs[0] if doc.paragraphs else doc.title)[:SNIPPET_LEN]


class BoeSearch:
    def __init__(self, source: DocumentSource) -> None:
        self._docs = source.all_documents()

    def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        terms = set(tokens(query))
        if not terms or limit < 1:
            return []
        hits: list[SearchHit] = []
        for doc in self._docs:
            title_toks = tokens(doc.title)
            body_toks = tokens(" ".join(doc.paragraphs))
            score = sum(TITLE_WEIGHT * title_toks.count(t) + body_toks.count(t) for t in terms)
            if score:
                hits.append(SearchHit(doc, score, _snippet(doc, terms)))
        hits.sort(key=lambda h: (-h.score, h.doc.id))
        return hits[:limit]

    def get(self, doc_id: str) -> BoeDocument | None:
        return next((d for d in self._docs if d.id == doc_id), None)

    def all(self) -> tuple[BoeDocument, ...]:
        """Every bundled document, ordered by id."""
        return tuple(sorted(self._docs, key=lambda d: d.id))
