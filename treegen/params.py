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


def option_values(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Every on/off switch (a boolean) and every ``stage`` selector in a
    parameter tree, by dotted path, e.g. {"light.woody_shade.enabled": True,
    "pipe_model.stem_theory.stage": 2}."""
    out: dict[str, Any] = {}
    items = vars(obj).items() if isinstance(obj, SimpleNamespace) else obj.items() if isinstance(obj, dict) else ()
    for k, v in items:
        key = f"{prefix}{k}"
        if isinstance(v, bool):
            out[key] = v
        elif k == "stage" and isinstance(v, int):
            out[key] = v
        elif isinstance(v, (SimpleNamespace, dict)):
            out.update(option_values(v, key + "."))
    return out


def run_manifest(species: str | Path, environment: str | Path, sp: SimpleNamespace) -> tuple[dict, dict]:
    """What a run was made from: git commit (and whether tracked files had
    uncommitted changes), the species and environment files with their
    SHA-256, and every option switched on.  Returns (manifest, options),
    options being option_values(sp) of the parameters actually used."""
    import hashlib
    import subprocess

    def git(*a):
        p = subprocess.run(["git", *a], cwd=str(ROOT), capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else None

    def file_info(name, directory):
        p = _resolve(name, directory)
        try:
            shown = str(p.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
        except ValueError:
            shown = str(p)
        return shown, hashlib.sha256(p.read_bytes()).hexdigest()

    sp_file, sp_hash = file_info(species, SPECIES_DIR)
    env_file, env_hash = file_info(environment, ENVIRONMENT_DIR)
    status = git("status", "--porcelain", "--untracked-files=no")
    options = option_values(sp)
    manifest = {
        "git_commit": git("rev-parse", "HEAD"),
        "git_tracked_changes": None if status is None else bool(status),
        "species_file": sp_file,
        "species_sha256": sp_hash,
        "environment_file": env_file,
        "environment_sha256": env_hash,
        "options_on": sorted(k if v is True else f"{k}={v}" for k, v in options.items() if v not in (False, 0)),
    }
    return manifest, options


def load_yaml(name_or_path: str | Path, directory: Path) -> tuple[SimpleNamespace, dict]:
    path = _resolve(name_or_path, directory)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return to_namespace(raw), raw


def load_species(name_or_path: str | Path) -> tuple[SimpleNamespace, dict]:
    return load_yaml(name_or_path, SPECIES_DIR)


def load_environment(name_or_path: str | Path) -> tuple[SimpleNamespace, dict]:
    return load_yaml(name_or_path, ENVIRONMENT_DIR)
