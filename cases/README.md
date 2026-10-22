# cases

One `*.case.json` = one experiment contract = one walk. Groups:

- `accept/` — year-1 SLA kernels (`copy`, `gemm_tile`) on NVIDIA (`emit: cubin`) and Ascend (`emit: npu-bin`).
- `reject/` — one case per `choreo/examples/fails/*.json`; each ends in `fallback`.
- `search/` — multi-candidate walks; a reject is an edge to the next candidate.

Format and the full list: `docs/TESTING.md`. Kernels live in the `choreo/` submodule; cases only reference them.
