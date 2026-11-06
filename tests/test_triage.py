from mcp_toolbox.application.triage import TenderTriage


def test_filters_combine_and_limit() -> None:
    t = TenderTriage()
    assert len(t.select(None, None, 20)) == 10
    assert {x["verdict"] for x in t.select("NO_GO", None, 20)} == {"NO_GO"}
    assert len(t.select("NO_GO", None, 3)) == 3
    assert t.select(None, "zzzz-nothing", 5) == []
