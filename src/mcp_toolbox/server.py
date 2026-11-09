"""MCP server (stdio) exposing two read-only BOE tools over the bundled offline corpus."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_toolbox.adapters.fixture_corpus import DirectoryCorpus
from mcp_toolbox.application.search import BoeSearch
from mcp_toolbox.application.triage import TenderTriage
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


def build_server(search: BoeSearch | None = None, triage: TenderTriage | None = None) -> FastMCP:
    engine = search or BoeSearch(DirectoryCorpus())
    tenders = triage or TenderTriage()
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

    @mcp.tool()
    def triage_tenders(  # pyright: ignore[reportUnusedFunction]
        verdict: str | None = None, query: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        """List recorded TED/PLACSP tenders screened against a fictional profile.

        Rule-based GO / REVIEW / NO_GO with per-criterion evidence (open-tender-radar report,
        recorded 2026-11-04). Optional verdict filter and keyword query. Offline, read-only.
        """
        rows = tenders.select(verdict, query, min(max(limit, 1), MAX_LIMIT))
        return {"summary": tenders.summary, "count": len(rows), "tenders": rows}

    @mcp.resource("boe://index", mime_type="application/json")
    def boe_index() -> str:  # pyright: ignore[reportUnusedFunction]
        """Index of every bundled BOE document (id, title, department, date, URL)."""
        docs = [_summary(d) for d in engine.all()]
        return json.dumps({"count": len(docs), "documents": docs}, ensure_ascii=False)

    @mcp.resource("boe://document/{doc_id}", mime_type="application/json")
    def boe_document(doc_id: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """One bundled BOE document (metadata + paragraphs), readable without a tool call."""
        doc = engine.get(doc_id)
        if doc is None:
            raise ValueError(f"unknown document id: {doc_id!r}")
        return json.dumps({**_summary(doc), "paragraphs": list(doc.paragraphs)}, ensure_ascii=False)

    @mcp.resource("tenders://report", mime_type="application/json")
    def tenders_report() -> str:  # pyright: ignore[reportUnusedFunction]
        """Whole recorded tender triage report (same payload as triage_tenders without filters)."""
        rows = tenders.select(None, None, len(tenders.all()))
        return json.dumps(
            {"summary": tenders.summary, "count": len(rows), "tenders": rows}, ensure_ascii=False
        )

    @mcp.resource("tenders://report/{verdict}", mime_type="application/json")
    def tenders_by_verdict(verdict: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Recorded tenders with one verdict (GO, REVIEW or NO_GO)."""
        rows = tenders.select(verdict, None, len(tenders.all()))
        return json.dumps(
            {"summary": tenders.summary, "count": len(rows), "tenders": rows}, ensure_ascii=False
        )

    @mcp.prompt(title="Summarise a BOE document")
    def summarise_boe_document(doc_id: str, audience: str = "a non-lawyer") -> str:  # pyright: ignore[reportUnusedFunction]
        """Prompt template: summarise one bundled BOE document for a given audience."""
        doc = engine.get(doc_id)
        if doc is None:
            raise ValueError(f"unknown document id: {doc_id!r}")
        body = "\n\n".join(f"[{i}] {p}" for i, p in enumerate(doc.paragraphs, 1))
        return (
            f"Summarise the official BOE document below for {audience}.\n"
            "Rules: use only the text provided, cite paragraph numbers like [2], "
            "and say explicitly when the text does not answer something.\n"
            "Structure: one-sentence gist, key facts (who, what, dates, deadlines), "
            "open questions.\n\n"
            f"Title: {doc.title}\nDepartment: {doc.department}\nSource: {doc.url}\n\n{body}"
        )

    return mcp


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
