"""Where a tree's highest point is, year by year, and how it got there.  Only reads the model while it grows.

    python tools/height_trace.py tree --label node_ht_a --seeds 11,14 [--years 60] [--set key=json ...]
    python tools/height_trace.py plot --label node_ht_p --seed 1 --years 45 [--area 1000] [--set key=json ...]

A tree's reported height (GrowthModel.measure, height_m) is its highest living node; the height curve limits only
the leader's step (GrowthModel._height_limit_plan), so the stem's top and the highest point can differ.  Each year
this records, beside height_m: the stem's top (the last node of Tree.trunk_chain), the leader's limit (_hd_ref),
and the highest living node with its lineage: branching order, what axis it is on (stem, limb, twig on a limb,
fork, reiterated limb, the tree's one second top), the limb it belongs to (its first node, birth year, height on
the stem, whether and when it was reiterated), the node's own birth year and the height it was born at, and how
far it moved this year in the mechanics (bending under the year's load, then posture control), as _finish_year
runs them.  A stand tree also records the height its neighbours' schedule row was read at this year, and that
row's stems per hectare (GrowthModel._stand_cell): the neighbours the tree grew among.

'tree' grows stand trees as tools/tree_table.py does (one after the other, in one process) and writes
out/bench/ensemble/<label>/<seed>_trace.json, with every node within --zone m of the stem's top from --from-year on.
'plot' grows a forest plot as tools/forest.py run does (natural mode, the same settings) and writes
out/bench/ensemble/<label>/plot_<seed>_trace.json: from --from-year on, a short row per tree-year, and the
lineage of the highest point wherever it stands more than --detail m above the stem's top.

How it reads: GrowthModel._finish_year, fast.bend_steps and, for a stand tree, the tree's _stand_cell are wrapped.
Each wrapper copies positions out and calls the original with the same arguments, returning what it returns.
Nothing here calls a model method that stores anything (the frame's second top is read from the model's own
attributes, never through _frame_tops, which caches).  A run with speed.drop_dead on is refused: it renumbers
nodes.  The proof that it changes nothing: each run's height_m, year by year, against the same seed's saved run
(the control's stats.json, or its tree lists).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from treegen import checkpoint, fast  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402

BASE = ROOT / "out" / "bench" / "ensemble"

_ORIG_FINISH = GrowthModel._finish_year
_ORIG_BEND = fast.bend_steps
_BEND = {"z": None}
_BIRTH_Z = {}         # id(model) -> each node's height in the year it was born, before that year's mechanics
_STEM_TOP = {}        # id(model) -> {year: the stem's top after that year}
_YEAR = {}            # id(model) -> this year's summary
_LAST = {}            # stand trees: the last year's positions before and during the mechanics, for the zone
_KEEP_ZONE = {"on": False}


def _bend(*args):
    """fast.bend_steps, unchanged; then a copy of the heights after bending (dm, args[14], has one value per node)."""
    out = _ORIG_BEND(*args)
    n = args[14].shape[0]
    _BEND["z"] = np.array(args[8][:n, 2], copy=True)
    return out


def _finish(self, t):
    """GrowthModel._finish_year, unchanged; with the heights and slopes before it copied out first."""
    T = self.tree
    n = T.n
    z_pre = np.array(T.pos[:n, 2], copy=True)
    dz_pre = np.array(T.dir[:n, 2], copy=True)
    _BEND["z"] = None
    _ORIG_FINISH(self, t)
    _YEAR[id(self)] = _summary(self, t, z_pre, dz_pre, _BEND["z"])
    if _KEEP_ZONE["on"]:
        _LAST.update({"model": id(self), "z_pre": z_pre, "z_bend": _BEND["z"]})


def _install():
    GrowthModel._finish_year = _finish
    fast.bend_steps = _bend


def _kind(m, node: int) -> str:
    """What the node's axis is, read from the model's own attributes."""
    T = m.tree
    ax = int(T.axis[node])
    if ax in m.leader_axes:
        return "stem"
    second = m.__dict__.get("_frame_second_top")
    if second is not None and ax == int(second) and m.__dict__.get("_frame_forks"):
        return "second_top"
    if ax in m.reit_axes:
        return "reiterated_limb_axis"
    if ax in (m.__dict__.get("_frame_fork_of") or {}):
        return "fork"
    s = int(T.scaffold[node])
    if s > 0 and int(T.axis[s]) == ax:
        return "limb_axis"
    return f"twig_order_{int(T.order[node])}"


def _summary(m, t, z_pre, dz_pre, z_bend) -> dict:
    T = m.tree
    n = T.n
    key = id(m)
    bz = _BIRTH_Z.get(key)
    if bz is None or len(bz) < n:
        grown = np.full(n, np.nan, np.float32)
        if bz is not None:
            grown[: len(bz)] = bz
        bz = grown
    born = np.nonzero(T.birth[:n] == t)[0]
    bz[born] = z_pre[born]
    _BIRTH_Z[key] = bz
    alive = T.death[:n] < 0
    if not alive.any():
        return {"year": int(t), "height_m": None}
    z = T.pos[:n, 2]
    live = np.nonzero(alive)[0]
    top = int(live[np.argmax(z[live])])
    tip = int(T.trunk_chain(m.leader_axes)[-1])
    stem_top = float(z[tip])
    _STEM_TOP.setdefault(key, {})[int(t)] = round(stem_top, 4)
    hd = getattr(m, "_hd", None)
    log = getattr(m, "_driver_log", None)
    return {"year": int(t), "height_m": float(m.stats[-1]["height_m"]), "stem_top_m": round(stem_top, 4),
            "stem_top_pre_mech_m": round(float(z_pre[tip]), 4) if tip < len(z_pre) else None,
            "limit_m": round(float(getattr(m, "_hd_ref", float("nan"))), 4),
            "leader_bud_z_m": None if hd is None else round(float(hd["z"]), 4),
            "leader_gain_m": log.get("got_m") if isinstance(log, dict) else None,
            "reiterated": {int(k): int(v[0]) for k, v in m.reit.items()},
            "forks": bool(m.__dict__.get("_frame_forks")), "second_top_axis": m.__dict__.get("_frame_second_top"),
            "top": _node(m, top, t, z_pre, dz_pre, z_bend, bz)}


def _node(m, node, t, z_pre, dz_pre, z_bend, bz) -> dict:
    """The lineage of one node: its axis, its limb, its birth, and how it moved this year."""
    T = m.tree
    z = float(T.pos[node, 2])
    pre = float(z_pre[node]) if node < len(z_pre) else float("nan")
    bend = float(z_bend[node]) if z_bend is not None and node < len(z_bend) else float("nan")
    born = int(T.birth[node])
    rec = {"node": int(node), "z_m": round(z, 4), "order": int(T.order[node]), "kind": _kind(m, node), "axis": int(T.axis[node]),
           "born": born, "z_at_birth_m": None if not np.isfinite(bz[node]) else round(float(bz[node]), 4),
           "stem_top_at_birth_m": _STEM_TOP.get(id(m), {}).get(born),
           "mech_bend_m": round(bend - pre, 4) if np.isfinite(bend) else None,
           "mech_posture_m": round(z - bend, 4) if np.isfinite(bend) else None,
           "mech_total_m": round(z - pre, 4)}
    if born == t:
        # this year's shoot: the node it grew from, before the mechanics, and its first and last segment's slope
        a = int(T.axis[node])
        j, first = node, node
        while j > 0 and int(T.birth[j]) == t and int(T.axis[j]) == a:
            first = j
            j = int(T.parent[j])
        rec.update({"shoot_from_z_m": round(float(z_pre[j]), 4), "shoot_rise_m": round(pre - float(z_pre[j]), 4),
                    "shoot_first_dz": round(float(dz_pre[first]), 3), "shoot_last_dz": round(float(dz_pre[node]), 3),
                    "shoot_new_axis": bool(T.is_lateral[first])})
    s = int(T.scaffold[node])
    if s > 0:
        limb_ax = int(T.axis[s])
        own = (T.axis[: T.n] == limb_ax) & (T.death[: T.n] < 0)
        r = m.reit.get(s)
        rec["limb"] = {"first_node": s, "born": int(T.scaffold_birth[node]), "base_z_m": round(float(T.pos[T.parent[s], 2]), 4),
                       "base_radius_cm": round(100.0 * float(T.radius[s]), 3), "own_axis_m": round(float(T.length[: T.n][own].sum()), 3),
                       "reiterated_year": None if r is None else int(r[0]), "on_stem": bool(int(T.axis[T.parent[s]]) in m.leader_axes)}
    return rec


def _zone_nodes(m, t) -> list:
    """Every living node within the zone under the stem's top: node, z, z before the mechanics, z after bending, born, axis, limb's first node."""
    if _LAST.get("model") != id(m):
        return []
    T = m.tree
    n = T.n
    z_pre, z_bend = _LAST["z_pre"], _LAST["z_bend"]
    z = T.pos[:n, 2]
    pick = np.nonzero((T.death[:n] < 0) & (z >= _STEM_TOP[id(m)][int(t)] - _KEEP_ZONE["m"]))[0]
    return [[i, round(float(z[i]), 4), round(float(z_pre[i]), 4) if i < len(z_pre) else None,
             round(float(z_bend[i]), 4) if z_bend is not None and i < len(z_bend) else None,
             int(T.birth[i]), int(T.axis[i]), int(T.scaffold[i])] for i in pick.tolist()]


def tree(a) -> int:
    """Stand trees, as tools/tree_table.py one grows them."""
    from treegen.environment import make_environment, make_soil
    from treegen.params import load_environment, load_species

    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    _KEEP_ZONE.update({"on": True, "m": a.zone})
    _install()
    for seed in [int(x) for x in a.seeds.split(",") if x.strip()]:
        t0 = time.time()
        sp, _ = load_species("betula_pendula")
        checkpoint.set_values(sp, a.set)
        if fast.on(sp, "drop_dead"):
            print("speed.drop_dead renumbers nodes: not traced")
            return 2
        env_p, _ = load_environment("sweden_open_field")
        m = GrowthModel(sp, make_environment(env_p), seed, stand=True, soil=make_soil(env_p), lean=True)
        used = {}
        orig_cell = m._stand_cell

        def cell(pos, w, height, wood_pos=None, wood_w=None, _m=m, _orig=orig_cell):
            # the height the neighbours' row is read at this year, and the row it gives; then the original, unchanged
            used[_m.year + 1] = (float(height), float(_m.stems_per_ha(height)))
            return _orig(pos, w, height, wood_pos, wood_w)

        m._stand_cell = cell
        years, zone = [], {}
        for year in range(1, a.years + 1):
            m.step()
            rec = _YEAR.pop(id(m))
            h_row, d_row = used.get(year, (None, None))
            rec["row_read_at_m"] = None if h_row is None else round(h_row, 4)
            rec["row_stems_per_ha"] = None if d_row is None else round(d_row, 1)
            rec["damage"] = [{k: e.get(k) for k in ("year", "cause", "fatal", "snap_height_m", "took")}
                             for e in m.__dict__.get("damage_log", []) if e.get("year") == year]
            years.append(rec)
            if year >= a.from_year:
                zone[year] = _zone_nodes(m, year)
        doc = {"seed": seed, "label": a.label, "sets": list(a.set), "years": years, "zone_m": a.zone,
               "zone_columns": ["node", "z_m", "z_pre_mech_m", "z_after_bend_m", "born", "axis", "limb_first_node"], "zone": zone,
               "runtime_s": round(time.time() - t0, 1), "what": __doc__.split("\n\n")[1]}
        (out / f"{seed}_trace.json").write_text(json.dumps(doc), encoding="utf-8")
        _BIRTH_Z.pop(id(m), None)
        _STEM_TOP.pop(id(m), None)
        _LAST.clear()
        print(f"seed {seed}: {time.time() - t0:.0f} s, height {m.stats[-1]['height_m']:.4f} m", flush=True)
    return 0


def plot(a) -> int:
    """A forest plot, as tools/forest.py run grows it."""
    import cli
    from treegen.plot import Plot

    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    _install()
    items = ["plot.stand_measures=true", "plot.natural_start.enabled=true", f"plot.natural_start.stems_per_ha={a.stems}",
             "mortality.enabled=true", f"plot.natural_start.area_m2={a.area}"] + list(a.set)
    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, items)
    if fast.on(sp, "drop_dead"):
        print("speed.drop_dead renumbers nodes: not traced")
        return 2
    env_p, _ = cli.load_environment("sweden_open_field")
    t0 = time.time()
    p = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), seed=a.seed, mode="natural", lean=True)
    rows, detail = [], []
    while p.year < a.years and p.alive:
        p.step()
        for k in p.alive:
            rec = _YEAR.get(id(p.trees[k]))
            if rec is None or rec.get("height_m") is None or p.year < a.from_year:
                continue
            rows.append([p.year, k, rec["height_m"], rec["stem_top_m"], rec["limit_m"]])
            if rec["height_m"] - rec["stem_top_m"] > a.detail:
                detail.append(dict(rec, tree=k))
        _YEAR.clear()
        living = {id(p.trees[k]) for k in p.alive}
        for key in [x for x in _BIRTH_Z if x not in living]:
            _BIRTH_Z.pop(key, None)
            _STEM_TOP.pop(key, None)
        if p.year % 5 == 0:
            print(f"year {p.year}: {len(p.alive)} trees, {time.time() - t0:.0f} s", flush=True)
    doc = {"seed": a.seed, "label": a.label, "area_m2": p.area, "sets": items, "years": p.year,
           "row_columns": ["year", "tree", "height_m", "stem_top_m", "limit_m"], "rows": rows,
           "detail_over_m": a.detail, "detail": detail, "runtime_s": round(time.time() - t0, 1), "what": __doc__.split("\n\n")[1]}
    (out / f"plot_{a.seed}_trace.json").write_text(json.dumps(doc), encoding="utf-8")
    print(f"done in {time.time() - t0:.0f} s", flush=True)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=["tree", "plot"])
    ap.add_argument("--label", required=True)
    ap.add_argument("--seeds", default="1", help="tree: comma-separated seeds, grown one after the other")
    ap.add_argument("--seed", type=int, default=1, help="plot: its seed")
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--area", type=float, default=1000.0, help="plot: m2, as tools/forest.py")
    ap.add_argument("--stems", type=float, default=16000.0, help="plot: stems/ha at the start, as tools/forest.py")
    ap.add_argument("--from-year", type=int, default=25, help="the first year whose zone (tree) or rows (plot) are kept")
    ap.add_argument("--zone", type=float, default=1.5, help="tree: keep every node within this many m under the stem's top")
    ap.add_argument("--detail", type=float, default=0.05, help="plot: keep the highest point's lineage where it is this many m over the stem's top")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    a = ap.parse_args(argv)
    return tree(a) if a.what == "tree" else plot(a)


if __name__ == "__main__":
    sys.exit(main())
