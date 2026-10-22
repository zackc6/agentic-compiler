from __future__ import annotations

from pathlib import Path

import pytest

from agentic_compiler.contract import CASES_DIR, require_submodules

CASE_FILES = sorted(CASES_DIR.rglob("*.case.json"))


def pytest_configure(config):
    try:
        require_submodules()
    except Exception as e:  # pragma: no cover
        pytest.exit(str(e), returncode=3)


@pytest.fixture(params=CASE_FILES, ids=[p.stem.replace(".case", "") for p in CASE_FILES])
def case_path(request) -> Path:
    return request.param
