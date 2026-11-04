# mcp-toolbox

A small, tested [MCP](https://modelcontextprotocol.io) server that lets an AI client search and read official Spanish BOE documents. It is the start of a toolbox of narrow servers reusing the adapters of [open-tender-radar](https://github.com/jorgitobg/open-tender-radar) and [sovereign-rag](https://github.com/jorgitobg/sovereign-rag).

## Current status (v0.1)

One server, two read-only tools, stdio transport, built on the official Python SDK (`mcp>=1.12,<2`):

- `search_boe(query, limit=5)`: ranked keyword search (accent-insensitive, title matches weigh 3x) with snippets and source URLs.
- `get_boe_document(doc_id)`: metadata and paragraphs of one document; unknown ids return an MCP tool error.

Data: 11 recorded BOE documents (BOE of 2026-11-03) bundled in the package. No network, keys or LLM at runtime or in tests.

## Quickstart

Python 3.12+.

```bash
git clone https://github.com/jorgitobg/mcp-toolbox
cd mcp-toolbox
python -m venv .venv && . .venv/bin/activate
pip install -e .
mcp-toolbox-demo        # or: python -m mcp_toolbox.demo
```

Use it from an MCP client by launching `python -m mcp_toolbox` (or `mcp-toolbox`) over stdio.

Development: `pip install -e '.[dev]'`, then `ruff check . && ruff format --check . && pyright && pytest` (coverage gate 85%). Only editable installs are exercised.

## Demo output

The demo spawns the real server as a subprocess and talks to it with the official MCP client. Real output:

```text
tools: get_boe_document, search_boe
search_boe('plazas Subalterno Ayuntamiento'): 3 result(s)
  BOE-A-2026-23041 score=8 Resolución de 28 de octubre de 2026, del Ayuntamiento de Torrox (Málaga), referente a la c
  BOE-A-2026-23049 score=8 Resolución de 29 de octubre de 2026, del Ayuntamiento de Borriana/Burriana (Castellón/Cast
  BOE-A-2026-23045 score=7 Resolución de 29 de octubre de 2026, del Ayuntamiento de Tarragona, Instituto Municipal de
get_boe_document(BOE-A-2026-23041): 6 paragraphs, https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-23041```

## Layout

Hexagonal: `domain/` (models, `DocumentSource` port), `application/search.py`, `adapters/` (BOE XML parser, bundled corpus), `server.py` (MCP wiring). See `docs/spec/0001-boe-search-server.md` and `docs/adr/`.

## Limitations

- Keyword counting only: no stemming, phrases or semantics.
- Static snapshot of 11 documents; no live BOE or TED access yet.
- stdio only; no HTTP transport or auth.
- `mcp` 2.x is not supported yet (API renamed); pinned below 2.

## Licence

Apache-2.0. BOE content is reused under the Agency's reuse licence (see `src/mcp_toolbox/data/SOURCES.md`).
