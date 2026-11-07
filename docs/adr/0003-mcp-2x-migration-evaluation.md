# ADR 0003: mcp 2.x migration evaluated, not adopted yet

Status: accepted (2026-11-07)

## Context
The package pins `mcp>=1.12,<2`. The official SDK now ships 2.x (2.3.0 tried).

## What was tried
A throwaway copy of this repo was installed against `mcp==2.3.0` and its test suite run
after mechanical renames. With these changes all 26 tests passed:
- `from mcp.server.fastmcp import FastMCP` -> `from mcp.server.mcpserver import MCPServer`
- `McpError` -> `MCPError`
- client result attributes became snake_case: `isError` -> `is_error`,
  `serverInfo` -> `server_info`, `inputSchema` -> `input_schema`,
  `resourceTemplates` -> `resource_templates`, `uriTemplate` -> `uri_template`
- `read_resource` takes a plain `str` URI instead of `AnyUrl`

Without the renames, importing the server fails immediately (the 2.x error message points
to the migration guide).

## Decision
Stay on 1.x for now. The migration is small and mechanical, but 1.x and 2.x are not
source-compatible, so supporting both needs either a compatibility shim or a second CI
matrix leg. Neither is worth it until 2.x is what MCP clients actually ship against.
The test suite is the safety net for the future switch: it already exercises the real
server over stdio, so the move is "apply the renames above, run the suite".

## Consequences
- `pyproject.toml` keeps `<2`; the README says so.
- Only the throwaway run above was checked on 2.x: not CI, not the demo, not Windows.
