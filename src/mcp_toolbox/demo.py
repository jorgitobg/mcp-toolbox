"""Offline demo: spawn the real server over stdio and call it with the official MCP client."""

from __future__ import annotations

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

QUERY = "plazas Subalterno Ayuntamiento"


async def run(query: str = QUERY) -> list[str]:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_toolbox"])
    lines: list[str] = []
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        lines.append("tools: " + ", ".join(sorted(t.name for t in tools.tools)))
        res = await session.call_tool("search_boe", {"query": query, "limit": 3})
        data = json.loads(res.content[0].text)  # type: ignore[union-attr]
        lines.append(f"search_boe({query!r}): {data['count']} result(s)")
        for r in data["results"]:
            lines.append(f"  {r['id']} score={r['score']} {r['title'][:90]}")
        if data["results"]:
            top = data["results"][0]["id"]
            doc = await session.call_tool("get_boe_document", {"doc_id": top})
            d = json.loads(doc.content[0].text)  # type: ignore[union-attr]
            lines.append(f"get_boe_document({top}): {len(d['paragraphs'])} paragraphs, {d['url']}")
        tri = await session.call_tool("triage_tenders", {"verdict": "GO"})
        t = json.loads(tri.content[0].text)  # type: ignore[union-attr]
        lines.append(
            f"triage_tenders(verdict='GO'): {t['count']} of {t['summary']['matched']} matched"
        )
        for row in t["tenders"]:
            lines.append(f"  [{row['verdict']}] {row['source']}:{row['id']} {row['title'][:60]}")
            lines.extend(
                f"    {k:<9} {v['outcome']:<7} {v['evidence']}" for k, v in row["criteria"].items()
            )
    return lines


def main() -> None:
    print("\n".join(asyncio.run(run())))


if __name__ == "__main__":
    main()
