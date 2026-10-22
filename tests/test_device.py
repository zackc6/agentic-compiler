"""Runs only where a device toolchain exists. Elsewhere these skip, never fake."""

import pytest
from choreoir import find_ccec, find_nvcc

from agentic_compiler import load_case, walk

pytestmark = pytest.mark.device


@pytest.mark.skipif(find_nvcc() is None, reason="nvcc not found")
def test_nvidia_freeze_is_a_cubin(tmp_path):
    res = walk(load_case("accept/gemm_tile_nvidia.case.json"), tmp_path)
    assert res.decision == "freeze"
    assert res.records[-1]["artifact"]["kind"] == "cubin"
    assert res.records[-1]["oracles"][-2]["name"] == "sink.compile"


@pytest.mark.skipif(find_ccec() is None, reason="ccec not found")
def test_ascend_freeze_is_an_npu_bin(tmp_path):
    res = walk(load_case("accept/gemm_tile_ascend.case.json"), tmp_path)
    assert res.decision == "freeze"
    assert res.records[-1]["artifact"]["kind"] == "npu-bin"
