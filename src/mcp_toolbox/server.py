"""MCP server (stdio) exposing two read-only BOE tools over the bundled offline corpus."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_toolbox.adapters.fixture_corpus import DirectoryCorpus
from mcp_toolbox.application.search import BoeSearch
from mcp_toolbox.domain.models import BoeDocument

MAX_LIMIT = 20


def _summary(doc: BoeDocument) -> dict[str, Any]:
    return {
        "id": doc.id,
        "title": doc.title,
        "department": doc.department,
        "published": doc.published.isoformat() if doc.published else None,
        "url": doc.url,
    }


def build_server(search: BoeSearch | None = None) -> FastMCP:
    engine = search or BoeSearch(DirectoryCorpus())
    mcp = FastMCP("mcp-toolbox", log_level="WARNING")

    @mcp.tool()
    def search_boe(query: str, limit: int = 5) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """Search the bundled BOE corpus by keywords. Title matches weigh 3x. Offline, read-only."""
        hits = engine.search(query, min(max(limit, 1), MAX_LIMIT))
        return {
            "query": query,
            "count": len(hits),
            "results": [{**_summary(h.doc), "score": h.score, "snippet": h.snippet} for h in hits],
        }

    @mcp.tool()
    def get_boe_document(doc_id: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """Return one bundled BOE document (metadata + paragraphs) by identifier."""
        doc = engine.get(doc_id)
        if doc is None:
            raise ValueError(f"unknown document id: {doc_id!r}")
        return {**_summary(doc), "paragraphs": list(doc.paragraphs)}

    return mcp


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
