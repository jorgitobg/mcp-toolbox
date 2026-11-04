from datetime import date

import pytest

from mcp_toolbox.adapters.boe_xml import parse_boe
from mcp_toolbox.adapters.fixture_corpus import DirectoryCorpus
from mcp_toolbox.application.search import BoeSearch, fold, tokens
from mcp_toolbox.domain.models import BoeDocument

XML = (
    "<documento><metadatos><identificador>BOE-A-1</identificador>"
    "<titulo>Título de prueba</titulo><fecha_publicacion>20261103</fecha_publicacion>"
    "<departamento>Dept</departamento></metadatos>"
    "<texto><p>Primer párrafo\u00a0uno.</p><p>  </p><p>Segundo.</p></texto></documento>"
).encode()


def test_parse_minimal_document() -> None:
    doc = parse_boe(XML)
    assert doc.id == "BOE-A-1"
    assert doc.published == date(2026, 11, 3)
    assert doc.paragraphs == ("Primer párrafo uno.", "Segundo.")
    assert doc.url.endswith("id=BOE-A-1")


def test_parse_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="invalid XML"):
        parse_boe(b"<nope")
    with pytest.raises(ValueError, match="missing"):
        parse_boe(b"<documento><metadatos/></documento>")


def test_bad_date_becomes_none() -> None:
    doc = parse_boe(XML.replace(b"20261103", b"xx"))
    assert doc.published is None


def test_fold_and_tokens_are_accent_insensitive() -> None:
    assert fold("Ñandú Ayuntamiento") == "nandu ayuntamiento"
    assert tokens("Los plazas del Ayuntamiento") == ["plazas", "ayuntamiento"]


def test_bundled_corpus_loads_all_documents() -> None:
    assert len(DirectoryCorpus().all_documents()) == 11


def _search() -> BoeSearch:
    return BoeSearch(DirectoryCorpus())


def test_search_ranks_and_is_deterministic() -> None:
    first = _search().search("Torrox Subalterno")
    assert first and first[0].doc.id == "BOE-A-2026-23041"
    assert first == _search().search("Torrox Subalterno")
    assert [h.score for h in first] == sorted((h.score for h in first), reverse=True)


def test_search_accent_insensitive() -> None:
    a = _search().search("Málaga")
    b = _search().search("malaga")
    assert a and [h.doc.id for h in a] == [h.doc.id for h in b]


def test_search_empty_and_no_match() -> None:
    s = _search()
    assert s.search("") == []
    assert s.search("zzzzqqqq") == []
    assert s.search("Torrox", limit=0) == []


def test_limit_and_get() -> None:
    s = _search()
    assert len(s.search("resolución", limit=2)) == 2
    assert s.get("BOE-A-2026-23041") is not None
    assert s.get("nope") is None


def test_snippet_fallbacks() -> None:
    empty = BoeDocument("X", "Solo titulo unico", "", None, "u", ())

    class Src:
        def all_documents(self) -> tuple[BoeDocument, ...]:
            return (empty,)

    hit = BoeSearch(Src()).search("unico")[0]
    assert hit.snippet == "Solo titulo unico"
