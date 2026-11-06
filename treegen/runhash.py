"""Digests of what a run produced, to show two runs are the same tree.

output_digest covers every yearly stat and the final tree.  scored_digest covers the
stats the scorecard and the screen read, and the final tree, so it holds with lean
mode on or off."""
from __future__ import annotations

import hashlib
import json

# What the scorecard and the sensitivity screen read, plus the values growth itself
# reads back from its yearly stats.
SCORED_KEYS = ("year", "height_m", "dbh_cm", "crown_width_m", "crown_width_x_m", "crown_width_y_m",
               "crown_projected_diameter_m", "crown_base_height_m", "crown_ratio", "lowest_live_branch_m",
               "leaf_area_m2", "lai", "stand_spacing_m", "subcanopy_light_pct", "subcanopy_diffuse_light_pct",
               "water", "carbon", "apical_control", "reiterated_limbs", "loss_of_dominance_year",
               "living_internodes", "living_spurs", "leaves")


def _json(o) -> bytes:
    return json.dumps(o, sort_keys=True, default=lambda v: v.tolist() if hasattr(v, "tolist") else str(v)).encode()


def _tree_arrays(h, model) -> None:
    for tree in (model.tree, model.roots.tree if model.roots is not None else None):
        if tree is None:
            continue
        for name in ("pos", "radius", "parent", "death"):
            h.update(getattr(tree, name)[:tree.n].tobytes())


def output_digest(model) -> str:
    h = hashlib.sha256()
    h.update(_json(model.stats))
    _tree_arrays(h, model)
    return h.hexdigest()


def scored_digest(model) -> str:
    h = hashlib.sha256()
    h.update(_json([{k: s.get(k) for k in SCORED_KEYS} for s in model.stats]))
    _tree_arrays(h, model)
    return h.hexdigest()
