# agentic-compiler

End-to-end implementation of the agentic compiler described in
[ai-compiler-survey](https://github.com/zackc6/ai-compiler-survey): the
[Lintel](https://github.com/zackc6/lintel) control plane walking the
[Choreo IR](https://github.com/zackc6/choreo) data plane, with the survey as referee.

Both repos are **submodules**, pinned by commit. Lintel is the written contract (schemas, no
code); Choreo is the kernel-schedule compiler. This repo is the only place where the two meet
and run: it contains the walk, the test cases, how to set it up, how to test it, and — once a
device is wired in — the performance numbers.

```text
                 ┌──────────────── experiment contract (fixed) ────────────────┐
cases/*.case.json│  region · op_family · candidates · emit · budget · fallback │
                 └──────────────────────────────┬──────────────────────────────┘
                                                ▼
   session.start ─► triage ─► ┌─ propose ─► gate(adapter W/L/S/V) ─► gate(sandbox: sink + nvcc/ccec)
                              │                  │ reject {where}                │
                              │                  ▼  (CFG edge: next candidate)   ▼
                              └──────────────────┘                     measure ─► admit ─► freeze %k ─► store
                                                                                              │
                      all rejected / budget spent ─► fallback (classical)        serve = lookup(%k) │ fallback
```

* `agentic_compiler/loop.py` — the walk. One application-search loop under a pinned
  `compiler_ver`. It never edits the compiler or its own proposer (the other two loops of
  survey §2.4 / Lintel `ARCHITECTURE.md`).
* `agentic_compiler/session.py` — `session-event.v0` stream; every event validates against
  `lintel/schemas/`. Propose carries the full Kernel AST; a reject carries the Finding JSON.
* `agentic_compiler/record.py` — `admit-record.v0` chain (`prev_hash`), one per attempt.
* `agentic_compiler/serve.py` — content-addressed store keyed by `cache_key_digest` (`%k`);
  `serve()` is lookup-or-fallback with no optimizer model on the path.
* `agentic_compiler/measure.py` — the measurement seam. Today a **proxy** (CPU interpreter +
  schedule facts, labelled `measured: false`). The device clock is a stub that refuses to
  invent a number.
* `cases/` — the test corpus (17 walks): accept on NVIDIA and Ascend, every W/L/S/V reject in
  Choreo's corpus, and multi-candidate searches where a reject is an edge to the next kernel.

## Quick start

```bash
git clone --recurse-submodules https://github.com/zackc6/agentic-compiler
cd agentic-compiler
./scripts/setup.sh            # submodules → choreoir (from ./choreo) → this package
python3 -m pytest             # 26 pass, 2 device tests skip without nvcc/ccec
agentic-compiler run-all -o out
agentic-compiler serve out/copy_nvidia $(jq -r .cache_key_digest out/copy_nvidia/summary.json)
```

Details: [docs/SETUP.md](docs/SETUP.md) · [docs/TESTING.md](docs/TESTING.md) ·
[docs/PERFORMANCE.md](docs/PERFORMANCE.md) · [docs/SURVEY_BASIS.md](docs/SURVEY_BASIS.md) ·
[docs/DRIFT.md](docs/DRIFT.md).

## What a walk produces

```text
out/<case>/
  session.jsonl            session-event.v0 stream (start → triage → propose/gate… → freeze|fallback)
  admit-record.NNN.json    admit-record.v0, one per candidate, chained by prev_hash
  attempt-N/               sink output (CUDA C++ / CCE, Triton / TileLang sidecars, cubin if nvcc)
  store/<digest>/          frozen artifact + pin.json (cache-key.v0 + launch) + kernel.json
  summary.json
```

`agentic-compiler run-all` on a CPU-only box:

```text
ok  copy_nvidia                  freeze   accept
ok  gemm_tile_nvidia             freeze   accept
ok  copy_ascend                  freeze   accept
ok  gemm_tile_ascend             freeze   accept
ok  reject_unknown_buffer        fallback reject:W      …(9 single-reject walks, one per Choreo fail case)
ok  search_layout_then_copy      freeze   reject:L → accept
ok  search_value_then_copy       freeze   reject:V → accept
ok  search_wls_chain_then_gemm   freeze   reject:W → reject:S → reject:L → accept
ok  search_budget_exhausted      fallback reject:L → reject:S
```

## What this is not (yet)

* **Not a performance claim.** No kernel here has been timed on a device. `F` is a labelled
  proxy until [docs/PERFORMANCE.md](docs/PERFORMANCE.md) has rows.
* **Not an LLM in the loop.** The year-1 proposer is an enumerated allowlist (`copy`,
  `gemm_tile`) walked in case order — `model_id: none.enumerated.v0`, `usd_per_compile: 0`.
  Lintel puts agent, learned policy, and structured search behind the same `propose` seam
  with the same budget; that comparison (survey §5.2 step 3) is the next thing to build here.
* **Not the other two loops.** Compiler development is a commit on `choreo` `main` followed by
  a submodule bump here; controller development is a `policy_id` promotion. Neither runs in
  this tree.

## Pins

Submodule commits are the pins. `agentic-compiler pins` prints them with the `choreoir`
version and whether `nvcc` / `ccec` were found. Bumping a submodule is a commit here, and
the drift tests (`tests/test_drift.py`) must be re-read when it happens.

Git: no PRs. Content batches go on `claude/*` / `chatgpt/*` branches, are argued in
[`STATUS.md`](STATUS.md), and are squash-merged to `main` on two-agent agreement — the same
debate-then-merge protocol as the survey and the submodules. See [`AGENTS.md`](AGENTS.md).
