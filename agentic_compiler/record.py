"""admit-record.v0 builder. "If it is not in this record, it did not happen."

One record per specialize attempt (one candidate), chained by ``prev_hash`` inside a walk.
The last record in the chain carries the walk's decision (``freeze`` or ``fallback``);
earlier ones are ``reject``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .contract import sha256_doc, validate

SCHEMA = "admit-record.v0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_record(
    *,
    record_id: str,
    prev_hash: str | None,
    region_id: str,
    graph_hash: str,
    op_family: str,
    pins: dict,
    enum_id: str,
    kernel: dict,
    oracles: list[dict],
    cache_key: dict,
    cache_key_digest: str,
    artifact: dict,
    fitness: dict,
    decision: str,
    fallback: str,
    commentary: str = "",
    created_at: str | None = None,
) -> dict:
    rec = {
        "schema_version": SCHEMA,
        "record_id": record_id,
        "prev_hash": prev_hash,
        "created_at": created_at or _now(),
        "commentary": commentary,
        "region": {"region_id": region_id, "graph_hash": graph_hash, "op_family": op_family},
        "pins": pins,
        "actions": [{"kind": "propose_kernel", "enum_id": enum_id, "kernel": kernel}],
        "oracles": oracles,
        "cache_key": cache_key,
        "cache_key_digest": cache_key_digest,
        "artifact": artifact,
        "fitness": fitness,
        "decision": decision,
        "fallback": fallback,
    }
    return rec


def record_hash(rec: dict) -> str:
    return sha256_doc(rec)


def record_errors(rec: dict) -> list[str]:
    return validate(rec, SCHEMA)


def write_chain(records: list[dict], out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, rec in enumerate(records):
        p = out_dir / f"admit-record.{i:03d}.json"
        p.write_text(json.dumps(rec, indent=2) + "\n")
        paths.append(p)
    return paths
