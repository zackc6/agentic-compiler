# Performance

**There are no performance numbers yet.** This page fixes the method and the table shape
first so that the first number to land cannot be a correctness-only result dressed as a
speedup, or a kernel speedup presented as an application gain (survey §9, "Keep the evidence
honest").

## What is measured today

Nothing is timed. `measure` uses `ProxyMeasurer`: the Choreo CPU interpreter for correctness
and the schedule facts (`n_copy`, `n_mma`, `n_barrier`, `pipeline_depth`, `partition_warps`,
`block`) as a proxy. Every measure event and admit record carries `F_name: proxy.schedule_facts`
and `measured: false`. `tests/test_e2e.py::test_measure_is_labelled_proxy_until_a_device_clock_exists`
pins that label.

## What a real row needs

`DeviceMeasurer` (`agentic_compiler/measure.py`) is the seam. To fill it:

1. Launch the frozen artifact from the store with `pin.launch` (`<<<grid, block>>>` for a cubin;
   one aicore for an NPU-bin) on the inputs the case names.
2. Warm up, then time N iterations; report the median and the spread, and write the raw
   samples to the trace URI the record already names.
3. Run the **baseline under the same inputs on the same device**: the vendor library
   (cuBLAS / CANN op) or the classical fallback the contract names. `fitness.baseline` and
   `fitness.delta` in the admit record are for this, and only this.
4. Report search cost **apart**: model tokens (0 for the enumerated proposer), compile time,
   device time, failed trials, wall-clock (survey §4.3). `usd_per_compile` in the record is
   that number, not a guess.
5. Measure at least the two year-1 kernels on at least one NVIDIA part before adding Ascend.

A result that is "as fast with cheaper search" is a search-efficiency result under a declared
tolerance, not a runtime gain; keep the two apart (survey §4.3, Helion example).

## Table (empty)

`perf/results/<date>-<hw_id>.json`, one object per measured `%k`:

```json
{
  "schema": "agentic-compiler.perf.v0",
  "date": "YYYY-MM-DD",
  "hw_id": "nvidia.sm_90",
  "cache_key_digest": "sha256:…",
  "enum_id": "gemm_tile",
  "shape": {"M": 0, "N": 0, "K": 0, "dtype": "f16"},
  "artifact_kind": "cubin",
  "launch": {"grid": 1, "block": 256, "num_warps": 8, "num_stages": 3},
  "median_us": null, "p10_us": null, "p90_us": null, "iters": 0,
  "baseline": {"name": "cublas", "median_us": null},
  "delta": null,
  "search_cost": {"model_tokens": 0, "compile_s": null, "device_s": null, "failed_trials": 0, "wall_s": null},
  "traces": ["…"],
  "measured": true
}
```

| date | hw_id | enum_id | shape | median µs | baseline (name, µs) | Δ | search cost | %k |
|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — |

## Falsifiers this table must be able to show

From Choreo's README, carried here because this is where they get tested:

* Under a matched budget and the same feedback, raw CUDA, PTX, or Triton matches or beats
  the Choreo representation on correctness and speed.
* A simpler existing interface gets the same attainable performance and validation, so the
  representation has not earned its cost.

And from Lintel's year-1 kill switches (`lintel/docs/RISKS.md`): "we compiled Choreo" without
serving `F` is the failure mode, not a milestone.
