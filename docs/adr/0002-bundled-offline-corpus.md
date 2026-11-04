# ADR 0002: Bundled offline corpus behind a `DocumentSource` port

**Decision.** Ship 11 recorded BOE XML documents inside the package and read them through a `DocumentSource` port; search is plain accent-folded term counting.

**Why.** Demo and tests must run from a clean clone with no keys or network, and the installed package must work without repository paths. A port keeps a live BOE adapter (or the TED adapter from open-tender-radar) a drop-in later. Term counting is deterministic and explainable; it is deliberately not presented as semantic search.

**Trade-offs.** Tiny corpus, no stemming, no phrase queries. Documents are static snapshots from 2026-11-03.
