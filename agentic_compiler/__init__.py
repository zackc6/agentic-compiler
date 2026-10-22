"""agentic-compiler: end-to-end walk of Lintel (control plane) over Choreo IR (data plane).

This package owns nothing that the two submodules own:

* ``lintel/``  — the written contract: schemas for session events, admit records,
  cache keys, adapter proposals. Field names come from there.
* ``choreo/``  — the kernel-schedule compiler: AST, W/L/S/V admit, CPU interpreter,
  CUDA C++ / CCE sinks, ``nvcc`` / ``ccec`` toolchain. Kernel encoding comes from there.

What lives here is the *walk*: propose → gate → measure → freeze-or-fallback → serve,
written as session events and admit records that validate against the Lintel schemas,
with the Choreo compiler pinned by submodule commit. See ``docs/`` for the survey basis,
setup, tests, and the (not yet measured) performance table.
"""

from .contract import Pins, pins
from .loop import Case, Candidate, WalkResult, load_case, walk
from .serve import Store, serve

__all__ = [
    "Case",
    "Candidate",
    "Pins",
    "Store",
    "WalkResult",
    "load_case",
    "pins",
    "serve",
    "walk",
]

__version__ = "0.1.0"
