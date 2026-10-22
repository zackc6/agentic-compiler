"""Where the contract lives and how it is checked.

Lintel is the source of truth for schema *field names*; Choreo for Kernel *encoding*.
This module reads both submodules in place. Nothing is copied.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTEL_DIR = REPO_ROOT / "lintel"
CHOREO_DIR = REPO_ROOT / "choreo"
SCHEMA_DIR = LINTEL_DIR / "schemas"
CASES_DIR = REPO_ROOT / "cases"

SCHEMAS = {
    "session-event.v0": "session-event.v0.schema.json",
    "admit-record.v0": "admit-record.v0.schema.json",
    "cache-key.v0": "cache-key.v0.schema.json",
    "adapter-proposal.v0": "adapter-proposal.v0.schema.json",
}


class ContractError(RuntimeError):
    """A submodule is missing or a document does not validate."""


def require_submodules() -> None:
    missing = [p.name for p in (LINTEL_DIR, CHOREO_DIR) if not (p / "README.md").exists()]
    if missing:
        raise ContractError(
            "submodule(s) not checked out: "
            + ", ".join(missing)
            + ". Run: git submodule update --init --recursive"
        )


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    require_submodules()
    path = SCHEMA_DIR / SCHEMAS[name]
    return json.loads(path.read_text())


def validate(doc: Any, schema_name: str) -> list[str]:
    """Return jsonschema error messages (empty list = valid). Never raises on invalid input."""
    schema = load_schema(schema_name)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    out = []
    for e in errs:
        where = "/".join(str(p) for p in e.absolute_path) or "<root>"
        out.append(f"{where}: {e.message}")
    return out


def canonical_json(doc: Any) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_doc(doc: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(doc).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _git_head(path: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


@dataclass(frozen=True)
class Pins:
    """What this walk ran against. Written into every session.start event."""

    lintel_commit: str
    choreo_commit: str
    choreoir_version: str
    compiler_ver: str  # Kernel.compiler_ver that Choreo stamps (e.g. "0.1.13")
    nvcc: str | None
    ccec: str | None

    def as_dict(self) -> dict:
        return {
            "lintel_commit": self.lintel_commit,
            "choreo_commit": self.choreo_commit,
            "choreoir_version": self.choreoir_version,
            "compiler_ver": self.compiler_ver,
            "nvcc": self.nvcc,
            "ccec": self.ccec,
        }


def pins() -> Pins:
    require_submodules()
    import choreoir

    nvcc = choreoir.find_nvcc()
    ccec = choreoir.find_ccec()
    return Pins(
        lintel_commit=_git_head(LINTEL_DIR),
        choreo_commit=_git_head(CHOREO_DIR),
        choreoir_version=choreoir.__version__,
        compiler_ver=choreoir.COMPILER_VER,
        nvcc=str(nvcc) if nvcc else None,
        ccec=str(ccec) if ccec else None,
    )
