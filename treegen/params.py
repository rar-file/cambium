"""Loading of species and environment parameter files (YAML).

Nothing species-specific is defined in code: every value used by the growth
model comes from ``species/<name>.yaml``; light settings come from
``environments/<name>.yaml``.

A file may hold only the names in ``treegen/names.py``, rows of lists of records included: a
misspelt one is refused, with the nearest real names, instead of being ignored while the code reads
its fallback.
"""
from __future__ import annotations

import difflib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

from . import machine, names, threads

ROOT = Path(__file__).resolve().parent.parent
SPECIES_DIR = ROOT / "species"
ENVIRONMENT_DIR = ROOT / "environments"


class SettingError(KeyError, ValueError):
    """A setting name the model doesn't have, or a value it can't read.  A KeyError, as a --set of a
    missing name always was, and a ValueError, as every other bad input is."""

    def __str__(self) -> str:
        return str(self.args[0]) if self.args else ""


def to_namespace(obj: Any) -> Any:
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [to_namespace(v) for v in obj]
    return obj


def _items(obj: Any) -> dict:
    return vars(obj) if isinstance(obj, SimpleNamespace) else obj if isinstance(obj, dict) else {}


def setting_names(obj: Any, prefix: str = "") -> set[str]:
    """Every dotted name in a parameter tree (a dict or a namespace), blocks as well as values.  A map
    in names.FREE_MAPS (appearance.provenance) is one value: its keys are data, not settings.  Rows
    of a list of records aren't looked into here (row_names)."""
    out = set()
    for k, v in _items(obj).items():
        out.add(prefix + str(k))
        if (isinstance(v, (dict, SimpleNamespace)) and prefix + str(k) not in names.FREE_MAPS):
            out |= setting_names(v, prefix + str(k) + ".")
    return out


def blocks_of(known) -> set[str]:
    """The blocks above a set of dotted value names."""
    return {k.rsplit(".", i)[0] for k in known for i in range(1, k.count(".") + 1)}


def nearest(name: str, known) -> str:
    """The real names closest to a misspelt one, for an error message."""
    close = difflib.get_close_matches(name, sorted(known), n=3, cutoff=0.6)
    return f"nearest: {', '.join(close)}" if close else "no setting has a name close to it"


def check_row(row: Any, key: str, need: frozenset, may: frozenset, where: str) -> None:
    """One row of a list of records: a record, holding every name in ``need`` and only names in ``may``."""
    if not isinstance(row, (dict, SimpleNamespace)):
        raise SettingError(f"{where}: {key} is a list of records, e.g. {{{', '.join(f'{n!r}: ...' for n in sorted(need))}}}, not {row!r}")
    have = setting_names(row)
    known = may | blocks_of(may)
    for name in sorted(have):
        if name not in known:
            raise SettingError(f"{where}: unknown name {name!r} in a row of {key}; {nearest(name, known)}")
    missing = sorted(need - have)
    if missing:
        raise SettingError(f"{where}: a row of {key} must hold {', '.join(missing)}")


def check_names(raw: Any, known: frozenset, where: str) -> None:
    """Refuse what a file can't mean (SettingError): a name the model doesn't have, named with the
    nearest real ones; a dot in a name, outside names.FREE_MAPS; a single value where a block of
    settings belongs, or a block where a single value does; and a row of a list of records (names.ROWS)
    with a name it can't hold or without one it must."""
    blocks = blocks_of(known)

    def walk(node: dict, prefix: str) -> None:
        for k, v in node.items():
            name = prefix + str(k)
            if "." in str(k):
                raise SettingError(f"{where}: {name!r} has a dot in its name; write each part as its own block"
                                   f" (only {', '.join(sorted(names.FREE_MAPS))} is keyed by dotted names)")
            if name not in known and name not in blocks:
                raise SettingError(f"{where}: unknown setting {name!r}; {nearest(name, known | blocks)}"
                                   " (a new setting is added to treegen/names.py)")
            if name in blocks:
                if isinstance(v, dict):
                    walk(v, name + ".")
                elif v is not None:      # an empty block (the template's) holds nothing
                    raise SettingError(f"{where}: {name} is a block of settings, not one value ({v!r})")
            elif name in names.ROWS:
                if not isinstance(v, list):
                    raise SettingError(f"{where}: {name} is a list of records, not {v!r}")
                for row in v:
                    check_row(row, name, *names.ROWS[name], where)
            elif isinstance(v, dict) and name not in names.FREE_MAPS:
                raise SettingError(f"{where}: {name} is one value, not a block of settings")
            elif isinstance(v, list) and any(isinstance(x, dict) for x in v):
                raise SettingError(f"{where}: {name} is not a list of records (names.ROWS)")

    if not isinstance(raw, dict):
        raise SettingError(f"{where}: the file holds no blocks of settings")
    walk(raw, "")


def _resolve(name_or_path: str | Path, directory: Path) -> Path:
    p = Path(name_or_path)
    if p.suffix in (".yaml", ".yml") and p.exists():
        return p
    candidate = directory / f"{name_or_path}.yaml"
    if candidate.exists():
        return candidate
    known = ", ".join(sorted(f.stem for f in directory.glob("*.yaml") if not f.stem.startswith("_")))
    raise FileNotFoundError(f"no parameter file for {str(name_or_path)!r} in {directory.name}/; known: {known}, or a path to a .yaml file")


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


def uncommitted_fingerprint(root: Path = ROOT) -> dict:
    """A fingerprint of the code changes not yet committed, so a run made before
    its commit can still be identified: SHA-256 of `git diff HEAD` plus the names
    and contents of untracked files, and the list of those files.  Ignored files
    (run outputs, scratch work) don't count.  A clean tree gives None."""
    import hashlib
    import subprocess

    def git(*a) -> bytes | None:
        try:
            p = subprocess.run(["git", *a], cwd=str(root), capture_output=True)
        except FileNotFoundError:   # git isn't installed (a second PC, say)
            return None
        return p.stdout if p.returncode == 0 else None

    diff = git("diff", "HEAD", "--binary")
    changed = git("diff", "HEAD", "--name-only")
    untracked = git("ls-files", "--others", "--exclude-standard")
    if diff is None or changed is None or untracked is None:
        return {"uncommitted_sha256": None, "uncommitted_files": None}
    new_files = sorted(untracked.decode("utf-8", "replace").split("\n")[:-1]) if untracked else []
    files = sorted(set(changed.decode("utf-8", "replace").split("\n")[:-1]) | set(new_files))
    if not files:
        return {"uncommitted_sha256": None, "uncommitted_files": []}
    h = hashlib.sha256(diff)
    for name in new_files:
        h.update(name.encode("utf-8"))
        p = Path(root) / name
        if p.is_file():
            h.update(p.read_bytes())
    return {"uncommitted_sha256": h.hexdigest(), "uncommitted_files": files}


def run_manifest(species: str | Path, environment: str | Path, sp: SimpleNamespace) -> tuple[dict, dict]:
    """What a run was made from: git commit (and whether tracked files had
    uncommitted changes, with a fingerprint of those changes), the species and
    environment files with their SHA-256, and every option switched on.  Returns
    (manifest, options), options being option_values(sp) of the parameters
    actually used."""
    import hashlib
    import subprocess

    def git(*a):
        try:
            p = subprocess.run(["git", *a], cwd=str(ROOT), capture_output=True, text=True)
        except FileNotFoundError:   # git isn't installed (a second PC, say)
            return None
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
        # the node gets the code at a fixed commit, without git, with that commit in a file
        "git_commit": git("rev-parse", "HEAD") or ((ROOT / "COMMIT").read_text().strip() if (ROOT / "COMMIT").exists() else None),
        "git_tracked_changes": None if status is None else bool(status),
        **uncommitted_fingerprint(),
        # every comparison runs entirely on one machine (PROTOCOL.md section 6)
        "machine": machine.describe_machine(),
        "math_threads": threads.actual_threads(),
        "math_libraries": threads.library_versions(),
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
    """A species file's values.  Its names must be in names.SPECIES; a value the file leaves out
    that names.DEFAULTS holds gets that default, the value the code would use in its place."""
    sp, raw = load_yaml(name_or_path, SPECIES_DIR)
    check_names(raw, names.SPECIES, _resolve(name_or_path, SPECIES_DIR).name)
    for key, value in names.DEFAULTS.items():
        *path, last = key.split(".")
        holder = sp
        for part in path:
            holder = getattr(holder, part, None)
        if holder is not None and not hasattr(holder, last):
            setattr(holder, last, value)
    return sp, raw


def load_environment(name_or_path: str | Path) -> tuple[SimpleNamespace, dict]:
    env, raw = load_yaml(name_or_path, ENVIRONMENT_DIR)
    check_names(raw, names.ENVIRONMENT, _resolve(name_or_path, ENVIRONMENT_DIR).name)
    return env, raw
