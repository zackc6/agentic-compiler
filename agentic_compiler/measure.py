"""Measurement seam. One interface, two implementations.

* ``ProxyMeasurer`` — what runs today on a CPU-only box: the Choreo interpreter for
  correctness plus schedule facts (copies, MMAs, barriers, pipeline depth, block) as a
  *proxy*. It is **not** a performance number and is labelled ``measured: false``.
* ``DeviceMeasurer`` — the seam where real device timing goes once a GPU / NPU with
  ``nvcc`` / ``ccec`` is wired in. It refuses to invent a number.

Lintel's rule: application metric and search cost are reported apart. The walk records
``usd_per_compile`` separately from ``F``; with an enumerated (non-LLM) proposer that
cost is 0 model tokens, and is written as such rather than omitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from choreoir import Kernel, simulate
from choreoir.lower import Lowered


@dataclass
class Measurement:
    F_name: str
    value: dict
    measured: bool  # True only when a device clock produced `value`
    traces: list[str] = field(default_factory=list)
    baseline: float | None = None
    delta: float | None = None
    findings: list[dict] = field(default_factory=list)

    def as_payload(self) -> dict:
        out = {
            "F_name": self.F_name,
            "value": self.value,
            "measured": self.measured,
            "traces": list(self.traces),
            "findings": list(self.findings),
        }
        if self.baseline is not None:
            out["baseline"] = self.baseline
        if self.delta is not None:
            out["delta"] = self.delta
        return out


class Measurer(Protocol):
    name: str

    def measure(
        self, kernel: Kernel, lowered: Lowered, tensors: dict | None, trace_uri: str
    ) -> Measurement: ...


class ProxyMeasurer:
    """CPU interpreter + schedule facts. Not time. Not throughput."""

    name = "proxy.sim+facts"

    def measure(
        self, kernel: Kernel, lowered: Lowered, tensors: dict | None, trace_uri: str
    ) -> Measurement:
        value: dict = {}
        findings: list[dict] = []
        if lowered.facts is not None:
            f = lowered.facts
            value.update(
                {
                    "n_copy": f.n_copy,
                    "n_mma": f.n_mma,
                    "n_barrier": f.n_barrier,
                    "pipeline_depth": f.pipeline_depth,
                    "partition_warps": f.partition_warps,
                    "block": f.block,
                    "family": f.family,
                    "arch": f.arch,
                }
            )
        if tensors is not None:
            outputs, sim_findings = simulate(kernel, tensors)
            findings = [x.as_dict() for x in sim_findings]
            value["sim_outputs"] = sorted(outputs.keys())
            value["sim_ok"] = not any(x.severity == "error" for x in sim_findings)
        return Measurement(
            F_name="proxy.schedule_facts",
            value=value,
            measured=False,
            traces=[trace_uri],
            findings=findings,
        )


class DeviceMeasurer:
    """Placeholder for the real clock. Raises until a device path is implemented.

    When it lands it must: launch the frozen cubin / NPU-bin with ``pin.launch``
    (``<<<grid, block>>>``), time N iterations after warm-up, report the median and the
    baseline (cuBLAS / vendor library or the classical fallback) under the same inputs,
    and write the raw samples to ``trace_uri``. See docs/PERFORMANCE.md.
    """

    name = "device.clock"

    def measure(
        self, kernel: Kernel, lowered: Lowered, tensors: dict | None, trace_uri: str
    ) -> Measurement:
        raise NotImplementedError(
            "device timing is not implemented; run with the proxy measurer or add a device path"
        )
