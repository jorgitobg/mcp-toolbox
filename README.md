# mcp-toolbox

A small, tested [MCP](https://modelcontextprotocol.io) server that lets an AI client search and read official Spanish BOE documents. It is the start of a toolbox of narrow servers reusing the adapters of [open-tender-radar](https://github.com/jorgitobg/open-tender-radar) and [sovereign-rag](https://github.com/jorgitobg/sovereign-rag).

## Current status (v0.1)

One server, three read-only tools and two resources, stdio transport, built on the official Python SDK (`mcp>=1.12,<2`):

- `search_boe(query, limit=5)`: ranked keyword search (accent-insensitive, title matches weigh 3x) with snippets and source URLs.
- `get_boe_document(doc_id)`: metadata and paragraphs of one document; unknown ids return an MCP tool error.
- `triage_tenders(verdict=None, query=None, limit=10)`: lists the recorded [open-tender-radar](https://github.com/jorgitobg/open-tender-radar) report (10 public TED/PLACSP tenders screened against a fictional profile on 2026-11-04) with GO / REVIEW / NO_GO and per-criterion evidence. Rule-based screening, not bid advice; evidence like "days left" is frozen at the recording date. Provenance in `src/mcp_toolbox/data/tenders/SOURCES.md`.

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

### Configure a desktop MCP client

Most desktop clients read a JSON file with an `mcpServers` map (the file location depends on the client). Point `command` at the Python of the virtualenv where you ran `pip install -e .` (use an absolute path):

```json
{
  "mcpServers": {
    "mcp-toolbox": {
      "command": "/absolute/path/to/mcp-toolbox/.venv/bin/python",
      "args": ["-m", "mcp_toolbox"]
    }
  }
}
```

Besides the three tools, the server exposes two read-only **resources** that a client can attach to a conversation without a tool call: `boe://index` (all bundled documents) and `boe://document/{doc_id}` (one document, same payload as `get_boe_document`). This snippet follows the common client convention and was not tested against a specific desktop client here; the server itself is exercised by the test-suite with the official Python MCP client over stdio.

Development: `pip install -e '.[dev]'`, then `ruff check . && ruff format --check . && pyright && pytest` (coverage gate 85%). Only editable installs are exercised.

## Demo output

The demo spawns the real server as a subprocess and talks to it with the official MCP client. Real output:

```text
tools: get_boe_document, search_boe
search_boe('plazas Subalterno Ayuntamiento'): 3 result(s)
  BOE-A-2026-23041 score=8 Resolución de 28 de octubre de 2026, del Ayuntamiento de Torrox (Málaga), referente a la c
  BOE-A-2026-23049 score=8 Resolución de 29 de octubre de 2026, del Ayuntamiento de Borriana/Burriana (Castellón/Cast
  BOE-A-2026-23045 score=7 Resolución de 29 de octubre de 2026, del Ayuntamiento de Tarragona, Instituto Municipal de
get_boe_document(BOE-A-2026-23041): 6 paragraphs, https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-23041
triage_tenders(verdict='GO'): 1 of 10 matched
  [GO] PLACSP:412026 Servicios de operación del Centro de Operaciones de Segurida
    cpv       pass    CPV 72222300 within profile
    deadline  pass    7 days left
    keywords  unknown no profile keyword in title
    value     pass    206,612 EUR within limits
```

## Layout

Hexagonal: `domain/` (models, `DocumentSource` port), `application/search.py`, `adapters/` (BOE XML parser, bundled corpus), `server.py` (MCP wiring). See `docs/spec/0001-boe-search-server.md` and `docs/adr/`.

## Limitations

- Keyword counting only: no stemming, phrases or semantics.
- Static snapshots (11 BOE documents, one tender report); no live BOE, TED or PLACSP access, and the tender report is a copy, not a live call into open-tender-radar.
- stdio only; no HTTP transport or auth.
- `mcp` 2.x is not supported yet (API renamed); pinned below 2. A throwaway run of the tests against 2.3.0 passed after mechanical renames, see [ADR 0003](docs/adr/0003-mcp-2x-migration-evaluation.md).

## Licence

Apache-2.0. BOE content is reused under the Agency's reuse licence (see `src/mcp_toolbox/data/SOURCES.md`).
