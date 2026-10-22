# Contract drift between the pins

Lintel (`8b4a7a9`) and Choreo (`f683e5d`) disagree in places. This repo does not paper over
that: the walk follows Choreo's live contract (`choreo/docs/LINTEL_CONSUME.md`) for Kernel
encoding and artifact kinds, validates against Lintel's schemas for field names, and records
where the two part ways. `tests/test_drift.py` fails the day a bump fixes an item so this
page gets updated in the same commit.

`agentic-compiler check-contract` runs Choreo's own `consume-check` against the Lintel pin
and prints the full list (39 items at these pins).

## DRIFT-1 — `admit-record.v0.artifact.kind` has no `source` / `cubin` / `npu-bin`

* Lintel schema enum: `triton_kernel | acf | schedule_ir | none`.
* Choreo contract: the freeze artifact is an `nvcc` cubin or a `ccec` NPU-bin (`kind=cubin`,
  `artifact.launch` on the pin); without a toolchain the sink *source* is what exists.
* Here: records write the true kind. Reject records (`kind: none`) validate fully; freeze
  records fail on exactly this one field and `tests/test_e2e.py` asserts it is the only error.
* Fix belongs in Lintel: extend the enum (`source`, `cubin`, `npu-bin`), then bump the pin and
  drop the `KNOWN_DRIFT` allowance in the test.

## DRIFT-2 — Lintel `main` still carries the Triton-era PoC

`consume-check` groups (counts at these pins):

| Lintel file | Items | What |
|---|---|---|
| `examples/admit-record.json` | 9 | `compiler_ver` names Triton as the sink; attention slots (`choreo.attn.d3.w4`) are not year-1 SLA slots (`copy` / `gemm_tile`); PascalCase ops; no `target`. |
| `examples/session-log.jsonl` | 7 | propose carries a Triton knob `schedule`, not a Kernel AST; freeze has no `cache_key` / `launch`; artifact kind not cubin/npu-bin. |
| `examples/admit-record.fallback.json` | 5 | same family as above. |
| `examples/poc/*` | 16 | attn PoC kernels: non-SLA names/slots, Triton sink pin, marker `Pipeline` with empty body (`{where: W}` at `pipe0` under live `propose`). |
| `examples/lintel-ir/*` | 2 | Triton pin. |

Choreo's `LINTEL_CONSUME.md` lists the absorb commits that fix all of this on a local Lintel
`main` that could not be pushed (`cursor[bot]` 403). Once those land on
`github.com/zackc6/lintel`, bump the submodule here; `test_lintel_pin_fails_choreo_consume_check`
will fail and should be deleted along with this section.

**This repo's own session logs and records are not affected**: they are generated from the
live Choreo envelope and already satisfy the consume contract (full AST in propose, Finding
sibling of `reject`, `cache_key` + `launch` on freeze, `%k` = sha256 of canonical key).

## Not drift, by design

* `Kernel.compiler_ver` (`0.1.13`) vs `cache_key.compiler_ver` (`choreoir==0.1.13;cuda.cxx`):
  the key names both the compiler and the sink; the Kernel names only the compiler.
* `Kernel.target` is pin **payload** (so `lower()` can replay), not a key field; admission is
  `hw_id`.
* `attrs.num_warps` / `num_stages` are Triton-sidecar knobs; `pin.launch.block` comes from
  summed `Partition.width`.
