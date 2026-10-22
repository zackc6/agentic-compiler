"""The application-search walk. One loop, pinned compiler, fixed contract.

    session.start → triage → [ propose → gate(adapter) → gate(sandbox) → measure → admit ]* →
    freeze  (first admitted candidate; artifact into the store under %k)
    fallback (budget exhausted or every candidate rejected; classical fallback)

Three loops stay apart (lintel/docs/ARCHITECTURE.md, choreo/goals/lintel-codesign.md):
this file is *application search only*. It never edits ``choreoir`` (compiler development)
and never edits its own candidate order (controller development). A reject ``{where}``
is a CFG edge to the next candidate, not a reason to rewrite a check.

The proposer here is the year-1 ``lintel.specialize.v0`` slot: an enumerated allowlist
(``copy`` / ``gemm_tile``) walked in case order. No LLM is on this path. That is a
deliberate baseline, not the end state — Lintel's architecture puts agent, learned
policy, and structured search behind the same ``propose`` seam with the same budget.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from choreoir import (
    FACE_ADAPTER_ID,
    adapter_proposal,
    kernel_to_dict,
    load_kernel_doc,
    materialize,
)
from choreoir.lower import Lowered
from choreoir.pin import policy_id_of

from .contract import CASES_DIR, REPO_ROOT, pins as read_pins, sha256_doc
from .measure import Measurement, Measurer, ProxyMeasurer
from .record import build_record, record_hash, write_chain
from .serve import Store
from .session import SessionLog

CASE_SCHEMA = "agentic-compiler.case.v0"
MODEL_ID_ENUMERATED = "none.enumerated.v0"  # no optimizer model on this walk
FALSE_NEG_OWNER_DEFAULT = "zackc6"


@dataclass
class Candidate:
    enum_id: str
    kernel: Path
    tensors: Path | None = None
    expected: Path | None = None
    target: str | None = None  # override Kernel.target (e.g. "ascend-a2")


@dataclass
class Case:
    name: str
    region_id: str
    op_family: str  # attention | gemm | other
    candidates: list[Candidate]
    emit: str = "source"  # source | cubin | npu-bin
    budget_tries: int | None = None
    fallback: str = "classical"
    false_neg_owner: str = FALSE_NEG_OWNER_DEFAULT
    expect: dict = field(default_factory=dict)
    source: Path | None = None


def _resolve(p: str | None, base: Path) -> Path | None:
    if p is None:
        return None
    path = Path(p)
    if path.is_absolute():
        return path
    # Case files reference submodule examples relative to the repo root.
    for root in (REPO_ROOT, base):
        cand = root / path
        if cand.exists():
            return cand
    return REPO_ROOT / path


def load_case(path: Path) -> Case:
    path = Path(path)
    if not path.exists() and (CASES_DIR / path).exists():
        path = CASES_DIR / path
    d = json.loads(path.read_text())
    if d.get("schema") != CASE_SCHEMA:
        raise ValueError(f"{path}: schema must be {CASE_SCHEMA!r}")
    cands = [
        Candidate(
            enum_id=c["enum_id"],
            kernel=_resolve(c["kernel"], path.parent),
            tensors=_resolve(c.get("tensors"), path.parent),
            expected=_resolve(c.get("expected"), path.parent),
            target=c.get("target"),
        )
        for c in d["candidates"]
    ]
    return Case(
        name=d["name"],
        region_id=d["region_id"],
        op_family=d.get("op_family", "other"),
        candidates=cands,
        emit=d.get("emit", "source"),
        budget_tries=d.get("budget_tries"),
        fallback=d.get("fallback", "classical"),
        false_neg_owner=d.get("false_neg_owner", FALSE_NEG_OWNER_DEFAULT),
        expect=d.get("expect", {}),
        source=path,
    )


@dataclass
class Attempt:
    enum_id: str
    outcome: str  # "accept" | "reject:W" | "reject:L" | "reject:S" | "reject:V" | "reject:sink"
    envelope: dict
    lowered: Lowered | None = None
    measurement: Measurement | None = None
    pin: dict | None = None


@dataclass
class WalkResult:
    case: Case
    out_dir: Path
    session: SessionLog
    attempts: list[Attempt]
    records: list[dict]
    decision: str  # freeze | fallback
    cache_key_digest: str | None
    store_slot: Path | None

    @property
    def outcomes(self) -> list[str]:
        return [a.outcome for a in self.attempts]

    def summary(self) -> dict:
        return {
            "case": self.case.name,
            "decision": self.decision,
            "walk": self.outcomes,
            "cache_key_digest": self.cache_key_digest,
            "store_slot": str(self.store_slot) if self.store_slot else None,
            "session": str(self.out_dir / "session.jsonl"),
            "records": len(self.records),
        }


def _load_json(p: Path | None) -> dict | None:
    return json.loads(Path(p).read_text()) if p else None


def _oracle(name: str, version: str, result: str, owner: str, detail: str = "") -> dict:
    return {
        "name": name,
        "version": version,
        "result": result,
        "false_neg_owner": owner,
        "detail": detail,
    }


def walk(
    case: Case,
    out_dir: Path,
    *,
    measurer: Measurer | None = None,
    store: Store | None = None,
    session: SessionLog | None = None,
) -> WalkResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    measurer = measurer or ProxyMeasurer()
    store = store or Store(out_dir / "store")
    log = session or SessionLog.new()
    pin_info = read_pins()
    choreo_ver = f"choreoir=={pin_info.choreoir_version}"

    policy_id = "lintel.specialize.v0"
    log.start(policy_id, "sku", pin_info.as_dict(), case.name)
    log.triage(case.region_id, case.op_family)

    attempts: list[Attempt] = []
    records: list[dict] = []
    prev_hash: str | None = None
    decision = "fallback"
    frozen_digest: str | None = None
    slot: Path | None = None
    budget = case.budget_tries or len(case.candidates)

    for idx, cand in enumerate(case.candidates[:budget]):
        kernel = load_kernel_doc(_load_json(cand.kernel))
        if cand.target:
            kernel.target = cand.target
        kernel.attrs.setdefault("enum_id", cand.enum_id)
        tensors = _load_json(cand.tensors)
        expected = _load_json(cand.expected)
        kernel_json = kernel_to_dict(kernel)
        owner = case.false_neg_owner
        oracles: list[dict] = []

        # ---- propose: Choreo emits the envelope; Lintel copies it onto the stream.
        envelope = adapter_proposal(kernel, tensors=tensors, expected=expected)
        log.propose(envelope)
        attempt = Attempt(cand.enum_id, "accept", envelope)
        attempts.append(attempt)

        cache_key = {
            "schema_version": "cache-key.v0",
            "graph_hash": envelope["graph_hash"],
            "hw_id": envelope["hw_id"],
            "compiler_ver": envelope["compiler_ver"],
            "adapter_id": envelope["adapter_id"],
            "policy_id": policy_id_of(kernel),
        }
        rec_pins = {
            "hw_id": envelope["hw_id"],
            "compiler_ver": envelope["compiler_ver"],
            "adapter_id": FACE_ADAPTER_ID,
            "model_id": MODEL_ID_ENUMERATED,
            "policy_id": policy_id,
        }
        trace_uri = f"{log.session_id}/attempt-{idx}"
        fitness = {"F_name": measurer.name, "traces": [trace_uri], "usd_per_compile": 0.0}

        # ---- gate(adapter): W/L/S (+V when tensors/expected given) — the CFG edge.
        reject = envelope.get("reject")
        gates_run = "WLSV" if (tensors is not None and expected is not None) else "WLS"
        if reject:
            log.gate(
                "adapter",
                False,
                reject=reject,
                finding=reject["finding"],
                detail={"gates": gates_run},
            )
            attempt.outcome = f"reject:{reject['where']}"
            oracles.append(
                _oracle(f"choreo.admit.{gates_run}", choreo_ver, "fail", owner, reject["reason"])
            )
            rec = build_record(
                record_id=f"rec_{log.session_id}_{idx:03d}",
                prev_hash=prev_hash,
                region_id=case.region_id,
                graph_hash=envelope["graph_hash"],
                op_family=case.op_family,
                pins=rec_pins,
                enum_id=cand.enum_id,
                kernel=kernel_json,
                oracles=oracles,
                cache_key=cache_key,
                cache_key_digest=sha256_doc(cache_key),
                artifact={"digest": sha256_doc(kernel_json), "kind": "none"},
                fitness=fitness,
                decision="reject",
                fallback="none",
                commentary=f"{{where: {reject['where']}}} at {reject['hint']}: next candidate",
            )
            records.append(rec)
            prev_hash = record_hash(rec)
            continue
        log.gate("adapter", True, detail={"gates": gates_run})
        oracles.append(_oracle(f"choreo.admit.{gates_run}", choreo_ver, "pass", owner))

        # ---- gate(sandbox): sink + toolchain. Missing nvcc/ccec is a warning, not a fake binary.
        sink_dir = out_dir / f"attempt-{idx}"
        lowered = materialize(kernel, sink_dir, emit=case.emit)
        attempt.lowered = lowered
        sink_errors = [f.as_dict() for f in lowered.errors()]
        warnings = [f.as_dict() for f in lowered.findings if f.severity == "warning"]
        if sink_errors:
            first = sink_errors[0]
            log.gate(
                "sandbox",
                False,
                reject={"where": first["where"], "reason": first["msg"], "hint": first["node"]},
                finding=first,
                detail={"sink_id": lowered.as_k()["sink_id"], "emit": case.emit},
            )
            attempt.outcome = "reject:sink"
            oracles.append(_oracle("sink.lower", choreo_ver, "fail", owner, first["msg"]))
            rec = build_record(
                record_id=f"rec_{log.session_id}_{idx:03d}",
                prev_hash=prev_hash,
                region_id=case.region_id,
                graph_hash=envelope["graph_hash"],
                op_family=case.op_family,
                pins=rec_pins,
                enum_id=cand.enum_id,
                kernel=kernel_json,
                oracles=oracles,
                cache_key=cache_key,
                cache_key_digest=sha256_doc(cache_key),
                artifact={"digest": sha256_doc(kernel_json), "kind": "none"},
                fitness=fitness,
                decision="reject",
                fallback="none",
            )
            records.append(rec)
            prev_hash = record_hash(rec)
            continue
        pin = lowered.as_k()
        attempt.pin = pin
        compile_ok = lowered.artifact_kind in ("cubin", "npu-bin")
        log.gate(
            "sandbox",
            True,
            detail={
                "sink_id": pin["sink_id"],
                "emit": case.emit,
                "artifact_kind": lowered.artifact_kind,
                "compile_ok": compile_ok,
                "toolchain": lowered.toolchain,
                "warnings": warnings,
            },
        )
        oracles.append(
            _oracle(
                "sink.compile",
                choreo_ver,
                "pass" if compile_ok else "skip",
                owner,
                lowered.toolchain or f"{case.emit}: no device toolchain; source only",
            )
        )

        # ---- measure: application metric and search cost reported apart.
        m = measurer.measure(kernel, lowered, tensors, trace_uri)
        attempt.measurement = m
        log.measure({"measurer": measurer.name, **m.as_payload(), "search_cost": {"usd": 0.0, "model_tokens": 0}})
        sim_ok = m.value.get("sim_ok")
        if tensors is not None:
            oracles.append(
                _oracle("choreo.sim", choreo_ver, "pass" if sim_ok else "fail", owner)
            )
        fitness = {"F_name": m.F_name, "traces": list(m.traces), "usd_per_compile": 0.0}
        if m.baseline is not None:
            fitness["baseline"] = m.baseline
        if m.delta is not None:
            fitness["delta"] = m.delta

        # ---- admit + freeze: %k is the address; the AST and the sink output are the value.
        if sim_ok is False:
            # V already ran inside the adapter gate when tensors+expected were given; this
            # only fires when tensors came without an expected oracle and the sim itself errored.
            log.admit({"decision": "reject", "reason": "simulation error", "cache_key_digest": pin["cache_key_digest"]})
            attempt.outcome = "reject:V"
            rec = build_record(
                record_id=f"rec_{log.session_id}_{idx:03d}",
                prev_hash=prev_hash,
                region_id=case.region_id,
                graph_hash=envelope["graph_hash"],
                op_family=case.op_family,
                pins=rec_pins,
                enum_id=cand.enum_id,
                kernel=kernel_json,
                oracles=oracles,
                cache_key=pin["cache_key"],
                cache_key_digest=pin["cache_key_digest"],
                artifact={"digest": sha256_doc(kernel_json), "kind": "none"},
                fitness=fitness,
                decision="reject",
                fallback="none",
            )
            records.append(rec)
            prev_hash = record_hash(rec)
            continue

        artifact_path = Path(lowered.artifact_path) if lowered.artifact_path else None
        if artifact_path is None:
            # emit=source: the sink text is the artifact.
            ext = "cce" if lowered.family == "ascend" else "cu"
            artifact_path = sink_dir / f"{lowered.kernel_name}.{ext}"
        slot = store.freeze(pin, artifact_path, kernel_json)
        stored = json.loads((slot / "pin.json").read_text())
        artifact_digest = stored["artifact_file_sha256"]
        log.admit({"decision": "freeze", "cache_key_digest": pin["cache_key_digest"], "enum_id": cand.enum_id})
        log.freeze(
            {
                "cache_key": pin["cache_key"],
                "cache_key_digest": pin["cache_key_digest"],
                "kind": lowered.artifact_kind,
                "artifact_sha256": artifact_digest,
                "launch": pin["launch"],
                "sink_id": pin["sink_id"],
                "store": str(slot),
            }
        )
        rec = build_record(
            record_id=f"rec_{log.session_id}_{idx:03d}",
            prev_hash=prev_hash,
            region_id=case.region_id,
            graph_hash=envelope["graph_hash"],
            op_family=case.op_family,
            pins=rec_pins,
            enum_id=cand.enum_id,
            kernel=kernel_json,
            oracles=oracles,
            cache_key=pin["cache_key"],
            cache_key_digest=pin["cache_key_digest"],
            artifact={
                "digest": artifact_digest,
                "kind": lowered.artifact_kind,
                "uri": str(slot / stored["artifact_uri"]),
            },
            fitness=fitness,
            decision="freeze",
            fallback=case.fallback,
        )
        records.append(rec)
        prev_hash = record_hash(rec)
        decision = "freeze"
        frozen_digest = pin["cache_key_digest"]
        break

    if decision != "freeze":
        log.fallback(
            {
                "fallback": case.fallback,
                "reason": "budget exhausted" if budget < len(case.candidates) else "all candidates rejected",
                "tried": [a.outcome for a in attempts],
            }
        )
        if records:
            records[-1]["decision"] = "fallback"
            records[-1]["fallback"] = case.fallback

    log.write(out_dir / "session.jsonl")
    write_chain(records, out_dir)
    result = WalkResult(case, out_dir, log, attempts, records, decision, frozen_digest, slot)
    (out_dir / "summary.json").write_text(json.dumps(result.summary(), indent=2) + "\n")
    return result
