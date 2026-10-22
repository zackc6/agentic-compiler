# Setup

## Requirements

* Python 3.11+ (3.13 tested), `git`.
* Optional, for a real NVIDIA freeze: `nvcc` on `PATH`, or `CHOREO_FETCH_NVCC=1` to let
  `choreoir.toolchain.ensure_nvcc()` fetch the official redist into `~/.local/cuda-nvcc`
  (no GPU needed to *compile* a cubin; a GPU is needed to *time* it).
* Optional, for a real Ascend freeze: CANN with `ccec` (not a public redist).

## Install

```bash
git clone --recurse-submodules https://github.com/zackc6/agentic-compiler
cd agentic-compiler
./scripts/setup.sh
```

`setup.sh` does three things, in order, and prints the pins at the end:

1. `git submodule update --init --recursive` — `lintel/` and `choreo/` at their pinned commits.
2. `pip install -e './choreo[dev]'` — `choreoir` **from the submodule**, never from PyPI.
   `tests/test_setup.py::test_choreoir_is_the_submodule` fails if some other `choreoir` wins
   the import; that is intentional.
3. `pip install -e '.[dev]'` — this package and the `agentic-compiler` CLI.

If you already cloned without `--recurse-submodules`, step 1 fixes it.

## Verify

```bash
agentic-compiler pins
# {"lintel_commit": "8b4a7a9…", "choreo_commit": "f683e5d…", "choreoir_version": "0.1.13",
#  "compiler_ver": "0.1.13", "nvcc": null, "ccec": null}
python3 -m pytest
agentic-compiler run accept/copy_nvidia.case.json -o out
agentic-compiler check-contract        # Choreo's consume-check against the Lintel pin (docs/DRIFT.md)
```

## Bumping a submodule

```bash
git -C choreo fetch && git -C choreo checkout origin/main
./scripts/setup.sh && python3 -m pytest
git add choreo && git commit -m "pin choreo <sha>: <what changed>"
```

A `choreoir` version bump changes `compiler_ver`, so every `%k` changes: that is the
compiler-development loop landing, and the store from older walks is stale by design.
Re-read `docs/DRIFT.md` and `tests/test_drift.py` on every bump of either submodule.

## Layout

```text
agentic_compiler/   the walk (loop), session stream, admit records, store/serve, measurement seam, CLI
cases/              accept/ · reject/ · search/ — *.case.json, see docs/TESTING.md
tests/              pytest: setup, one walk per case, serve, drift, device (skips without toolchain)
docs/               this file, TESTING, PERFORMANCE, SURVEY_BASIS, DRIFT
perf/               results/ (empty until a device clock exists) — schema in docs/PERFORMANCE.md
scripts/setup.sh
lintel/  choreo/    submodules (read in place; nothing is copied out of them)
```
