"""Serve: ``lookup(cache_key_digest)`` → frozen artifact, else fallback.

No optimizer model on this path. The store is content-addressed by the Lintel
``cache_key_digest`` (sha256 of canonical cache-key.v0 JSON). The Kernel AST and the
sink output are the *value* at that address, never part of the key.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from choreoir import pin_doc_errors

from .contract import ContractError, sha256_file


@dataclass(frozen=True)
class Served:
    hit: bool
    cache_key_digest: str
    artifact_path: Path | None
    artifact_kind: str | None
    launch: dict | None
    fallback: str | None  # "classical" | "last_good" when hit is False


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _slot(self, digest: str) -> Path:
        return self.root / digest.replace("sha256:", "")

    def freeze(self, pin: dict, artifact_path: Path, kernel_json: dict) -> Path:
        errs = pin_doc_errors(pin)
        if errs:
            raise ContractError(f"refusing to freeze an invalid pin: {errs}")
        slot = self._slot(pin["cache_key_digest"])
        slot.mkdir(parents=True, exist_ok=True)
        dest = slot / Path(artifact_path).name
        shutil.copyfile(artifact_path, dest)
        pin = dict(pin)
        pin["artifact_uri"] = dest.name
        pin["artifact_file_sha256"] = sha256_file(dest)
        (slot / "pin.json").write_text(json.dumps(pin, indent=2) + "\n")
        (slot / "kernel.json").write_text(json.dumps(kernel_json, indent=2) + "\n")
        return slot

    def lookup(self, digest: str) -> dict | None:
        p = self._slot(digest) / "pin.json"
        if not p.exists():
            return None
        return json.loads(p.read_text())


def serve(store: Store, digest: str, *, fallback: str = "classical") -> Served:
    pin = store.lookup(digest)
    if pin is None:
        return Served(False, digest, None, None, None, fallback)
    slot = store._slot(digest)
    art = slot / pin["artifact_uri"]
    if not art.exists() or sha256_file(art) != pin["artifact_file_sha256"]:
        # A tampered or missing artifact is a miss, not a crash: serve the fallback.
        return Served(False, digest, None, None, None, fallback)
    return Served(True, digest, art, pin.get("artifact_kind"), pin.get("launch"), None)
