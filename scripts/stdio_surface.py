"""Dump what an MCP client sees over stdio, as sorted JSON, for any installed `mcp`.

Run it with the interpreter of an environment that has this package and some `mcp`
version installed, then diff the output of two environments:

    python scripts/stdio_surface.py > surface-1x.json     # mcp 1.x environment
    python scripts/stdio_surface.py > surface-2x.json     # mcp 2.x environment (patched checkout)
    diff surface-1x.json surface-2x.json

It is a measuring tool for ADR 0004, not part of the shipped package. It reads only the
bundled offline corpora; no network.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CALLS: list[tuple[str, dict[str, Any]]] = [
    ("search_boe", {"query": "contratos"}),
    ("get_boe_document", {"doc_id": "BOE-A-2026-23041"}),
    ("triage_tenders", {"verdict": "GO"}),
    ("get_tender", {"tender_id": "PLACSP:412026"}),
    ("get_tender", {"tender_id": "nope"}),
]
RESOURCES = [
    "boe://index",
    "boe://document/BOE-A-2026-23041",
    "tenders://report",
    "tenders://report/go",
    "tenders://tender/412026",
    "tenders://tender/nope",
    "tenders://report/maybe",
]


def _attr(obj: Any, *names: str) -> Any:
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    raise AttributeError(names)


async def _read(session: ClientSession, uri: str) -> Any:
    try:
        result = await session.read_resource(uri)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001 - the error text is the measurement
        return f"ERR {type(exc).__name__}: {exc}"
    return [(c.text, _attr(c, "mimeType", "mime_type")) for c in result.contents]  # type: ignore[attr-defined]


async def surface() -> dict[str, Any]:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_toolbox"])
    out: dict[str, Any] = {}
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools
        out["tools"] = sorted(
            (
                t.name,
                t.description,
                json.dumps(_attr(t, "inputSchema", "input_schema"), sort_keys=True),
            )
            for t in tools
        )
        for name, args in CALLS:
            res = await session.call_tool(name, args)
            out[f"call:{name}:{json.dumps(args)}"] = [
                _attr(res, "isError", "is_error"),
                [c.text for c in res.content],  # type: ignore[union-attr]
            ]
        for uri in RESOURCES:
            out[f"resource:{uri}"] = await _read(session, uri)
        templates = await session.list_resource_templates()
        out["templates"] = sorted(
            _attr(t, "uriTemplate", "uri_template")
            for t in _attr(templates, "resourceTemplates", "resource_templates")
        )
        out["prompts"] = [(p.name, p.description) for p in (await session.list_prompts()).prompts]
    return out


def main() -> None:
    print(json.dumps(asyncio.run(surface()), indent=1, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
