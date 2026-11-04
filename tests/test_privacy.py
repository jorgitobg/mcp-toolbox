import re
from pathlib import Path

DATA = Path(__file__).parent.parent / "src" / "mcp_toolbox" / "data"
PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "dni_nie": re.compile(r"\b[XYZ]?\d{7,8}-?[A-Z]\b"),
    "phone": re.compile(r"(?<!\d)(?:\+34)?[ .]?[6-9]\d{2}[ .]?\d{3}[ .]?\d{3}(?!\d)"),
    "iban": re.compile(r"\bES\d{2}[ ]?\d{4}"),
}


def test_no_personal_identifiers_in_bundled_corpus() -> None:
    for path in DATA.glob("*.xml"):
        text = path.read_text(encoding="utf-8")
        for name, pat in PATTERNS.items():
            assert not pat.search(text), f"{path.name}: {name}"


def test_sources_lists_exactly_the_bundled_files() -> None:
    listed = set(re.findall(r"BOE-A-\d{4}-\d+", (DATA / "SOURCES.md").read_text(encoding="utf-8")))
    assert listed == {p.stem for p in DATA.glob("*.xml")}
