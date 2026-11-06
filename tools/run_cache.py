"""Never rerun a finished case (campaign P0, A3).

A case's key is a SHA-256 of everything its result depends on: the model code, every
parameter actually used, the seed, the run's length, lean or not, the maths-library
thread count and versions, and the kernel OpenBLAS picked on this CPU.  If any of
those differ the key differs and the case runs.  Results live in out/cache/.

Golden runs never use this: their point is to run again.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from treegen.machine import describe_machine  # noqa: E402

CACHE = ROOT / "out" / "cache"


def plain(o):
    """Parameters as plain JSON-ready data."""
    if isinstance(o, SimpleNamespace):
        return {k: plain(v) for k, v in vars(o).items()}
    if isinstance(o, dict):
        return {str(k): plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [plain(v) for v in o]
    if hasattr(o, "item"):
        return o.item()
    return o


def code_version(root: Path = ROOT) -> str:
    """SHA-256 of the code that decides what a run produces.  Line endings count as
    written; a change to a comment changes the key, which only costs a rerun."""
    h = hashlib.sha256()
    for f in sorted((root / "treegen").glob("*.py")) + [root / "cli.py"]:
        h.update(f.relative_to(root).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def settings() -> dict:
    m = describe_machine()
    return {"math_threads": m["math_threads"], "math_libraries": m["math_libraries"],
            "numpy_openblas_kernel": m["numpy_openblas_kernel"], "scipy_openblas_kernel": m["scipy_openblas_kernel"]}


def case_key(kind: str, species, environment, seed: int, years: int, lean: bool, code: str | None = None,
             machine: dict | None = None) -> str:
    payload = {"kind": kind, "species": plain(species), "environment": plain(environment), "seed": int(seed),
               "years": int(years), "lean": bool(lean), "code": code or code_version(), "settings": machine or settings()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Cache:
    def __init__(self, root: Path = CACHE):
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict | None:
        p = self._path(key)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def put(self, key: str, result: dict) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(result), encoding="utf-8")
        tmp.replace(p)
