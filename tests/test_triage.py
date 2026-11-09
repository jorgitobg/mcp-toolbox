from mcp_toolbox.application.triage import TenderTriage


def test_filters_combine_and_limit() -> None:
    t = TenderTriage()
    assert len(t.select(None, None, 20)) == 10
    assert {x["verdict"] for x in t.select("NO_GO", None, 20)} == {"NO_GO"}
    assert len(t.select("NO_GO", None, 3)) == 3
    assert t.select(None, "zzzz-nothing", 5) == []


def test_get_by_id_with_optional_source_prefix() -> None:
    t = TenderTriage()
    row = t.select(None, None, 1)[0]
    assert t.get(row["id"]) == row
    assert t.get(f"{row['source']}:{row['id']}") == row
    assert t.get("TED:" + row["id"]) is None if row["source"] != "TED" else True
    assert t.get("missing") is None
