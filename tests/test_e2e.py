"""One walk per case file. Session log, admit-record chain, store, and serve are all checked."""

import json

import pytest

from agentic_compiler import Store, load_case, serve, walk
from agentic_compiler.contract import validate
from agentic_compiler.record import record_errors, record_hash
from agentic_compiler.session import SessionLog

KNOWN_DRIFT = "artifact/kind:"  # DRIFT-1 in docs/DRIFT.md


def test_walk_matches_expectation(case_path, tmp_path):
    case = load_case(case_path)
    res = walk(case, tmp_path / case.name)
    assert res.decision == case.expect["decision"], res.summary()
    assert res.outcomes == case.expect["walk"], res.summary()

    # --- session stream: every event re-validates from disk, seq is dense, start carries pins
    events = SessionLog.read(res.out_dir / "session.jsonl")
    assert [e["seq"] for e in events] == list(range(len(events)))
    for e in events:
        assert validate(e, "session-event.v0") == [], e
    assert events[0]["kind"] == "session.start" and "pins" in events[0]["payload"]
    assert events[-1]["kind"] == ("freeze" if res.decision == "freeze" else "fallback")

    # --- propose payload is the full AST (Harness invariant), reject carries Finding sibling
    for e in events:
        if e["kind"] == "propose":
            k = e["payload"]["kernel"]
            assert {"name", "buffers", "partitions", "body"} <= set(k)
        if e["kind"] == "gate" and not e["payload"]["passed"]:
            assert set(e["payload"]["reject"]) <= {"where", "reason", "hint"}
            assert "finding" in e["payload"] and "where" not in e["payload"]["finding"]

    # --- admit-record chain
    assert len(res.records) == len(res.attempts)
    prev = None
    for rec in res.records:
        assert rec["prev_hash"] == prev
        prev = record_hash(rec)
    final = res.records[-1]
    assert final["decision"] == res.decision
    for rec in res.records[:-1]:
        assert rec["decision"] == "reject" and record_errors(rec) == []
    errs = record_errors(final)
    if res.decision == "freeze":
        # DRIFT-1: Lintel's enum has no `source` / `cubin` / `npu-bin` artifact kind.
        assert errs and all(KNOWN_DRIFT in e for e in errs), errs
    else:
        assert errs == []

    # --- serve: %k lookup hits the frozen artifact; a miss serves the fallback
    store = Store(res.out_dir / "store")
    if res.decision == "freeze":
        got = serve(store, res.cache_key_digest)
        assert got.hit and got.artifact_path.exists() and got.launch["block"] >= 1
        pin = json.loads((res.store_slot / "pin.json").read_text())
        assert pin["cache_key_digest"] == res.cache_key_digest
        assert final["artifact"]["digest"] == pin["artifact_file_sha256"]
    miss = serve(store, "sha256:" + "0" * 64)
    assert not miss.hit and miss.fallback == "classical"


def test_measure_is_labelled_proxy_until_a_device_clock_exists(tmp_path):
    case = load_case("accept/copy_nvidia.case.json")
    res = walk(case, tmp_path)
    m = [e for e in res.session.events if e["kind"] == "measure"]
    assert m and m[0]["payload"]["measured"] is False
    assert m[0]["payload"]["F_name"].startswith("proxy.")
    assert m[0]["payload"]["search_cost"] == {"usd": 0.0, "model_tokens": 0}


def test_same_kernel_same_key_across_walks(tmp_path):
    """%k is a function of (graph, hw, compiler, adapter, policy) — not of the session."""
    case = load_case("accept/copy_nvidia.case.json")
    a = walk(case, tmp_path / "a").cache_key_digest
    b = walk(case, tmp_path / "b").cache_key_digest
    assert a == b


def test_ascend_and_nvidia_are_different_keys(tmp_path):
    a = walk(load_case("accept/copy_nvidia.case.json"), tmp_path / "nv").cache_key_digest
    b = walk(load_case("accept/copy_ascend.case.json"), tmp_path / "npu").cache_key_digest
    assert a != b
