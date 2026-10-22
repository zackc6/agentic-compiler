"""session-event.v0 writer. Append-only; every event validates against the Lintel schema.

Lintel's invariant (from DeepSeek Harness): model-visible context must be reconstructable
from this stream. So the propose payload carries the *full* Kernel AST, and a gate's
reject carries the Finding JSON as a sibling of ``reject`` (``reject`` itself is closed:
``where`` / ``reason`` / ``hint`` only).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .contract import ContractError, validate

SCHEMA = "session-event.v0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class SessionLog:
    session_id: str
    parent_session_id: str | None = None
    events: list[dict] = field(default_factory=list)
    clock: "callable" = _now

    @classmethod
    def new(cls, prefix: str = "ses") -> "SessionLog":
        return cls(session_id=f"{prefix}_{uuid.uuid4().hex[:12]}")

    def emit(self, kind: str, payload: dict) -> dict:
        ev = {
            "schema_version": SCHEMA,
            "event_id": f"evt_{len(self.events)}",
            "seq": len(self.events),
            "ts": self.clock(),
            "session_id": self.session_id,
            "parent_session_id": self.parent_session_id,
            "kind": kind,
            "payload": payload,
        }
        errs = validate(ev, SCHEMA)
        if errs:
            raise ContractError(f"session event {kind} seq={ev['seq']} invalid: {errs}")
        self.events.append(ev)
        return ev

    # Convenience emitters, one per Lintel `kind` the walk uses.

    def start(self, policy_id: str, mode: str, pins: dict, case: str) -> dict:
        return self.emit(
            "session.start",
            {"policy_id": policy_id, "mode": mode, "pins": pins, "case": case},
        )

    def triage(self, region_id: str, op_family: str, amdahl_rank: int = 1) -> dict:
        return self.emit(
            "triage", {"region_id": region_id, "op_family": op_family, "amdahl_rank": amdahl_rank}
        )

    def propose(self, envelope: dict) -> dict:
        """Copy rule from choreo/docs/LINTEL_CONSUME.md: kernel is the full AST."""
        return self.emit(
            "propose",
            {
                "enum_id": envelope["enum_id"],
                "adapter_id": envelope["adapter_id"],
                "compiler_ver": envelope["compiler_ver"],
                "hw_id": envelope["hw_id"],
                "graph_hash": envelope["graph_hash"],
                "gates": envelope["gates"],
                "kernel": envelope["kernel"],
            },
        )

    def gate(
        self,
        seam: str,
        passed: bool,
        *,
        reject: dict | None = None,
        finding: dict | None = None,
        detail: dict | None = None,
    ) -> dict:
        payload: dict = {"seam": seam, "passed": passed}
        if reject is not None:
            payload["reject"] = {
                k: v for k, v in reject.items() if k in ("where", "reason", "hint") and v is not None
            }
        if finding is not None:
            payload["finding"] = finding  # sibling, never inside reject
        if detail:
            payload.update(detail)
        return self.emit("gate", payload)

    def measure(self, payload: dict) -> dict:
        return self.emit("measure", payload)

    def admit(self, payload: dict) -> dict:
        return self.emit("admit", payload)

    def freeze(self, payload: dict) -> dict:
        return self.emit("freeze", payload)

    def fallback(self, payload: dict) -> dict:
        return self.emit("fallback", payload)

    def write(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            for ev in self.events:
                fh.write(json.dumps(ev, separators=(",", ":")) + "\n")
        return path

    @staticmethod
    def read(path: Path) -> list[dict]:
        return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
