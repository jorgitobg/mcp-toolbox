"""Integration: the real server process, driven by the official MCP client over stdio."""

import json
import sys
from typing import Any

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_toolbox import demo
from mcp_toolbox.server import build_server


def _params() -> StdioServerParameters:
    return StdioServerParameters(command=sys.executable, args=["-m", "mcp_toolbox"])


async def _call(session: ClientSession, name: str, args: dict[str, Any]) -> Any:
    res = await session.call_tool(name, args)
    return res, json.loads(res.content[0].text) if not res.isError else None  # type: ignore[union-attr]


async def test_handshake_lists_two_read_only_tools() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        init = await session.initialize()
        assert init.serverInfo.name == "mcp-toolbox"
        tools = {t.name: t for t in (await session.list_tools()).tools}
        assert set(tools) == {"search_boe", "get_boe_document"}
        assert "query" in tools["search_boe"].inputSchema["properties"]


async def test_search_and_get_roundtrip() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        _, data = await _call(
            session, "search_boe", {"query": "Ayuntamiento Subalterno", "limit": 2}
        )
        assert data["count"] == 2
        top = data["results"][0]
        assert top["id"] == "BOE-A-2026-23041"  # Torrox
        _, doc = await _call(session, "get_boe_document", {"doc_id": top["id"]})
        assert doc["paragraphs"] and doc["url"].startswith("https://www.boe.es/")


async def test_unknown_document_is_a_tool_error() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        res, _ = await _call(session, "get_boe_document", {"doc_id": "nope"})
        assert res.isError


async def test_limit_is_clamped() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        _, data = await _call(session, "search_boe", {"query": "resolución", "limit": 9999})
        assert data["count"] <= 20


async def test_in_process_server_builds() -> None:
    server = build_server()
    assert {t.name for t in await server.list_tools()} == {"search_boe", "get_boe_document"}


async def test_demo_output_is_deterministic() -> None:
    a = await demo.run()
    b = await demo.run()
    assert a == b
    assert a[0] == "tools: get_boe_document, search_boe"
    assert "BOE-A-2026-23041" in a[2]


@pytest.mark.parametrize("bad", [{}, {"query": 5}])
async def test_invalid_arguments_rejected(bad: dict[str, Any]) -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        res = await session.call_tool("search_boe", bad)
        assert res.isError
