"""Where a tree's branch wood is, limb by limb, read off a grown tree.  tools/tree_table.py calls these as it measures a
stand tree; nothing here changes the tree (tests/test_logging.py).

    python tools/limb_wood.py scans X Y      # limbs beside the six Nordic scans, at the snapshot nearest their height
    python tools/limb_wood.py wood X Y       # branch wood by order, crown quarter and limb age, and what was shed

A limb is a side axis on the stem, or on a leader that replaced it (tools/tree_table.py's first-order branch).  Wood is
every living internode as a cylinder, pi r^2 L x 530 kg/m3: wood only, no bark.

* by order: 1 the limbs' own axes, 2 the axes on them, 3+ anything finer.  A piece of an old leader left beside the stem
  counts as order 1.
* by crown quarter: the crown from its base (tools/tree_table.py's crown base, limbs counted on the stem) to the tree's top
  in four equal lengths, 1 the lowest, as Repola 2008 weighed branches "by four equal crown sections" (p. 608, as read in
  reports/design/2026-11-11_branch_wood.md).  A limb's whole wood goes to the quarter it leaves the stem in; "below" is
  limbs under the crown base.
* by limb age: years since the limb's first node was made: under 10, 10 to 20, over 20.
* the scan measures, as KNOWN_ISSUES.md defines them for the six Nordic stand scans (15.5-19.7 m tall): a limb's base
  diameter is the smaller of its first two internodes'; limbs over 2, 5 and 10 cm; limb over stem diameter where it
  leaves the stem, for limbs over 2 cm below 0.8 of the height (largest and 90th percentile); limbs over 2 cm below half
  the height, and how many of those leave within 45 degrees of the stem's own line; length of branch wood 1 cm thick
  or more.  A scan's figures are an upper bound for thin wood (the same file says why), so these are for a look.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from treegen import fast, logs  # noqa: E402

DENSITY = 530.0
E = ROOT / "out" / "bench" / "ensemble"
# KNOWN_ISSUES.md, "Nordic stand-grown scans": medians of 6 trees 15.5-19.7 m tall (p10-p90 in the file)
SCANS = {"height_m": (15.5, 19.7), "limbs_over_2cm": 58, "limb_over_stem_p90": 0.67, "limb_over_stem_max": 0.95, "low_limbs_over_2cm": 5,
         "low_limbs_ascending": 2.5, "branch_m_over_1cm": 869}
LIMB_COLUMNS = ("year", "node", "birth_year", "z_m", "base_d_cm", "stem_d_cm", "length_m", "wood_kg", "leaf_area_m2",
                "ring_replaced", "ring_more_leaf", "ring_wind", "own_carbon", "upkeep")
LIMBS_WHAT = ("One row a living limb a year, the limb as it stands after that year.  node: its first node, the limb's name within a run.  birth_year: the tree year that node "
              "was made in.  z_m: the height it leaves the stem at.  base_d_cm: the smaller of its first two internodes' diameters; stem_d_cm: the stem's there.  length_m: its "
              "own axis.  wood_kg (530 kg/m3, no bark) and leaf_area_m2 (each leaf at its own size): everything on it.  ring_replaced, ring_more_leaf, ring_wind: the carbon "
              "its rings took this year, in the pool's units: sapwood that replaces what stopped conducting, sapwood for more foliage, the wind's extra (log.rings).  "
              "own_carbon, upkeep: what its own leaves fixed, after the roots' share, and the upkeep of its wood and leaves, as the shedding test read them at the "
              "start of the year (shedding.log_limbs), in the same units.  Null where that log is off, or doesn't hold the limb: one too young for the shedding test, "
              "or made stem or limb by a change of leader within the year.")
# shedding.log_limbs (2026-11-12, reports/design/2026-11-12_limbs_challenge.md section 9): limb_light.json, beside limbs.json
LIGHT_COLUMNS = ("year", "node", "light", "kind", "fork_axes")
LIGHT_WHAT = ("Written only with shedding.log_limbs on; limbs.json is as it is without it.  One row a living limb a year, the same limbs in the same order as "
              "limbs.json's rows of that year (year and node as there).  light: the leaf-weighted mean light on the buds of everything on the limb, as the "
              "shedding test read it at the start of the year (treegen/growth.py, the ratio it holds against shedding.light_per_leaf_threshold; 1 = open "
              "sky, the herb layer's shade included).  Null for a limb too young for the test (shedding.min_branch_age), one made limb by a change of "
              "leader within the year, and every limb with speed.drop_dead on.  kind, at the end of the year: second_top, the one reiterated limb that "
              "goes up as a second top (crown_frame.earned, on a tree drawn to fork); reiterated, a limb made a reiterated complex (resource.reiteration); "
              "limb, any other.  fork_axes: how many living axes on the limb the model named as its forks (crown_frame.fork_leaf_area_m2), at the end "
              "of the year; 0 for none.")


def limbs(model) -> dict:
    """Every living limb now, one entry each in every array: its first node, the year that node was made, the height it leaves the
    stem at, its base diameter (the smaller of its first two internodes') and the stem's there (m), the length of its own axis, and
    the wood volume (m3), leaf area (m2, each leaf at its own size) and count of nodes of everything on it."""
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    first = logs.limb_starts(model, n, alive)
    volume = np.where(alive, math.pi * T.radius[:n] ** 2 * T.length[:n], 0.0)
    leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
    whole = T.basipetal(T.levels(alive), np.stack([volume, leaves, alive.astype(float)], 1))[first]
    second = T.main_child[first]
    has_second = (second >= 0) & alive[np.maximum(second, 0)]
    d1 = 2.0 * T.radius[first]
    base_d = np.where(has_second, np.minimum(d1, 2.0 * T.radius[np.maximum(second, 0)]), d1)
    length, angle = np.zeros(len(first)), np.zeros(len(first))
    for i, start in enumerate(first):
        node, along, chord, base = int(start), 0.0, None, int(T.parent[start])
        while node >= 0 and alive[node]:
            along += float(T.length[node])
            if chord is None and along >= 0.5:
                chord = T.pos[node] - T.pos[base]
            last = node
            node = int(T.main_child[node])
        chord = T.pos[last] - T.pos[base] if chord is None else chord
        line = T.dir[base]
        cos = float(np.dot(chord, line)) / max(float(np.linalg.norm(chord)) * float(np.linalg.norm(line)), 1e-12)
        length[i], angle[i] = along, math.degrees(math.acos(min(max(cos, -1.0), 1.0)))
    return {"node": first, "birth_year": T.birth[first].astype(np.int64), "z_m": T.pos[T.parent[first], 2].copy(), "base_d_m": base_d,
            "stem_d_m": 2.0 * T.radius[T.parent[first]], "length_m": length, "angle_deg": angle, "wood_m3": whole[:, 0],
            "leaf_area_m2": whole[:, 1] * float(model.light.leaf_area), "nodes": whole[:, 2]}


def branch_wood(model, crown_base_m=None) -> dict:
    """Branch wood now (kg), split three ways that each add up to it, and the scan measures.  crown_base_m: the crown base
    the quarters start at; None gives no quarters."""
    T, s = model.tree, model.stats[-1]
    n = T.n
    alive = T.death[:n] < 0
    volume = np.where(alive, math.pi * T.radius[:n] ** 2 * T.length[:n], 0.0)
    on_stem = np.zeros(n, bool)
    on_stem[np.asarray(T.trunk_chain(model.leader_axes), dtype=np.int64)] = True
    branch = alive & ~on_stem
    # order from the stem: one more at each side axis on the way out
    order = np.zeros(n, np.int64)
    for depth, (seg, mains, lats) in enumerate(T.levels(alive)):
        if depth == 0:
            continue
        order[mains] = order[T.parent[mains]]
        order[lats] = order[T.parent[lats]] + 1
        order[seg[on_stem[seg]]] = 0
    order = np.maximum(order, 1)
    by_order = {"1": float(volume[branch & (order == 1)].sum()) * DENSITY, "2": float(volume[branch & (order == 2)].sum()) * DENSITY,
                "3_up": float(volume[branch & (order >= 3)].sum()) * DENSITY}
    total = float(volume[branch].sum()) * DENSITY
    L = limbs(model)
    kg = L["wood_m3"] * DENSITY
    off_limbs = total - float(kg.sum())      # a piece of an old leader beside the stem: on no limb
    age = int(model.year) - L["birth_year"]
    by_age = {"under_10": float(kg[age < 10].sum()), "10_to_20": float(kg[(age >= 10) & (age <= 20)].sum()), "over_20": float(kg[age > 20].sum()),
              "on_no_limb": off_limbs}
    H = float(s["height_m"])
    by_quarter = None
    if crown_base_m is not None and H > crown_base_m:
        q = np.clip(np.floor((L["z_m"] - crown_base_m) / (H - crown_base_m) * 4.0).astype(np.int64), 0, 3)
        under = L["z_m"] < crown_base_m
        by_quarter = {"below": float(kg[under].sum()), **{str(k + 1): float(kg[~under & (q == k)].sum()) for k in range(4)}, "on_no_limb": off_limbs}
    d = L["base_d_m"]
    over2 = d > 0.02
    ratio = (d / np.maximum(L["stem_d_m"], 1e-9))[over2 & (L["z_m"] < 0.8 * H)]
    low = over2 & (L["z_m"] < 0.5 * H)
    thick = branch & (2.0 * T.radius[:n] >= 0.01)
    scan = {"limbs_over_2cm": int(over2.sum()), "limbs_over_5cm": int((d > 0.05).sum()), "limbs_over_10cm": int((d > 0.10).sum()),
            "limb_over_stem_max": float(ratio.max()) if ratio.size else None, "limb_over_stem_p90": float(np.percentile(ratio, 90)) if ratio.size else None,
            "low_limbs_over_2cm": int(low.sum()), "low_limbs_ascending": int((low & (L["angle_deg"] < 45.0)).sum()),
            "branch_m_over_1cm": float(T.length[:n][thick].sum()), "branch_kg_over_1cm": float(volume[thick].sum()) * DENSITY}
    return {"branch_kg": total, "limbs": int(len(d)), "by_order": by_order, "by_limb_age": by_age, "by_crown_quarter": by_quarter, "scan": scan}


def shed_wood(model, year: int):
    """Wood on the nodes that died in this year (kg), as thick as they were then: branch (anything off the stem's axes) and stem (a
    lost top).  Call it right after the year's step.  None with speed.drop_dead on, which may already have dropped them."""
    if fast.on(model.sp, "drop_dead"):
        return None
    T = model.tree
    n = T.n
    gone = T.death[:n] == year
    volume = math.pi * T.radius[:n] ** 2 * T.length[:n]
    on_lead = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    return {"branch_kg": float(volume[gone & ~on_lead].sum()) * DENSITY, "stem_kg": float(volume[gone & on_lead].sum()) * DENSITY}


def year_record(model, year: int) -> dict:
    """What tools/tree_table.py adds to a year's row: wood shed, what the year had to pay against its pool, leaf area three ways, and
    with log.rings on the year's rings split (treegen/logs.py)."""
    out = {"shed_wood": shed_wood(model, year), "must": getattr(model, "_must_log", None) if logs.grew_this_year(model) else None,
           **logs.leaf_areas(model), "leaf_area_lit_m2": getattr(model, "_lit_leaf_m2", None)}
    ring = getattr(model, "_ring_log", None)
    if ring is not None and ring["year"] == year:
        out["rings"] = {"stem": ring["stem"], "branch": ring["branch"]}
    return out


def limb_rows(model, year: int) -> list:
    """One row a living limb, in LIMB_COLUMNS' order, for limbs.json: the limb as it stands after the year, the carbon its rings took
    this year by kind (log.rings), and what its own leaves fixed against its upkeep as the shedding test read them
    (shedding.log_limbs).  The last five are None for a limb the log doesn't hold, and for every limb with speed.drop_dead on,
    which renumbers the nodes the logs are kept by."""
    L = limbs(model)
    same_numbers = not fast.on(model.sp, "drop_dead")
    ring = getattr(model, "_ring_log", None)
    ring = ring if ring is not None and ring["year"] == year and same_numbers else None
    rings = {} if ring is None else {int(k): (float(a), float(b), float(c)) for k, a, b, c in
                                     zip(ring["limb_node"], ring["limb_replaced"], ring["limb_more_leaf"], ring["limb_wind"])}
    carbon = getattr(model, "_limb_carbon", None) if logs.grew_this_year(model) and same_numbers else None
    earned = {} if carbon is None else {int(k): (float(a), float(b)) for k, a, b in zip(carbon["node"], carbon["own"], carbon["upkeep"])}
    rows = []
    for i, node in enumerate(L["node"].tolist()):
        rows.append([year, node, int(L["birth_year"][i]), round(float(L["z_m"][i]), 3), round(100.0 * float(L["base_d_m"][i]), 3),
                     round(100.0 * float(L["stem_d_m"][i]), 3), round(float(L["length_m"][i]), 3), float(f"{L['wood_m3'][i] * DENSITY:.5g}"),
                     float(f"{L['leaf_area_m2'][i]:.5g}"), *[None if v is None else float(f"{v:.5g}") for v in rings.get(node, (None, None, None))],
                     *[None if v is None else float(f"{v:.5g}") for v in earned.get(node, (None, None))]])
    return rows


def light_log_on(sp) -> bool:
    """Is shedding.log_limbs on?  (A species file from before it: no.)"""
    return bool(getattr(getattr(sp, "shedding", None), "log_limbs", False))


def limb_light_rows(model, year: int) -> list:
    """One row a living limb, in LIGHT_COLUMNS' order, for limb_light.json (LIGHT_WHAT): the light the shedding test read on
    its leaves at the start of the year (model._limb_log, kept with shedding.log_limbs on), and what the limb is and how many
    fork axes it carries now.  Reads only: model.__dict__ is read, not _frame_tops(), which would name the second top."""
    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    first = logs.limb_starts(model, n, alive)
    log = getattr(model, "_limb_log", None)
    light = {} if log is None or log["year"] != year or fast.on(model.sp, "drop_dead") else \
        {int(k): float(q) for k, q in zip(log["node"], log["ratio"])}
    reiterated = getattr(model, "reit", None) or {}
    top = model.__dict__.get("_frame_second_top")
    forks = {}
    fork_of = model.__dict__.get("_frame_fork_of") or {}
    if fork_of:
        living = set(np.unique(T.axis[:n][alive]).tolist())
        for ax, limb in fork_of.items():
            if int(ax) in living:
                forks[int(limb)] = forks.get(int(limb), 0) + 1
    rows = []
    for node in first.tolist():
        kind = "second_top" if top is not None and int(T.axis[node]) == int(top) else ("reiterated" if node in reiterated else "limb")
        q = light.get(node)
        rows.append([year, node, None if q is None else float(f"{q:.5g}"), kind, forks.get(node, 0)])
    return rows


# -- reading saved runs ---------------------------------------------------
def load(label: str) -> dict:
    out = {}
    for d in sorted((E / label).glob("*_stand"), key=lambda p: int(p.name.split("_")[0])):
        if (d / "tree.json").exists() and (d / "stats.json").exists():
            doc = json.loads((d / "tree.json").read_text(encoding="utf-8"))
            years = {r["year"]: r for r in json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]}
            out[int(d.name.split("_")[0])] = {"snap": {s["age"]: s for s in doc["snapshots"]}, "yearly": {r["year"]: r for r in doc["yearly"]}, "per_year": years}
    return out


def _mean(xs: list, f: str = ".2f") -> str:
    xs = [x for x in xs if x is not None]
    return "-" if not xs else f"{statistics.fmean(xs):{f}} ({min(xs):{f}}-{max(xs):{f}})"


def scans(labels: list) -> None:
    lo, hi = SCANS["height_m"]
    print(f"Limbs beside the six Nordic stand scans (KNOWN_ISSUES.md; trees {lo}-{hi} m tall; medians). The scans count thin wood generously, so they are an upper bound "
          "there. Means over seeds, (lowest-highest). 'At the scans' height': each seed's snapshot nearest the middle of that range.\n")
    print("| Set | Read at | Seeds | Height (m) | Limbs over 2 cm | Over 5 cm | Limb over stem, 90th percentile | Largest | Limbs over 2 cm below half height | Of those, within 45 deg of the stem | Branch wood 1 cm or thicker (m) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    print(f"| the scans | {lo}-{hi} m | 6 trees | - | {SCANS['limbs_over_2cm']} | 3 | {SCANS['limb_over_stem_p90']} | {SCANS['limb_over_stem_max']} | {SCANS['low_limbs_over_2cm']} | "
          f"{SCANS['low_limbs_ascending']} | {SCANS['branch_m_over_1cm']} |")
    for label in labels:
        runs = load(label)
        picks = [("at the scans' height", None)] + [(f"age {a}", a) for a in (30, 50, 60)]
        for name, age in picks:
            rows = []
            for r in runs.values():
                ages = [a for a in r["snap"] if a in r["per_year"] and "branch_wood" in r["snap"][a]]
                if not ages or (age is not None and age not in ages):
                    continue
                at = age if age is not None else min(ages, key=lambda a: abs(r["per_year"][a]["height_m"] - 0.5 * (lo + hi)))
                rows.append((r["per_year"][at]["height_m"], r["snap"][at]["branch_wood"]["scan"]))
            if not rows:
                continue
            m = lambda k, f=".1f": _mean([s[k] for _, s in rows], f)
            print(f"| `{label}` | {name} | {len(rows)} | {_mean([h for h, _ in rows], '.1f')} | {m('limbs_over_2cm')} | {m('limbs_over_5cm')} | {m('limb_over_stem_p90', '.2f')} | "
                  f"{m('limb_over_stem_max', '.2f')} | {m('low_limbs_over_2cm')} | {m('low_limbs_ascending')} | {m('branch_m_over_1cm', '.0f')} |")


def wood(labels: list, ages=(20, 30, 40, 50, 60)) -> None:
    print("Branch wood (kg dry mass, wood only), means over seeds. Order 1: the limbs' own axes; 2: the axes on them; 3+: finer. Quarters: the crown in four equal lengths, 1 the lowest. "
          "Shed: wood on what died, a year, over the 5 years to that age.\n")
    print("| Set | Age | Seeds | Branch wood | Order 1 | Order 2 | Order 3+ | Below the crown base | Quarter 1 | 2 | 3 | 4 | Limbs under 10 y | 10-20 y | Over 20 y | Branch wood shed a year | Years short of sapwood, to this age |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        for age in ages:
            rows = [r for r in runs.values() if age in r["snap"] and "branch_wood" in r["snap"][age]]
            if not rows:
                continue
            bw = [r["snap"][age]["branch_wood"] for r in rows]
            f = lambda get: f"{statistics.fmean(get(b) for b in bw):.1f}"
            quarters = [b["by_crown_quarter"] for b in bw if b.get("by_crown_quarter")]
            fq = lambda k: f"{statistics.fmean(q[k] for q in quarters):.1f}" if quarters else "-"
            shed = [statistics.fmean(r["yearly"][y]["shed_wood"]["branch_kg"] for y in range(age - 4, age + 1)) for r in rows
                    if all(y in r["yearly"] and r["yearly"][y].get("shed_wood") for y in range(age - 4, age + 1))]
            short = [sum(1 for y in range(1, age + 1) if (r["yearly"].get(y, {}).get("must") or {}).get("paid", 1.0) < 1.0) for r in rows]
            print(f"| `{label}` | {age} | {len(rows)} | {f(lambda b: b['branch_kg'])} | {f(lambda b: b['by_order']['1'])} | {f(lambda b: b['by_order']['2'])} | {f(lambda b: b['by_order']['3_up'])} | "
                  f"{fq('below')} | {fq('1')} | {fq('2')} | {fq('3')} | {fq('4')} | {f(lambda b: b['by_limb_age']['under_10'])} | {f(lambda b: b['by_limb_age']['10_to_20'])} | "
                  f"{f(lambda b: b['by_limb_age']['over_20'])} | {statistics.fmean(shed) if shed else float('nan'):.2f} | {_mean(short, '.0f')} |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("scans", "wood"))
    ap.add_argument("labels", nargs="+")
    a = ap.parse_args(argv)
    (scans if a.what == "scans" else wood)(a.labels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
