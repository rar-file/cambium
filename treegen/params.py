"""Loading of species and environment parameter files (YAML).

Nothing species-specific is defined in code: every value used by the growth
model comes from ``species/<name>.yaml``; light settings come from
``environments/<name>.yaml``.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPECIES_DIR = ROOT / "species"
ENVIRONMENT_DIR = ROOT / "environments"


def to_namespace(obj: Any) -> Any:
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [to_namespace(v) for v in obj]
    return obj


def _resolve(name_or_path: str | Path, directory: Path) -> Path:
    p = Path(name_or_path)
    if p.suffix in (".yaml", ".yml") and p.exists():
        return p
    candidate = directory / f"{name_or_path}.yaml"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"no parameter file for {name_or_path!r} in {directory}")


def load_yaml(name_or_path: str | Path, directory: Path) -> tuple[SimpleNamespace, dict]:
    path = _resolve(name_or_path, directory)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return to_namespace(raw), raw


def load_species(name_or_path: str | Path) -> tuple[SimpleNamespace, dict]:
    return load_yaml(name_or_path, SPECIES_DIR)


def load_environment(name_or_path: str | Path) -> tuple[SimpleNamespace, dict]:
    return load_yaml(name_or_path, ENVIRONMENT_DIR)
