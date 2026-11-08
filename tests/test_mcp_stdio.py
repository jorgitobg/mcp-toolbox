"""Integration: the real server process, driven by the official MCP client over stdio."""

import json
import sys
from typing import Any

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError
from pydantic import AnyUrl

from mcp_toolbox import demo
from mcp_toolbox.server import build_server


def _params() -> StdioServerParameters:
    return StdioServerParameters(command=sys.executable, args=["-m", "mcp_toolbox"])


async def _call(session: ClientSession, name: str, args: dict[str, Any]) -> Any:
    res = await session.call_tool(name, args)
    return res, json.loads(res.content[0].text) if not res.isError else None  # type: ignore[union-attr]


async def test_handshake_lists_three_read_only_tools() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        init = await session.initialize()
        assert init.serverInfo.name == "mcp-toolbox"
        tools = {t.name: t for t in (await session.list_tools()).tools}
        assert set(tools) == {"search_boe", "get_boe_document", "triage_tenders"}
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
    assert {t.name for t in await server.list_tools()} == {
        "search_boe",
        "get_boe_document",
        "triage_tenders",
    }


async def test_demo_output_is_deterministic() -> None:
    a = await demo.run()
    b = await demo.run()
    assert a == b
    assert a[0] == "tools: get_boe_document, search_boe, triage_tenders"
    assert "BOE-A-2026-23041" in a[2]


@pytest.mark.parametrize("bad", [{}, {"query": 5}])
async def test_invalid_arguments_rejected(bad: dict[str, Any]) -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        res = await session.call_tool("search_boe", bad)
        assert res.isError


async def test_triage_tenders_over_stdio() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
        assert "triage_tenders" in names
        _, data = await _call(session, "triage_tenders", {})
        assert data["summary"]["verdicts"] == {"GO": 1, "NO_GO": 7, "REVIEW": 2}
        assert data["count"] == 10
        _, go = await _call(session, "triage_tenders", {"verdict": "go"})
        assert [t["id"] for t in go["tenders"]] == ["412026"]
        assert go["tenders"][0]["criteria"]["cpv"]["outcome"] == "pass"
        _, q = await _call(session, "triage_tenders", {"query": "SERVIDORES informacion"})
        assert q["count"] >= 1 and all(t["verdict"] for t in q["tenders"])
        _, one = await _call(session, "triage_tenders", {"limit": 1})
        assert one["count"] == 1


async def test_triage_rejects_unknown_verdict() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        res, _ = await _call(session, "triage_tenders", {"verdict": "MAYBE"})
        assert res.isError


async def test_resources_list_and_read_over_stdio() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        init = await session.initialize()
        assert init.capabilities.resources is not None
        listed = (await session.list_resources()).resources
        assert [str(x.uri) for x in listed] == ["boe://index"]
        templates = (await session.list_resource_templates()).resourceTemplates
        assert [t.uriTemplate for t in templates] == ["boe://document/{doc_id}"]

        index = await session.read_resource(AnyUrl("boe://index"))
        data = json.loads(index.contents[0].text)  # type: ignore[union-attr]
        assert data["count"] == 11 == len(data["documents"])
        ids = [d["id"] for d in data["documents"]]
        assert ids == sorted(ids)

        doc = await session.read_resource(AnyUrl("boe://document/BOE-A-2026-23041"))
        body = json.loads(doc.contents[0].text)  # type: ignore[union-attr]
        assert body["id"] == "BOE-A-2026-23041" and body["paragraphs"]
        _, via_tool = await _call(session, "get_boe_document", {"doc_id": "BOE-A-2026-23041"})
        assert body == via_tool


async def test_unknown_resource_document_is_an_error() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        with pytest.raises(McpError):
            await session.read_resource(AnyUrl("boe://document/nope"))


async def test_prompt_listed_and_rendered_over_stdio() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        init = await session.initialize()
        assert init.capabilities.prompts is not None
        prompts = (await session.list_prompts()).prompts
        assert [p.name for p in prompts] == ["summarise_boe_document"]
        assert {a.name: a.required for a in prompts[0].arguments or []} == {
            "doc_id": True,
            "audience": False,
        }
        got = await session.get_prompt(
            "summarise_boe_document", {"doc_id": "BOE-A-2026-23041", "audience": "a mayor"}
        )
        text = got.messages[0].content.text  # type: ignore[union-attr]
        assert got.messages[0].role == "user"
        assert "for a mayor" in text and "Torrox" in text and "[1] " in text
        assert "https://www.boe.es/" in text


async def test_prompt_unknown_document_is_an_error() -> None:
    async with stdio_client(_params()) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        with pytest.raises(McpError):
            await session.get_prompt("summarise_boe_document", {"doc_id": "nope"})
