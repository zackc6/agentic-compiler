# Testing

```bash
./scripts/setup.sh && agentic-compiler run-all -o out   # every case under cases/, outputs on disk
```

The pytest suite was removed on 2026-10-23: while the two IRs are being designed, cases are
illustrative walks, not a correctness contract. The gate is every case `ok`. Drift between the
pins is recorded in `docs/DRIFT.md`.

## Case files

A case is one experiment contract: what region, which candidates in which order, what the
sink should emit, how many tries, and what to fall back to. The walk is not allowed to change
any of it (survey §2.3: the optimizer must not redefine the acceptance criteria).

```json
{
  "schema": "agentic-compiler.case.v0",
  "name": "search_layout_then_copy",
  "region_id": "copy.gmem",
  "op_family": "other",
  "emit": "cubin",
  "fallback": "classical",
  "false_neg_owner": "zackc6",
  "budget_tries": null,
  "candidates": [
    {"enum_id": "copy", "kernel": "choreo/examples/fails/layout_cover.json"},
    {"enum_id": "copy", "kernel": "choreo/examples/copy.json",
     "tensors": "choreo/examples/copy.tensors.json", "expected": "choreo/examples/copy.expected.json"}
  ],
  "expect": {"decision": "freeze", "walk": ["reject:L", "accept"]}
}
```

* `kernel` paths point **into the submodules**. The kernels are Choreo's; this repo adds the
  walk around them, not new kernels.
* `tensors` + `expected` opt a candidate into the V gate (value sim). Without both, the
  adapter gate is W/L/S only — Choreo does not invent a V edge.
* `target` on a candidate overrides `Kernel.target` (`ascend-a2` for the NPU cases).
* `expect.walk` is the per-candidate outcome: `accept`, `reject:W|L|S|V`, or `reject:sink`.

## The corpus (17 walks)

| Group | Cases | What it checks |
|---|---|---|
| `accept/` | `copy_nvidia`, `gemm_tile_nvidia`, `copy_ascend`, `gemm_tile_ascend` | The year-1 SLA kernels freeze on both sink families. Same Kernel → same `%k` across walks; NVIDIA and Ascend → different `%k`. |
| `reject/` | one per file in `choreo/examples/fails/` — W×4, L×2, S×2, V×1 | Each reject names `{where}` and a program point; the walk ends in `fallback: classical` with a valid record chain. |
| `search/` | `layout_then_copy`, `value_then_copy`, `wls_chain_then_gemm`, `budget_exhausted` | A reject is a CFG edge to the next candidate, not a reason to touch the checker. Budget is enforced from the contract. |

## What each walk asserts (`tests/test_e2e.py`)

1. Decision and per-candidate outcomes match `expect`.
2. Every `session-event.v0` re-validates from disk against the Lintel schema; `seq` is dense;
   `session.start` carries the pins; the stream ends in `freeze` or `fallback`.
3. `propose.payload.kernel` is the full AST (name / buffers / partitions / body) — the
   DeepSeek-Harness invariant that model-visible context is reconstructable from the stream.
4. A failed gate's `reject` is exactly `{where, reason, hint}`; the Finding JSON is a sibling,
   and does not repeat `where`.
5. One `admit-record.v0` per attempt, chained by `prev_hash`; rejected attempts validate
   fully; the freeze record validates **except** for `artifact.kind` (DRIFT-1 — see
   `docs/DRIFT.md`; the test asserts that this is the *only* error).
6. `serve(store, %k)` hits the frozen artifact and returns `launch`; a wrong key, or a
   tampered artifact (`tests/test_serve.py`), is a miss that returns the fallback.
7. `measure` is labelled `measured: false` and `F_name: proxy.*` until a device clock exists;
   search cost is reported apart from `F` (survey §4.3).

## Device tests

`tests/test_device.py` runs only where `nvcc` / `ccec` are found and asserts that the frozen
artifact is a real `cubin` / `npu-bin`. CI's second job fetches the official `nvcc` (as
Choreo's own CI does) so the NVIDIA half runs on GitHub; `ccec` is not a public redist.

## Adding a case

Drop a `*.case.json` under `cases/<group>/`; it is picked up by `run-all`.
If it needs a kernel that is not in `choreo/examples/`, that kernel belongs in Choreo first.
