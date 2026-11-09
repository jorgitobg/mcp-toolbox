"""Filter a recorded open-tender-radar report (read-only, offline)."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

REPORT = Path(__file__).resolve().parent.parent / "data" / "tenders" / "triage_report.json"
VERDICTS = ("GO", "REVIEW", "NO_GO")


def _fold(text: str) -> str:
    nfd = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in nfd if not unicodedata.combining(c))


class TenderTriage:
    def __init__(self, path: Path = REPORT) -> None:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        self.summary: dict[str, Any] = data["summary"]
        self._tenders: tuple[dict[str, Any], ...] = tuple(data["tenders"])

    def all(self) -> tuple[dict[str, Any], ...]:
        return self._tenders

    def get(self, tender_id: str) -> dict[str, Any] | None:
        """Look up one tender by id; an optional ``SOURCE:`` prefix (TED, PLACSP) disambiguates."""
        source, _, ident = tender_id.rpartition(":")
        for t in self._tenders:
            if t["id"] == ident and (not source or t["source"].casefold() == source.casefold()):
                return t
        return None

    def select(self, verdict: str | None, query: str | None, limit: int) -> list[dict[str, Any]]:
        if verdict is not None and verdict.upper() not in VERDICTS:
            raise ValueError(f"verdict must be one of {', '.join(VERDICTS)}")
        words = _fold(query).split() if query else []
        out: list[dict[str, Any]] = []
        for t in self._tenders:
            if verdict is not None and t["verdict"] != verdict.upper():
                continue
            hay = _fold(f"{t['title']} {t['buyer']}")
            if all(w in hay for w in words):
                out.append(t)
        return out[:limit]
