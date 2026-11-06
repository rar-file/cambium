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
import os
import pickle
from pathlib import Path


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


def set_values(species, items) -> None:
    """Apply "dotted.key=JSON" overrides to a parameter namespace."""
    for item in items:
        key, val = item.split("=", 1)
        obj = species
        parts = key.split(".")
        for part in parts[:-1]:
            obj = getattr(obj, part)
        if not hasattr(obj, parts[-1]):
            raise KeyError(f"no such parameter: {key}")
        setattr(obj, parts[-1], json.loads(val))
