"""The tree agent's one-pass measure: one stand tree per seed, everything the brief asks for from one run.

    python tools/tree_table.py run --label X --seeds 8 [--first-seed 1] [--years 60] [--set key=json ...]
    python tools/tree_table.py table X Y            # means over seeds at 20, 30, 40, 50, 60, against the targets
    python tools/tree_table.py seeds X              # the same, seed by seed: a mean can hide outliers
    python tools/tree_table.py fall X Y             # twigs and branches shed, crown base, lowest branch, crown ratio
    python tools/tree_table.py driver X             # what held the leader back, year by year, across seeds
    python tools/tree_table.py height X Y           # where the leaf area and crown width peak by height, beside Hagemeier & Leuschner 2019a
    python tools/tree_table.py limbs X Y            # limb sizes, forks, the crown's diameter as Dubois 2021 measured it, and the carbon lost

Writes out/bench/ensemble/<label>/<seed>_stand/, the same stats.json an ensemble writes (so tools/scorecard.py,
tools/m3_alternation.py and tools/m3_crown_compare.py read it), plus tree.json: new shoot length each year, wood and
first-order branches at set ages, and every shedding event read back from the nodes' death years.  It only reads the
model, so it changes no number: tests/test_tree_table.py.

Sources for the comparison columns are the tools' own: Repola 2008 (tools/m3_wood.py), Evo TLS 2024
(tools/m3_crown_compare.py), Lintunen 2013 (tools/m3_branches.py).  Those three are for a look, not a verdict.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import Job, run_batch  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
AGES = (20, 30, 40, 50, 60)
SNAPSHOT_EVERY = 5
DENSITY = 530.0
WINDOWS = ((5, 14), (15, 19), (20, 39), (40, 60))
LINTUNEN_M, LINTUNEN_PER_10 = 1.02, 5.2
LAI_FLOOR, LIGHT_BAND = 3.6, (6.4, 19.8)
DENSE_CROWN_RATIO = (0.30, 0.45)    # dense unmanaged plots, ages 11-22: not a stand-tree target; shown as information
REPOLA_CROWN_RATIO = (0.29, 0.96)   # Repola 2008 Table 2, single sample trees, mean 0.58; information in the target file
CROWN_RATIO_FLOOR = 0.50            # Hynynen 2010: a recommendation for managed crop trees; information in the target file


def snapshot(model, year: int) -> dict:
    """Wood and first-order branches now.  Same definitions as tools/m3_wood.py and tools/m3_branches.py."""
    import numpy as np

    T, s = model.tree, model.stats[-1]
    n = T.n
    alive = T.death[:n] < 0
    volume = np.where(alive, math.pi * T.radius[:n] ** 2 * T.length[:n], 0.0)
    stem_nodes = np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)
    stem_v = float(volume[stem_nodes].sum())
    total_v = float(volume.sum())
    # a first-order branch: a side axis on the stem, or on a leader that replaced it (tools/m3_branches.py uses order == 1,
    # which reads a stem that changed axis as one very long branch; it takes medians for that reason)
    on_lead = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    starts = np.nonzero(alive & T.is_lateral[:n] & ~on_lead & on_lead[np.maximum(T.parent[:n], 0)])[0]
    lengths = []
    for start in starts:
        total, node = 0.0, int(start)
        while node >= 0 and alive[node]:
            total += float(T.length[node])
            node = int(T.main_child[node])
        lengths.append(total)
    real = [x for x in lengths if x >= 0.05]
    # the crown base as the model measures it, but with limbs counted on the stem: see stats.limbs_on_leader
    leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
    crown_base_stem = lowest_stem = None
    if starts.size:
        lowest_stem = float(T.pos[T.parent[starts], 2].min())
        lv = T.basipetal(T.levels(alive), leaves)[starts]
        carrying = starts[lv >= max(5.0, float(model.sp.stats.crown_base_min_leaf_share) * float(leaves.sum()))]
        if carrying.size:
            crown_base_stem = float(T.pos[T.parent[carrying], 2].min())
    h = float(s["height_m"])
    roots = {}
    if model.roots is not None:
        R = model.roots.tree
        live = R.death[: R.n] < 0
        lc = model.sp.resource.leaf_costs
        carbon = s.get("carbon", {})
        roots = {"root_wood_kg": float(np.where(live, math.pi * R.radius[: R.n] ** 2 * R.length[: R.n], 0.0).sum()) * DENSITY,
                 "root_length_m": float(R.length[: R.n][live].sum()),
                 "fine_root_kg": float(carbon.get("leaf_dm_g", 0.0)) * float(lc.fine_root_to_leaf_mass) / 1000.0,
                 "root_share": float(s.get("water", {}).get("root_share", 0.0)),
                 "root_carbon": float(carbon.get("root", 0.0)), "fixed_carbon": float(carbon.get("fixed", 0.0))}
    return {"age": year, **roots, "shape": crown_shape(model), "d0_mm": 2000.0 * float(T.radius[0]), "stem_top_m": float(T.pos[stem_nodes[-1], 2]), "stem_m3": stem_v,
            "crown_base_stem_m": crown_base_stem, "lowest_stem_branch_m": lowest_stem,
            "crown_ratio_stem": None if crown_base_stem is None or h <= 0.0 else (h - crown_base_stem) / h, "leader_losses": len(model.leader_losses),
            "stem_kg": stem_v * DENSITY, "branch_kg": (total_v - stem_v) * DENSITY,
            "leaf_kg": float(s["carbon"].get("leaf_dm_g", 0.0)) / 1000.0, "branches": len(real),
            "mean_branch_m": statistics.fmean(real) if real else 0.0, "median_branch_m": statistics.median(real) if real else 0.0,
            "p90_branch_m": float(np.percentile(real, 90)) if real else 0.0}


def side_fill(pos, area, cell: float = 0.25) -> float:
    """The share of sky the crown blocks seen from the side, inside its own outline: leaf area into 0.25 m cells from two sides,
    each cell blocking 1 - exp(-0.5 area / cell^2) (leaves at random angles), the outline running from the lowest to the highest
    occupied cell of each row.  My own measure, for comparing settings and for a look at photos; no paper read gives it."""
    import numpy as np

    shares = []
    for axis in (0, 1):
        col = np.floor(pos[:, axis] / cell).astype(np.int64)
        row = np.floor(pos[:, 2] / cell).astype(np.int64)
        col -= col.min()
        row -= row.min()
        grid = np.zeros((int(row.max()) + 1, int(col.max()) + 1))
        np.add.at(grid, (row, col), area)
        blocked = 1.0 - np.exp(-0.5 * grid / cell ** 2)
        total, inside = 0.0, 0
        for r in range(grid.shape[0]):
            hit = np.nonzero(grid[r] > 0)[0]
            if hit.size:
                total += float(blocked[r, hit[0]: hit[-1] + 1].sum())
                inside += int(hit[-1] - hit[0] + 1)
        shares.append(total / max(inside, 1))
    return float(np.mean(shares))


def crown_shape(model) -> dict:
    """Crown shape from the living nodes, for telling a birch from a cone.  Reads only.

    widest_at: where the widest tenth of the crown sits, 0 at the crown base and 1 at the top.  Width of a tenth: twice the 95th
    percentile of its leafy nodes' distance from the stem.  width_ratio_top: the top third's mean width over the widest.
    angle_low, _mid, _up: limbs' angle from vertical at the stem, by where they sit in the crown: from their first node to the point
    0.5 m along (or their end).  tip_angle: the same from their base to their tip.
    leader_rival: in the top 20 % of the crown, the thickest limb's base diameter over the stem's diameter there; near 1, no one leader.
    tops: living tips within 0.5 m of the top, the stem's own not counted.  bare_top_m: stem above its highest limb of 0.3 m or longer.
    hang_mean, hang_p90, hang_max: hanging runs of 0.2 m or more (internodes over 30 deg below level), length of each.  hang_leaves: share of
    leaves on such runs.  lone: limbs below the height under which 5 % of the leaves sit.  gap_m: largest stretch of stem with no limb,
    between the lowest limb and the top.
    """
    import numpy as np

    T, s = model.tree, model.stats[-1]
    n = T.n
    alive = T.death[:n] < 0
    H = float(s["height_m"])
    stem = np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)
    on_lead = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    limbs = np.nonzero(alive & T.is_lateral[:n] & ~on_lead & on_lead[np.maximum(T.parent[:n], 0)])[0]
    leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
    leafy = np.nonzero(leaves > 0)[0]
    if not limbs.size or not leafy.size:
        return {}
    pos = T.pos[:n]
    stem_z = pos[stem, 2]
    at = np.clip(np.searchsorted(stem_z, pos[leafy, 2]), 0, len(stem) - 1)
    radial = np.hypot(pos[leafy, 0] - pos[stem[at], 0], pos[leafy, 1] - pos[stem[at], 1])
    order = np.argsort(pos[leafy, 2])
    cum = np.cumsum(leaves[leafy][order]) / leaves[leafy].sum()
    z5 = float(pos[leafy, 2][order][np.searchsorted(cum, 0.05)])
    lv = T.basipetal(T.levels(alive), leaves)[limbs]
    carrying = limbs[lv >= max(5.0, float(model.sp.stats.crown_base_min_leaf_share) * float(leaves.sum()))]
    base = float(pos[T.parent[carrying], 2].min()) if carrying.size else z5
    crown = max(H - base, 1e-6)
    band = np.clip(((pos[leafy, 2] - base) / crown * 10).astype(int), 0, 9)
    widths = np.array([2.0 * float(np.percentile(radial[band == b], 95)) if (band == b).sum() >= 5 else 0.0 for b in range(10)])
    widest = float(widths.max())
    out = {"widest_at": (int(np.argmax(widths)) + 0.5) / 10.0, "width_ratio_top": float(widths[7:].mean()) / max(widest, 1e-6), "profile": [round(float(x), 2) for x in widths]}
    # by height on the tree, as Hagemeier & Leuschner 2019a report it: where the leaf area and the crown's width peak, and leaf area
    # density in tenths of height, m2 of leaf per m3 of the layer's own crown cylinder
    area = leaves[leafy] * float(model.light.leaf_area)
    tenth = np.clip((pos[leafy, 2] / H * 10).astype(int), 0, 9)
    by_area = np.bincount(tenth, weights=area, minlength=10)
    r95 = np.array([float(np.percentile(radial[tenth == b], 95)) if (tenth == b).sum() >= 5 else 0.0 for b in range(10)])
    out["leaf_peak_at"] = (int(np.argmax(by_area)) + 0.5) / 10.0
    out["wide_peak_at"] = (int(np.argmax(r95)) + 0.5) / 10.0
    out["leaf_below_half"] = float(by_area[:5].sum() / max(by_area.sum(), 1e-9))
    out["lad"] = [round(float(by_area[b] / max(math.pi * r95[b] ** 2 * H / 10.0, 1e-6)), 3) if r95[b] > 0.0 else 0.0 for b in range(10)]
    rel = (pos[T.parent[limbs], 2] - base) / crown
    angles, tips, lengths = [], [], []
    for start in limbs:
        node, along, first = int(start), 0.0, int(T.parent[start])
        chord = None
        while node >= 0 and alive[node]:
            along += float(T.length[node])
            if chord is None and along >= 0.5:
                chord = pos[node] - pos[first]
            last = node
            node = int(T.main_child[node])
        whole = pos[last] - pos[first]
        chord = whole if chord is None else chord
        angles.append(float(np.degrees(np.arctan2(np.hypot(chord[0], chord[1]), chord[2]))))
        tips.append(float(np.degrees(np.arctan2(np.hypot(whole[0], whole[1]), whole[2]))))
        lengths.append(along)
    angles, tips, lengths = np.array(angles), np.array(tips), np.array(lengths)
    for name, lo, hi in (("low", -9.0, 1 / 3), ("mid", 1 / 3, 2 / 3), ("up", 2 / 3, 9.0)):
        hit = (rel >= lo) & (rel < hi) & (lengths >= 0.3)
        out[f"angle_{name}"] = float(np.mean(angles[hit])) if hit.any() else None
        out[f"tip_angle_{name}"] = float(np.mean(tips[hit])) if hit.any() else None
    top_z = base + 0.8 * crown
    upper = limbs[pos[T.parent[limbs], 2] >= top_z]
    rival = 0.0
    if upper.size:
        rival = float((T.radius[upper] / np.maximum(T.radius[T.parent[upper]], 1e-9)).max())
    out["leader_rival"] = rival
    # double top, my own reading of Zeltins et al. 2018's "double tops", which it doesn't define: at least 3 m under the top, a limb at
    # least 0.7 as thick at its base as the stem just above it, whose own axis (not its twigs) ends within 0.5 m of the top
    forks = 0
    under_top = limbs[(pos[T.parent[limbs], 2] >= base) & (pos[T.parent[limbs], 2] <= H - 3.0)]
    if under_top.size:
        tip_z = np.zeros(int(T.axis[:n].max()) + 1)
        np.maximum.at(tip_z, T.axis[:n][alive], pos[:n, 2][alive])
        mains = T.main_child[T.parent[under_top]]
        above = np.where(mains >= 0, T.radius[np.maximum(mains, 0)], T.radius[T.parent[under_top]])
        forks = int(((T.radius[under_top] >= 0.7 * np.maximum(above, 1e-9)) & (tip_z[T.axis[under_top]] >= H - 0.5)).sum())
    out["double_tops"] = forks
    tips_all = np.nonzero(alive & (T.term[:n] == 1))[0]
    stem_axes = np.isin(T.axis[tips_all], np.fromiter(model.leader_axes, np.int64))
    out["tops"] = int(((pos[tips_all, 2] >= H - 0.5) & ~stem_axes).sum())
    real = pos[T.parent[limbs], 2][lengths >= 0.3]
    out["bare_top_m"] = H - float(real.max()) if real.size else H
    run = model.hanging_runs()
    ends = alive & (T.main_child[:n] < 0)
    ends[0] = False
    hr = run[ends]
    hr = hr[hr >= 0.2]
    out["hang_mean"] = float(hr.mean()) if hr.size else 0.0
    out["hang_p90"] = float(np.percentile(hr, 90)) if hr.size else 0.0
    out["hang_max"] = float(hr.max()) if hr.size else 0.0
    out["hang_count"] = int(hr.size)
    out["hang_leaves"] = float(leaves[run[:n] > 0].sum() / max(leaves.sum(), 1e-9))
    out["fill"] = side_fill(pos[leafy], leaves[leafy] * float(model.light.leaf_area))
    attach = np.sort(pos[T.parent[limbs], 2])
    out["lone"] = int((attach < z5).sum())
    out["gap_m"] = float(np.max(np.diff(np.concatenate([attach, [H]])))) if attach.size else H
    # limb sizes: a birch has a few thick limbs and many thin ones.  limb_d: limbs' base diameters (cm), largest first, the top 10; limb_d_med the median;
    # limb_top5: the top 5's mean over the median, limb_thick: limbs at least half as thick as the thickest.  limb_forks: axes on limbs at least 0.6 as thick at
    # their base as the limb just above them; forked: the share of limbs with one.  My own measures: no paper read gives them.
    real_limbs = limbs[lengths >= 0.3]
    d = np.sort(200.0 * T.radius[real_limbs])[::-1] if real_limbs.size else np.zeros(1)
    out["limb_d"] = [round(float(x), 2) for x in d[:10]]
    out["limb_d_med"] = float(np.median(d))
    out["limb_top5"] = float(d[:5].mean() / max(float(np.median(d)), 1e-6))
    out["limb_thick"] = int((d >= 0.5 * d[0]).sum())
    side = np.nonzero(alive & T.is_lateral[:n] & ~on_lead & ~on_lead[np.maximum(T.parent[:n], 0)])[0]
    limb_of = T.scaffold[:n].astype(np.int64)
    if side.size:
        parent = T.parent[side]
        over = T.main_child[parent]
        above = np.where(over >= 0, T.radius[np.maximum(over, 0)], T.radius[parent])
        fork = side[(T.radius[side] >= 0.6 * np.maximum(above, 1e-9)) & (200.0 * T.radius[side] >= 1.0)]
        out["limb_forks"] = int(fork.size)
        out["forked"] = float(np.unique(limb_of[fork]).size) / max(int(real_limbs.size), 1)
    else:
        out["limb_forks"], out["forked"] = 0, 0.0
    # the crown's diameter as Dubois et al. 2021 measured it: eight radii, each from the stem to the furthest leafy node's vertical projection in that direction
    base_xy = pos[stem[0], :2]
    off = pos[leafy, :2] - base_xy
    sector = np.floor((np.arctan2(off[:, 1], off[:, 0]) + math.pi) / (math.pi / 4.0)).astype(np.int64) % 8
    far = np.zeros(8)
    np.maximum.at(far, sector, np.hypot(off[:, 0], off[:, 1]))
    out["crown_d8"] = 2.0 * float(far.mean())
    return out


def shed_events(model) -> dict:
    """Year -> shed axes by size, read back from the nodes' death years, after the run.  An axis counts when its first
    node died and its parent didn't that year.  Branch: on the stem or a leader that replaced it.  Twig: on anything else.  Short shoots come
    from the model's own log."""
    import numpy as np

    T = model.tree
    n = T.n
    dead = np.nonzero((T.death[:n] >= 0) & T.is_lateral[:n])[0]
    par = T.parent[dead]
    roots = dead[(T.death[par] != T.death[dead])]
    on_lead = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    out: dict = {}
    for year, branch in zip(T.death[roots].tolist(), on_lead[T.parent[roots]].tolist()):
        row = out.setdefault(int(year), {"branches": 0, "twigs": 0, "short_shoots": 0})
        row["branches" if branch else "twigs"] += 1
    # what speed.drop_dead has dropped: the same count, kept as it went
    leaders = np.fromiter(model.leader_axes, np.int64)
    for years, axes in getattr(model, "shed_dropped", []):
        for year, branch in zip(years.tolist(), np.isin(axes, leaders).tolist()):
            row = out.setdefault(int(year), {"branches": 0, "twigs": 0, "short_shoots": 0})
            row["branches" if branch else "twigs"] += 1
    for year in model.spurs.death:
        if year is not None and year >= 0:
            row = out.setdefault(int(year), {"branches": 0, "twigs": 0, "short_shoots": 0})
            row["short_shoots"] += 1
    return out


def one(seed: int, sets: list, out: Path, years: int, stand: bool = True) -> int:
    import numpy as np

    import cli
    import root_measure
    from treegen import checkpoint, export
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    species, environment = "betula_pendula", "sweden_open_field"
    sp, _ = load_species(species)
    checkpoint.set_values(sp, sets)
    env_p, _ = load_environment(environment)
    model = GrowthModel(sp, make_environment(env_p), seed, stand=stand, soil=make_soil(env_p), lean=True)
    yearly, snaps = [], []
    for year in range(1, years + 1):
        root_wood_before = root_measure.wood_kg(model) if model.roots is not None else 0.0
        model.step()
        T = model.tree
        new = np.nonzero(T.birth[:T.n] == year)[0]     # by birth, not by count: speed.drop_dead renumbers nodes
        lead = np.isin(T.axis[new], np.fromiter(model.leader_axes, np.int64))
        lengths = T.length[new]
        c = model.stats[-1].get("carbon", {})
        pool = float(c.get("shoot", 0.0)) - float(c.get("wood_maint", 0.0)) - float(c.get("leaf_build", 0.0)) - float(c.get("leaf_maint", 0.0))
        yearly.append({"year": year, "new_m": float(lengths.sum()), "new_lateral_m": float(lengths[~lead].sum()),
                       "new_leader_m": float(lengths[lead].sum()), "new_nodes": int(len(new)), "leader_nodes": int(lead.sum()),
                       "ring_need": float(getattr(model, "_ring_need", 0.0)), "pool": max(pool, 0.0),
                       "store": float(getattr(model, "_carbon_store", 0.0)),
                       "stomata_leader": float(getattr(model, "_leader_phi", float("nan"))),
                       "driver": getattr(model, "_driver_log", None)})
        if model.roots is not None:
            yearly[-1]["root_ledger"] = root_measure.ledger_year(model, year, root_wood_before)
        if year % SNAPSHOT_EVERY == 0:
            snaps.append(snapshot(model, year))
            if model.roots is not None:
                snaps[-1]["root_arch"] = root_measure.architecture(model)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tree.json").write_text(json.dumps({"yearly": yearly, "snapshots": snaps, "shed": shed_events(model)}), encoding="utf-8")
    meta = {"species": sp.species.scientific_name, "species_file": species, "environment": environment, "mode": "stand", "seed": seed,
            "generator": "treegen 0.4, tools/tree_table.py"}
    meta["run_manifest"], meta["options"] = cli.run_manifest(species, environment, sp)
    meta["run_manifest"].update({"resumed_from": None, "scenario": list(sets)})
    export.write_stats(out / "stats.json", model, meta, cli.reference_block(sp, model.stats), cli.anchorage_numbers(model, sp))
    (out / "manifest.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return 0


def run(label: str, seeds: int, first: int, sets: list, years: int, stand: bool = True) -> int:
    folder = E / label
    extra = [x for v in sets for x in ("--set", v)] + ([] if stand else ["--open"])
    jobs = [Job(f"seed {s}", [sys.executable, str(Path(__file__).resolve()), "one", "--seed", str(s), "--years", str(years),
                              "--out", str(folder / f"{s}_stand"), *extra], folder / f"{s}_stand" / "manifest.json")
            for s in range(first, first + seeds)]
    return run_batch(jobs, 0.6, log=folder / "runs.csv")


def load(label: str) -> dict:
    out = {}
    for d in sorted((E / label).glob("*_stand"), key=lambda p: int(p.name.split("_")[0])):
        if not (d / "manifest.json").exists() or not (d / "tree.json").exists():
            continue
        stats = json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]
        extra = json.loads((d / "tree.json").read_text(encoding="utf-8"))
        out[int(d.name.split("_")[0])] = {"per_year": {r["year"]: r for r in stats}, **extra,
                                          "snap": {r["age"]: r for r in extra["snapshots"]},
                                          "new": {r["year"]: r for r in extra["yearly"]}}
    return out


def height_item() -> dict:
    from scorecard import load_approved_targets
    return load_approved_targets("targets-approved")["tree_allometry"]["site_index_curves"]


def reads_as(item: dict, height: float, age: float):
    from m2_shape import reads_as as ra
    return ra(item, height, age)


def evo_median(d_over_bark: float, evo: list) -> float | None:
    """Evo's median crown diameter in the tool's own stem-diameter bins (m3_crown_compare.BINS)."""
    from m3_crown_compare import BINS
    for lo, hi in BINS:
        if lo <= d_over_bark < hi:
            rows = [r["crown"] for r in evo if lo <= r["d_cm"] < hi]
            return statistics.median(rows) if len(rows) >= 2 else None
    return None


def under_2cm(run_: dict, lo: int, hi: int) -> tuple:
    small = total = 0
    for y in range(lo, hi + 1):
        if y in run_["per_year"] and y - 1 in run_["per_year"]:
            small += run_["per_year"][y]["height_m"] - run_["per_year"][y - 1]["height_m"] < 0.02
            total += 1
    return small, total


def fmt(xs: list, f: str = ".2f") -> str:
    return f"{statistics.fmean(xs):{f}} ({min(xs):{f}}-{max(xs):{f}})"


def table(labels: list) -> None:
    from bark import dbh_over_bark
    from m3_crown_compare import evo_rows
    from m3_wood import repola

    item = height_item()
    evo = evo_rows()
    print("Means over seeds, (lowest-highest seed). Height's site index is read on the approved equation and T13 rule. Light is diffuse, at 1-2 m, as the target measures it. Repola is at the tree's own size, over bark. Evo is the median of his trees in the same over-bark stem-diameter bin. Lintunen: 1.02 m, 5.2 per 10 % of crown length, ages 4-32.\n")
    print("| Set | Age | Seeds | Height (m) | Reads as SI | Stem over bark (cm) | LAI | Light (%) | Implied k | Stem wood (kg) | Repola stem | Branch wood (kg) | Repola branches | Crown width (m) | Evo at that stem | Branch mean, median (m) | Branches per 10 % |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        if not runs:
            print(f"| `{label}` | none yet |" + " |" * 15)
            continue
        for age in AGES:
            rows = [r for r in runs.values() if age in r["per_year"] and r["per_year"][age].get("dbh_cm") is not None]
            if not rows:
                continue
            at = [r["per_year"][age] for r in rows]
            sn = [r["snap"][age] for r in rows]
            h = [a["height_m"] for a in at]
            si = reads_as(item, statistics.fmean(h), age)
            lai = [a["lai"] for a in at]
            light = [a["subcanopy_diffuse_light_pct"] for a in at]
            ks = [-math.log(max(x, 1e-6) / 100.0) / max(y, 1e-6) for x, y in zip(light, lai)]
            ob = [float(dbh_over_bark(a["dbh_cm"])) for a in at]
            rep = [repola(d, a["height_m"]) for d, a in zip(ob, at)]
            ev = [evo_median(d, evo) for d in ob]
            ev = [x for x in ev if x is not None]
            crown = [a["crown_ratio"] or 0.0 for a in at]
            per10 = [s["branches"] / 10.0 for s in sn]
            print(f"| `{label}` | {age} | {len(rows)} | {fmt(h)} | {'-' if si is None else f'{si:.1f}'} | {statistics.fmean(ob):.1f} | {fmt(lai)} | {fmt(light, '.1f')} | {statistics.fmean(ks):.3f} | "
                  f"{statistics.fmean(s['stem_kg'] for s in sn):.0f} | {statistics.fmean(x[0] for x in rep):.0f} | {statistics.fmean(s['branch_kg'] for s in sn):.1f} | {statistics.fmean(x[1] for x in rep):.1f} | "
                  f"{fmt([a['crown_width_m'] for a in at])} | {statistics.fmean(ev) if ev else float('nan'):.1f} | {statistics.fmean(s['mean_branch_m'] for s in sn):.2f}, {statistics.fmean(s['median_branch_m'] for s in sn):.2f} | {fmt(per10, '.1f')} |")
    print("\nYears under 2 cm of height growth (all seeds), and whole-crown flips: years where side shoots total under a fifth of the median of the 5 years around them, or none at all.\n")
    print("| Set | Ages 5-14 under 2 cm | 15-19 | 20-39 | 40-60 | Crown flips 5-19 | 20-39 | 40-60 | Worst seed, flips | New side shoots at 50, 60 (m/yr) | Largest one-year fall in leaf area, 20-60: median seed, worst seed |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        if not runs:
            continue
        cells = []
        for lo, hi in WINDOWS:
            s = sum(under_2cm(r, lo, hi)[0] for r in runs.values())
            t = sum(under_2cm(r, lo, hi)[1] for r in runs.values())
            cells.append(f"{s}/{t}" if t else "-")
        flips = {w: [crown_flips(r, *w) for r in runs.values()] for w in ((5, 19), (20, 39), (40, 60))}
        worst = max(sum(flips[w][i] for w in flips) for i in range(len(runs)))
        fl = [f"{sum(flips[w])}/{sum(w[1] - w[0] + 1 for _ in runs)}" for w in flips]
        n50 = [r["new"][50]["new_lateral_m"] for r in runs.values() if 50 in r["new"]]
        n60 = [r["new"][60]["new_lateral_m"] for r in runs.values() if 60 in r["new"]]
        falls = [leaf_fall(r) for r in runs.values()]
        print(f"| `{label}` | {' | '.join(cells)} | {' | '.join(fl)} | {worst} | {statistics.fmean(n50) if n50 else 0:.1f}, {statistics.fmean(n60) if n60 else 0:.1f} | {100 * statistics.median(falls):.0f} %, {100 * max(falls):.0f} % |")


def leaf_fall(run_: dict) -> float:
    """The largest share of its leaf area a tree lost from one year to the next, ages 20-60."""
    worst = 0.0
    for y in range(21, 61):
        if y in run_["per_year"] and y - 1 in run_["per_year"]:
            before, after = run_["per_year"][y - 1]["leaf_area_m2"], run_["per_year"][y]["leaf_area_m2"]
            if before > 0.0:
                worst = max(worst, 1.0 - after / before)
    return worst


def crown_flips(run_: dict, lo: int, hi: int) -> int:
    count = 0
    for y in range(lo, hi + 1):
        if y not in run_["new"]:
            continue
        around = [run_["new"][k]["new_lateral_m"] for k in range(y - 2, y + 3) if k in run_["new"] and k != y]
        if not around:
            continue
        here = run_["new"][y]["new_lateral_m"]
        if here <= 0.0 or here < 0.2 * statistics.median(around):
            count += 1
    return count


def seeds(label: str) -> None:
    item = height_item()
    runs = load(label)
    print("| Seed | " + " | ".join(f"H{a}" for a in AGES) + " | SI 15 | SI 60 | " + " | ".join(f"LAI{a}" for a in (40, 50, 60)) + " | " + " | ".join(f"Light{a}" for a in (40, 50, 60))
          + " | Width 50, 60 | Crown ratio 20, 60 | Under 2 cm, 15-60 | Flips | Branches at 60 | Mean branch at 60 |")
    print("|---" * (len(AGES) + 13) + "|")
    for s, r in runs.items():
        py = r["per_year"]
        if not all(a in py for a in AGES):
            continue
        si15, si60 = reads_as(item, py[15]["height_m"], 15), reads_as(item, py[60]["height_m"], 60)
        u2 = under_2cm(r, 15, 60)[0]
        fl = crown_flips(r, 5, 60)
        print(f"| {s} | " + " | ".join(f"{py[a]['height_m']:.1f}" for a in AGES) + f" | {si15 or 0:.1f} | {si60 or 0:.1f} | " + " | ".join(f"{py[a]['lai']:.2f}" for a in (40, 50, 60)) + " | "
              + " | ".join(f"{py[a]['subcanopy_diffuse_light_pct']:.1f}" for a in (40, 50, 60))
              + f" | {py[50]['crown_width_m']:.1f}, {py[60]['crown_width_m']:.1f} | {py[20].get('crown_ratio') or 0:.2f}, {py[60].get('crown_ratio') or 0:.2f} | {u2} | {fl} | {r['snap'][60]['branches']} | {r['snap'][60]['mean_branch_m']:.2f} |")


def fall(labels: list) -> None:
    print(f"Twig and branch fall: an outcome of light and carbon in each tree, no schedule. Per year over the 5 years up to each age, means over seeds. Branch: a side axis on the stem. Twig: a side axis on anything else. "
          f"Crown ratio bands, all information only in the target file for stand trees: dense unmanaged plots at 11-22 yr {DENSE_CROWN_RATIO[0]}-{DENSE_CROWN_RATIO[1]} (Niemisto 1995, unchecked), Repola's trees {REPOLA_CROWN_RATIO[0]}-{REPOLA_CROWN_RATIO[1]}, mean 0.58, Hynynen's managed floor {CROWN_RATIO_FLOOR}.\n")
    print("| Set | Age | Seeds | Branches shed /yr | Twigs shed /yr | Short shoots lost /yr | Crown base (m), limbs on the stem | Lowest live branch (m), on the stem | Crown ratio, limbs on the stem | Crown ratio as stats.json has it | Trees with a replaced leader | Inside Repola's range | At or over Hynynen's 0.50 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        for age in AGES:
            rows = [r for r in runs.values() if age in r["per_year"]]
            if not rows:
                continue
            years = range(age - 4, age + 1)
            b = [sum(r["shed"].get(str(y), {}).get("branches", 0) for y in years) / 5.0 for r in rows]
            t = [sum(r["shed"].get(str(y), {}).get("twigs", 0) for y in years) / 5.0 for r in rows]
            s = [sum(r["shed"].get(str(y), {}).get("short_shoots", 0) for y in years) / 5.0 for r in rows]
            sn = [r["snap"][age] for r in rows]
            cb = [x.get("crown_base_stem_m") or 0.0 for x in sn]
            ll = [x.get("lowest_stem_branch_m") or 0.0 for x in sn]
            cr = [x.get("crown_ratio_stem") or 0.0 for x in sn]
            cr_stats = [r["per_year"][age].get("crown_ratio") or 0.0 for r in rows]
            inside = sum(REPOLA_CROWN_RATIO[0] <= x <= REPOLA_CROWN_RATIO[1] for x in cr)
            over = sum(x >= CROWN_RATIO_FLOOR for x in cr)
            lost = sum((x.get("leader_losses") or 0) > 0 for x in sn)
            print(f"| `{label}` | {age} | {len(rows)} | {fmt(b, '.1f')} | {fmt(t, '.0f')} | {fmt(s, '.0f')} | {fmt(cb, '.1f')} | {fmt(ll, '.1f')} | {fmt(cr)} | {fmt(cr_stats)} | {lost}/{len(rows)} | {inside}/{len(rows)} | {over}/{len(rows)} |")
    print("\nStems cleared by first thinning, Hynynen & Niemisto 2009 as in reports/birch_knowledge_base.md C1: 5-7 m at dominant height 13-15 m (planted, 1,600/ha; a cross-check, not a target). Each seed's snapshot nearest 14 m tall:\n")
    print("| Set | Seeds | Height there (m) | Lowest live branch there (m) | Seeds inside 5-7 m |")
    print("|---|---|---|---|---|")
    for label in labels:
        h14, low = [], []
        for r in load(label).values():
            ages = [a for a in r["snap"] if a in r["per_year"]]
            if not ages:
                continue
            near = min(ages, key=lambda a: abs(r["per_year"][a]["height_m"] - 14.0))
            h14.append(r["per_year"][near]["height_m"])
            low.append(r["snap"][near].get("lowest_stem_branch_m") or 0.0)
        if low:
            print(f"| `{label}` | {len(low)} | {fmt(h14, '.1f')} | {fmt(low, '.1f')} | {sum(5.0 <= x <= 7.0 for x in low)}/{len(low)} |")


def stem(labels: list) -> None:
    """Does the stem measure follow the real stem?  Its top should be the tree's height, and its volume shouldn't stand apart."""
    print("| Set | Seed | Leader lost | Height at 60 (m) | Top of the measured stem (m) | Stem volume (m3) | Stem wood (kg) | Repola stem (kg) | Branch wood (kg) | Repola branches (kg) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    from bark import dbh_over_bark
    from m3_wood import repola

    for label in labels:
        for s, r in load(label).items():
            if 60 not in r["snap"]:
                continue
            sn, p = r["snap"][60], r["per_year"][60]
            rp = repola(float(dbh_over_bark(p["dbh_cm"])), p["height_m"])
            print(f"| `{label}` | {s} | {sn.get('leader_losses')} | {p['height_m']:.2f} | {sn.get('stem_top_m') or 0:.2f} | {sn.get('stem_m3') or 0:.3f} | {sn['stem_kg']:.0f} | {rp[0]:.0f} | {sn['branch_kg']:.1f} | {rp[1]:.1f} |")


def shape(labels: list, per_seed: bool = False) -> None:
    """Crown shape at 30, 50, 60.  Angle from vertical.  Published: mean branch angle 43.2 deg, range 15-80, SD 10.4 (clonal plantation, Latvia, Forests 9:52, as the
    species file quotes it); no value by height in the crown, for where the crown is widest, for leader loss or for how far twigs hang in anything read so far."""
    print("Angle from vertical. Published: mean branch angle 43.2 deg, range 15-80 (Forests 9:52, as the species file quotes it). Nothing read gives a value by crown position, for where the crown is widest, for leader loss or for twig drop. Means over seeds, (lowest-highest).\n")
    print("| Set | Age | Seeds | Widest point, share of crown length | Top third's width over the widest | Limb angle at the stem, low | mid | up | Tip chord, low | mid | up | Thickest top-crown limb over stem | Rival tops | Bare stem at the top (m) | Hanging run, mean, p90, max (m) | Hanging runs | Leaves on them | Side fill (my own measure) | Lone limbs below the crown | Longest gap in limbs (m) | Trees with a second top |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        for age in (30, 50, 60):
            sh = {s: r["snap"][age]["shape"] for s, r in runs.items() if age in r["snap"] and r["snap"][age].get("shape")}
            if not sh:
                continue
            rows = [("mean", list(sh.values()))] + ([(str(s), [x]) for s, x in sh.items()] if per_seed else [])
            for name, xs in rows:
                def m(key, f=".1f"):
                    v = [x[key] for x in xs if x.get(key) is not None]
                    return "-" if not v else (f"{statistics.fmean(v):{f}}" if len(v) == 1 else fmt(v, f))
                tag = f"`{label}`" if name == "mean" else f"seed {name}"
                print(f"| {tag} | {age} | {len(xs)} | {m('widest_at', '.2f')} | {m('width_ratio_top', '.2f')} | {m('angle_low', '.0f')} | {m('angle_mid', '.0f')} | {m('angle_up', '.0f')} | {m('tip_angle_low', '.0f')} | {m('tip_angle_mid', '.0f')} | {m('tip_angle_up', '.0f')} | {m('leader_rival', '.2f')} | {m('tops', '.1f')} | {m('bare_top_m', '.1f')} | {m('hang_mean', '.2f')}, {m('hang_p90', '.2f')}, {m('hang_max', '.2f')} | {m('hang_count', '.0f')} | {m('hang_leaves', '.2f')} | {m('fill', '.2f')} | {m('lone', '.1f')} | {m('gap_m', '.1f')} | {sum(1 for x in xs if x.get('double_tops', 0) > 0)}/{len(xs)} |")


def limbsheet(labels: list) -> None:
    """Limb sizes and where the carbon goes.  Shows open or stand trees alike: the two are judged apart.  d8 is the crown's diameter as Dubois et al. 2021 measured it (eight radii);
    Hemery et al. 2005 (0.932 + 0.177 D) and Dubois (0.761 + 0.186 D) are for open-grown or crown-released trees, D the stem over bark in cm."""
    from bark import dbh_over_bark

    print("| Set | Age | Seeds | Stem over bark (cm) | Crown d8 (m) | Hemery, Dubois at that stem (m) | Widest, share of crown | Widest, share of height | Top third over widest | Thickest limb (cm) | 5th | Median | Top 5 over median | Limbs half as thick as the thickest | Forks | Limbs with a fork | Double tops | Pool lost (%) | Fixed lost (%) | Twigs at their cap (%) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        for age in (30, 50, 60):
            rows = [r for r in runs.values() if age in r["snap"] and r["snap"][age].get("shape") and "limb_d" in r["snap"][age]["shape"]]
            if not rows:
                continue
            sh = [r["snap"][age]["shape"] for r in rows]
            ob = [float(dbh_over_bark(r["per_year"][age]["dbh_cm"])) for r in rows]
            lost, fixed, cap = [], [], []
            for r in rows:
                for y in range(age - 4, age + 1):
                    u = (r["new"][y].get("driver") or {}).get("use")
                    if not u:
                        continue
                    spent = u["lead"] + u["limbs"] + u["twigs"] + u["rings"]
                    lost.append(max(u["pool"] - spent, 0.0) / max(u["pool"], 1e-9))
                    fix = float(r["per_year"][y].get("carbon", {}).get("fixed", 0.0))
                    fixed.append(max(u["pool"] - spent, 0.0) / max(fix, 1e-9))
                    cap.append(u["at_cap"] / max(u["twig_shoots"], 1))
            hem = statistics.fmean(0.932 + 0.177 * d for d in ob)
            dub = statistics.fmean(0.761 + 0.186 * d for d in ob)
            print(f"| `{label}` | {age} | {len(rows)} | {fmt(ob, '.1f')} | {fmt([x['crown_d8'] for x in sh])} | {hem:.2f}, {dub:.2f} | {fmt([x['widest_at'] for x in sh])} | {fmt([x['wide_peak_at'] for x in sh])} | {fmt([x['width_ratio_top'] for x in sh])} | "
                  f"{fmt([x['limb_d'][0] for x in sh], '.1f')} | {statistics.fmean(x['limb_d'][min(4, len(x['limb_d']) - 1)] for x in sh):.1f} | {statistics.fmean(x['limb_d_med'] for x in sh):.1f} | {fmt([x['limb_top5'] for x in sh], '.1f')} | "
                  f"{statistics.fmean(x['limb_thick'] for x in sh):.1f} | {statistics.fmean(x['limb_forks'] for x in sh):.1f} | {statistics.fmean(x['forked'] for x in sh):.2f} | {sum(1 for x in sh if x.get('double_tops', 0) > 0)}/{len(sh)} | "
                  f"{100.0 * statistics.fmean(lost) if lost else 0.0:.0f} | {100.0 * statistics.fmean(fixed) if fixed else 0.0:.0f} | {100.0 * statistics.fmean(cap) if cap else 0.0:.0f} |")


def crownheight(labels: list) -> None:
    """Where the leaves are by height on the tree, beside Hagemeier & Leuschner 2019a (6 felled birches 22-26 m tall, closed stands, Germany): all leaf area in the upper
    half, most at about 0.80 of height, and crown radius the same; density 0.142 + 2.91 x^9.02 m2/m3 at relative height x (their Figure 6's fit, as read by the main session).  For stand trees."""
    fit = [0.142 + 2.91 * ((b + 0.5) / 10.0) ** 9.02 for b in range(10)]
    print("Hagemeier & Leuschner 2019a: leaf area all in the upper half, most at about 0.80 of height, crown radius the same pattern. Leaf area density by tenth of height: their fit in the first row. Mine is leaf area per m3 of each layer's crown cylinder, at the layer's 95th percentile radius; theirs may be reckoned differently, so compare the shape first. Means over seeds, (lowest-highest).\n")
    print("| Set | Age | Seeds | Most leaf area at, share of height | Widest at, share of height | Share of leaf area below half height | LAD at 0.55 | 0.65 | 0.75 | 0.85 | 0.95 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    print(f"| their fit | - | 6 trees | about 0.80 | about 0.80 | none | {fit[5]:.2f} | {fit[6]:.2f} | {fit[7]:.2f} | {fit[8]:.2f} | {fit[9]:.2f} |")
    for label in labels:
        runs = load(label)
        for age in (30, 50, 60):
            sh = [r["snap"][age]["shape"] for r in runs.values() if age in r["snap"] and r["snap"][age].get("shape", {}).get("lad")]
            if not sh:
                continue
            lad = [statistics.fmean(x["lad"][b] for x in sh) for b in (5, 6, 7, 8, 9)]
            print(f"| `{label}` | {age} | {len(sh)} | {fmt([x['leaf_peak_at'] for x in sh])} | {fmt([x['wide_peak_at'] for x in sh])} | {fmt([x['leaf_below_half'] for x in sh])} | " + " | ".join(f"{v:.2f}" for v in lad) + " |")


def openset(labels: list) -> None:
    """Trees grown in the open, beside open-grown data: Hemery, Savill & Pryor 2005 Table 1, crown diameter = 0.932 + 0.177 DBH over bark (cm), as the target file has it (information
    only: paywalled, not opened).  Kalliovirta & Tokola 2005's birches are mixed stands, not open, so not used here."""
    from bark import dbh_over_bark

    print("Open-grown data: Hemery 2005 as the target file gives it, crown diameter = 0.932 + 0.177 x DBH over bark; information only, the paper wasn't opened. Means over seeds, (lowest-highest).\n")
    print("| Set | Age | Seeds | Height (m) | Stem over bark (cm) | Crown width (m) | Projected diameter (m) | Hemery at that stem (m) | Crown ratio | Leaf area (m2) | Side fill | Hanging run p90, max (m) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        for age in AGES:
            rows = [r for r in runs.values() if age in r["per_year"] and r["per_year"][age].get("dbh_cm") is not None]
            if not rows:
                continue
            at = [r["per_year"][age] for r in rows]
            sh = [r["snap"][age].get("shape") or {} for r in rows]
            ob = [float(dbh_over_bark(a["dbh_cm"])) for a in at]
            fill = [x["fill"] for x in sh if "fill" in x]
            print(f"| `{label}` | {age} | {len(rows)} | {fmt([a['height_m'] for a in at])} | {fmt(ob, '.1f')} | {fmt([a['crown_width_m'] for a in at])} | {fmt([a['crown_projected_diameter_m'] for a in at])} | {statistics.fmean(0.932 + 0.177 * d for d in ob):.2f} | "
                  f"{fmt([x.get('crown_ratio_stem') or 0.0 for x in (r['snap'][age] for r in rows)])} | {fmt([a['leaf_area_m2'] for a in at], '.0f')} | {fmt(fill) if fill else '-'} | {statistics.fmean(x.get('hang_p90', 0.0) for x in sh):.2f}, {statistics.fmean(x.get('hang_max', 0.0) for x in sh):.2f} |")


def rootsheet(labels: list) -> None:
    """Roots: their share of the carbon, and their mass.  Wood: pi r^2 L x 530 kg/m3, as the crown's.  Fine roots: 0.48 x
    leaf mass (resource.leaf_costs), so they follow the leaves by construction."""
    print("| Set | Age | Seeds | Root share of carbon | Carbon to roots (units) | Fixed (units) | Structural root wood (kg) | Root length (m) | Fine roots (kg) | Root wood per stem wood |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        for age in AGES:
            sn = [r["snap"][age] for r in runs.values() if age in r["snap"] and "root_wood_kg" in r["snap"][age]]
            if not sn:
                continue
            ratio = [x["root_wood_kg"] / max(x["stem_kg"], 1e-9) for x in sn]
            print(f"| `{label}` | {age} | {len(sn)} | {statistics.fmean(x['root_share'] for x in sn):.3f} | {statistics.fmean(x['root_carbon'] for x in sn):.0f} | {statistics.fmean(x['fixed_carbon'] for x in sn):.0f} | "
                  f"{fmt([x['root_wood_kg'] for x in sn], '.0f')} | {fmt([x['root_length_m'] for x in sn], '.0f')} | {statistics.fmean(x['fine_root_kg'] for x in sn):.2f} | {statistics.fmean(ratio):.2f} |")


def young(labels: list) -> None:
    """Young trees' leaf area beside Konopka et al. 2023 (Plants 12:1607): 2.37 m2 (D0 / 50 mm)^1.851, D0 50-100 mm, as the
    species file quotes it.  D0 is the model's wood at the base, no bark.  Outside that range it's only a look."""
    print("| Set | Age | Seeds | Height (m) | Base diameter D0 (mm) | Leaf area (m2) | Konopka at that D0 (m2) | Carbon not used, % of fixed, the 5 years to this age |")
    print("|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        for age in (5, 10, 15, 20):
            rows = [r for r in runs.values() if age in r["snap"]]
            if not rows:
                continue
            d0 = [r["snap"][age].get("d0_mm") or 0.0 for r in rows]
            la = [r["per_year"][age]["leaf_area_m2"] for r in rows]
            kon = [2.37 * (d / 50.0) ** 1.851 for d in d0]
            lost = []
            for r in rows:
                fixed = sum(r["per_year"][y]["carbon"].get("fixed", 0.0) for y in range(max(age - 4, 1), age + 1))
                gone = sum((r["new"][y].get("driver") or {}).get("unspent", 0.0) for y in range(max(age - 4, 1), age + 1))
                lost.append(100.0 * gone / max(fixed, 1e-9))
            print(f"| `{label}` | {age} | {len(rows)} | {statistics.fmean(r['per_year'][age]['height_m'] for r in rows):.2f} | {fmt(d0, '.0f')} | {fmt(la, '.1f')} | {statistics.fmean(kon):.1f} | {statistics.fmean(lost):.0f} |")


def driver(label: str) -> None:
    print("What held the leader back. `Cap` is the curve's allowance after light. `Got` is the shoot it built. Shares are seed-years in each window where that limit was the tightest.\n")
    print("| Ages | Seed-years | Curve's increment (m) | Light factor | Water factor | Got (m) | Nodes built | Leader's cost, % of pool | Held by curve | Held by light | Held by water | Held by carbon |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    runs = load(label)
    for lo, hi in ((1, 5), (6, 14), (15, 19), (20, 29), (30, 39), (40, 49), (50, 60)):
        rows = [r["new"][y]["driver"] for r in runs.values() for y in range(lo, hi + 1) if y in r["new"] and r["new"][y].get("driver")]
        if not rows:
            continue
        m = lambda k: statistics.fmean(x[k] for x in rows)
        by = {k: sum(x["held_by"] == k for x in rows) for k in ("curve", "light", "water", "carbon")}
        print(f"| {lo}-{hi} | {len(rows)} | {m('increment_m'):.3f} | {m('light'):.3f} | {m('water'):.3f} | {m('got_m'):.3f} | {m('nodes'):.1f} | {100 * m('cost_share'):.1f} | {by['curve']} | {by['light']} | {by['water']} | {by['carbon']} |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("run", "one", "table", "seeds", "fall", "driver", "young", "stem", "roots", "shape", "shapeseeds", "open", "height", "limbs"))
    ap.add_argument("labels", nargs="*")
    ap.add_argument("--label")
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--open", action="store_true", help="grow in the open, no neighbours; the folder keeps its _stand name so the readers find it")
    ap.add_argument("--out")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    a = ap.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    if a.what == "one":
        return one(a.seed, a.set, Path(a.out), a.years, not a.open)
    if a.what == "run":
        return run(a.label, a.seeds, a.first_seed, a.set, a.years, not a.open)
    if a.what == "table":
        table(a.labels)
    elif a.what == "seeds":
        seeds(a.labels[0])
    elif a.what == "fall":
        fall(a.labels)
    elif a.what == "young":
        young(a.labels)
    elif a.what == "stem":
        stem(a.labels)
    elif a.what == "roots":
        rootsheet(a.labels)
    elif a.what == "shape":
        shape(a.labels)
    elif a.what == "shapeseeds":
        shape(a.labels, per_seed=True)
    elif a.what == "open":
        openset(a.labels)
    elif a.what == "height":
        crownheight(a.labels)
    elif a.what == "limbs":
        limbsheet(a.labels)
    else:
        driver(a.labels[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
