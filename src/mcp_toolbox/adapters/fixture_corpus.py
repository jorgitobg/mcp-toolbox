"""DocumentSource backed by the BOE XML files bundled inside the package."""

from __future__ import annotations

from pathlib import Path

from mcp_toolbox.adapters.boe_xml import parse_boe
from mcp_toolbox.domain.models import BoeDocument

BUNDLED = Path(__file__).resolve().parent.parent / "data"


class DirectoryCorpus:
    def __init__(self, directory: Path = BUNDLED) -> None:
        self._docs = tuple(parse_boe(p.read_bytes()) for p in sorted(directory.glob("*.xml")))

    def all_documents(self) -> tuple[BoeDocument, ...]:
        return self._docs
