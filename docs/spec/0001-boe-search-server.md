# Spec 0001: BOE search MCP server

Corpus: 11 BOE disposition XML documents bundled in `src/mcp_toolbox/data/` (provenance and licence in `SOURCES.md`; institutional documents only, no candidate lists). Transport: stdio. Both tools are read-only and make no network calls.

## US1: Discover tools
- Given a client that connects over stdio, when it initialises and lists tools, then the server reports `mcp-toolbox` with exactly `search_boe` and `get_boe_document`, each with a JSON input schema.

## US2: Search
- Given the bundled corpus, when `search_boe` is called with "Ayuntamiento Subalterno", then results come back ranked by score (title matches weigh 3x), ties broken by id, each with id, title, department, date, source URL, score and a snippet.
- Given a query with accents or different case ("Málaga" / "malaga"), then the same documents are returned.
- Given an empty query or no matching term, then `count` is 0 and `results` is empty.
- Given `limit` above 20 or below 1, then it is clamped to 20 / 1.

## US3: Read a document
- Given a known id, when `get_boe_document` is called, then metadata and all paragraphs are returned.
- Given an unknown id, then the call fails as an MCP tool error (`isError`), not as a crash.

## US4: Safety
- Given invalid arguments (missing or mistyped `query`), then the call is rejected with a tool error.
- The bundled corpus contains no emails, ID numbers, phones or IBANs (enforced by tests).

## Non-goals (v0.1)
No semantic search, no live BOE/TED access, no write tools, no HTTP transport.
