# ADR 0001: Official Python SDK, stdio transport, pinned below 2.x

**Decision.** Build on the official `mcp` Python SDK (`FastMCP` API), stdio transport, `mcp>=1.12,<2`.

**Why.** Protocol correctness is the SDK's job; a hand-rolled JSON-RPC server would only prove my own reading of the spec. stdio is what desktop MCP clients launch directly and needs no ports or auth. The 2.x SDK renamed `FastMCP` to `MCPServer` and changed other APIs; the pin avoids a silent break and the migration is a deliberate future task.

**Consequences.** Tests drive the real server process with the SDK's own client, so the protocol path is exercised end to end. Servers are wrapped by thin tool functions; logic lives in the application layer.
