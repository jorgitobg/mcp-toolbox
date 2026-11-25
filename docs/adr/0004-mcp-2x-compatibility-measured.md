# ADR 0004: mcp 2.x compatibility measured; staying on 1.x

Status: accepted (2026-11-25). Supersedes the "not adopted yet" outlook of ADR 0003 with measurements.

## Context
`pyproject.toml` pins `mcp>=1.12,<2`. PyPI now lists `mcp 2.3.0` as the latest release and
`1.30.0` as the last 1.x. ADR 0003 said the migration was mechanical but only checked the
test suite once. This record measures the suite, the demo, the wheel and the client-visible
stdio surface on exact versions, in throwaway virtualenvs outside the repository.

## Measurements (Python 3.12, scratch virtualenvs, 2026-11-25)

mcp 1.30.0, repository unchanged:
- `pytest`: 34 passed, coverage 86.48% (gate 85%)
- `pyright` strict: 0 errors; `python -m mcp_toolbox.demo`: exit 0

mcp 2.3.0, with the ADR 0003 renames (`FastMCP` -> `MCPServer`, `McpError` -> `MCPError`,
snake_case client attributes, plain `str` URIs) and the dependency range changed to `>=2,<3`:
- Unmodified code does not even import (`McpError` is gone).
- With the renames, 33 of 34 tests passed. The failing one is the in-process
  `test_get_tender_in_process`: `Server.call_tool` now returns a `CallToolResult` instead of a
  `(content, structured)` tuple, and the original error message is no longer part of the
  raised exception. With that test adapted: 34 passed, coverage 86.48%.
- `python -m mcp_toolbox.demo`: exit 0, output identical to 1.30.0.
- Wheel: built from the 2.x-ranged tree, installed into a clean virtualenv with `mcp 2.3.0`,
  `scripts/verify_wheel.py` (with `isError` -> `is_error`) passed: bundled corpora and stdio
  answers present.
- Not verified: pyright strict on 2.x (the scratch edit left unrelated type errors in the
  adapted test), Windows, any MCP client other than the official Python one.

## Client-visible differences
`scripts/stdio_surface.py` dumps tools (names, descriptions, input schemas), all tool call
results, resource reads, templates and prompts as seen by a client over stdio. Diffing 1.30.0
against 2.3.0 shows byte-identical output for everything on the success path. The only
differences are error texts:
- tool `get_tender` with an unknown id: 1.x `Error executing tool get_tender: unknown tender id: 'nope'`, 2.x `Error executing tool get_tender`
- resources `tenders://tender/nope` and `tenders://report/maybe`: 1.x includes the reason
  (`unknown tender id: 'nope'`, `verdict must be one of GO, REVIEW, NO_GO`), 2.x only says the
  resource could not be created.

So 2.x hides the actionable validation message from clients unless the server raises a
different kind of exception. That is a behaviour regression for this server's users, not a rename.

## Decision
Option (a), stay on 1.x, without a CI leg yet:
- A 2.x leg would need the renames applied by script, so it would test a patched copy rather
  than the code that ships. Option (b) (import shim) would not fix the error-text difference;
  it needs real work on how errors are raised, and that work is only worth doing against a
  client base that has moved to 2.x.
- Option (c) would give clients a worse error experience today.
- Revisit when 2.x is what common clients ship against, or when the 2.x error handling
  exposes validation messages (check with `scripts/stdio_surface.py`).

## Consequences
- `pyproject.toml` keeps `mcp>=1.12,<2`; README Limitations links this record.
- `scripts/stdio_surface.py` makes the comparison repeatable for the next re-evaluation.
