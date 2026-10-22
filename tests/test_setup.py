"""Setup checks: the walk runs against pinned submodules, not a stray install."""

import choreoir

from agentic_compiler.contract import CHOREO_DIR, LINTEL_DIR, SCHEMAS, load_schema, pins


def test_submodules_present():
    assert (LINTEL_DIR / "schemas").is_dir()
    assert (CHOREO_DIR / "choreoir").is_dir()


def test_choreoir_is_the_submodule():
    # `pip install -e ./choreo` — the import must resolve inside the submodule.
    assert CHOREO_DIR in __import__("pathlib").Path(choreoir.__file__).resolve().parents


def test_pins_are_concrete():
    p = pins()
    assert len(p.lintel_commit) == 40 and len(p.choreo_commit) == 40
    assert p.choreoir_version == p.compiler_ver == choreoir.COMPILER_VER


def test_all_lintel_schemas_load():
    for name in SCHEMAS:
        s = load_schema(name)
        assert s["$schema"].startswith("https://json-schema.org/")
