"""Save a single tree's whole state at an age and carry on from it later (campaign
P0, A4).  The state includes every random-number generator, so a run saved at 30 and
resumed produces the same output as a straight run to 60 (tests/test_checkpoint.py,
tools/proof_checkpoint.py).  Plots have their own checkpoints (Plot.checkpoint).

A scenario changes values after resuming (set_values).  It only affects what the
model reads during a year: thinning, damage events, soil-water options and the like.
Values copied when the model was built, such as the voxel size or the pipe exponent,
keep their old value, so change those from the start of a run instead.
"""
from __future__ import annotations

import json
import math
import os
import pickle
from pathlib import Path
from types import SimpleNamespace

from . import names
from .params import SettingError, check_row, nearest, setting_names, to_namespace


def save_model(model, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    field, view = getattr(model, "_field", None), getattr(model, "_plot_view", None)
    model._field = model._plot_view = None   # one season's light; nothing reads it next year
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "wb") as f:
            pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)
    finally:
        model._field, model._plot_view = field, view
    return path


def load_model(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _kind(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, (bool, int, float)):   # one kind: the code reads true as 1 (crown_frame.twigs_browsed=true)
        return "a number or true/false"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "a list"
    return "a record"


def _finite(v, key: str) -> None:
    if isinstance(v, float) and not math.isfinite(v):
        raise SettingError(f"--set {key}: {v} isn't a number a run can use")
    for x in (v.values() if isinstance(v, dict) else v if isinstance(v, list) else ()):
        _finite(x, key)


def _check(current, value, key: str) -> None:
    """Refuse a value that can't stand where ``current`` is: a name a record gives that the block
    doesn't hold, a row of a list of records with a name it can't hold or without one it must
    (names.ROWS), or a value of another kind (text for a number, a number for a list, one value for a
    block).  Null is always taken: the code reads it as "off" or its own fallback (tests set many
    values to null), and a number and true/false are one kind, as Python reads them."""
    _finite(value, key)
    if isinstance(current, SimpleNamespace) and key not in names.FREE_MAPS:
        if not isinstance(value, dict):
            raise SettingError(f"--set {key}: a block of settings takes a record, e.g. {key}={{\"name\": value}},"
                               f" or set one value in it as {key}.name=value; not {_kind(value)}")
        for k, v in value.items():
            if not hasattr(current, k):
                raise SettingError(f"--set {key}: no such parameter in it: {k}; "
                                   f"{nearest(f'{key}.{k}', {f'{key}.{n}' for n in setting_names(current)})}")
            _check(getattr(current, k), v, f"{key}.{k}")
        return
    rows = names.ROWS.get(key)
    if rows is None and isinstance(current, list) and current and all(isinstance(r, SimpleNamespace) for r in current):
        have = [setting_names(r) for r in current]     # a list of records names.ROWS doesn't list: its own rows' names
        rows = (frozenset(set.intersection(*have)), frozenset(set.union(*have)))
    if rows is not None:
        if not isinstance(value, list):
            raise SettingError(f"--set {key}: a list of records, e.g. [{{...}}, {{...}}], not {_kind(value)}")
        for row in value:
            check_row(row, key, *rows, "--set")
        return
    if value is not None and current is not None and _kind(value) != _kind(current):
        raise SettingError(f"--set {key}: takes {_kind(current)}, as the species file has it, not {_kind(value)}")


def _apply(holder, name: str, current, value, key: str) -> None:
    """A record merges into its block, name by name; anything else replaces the value."""
    if isinstance(current, SimpleNamespace) and key not in names.FREE_MAPS:
        for k, v in value.items():
            _apply(current, k, getattr(current, k), v, f"{key}.{k}")
    else:
        setattr(holder, name, to_namespace(value))


def set_values(species, items) -> None:
    """Apply "dotted.key=JSON" overrides to a parameter namespace.  A name it doesn't hold is refused,
    with the nearest real ones, and so is a value of another kind than the one there (_check).

    A value is read as the species file's would be, so a row of a list of records (stand.thinning) is
    read by name, as the model reads it.  A list replaces the whole list.  A record given for a block
    merges into it: ``roots.paid={"enabled": true}`` switches the paid roots on with the block's other
    values as they were, the same as ``roots.paid.enabled=true``."""
    for item in items:
        key, eq, val = str(item).partition("=")
        if not eq or not key:
            raise SettingError(f"--set {item!r}: write it as KEY=JSON, e.g. resource.alpha=4.5")
        obj = species
        parts = key.split(".")
        for part in parts:
            if not isinstance(obj, SimpleNamespace) or not hasattr(obj, part):
                raise SettingError(f"no such parameter: {key}; {nearest(key, setting_names(species))}")
            holder, obj = obj, getattr(obj, part)
        try:
            value = json.loads(val)
        except ValueError:
            raise SettingError(f"--set {key}: {val!r} isn't JSON; write 4.5, true, \"text\" or [1, 2]") from None
        _check(obj, value, key)
        _apply(holder, parts[-1], obj, value, key)
