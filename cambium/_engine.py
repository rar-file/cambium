"""Where the engine's data and scripts are: in a source checkout, or in an installed wheel.

In a checkout, ``species/``, ``environments/``, ``reference/``, ``cli.py`` and ``tools/`` sit next to
``cambium/`` and are used where they are.  In a wheel, the build copies them into the package
(``cambium/data/`` and ``cambium/_scripts/``; see ``[tool.hatch.build.targets.wheel.force-include]`` in
pyproject.toml), so an installed Cambium runs the same files a checkout runs.

``cli.py`` and the tools are scripts, not package modules: each puts the project's folders on
``sys.path`` and imports its neighbours by plain name (``import cli``).  ``load()`` runs one under a
private module name, hands it the neighbours it imports, and puts ``sys.path`` and ``sys.modules`` back
as they were, so nothing named ``cli`` is left behind for other code to find.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from functools import cache
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
_CHECKOUT = PACKAGE.parent
# a source checkout (or an editable install of one) has the engine's files beside the package
SOURCE = all((_CHECKOUT / p).exists() for p in ("cli.py", "treegen/params.py", "species", "environments"))
DATA = _CHECKOUT if SOURCE else PACKAGE / "data"
SPECIES_DIR = DATA / "species"
ENVIRONMENT_DIR = DATA / "environments"
REFERENCE_DIR = DATA / "reference"

# script -> (its file in a checkout, the neighbours it imports by plain name)
_SCRIPTS = {
    "cli": ("cli.py", ()),
    "tree_list": ("tools/tree_list.py", ()),
    "game_export": ("tools/game_export.py", ("cli",)),
}


def script_path(name: str) -> Path:
    rel = _SCRIPTS[name][0]
    return _CHECKOUT / rel if SOURCE else PACKAGE / "_scripts" / Path(rel).name


@cache
def load(name: str):
    """The engine script ``name`` ("cli", "tree_list" or "game_export") as a module."""
    import treegen  # noqa: F401  (first: it sets the maths libraries to one thread before they load)

    neighbours = {n: load(n) for n in _SCRIPTS[name][1]}
    spec = importlib.util.spec_from_file_location(f"cambium._scripts.{name}", script_path(name))
    module = importlib.util.module_from_spec(spec)
    saved_path = list(sys.path)
    saved = {n: sys.modules.get(n) for n in neighbours}
    sys.modules.update(neighbours)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
    finally:
        sys.path[:] = saved_path
        for n, m in saved.items():
            if m is None:
                sys.modules.pop(n, None)
            else:
                sys.modules[n] = m
    return module


def _resolve(name: str | Path, directory: Path, kind: str, aliases: dict | None = None) -> Path:
    p = Path(name)
    if p.suffix in (".yaml", ".yml"):
        if p.is_file():
            return p.resolve()
        raise FileNotFoundError(f"no {kind} file {str(p)!r}")
    key = str(name).strip()
    key = (aliases or {}).get(key.lower(), key)
    f = directory / f"{key}.yaml"
    if f.is_file() and not key.startswith("_"):
        return f
    known = ", ".join(sorted(x.stem for x in directory.glob("*.yaml") if not x.stem.startswith("_")))
    raise ValueError(f"unknown {kind} {str(name)!r}; known: {known}, or a path to a .yaml file")


def environment_file(name: str | Path) -> Path:
    return _resolve(name, ENVIRONMENT_DIR, "environment")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
