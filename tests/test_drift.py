"""Known drift between the two pins. These fail loudly the day it is fixed, so the
pins (and docs/DRIFT.md) get updated together rather than silently."""

import pytest
from choreoir import consume_check

from agentic_compiler.contract import LINTEL_DIR


@pytest.mark.drift
def test_lintel_pin_fails_choreo_consume_check():
    problems = consume_check(LINTEL_DIR)
    # DRIFT-2: lintel main still carries Triton-era PoC examples and attn slots.
    assert problems, "lintel pin now passes consume-check: update docs/DRIFT.md and drop this test"
    assert any("triton" in p.lower() for p in problems)
