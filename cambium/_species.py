"""The species Cambium can grow: one parameter file each in ``species/``."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import _engine

# short names on the command line and in grow(); each species' common name also works, with _ for spaces
ALIASES = {"birch": "betula_pendula"}
LABELS = ("sourced", "DERIVED", "TUNED", "VERIFY")


@dataclass(frozen=True)
class Species:
    """A species file and what its values rest on.  ``labels`` counts the values by where they came
    from (``reference/<name>/labels.yaml``): sourced, DERIVED, TUNED or VERIFY."""

    name: str
    common_name: str
    scientific_name: str
    aliases: tuple = ()
    labels: dict = field(default_factory=dict)
    file: Path | None = None

    def __str__(self) -> str:
        return self.name


def _aliases() -> dict:
    out = dict(ALIASES)
    for f in sorted(_engine.SPECIES_DIR.glob("*.yaml")):
        if f.stem.startswith("_"):
            continue
        common = _header(f).get("common_name")
        if common:
            out.setdefault(str(common).lower().replace(" ", "_"), f.stem)
    return out


def _header(path: Path) -> dict:
    """The ``species:`` block, read without loading the whole file."""
    lines, inside = [], False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("species:"):
                inside = True
            elif inside and line.strip() and not line.startswith((" ", "#")):
                break
            if inside:
                lines.append(line)
    return (yaml.safe_load("".join(lines)) or {}).get("species") or {}


def _label_counts(name: str) -> dict:
    p = _engine.REFERENCE_DIR / name / "labels.yaml"
    if not p.is_file():
        return {}
    with open(p, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    counts = dict.fromkeys(LABELS, 0)
    for entry in raw.values():
        if isinstance(entry, dict) and entry.get("status") in counts:
            counts[entry["status"]] += 1
    return counts


def species_file(name: str | Path) -> Path:
    """The parameter file for a species name, alias ("birch") or path to a .yaml file."""
    return _engine._resolve(name, _engine.SPECIES_DIR, "species", _aliases())


def species() -> list[Species]:
    """Every species this installation can grow."""
    aliases = _aliases()
    out = []
    for f in sorted(_engine.SPECIES_DIR.glob("*.yaml")):
        if f.stem.startswith("_"):
            continue
        head = _header(f)
        out.append(Species(name=f.stem, common_name=str(head.get("common_name", "")),
                           scientific_name=str(head.get("scientific_name", "")),
                           aliases=tuple(sorted(a for a, n in aliases.items() if n == f.stem)),
                           labels=_label_counts(f.stem), file=f))
    return out
