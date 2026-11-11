"""Verify an installed wheel, not the source tree.

Run with the interpreter of a virtualenv where the built wheel was installed, from a
directory outside the checkout. Fails if the package still resolves to the source tree,
if the bundled offline corpora are missing from the artifact, or if the console script
cannot serve the tools over stdio.

The failure this guards against is real: code packages fine while the bundled XML corpus
and tender report stay behind, so the wheel imports and then answers every query with
nothing.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {"search_boe", "get_boe_document", "triage_tenders", "get_tender"}


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_not_from_source() -> None:
    import mcp_toolbox

    package_dir = Path(mcp_toolbox.__file__).resolve().parent
    if package_dir.parent.name == "src" or "site-packages" not in package_dir.parts:
        _fail(f"package resolved outside site-packages: {package_dir}")
    print(f"package: {package_dir}")


def check_bundled_corpora() -> None:
    data = resources.files("mcp_toolbox") / "data"
    if not data.is_dir():
        _fail("wheel ships no data directory: the offline corpora were left behind")
    documents = sorted(p.name for p in data.iterdir() if p.name.endswith(".xml"))
    if len(documents) < 1:
        _fail("no BOE XML documents shipped in the wheel")
    report = data / "tenders" / "triage_report.json"
    if not report.is_file():
        _fail("tender triage report missing from the wheel")
    payload: object = json.loads(report.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload.get("tenders"):
        _fail("tender report shipped but empty or malformed")
    print(f"bundled documents: {len(documents)}; tender report: ok")


async def check_stdio() -> None:
    # The console script belongs to the same virtualenv as this interpreter; PATH is not
    # guaranteed to include it when the job runs from a bare shell.
    console_script = Path(sys.executable).with_name("mcp-toolbox")
    command = str(console_script) if console_script.is_file() else shutil.which("mcp-toolbox")
    if command is None:
        _fail("console script mcp-toolbox not installed")
    params = StdioServerParameters(command=command, args=[])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = {t.name for t in (await session.list_tools()).tools}
        if tools != EXPECTED_TOOLS:
            _fail(f"unexpected tools over stdio: {sorted(tools)}")
        result = await session.call_tool("get_tender", {"tender_id": "PLACSP:412026"})
        if result.isError:
            _fail("get_tender failed against the packaged corpus")
        payload: Any = json.loads(result.content[0].text)  # type: ignore[union-attr]
        if payload.get("id") != "412026":
            _fail(f"unexpected tender payload: {payload}")
        resources_list = {str(r.uri) for r in (await session.list_resources()).resources}
        if "boe://index" not in resources_list:
            _fail(f"boe://index not advertised: {sorted(resources_list)}")
    print(f"stdio: {len(tools)} tools, tender 412026 and boe://index answered")


def main() -> None:
    check_not_from_source()
    check_bundled_corpora()
    asyncio.run(check_stdio())
    print("wheel verification passed")


if __name__ == "__main__":
    main()
