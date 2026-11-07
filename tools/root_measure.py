"""What the roots are and where their carbon goes.  It only reads the model, so it changes no number.

    python tools/root_measure.py ledger X [Y ...]    # where the root share of the carbon goes, in kg of dry matter a year
    python tools/root_measure.py mass X [Y ...]      # root wood by size against Repola 2008, Petersson & Stahl 2006, Varik 2014
    python tools/root_measure.py form X [Y ...]      # number, thickness, taper and reach of the proximal roots against Kalliokoski 2008
    python tools/root_measure.py anchor X [Y ...]    # root plate and critical turning moment at each age
    python tools/root_measure.py split X [Y ...]     # the year's production by organ against Aosaar 2016 and Varik 2014

Each reads what tools/tree_table.py wrote in out/bench/ensemble/<label>.  tree_table.py calls ``ledger_year`` every year and
``architecture`` at its snapshots.

Sources for the comparison columns:
  Repola 2008, Silva Fennica 42(4):605, Table 5, Eqs. 13-15 (birch, Finland; birch-data/04_biomass_partition).
    Stump, roots over 1 cm, both.  dS = 2 + 1.25 d (d: diameter at 1.3 m, cm).  Fixed part with half the variances added back.
  Petersson & Stahl 2006, Scand. J. For. Res. 21(S7):84, as written in the game's trees.json (growth.roots_petersson_stahl).  NOT READ AT
    SOURCE: the publisher's paywalled.  Roots of 5 mm and up with the stump.
  Kalliokoski, Nygren & Sievanen 2008, Silva Fennica 42(2):189, Tables 3, 4, 6, 7, 8: 20 excavated silver birch, S Finland.
  Varik 2014 (PhD thesis, Estonian University of Life Sciences), section 5.4.1: 32-year stand, one excavated tree;
    Table 6: carbon fluxes at 13, 32 and 45 years.  Coarse roots there follow from his 21 %, not measured each year.
  Aosaar et al. 2016, Silva Fennica 50(4):1628, Table 4: production at age 10; coarse roots assumed from the same 21 %.
"""
from __future__ import annotations

import argparse
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

STEM_DENSITY = 530.0   # kg/m3, as tools/tree_table.py
OVER_BARK = 1.098      # over-bark over wood diameter: species file, damage.dbh_over_bark_factor
AGES = (20, 30, 40, 50, 60)
# Kalliokoski 2008, Betula pendula.  stage, age, stump diameter D0 (cm), height (m), RelSumD2 Table 3, proximal number, mean d (cm),
# SD of d, mean depth of insertion (cm), adventitious number, max radial extension (m), mean of maxima (m), depth max, depth mean,
# taper a and b Table 7, standardised total ln number, ln length, ln mass Table 8, basic density Table 6
KALLIOKOSKI = {
    "sapling MT": dict(age=13, d0=8.1, h=4.9, rel=0.86, n=11, d=2.0, sd=0.9, dh=12, adv=6, rmax=5.7, rmean=3.2, a=2.860, b=-0.458, ln_len=4.23, ln_mass=3.20, rho=0.449),
    "pole MT": dict(age=29, d0=16.1, h=12.5, rel=1.02, n=20, d=3.1, sd=1.8, dh=30, adv=12, rmax=8.1, rmean=5.2, a=2.332, b=-0.287, ln_len=4.56, ln_mass=3.20, rho=0.385),
    "mature MT": dict(age=48, d0=30.0, h=20.9, rel=0.88, n=25, d=5.0, sd=2.9, dh=35, adv=21, rmax=20.5, rmean=11.6, a=1.112, b=-0.022, ln_len=4.81, ln_mass=3.94, rho=0.394),
    "pole OMT": dict(age=36, d0=26.4, h=19.0, rel=1.75, n=28, d=5.3, sd=3.9, dh=30, adv=14, rmax=10.2, rmean=6.6, a=2.701, b=-0.169, ln_len=4.17, ln_mass=3.17, rho=0.413),
    "pole VT": dict(age=32, d0=19.1, h=11.9, rel=1.29, n=16, d=4.7, sd=2.4, dh=25, adv=4, rmax=10.6, rmean=8.1, a=1.340, b=-0.039, ln_len=5.29, ln_mass=3.75, rho=0.411),
}


def repola_below(dbh_cm: float, h_m: float) -> dict:
    """Repola 2008 Table 5 model 1b.  kg dry mass: stump, roots over 1 cm, and the equation for both."""
    ds = 2.0 + 1.25 * dbh_cm
    stump = math.exp(-3.574 + 11.304 * ds / (ds + 26.0) + (0.02154 + 0.04542) / 2.0)
    roots = math.exp(-3.223 + 6.497 * ds / (ds + 22.0) + 1.033 * math.log(h_m) + (0.0480 + 0.02677) / 2.0)
    both = math.exp(-2.726 + 7.652 * ds / (ds + 24.0) + 0.799 * math.log(h_m) + (0.02623 + 0.02152) / 2.0)
    return {"stump": stump, "roots": roots, "both": both}


def petersson_below(dbh_cm: float) -> float:
    """As written in trees.json: ln g = 4.90864 + 9.91194 D / (D + 138), D in mm; kg; no back-transform correction there."""
    d = 10.0 * dbh_cm
    return math.exp(4.90864 + 9.91194 * d / (d + 138.0)) / 1000.0


def kalliokoski_taper(distance_m: float, a: float, b: float) -> float:
    """Eq. 2: diameter at a distance along a root's main axis over its diameter at the base."""
    return 1.0 / (1.0 + a * distance_m + b * distance_m * distance_m)


def unit_grams(model) -> float:
    """Grams of dry matter in one model carbon unit (treegen.growth._leaf_costs)."""
    sp = model.sp
    return float(sp.pipe_model.wood_volume_per_carbon) * float(sp.resource.leaf_costs.wood_basic_density_kg_m3) * 1000.0


def root_density(model) -> float:
    paid = getattr(model.sp.roots, "paid", None)
    return float(paid.wood_density_kg_m3) if paid is not None and bool(paid.enabled) else STEM_DENSITY


def wood_kg(model) -> float:
    """Structural root wood now, kg."""
    import numpy as np

    R = model.roots.tree
    live = R.death[: R.n] < 0
    return float(np.where(live, math.pi * R.radius[: R.n] ** 2 * R.length[: R.n], 0.0).sum()) * root_density(model)


def ledger_year(model, year: int, wood_before_kg: float) -> dict:
    """This year's root carbon, kg of dry matter (units x grams per unit / 1000), as the model spent it."""
    import numpy as np

    c = model.stats[-1].get("carbon", {})
    sp = model.sp
    u = unit_grams(model) / 1000.0
    g_resp = 1.0 + float(getattr(sp.resource, "growth_respiration_coefficient", 0.0))
    R = model.roots.tree
    new = np.nonzero(R.birth[: R.n] == year)[0]
    new_len = float(R.length[new].sum())
    per_unit = float(sp.resource.root_segments_per_unit)
    seg = float(sp.roots.segment_length)
    net = float(getattr(model, "_root_carbon", 0.0))
    out = {
        "fixed_kg": float(c.get("fixed", 0.0)) * u,
        "root_share_kg": float(c.get("root", 0.0)) * u,
        "fine_maint_kg": float(c.get("fine_root_maint", 0.0)) * u,
        "root_net_kg": net * u,                     # after fine-root upkeep
        "growth_resp_kg": net * (1.0 - 1.0 / g_resp) * u,
        "budget_kg": net / g_resp * u,              # what goes into roots.step, as carbon
        "paid_for_length_kg": new_len / seg / max(per_unit, 1e-12) * u,   # what the new length cost at root_segments_per_unit
        "new_root_m": new_len,
        "new_root_nodes": int(new.size),
        "wood_kg": wood_kg(model),
        "wood_gain_kg": wood_kg(model) - wood_before_kg,
        "fine_kg": float(c.get("leaf_dm_g", 0.0)) * float(sp.resource.leaf_costs.fine_root_to_leaf_mass) / 1000.0,
        "leaf_kg": float(c.get("leaf_dm_g", 0.0)) / 1000.0,
    }
    log = getattr(model.roots, "carbon_log", None)
    if log:
        out["paid"] = {k: float(v) * u for k, v in log.items()}
    return out


def architecture(model) -> dict:
    """The woody root system now: size classes, proximal roots, taper of the thick ones, what's near the surface."""
    import numpy as np

    Rs = model.roots
    R = Rs.tree
    n = R.n
    alive = R.death[:n] < 0
    idx = np.arange(n)
    r = R.radius[:n]
    L = R.length[:n]
    vol = np.where(alive, math.pi * r * r * L, 0.0)
    rho = root_density(model)
    d = 2.0 * r
    classes = {"lt2": d < 0.002, "2_5": (d >= 0.002) & (d < 0.005), "5_10": (d >= 0.005) & (d < 0.010), "10_50": (d >= 0.010) & (d < 0.05), "ge50": d >= 0.05}
    out = {"mass_kg": {k: float(vol[m].sum()) * rho for k, m in classes.items()},
           "length_m": {k: float(np.where(alive & m, L, 0.0).sum()) for k, m in classes.items()},
           "total_kg": float(vol.sum()) * rho, "total_m": float(np.where(alive, L, 0.0).sum())}
    # the first-order roots and every root that leaves the collar zone
    collar_axis = (Rs.kind[R.axis[:n]] == 0)
    first = np.nonzero(alive & R.is_lateral[:n] & collar_axis[np.maximum(R.parent[:n], 0)])[0]
    rows = []
    for s in first.tolist():
        chain = [s]
        while R.main_child[chain[-1]] >= 0 and R.death[R.main_child[chain[-1]]] < 0:
            chain.append(int(R.main_child[chain[-1]]))
        c = np.array(chain)
        along = np.cumsum(L[c]) - L[c] * 0.5
        rad = r[c]
        at = lambda x: float(np.interp(x, along, rad, right=0.0))
        p0 = R.pos[R.parent[s]]
        horiz = float(np.hypot(*(R.pos[c[-1], :2] - p0[:2])))
        mid = R.pos[c[np.searchsorted(along, min(1.0, along[-1]), side="left").clip(0, len(c) - 1)]]
        rows.append({"d_cm": 200.0 * float(r[s]), "depth_m": float(-p0[2]), "length_m": float(along[-1] + 0.5 * L[c[-1]]), "reach_m": horiz,
                     "r": [at(x) for x in (0.25, 0.5, 1.0, 2.0, 5.0)], "r3": at(3.0), "depth_at_1m": float(-mid[2]),
                     "tips": float(Rs.P[s]) if len(Rs.P) > s else 0.0,
                     "tips_at": [float(np.interp(x, along, Rs.P[c], right=0.0)) if len(Rs.P) >= n else 0.0 for x in (1.0, 2.0, 5.0)],
                     "depth_at": [float(np.interp(x, along, -R.pos[c, 2], right=float("nan"))) for x in (0.5, 1.0, 2.0, 3.0, 5.0)],
                     "azimuth": float(math.degrees(math.atan2(*(R.pos[c[-1], 1::-1] - p0[1::-1]))))})
    rows.sort(key=lambda x: -x["d_cm"])
    d0 = 2.0 * float(model.tree.radius[0])
    sum_d2 = sum((x["d_cm"] / 100.0) ** 2 for x in rows)
    stump = float(getattr(Rs, "stump_d_m", 0.0)) or d0
    chain = np.nonzero(alive & collar_axis)[0]
    thick = rows[0]["d_cm"] if rows else 0.0
    horiz = np.hypot(R.pos[:n, 0], R.pos[:n, 1])
    live_pos = R.pos[:n][alive & (idx > 0)]
    depth = -live_pos[:, 2] if len(live_pos) else np.zeros(1)
    ll = L[alive & (idx > 0)]
    mean_depth = float((depth * ll).sum() / max(ll.sum(), 1e-9)) if len(live_pos) else 0.0
    if model.stats and model.stats[-1].get("dbh_cm"):
        from treegen import damage

        an = damage.anchorage_of(model) or {}
        ct = an.get("critical_turning_moment") or {}
        out["anchorage"] = {"plate_radius_m": an.get("plate_radius_m"), "plate_depth_m": an.get("plate_depth_m"), "structural_roots": an.get("structural_roots"),
                            "resistance_knm": an.get("overturning_resistance_mean_knm"), "resistance_min_knm": an.get("overturning_resistance_min_knm"),
                            "soil_weight_knm": an.get("resistance_soil_weight_knm"), "empirical_knm": an.get("empirical_h_dbh2_knm"), "critical_knm": ct.get("mean_knm"),
                            "critical_min_knm": ct.get("min_knm"), "rooting_depth_m": ct.get("rooting_depth_m"), "depth_factor": ct.get("depth_factor"),
                            "asymmetry_factor_range": ct.get("asymmetry_factor_range")}
    out.update({
        "d0_cm": 100.0 * d0,
        "stump_d_cm": 100.0 * stump,
        "stump_kg": float(vol[chain].sum()) * rho,
        "rel_sum_stump": sum_d2 / max(stump * stump, 1e-12),
        "dominant_n": sum(1 for x in rows if x["d_cm"] >= 0.2 * thick),
        "proximal": rows[:40],
        "proximal_n": len(rows),
        "proximal_n_ge1cm": sum(1 for x in rows if x["d_cm"] >= 1.0),
        "rel_sum_d2": sum_d2 / max(d0 * d0, 1e-12),
        "reach_max_m": float(horiz[alive].max()) if alive.any() else 0.0,
        "depth_max_m": float(depth.max()),
        "depth_mean_m": mean_depth,
    })
    return out


# -- reading -------------------------------------------------------------------------------------------------------------------
_SAID = set()


def _load(label: str) -> dict:
    """The seeds of a set that grew.  One with no height at its last age never made a tree, and every comparison here needs one:
    it's left out, and said."""
    from tree_table import load

    runs = load(label)
    dead = sorted(s for s, r in runs.items() if float(r["per_year"][max(r["per_year"])].get("height_m") or 0.0) <= 0.0)
    if dead and label not in _SAID:
        print(f"`{label}`: left out, no height at their last age: seed {', '.join(str(s) for s in dead)}.  {len(runs) - len(dead)} of {len(runs)} seeds used.")
        _SAID.add(label)
    return {s: r for s, r in runs.items() if s not in dead}


def _mean(xs):
    xs = list(xs)
    return statistics.fmean(xs) if xs else float("nan")


WINDOWS = ((1, 5), (6, 10), (11, 14), (15, 29), (30, 44), (45, 50), (51, 60))


def _stems(height_m: float) -> float:
    """Stand trees' stems a hectare at this height, as the species file's stand.thinning has them."""
    return 1800.0 if height_m < 11.0 else 1000.0 if height_m < 16.0 else 450.0


def _unspent_kg(r: dict, y: int) -> float:
    """What the shoot side threw away that year (treegen.growth._unspent), kg of dry matter."""
    led = r["new"][y].get("root_ledger") or {}
    drv = r["new"][y].get("driver") or {}
    fixed_units = float((r["per_year"][y].get("carbon") or {}).get("fixed", 0.0))
    return float(drv.get("unspent", 0.0)) / fixed_units * float(led.get("fixed_kg", 0.0)) if fixed_units > 0.0 else 0.0


def ledger(labels: list) -> None:
    print("Where the root share goes, kg of dry matter a year, mean over seeds and years.  On plain settings carbon in `Budget not used`, and `Paid for new length` above the wood gained, goes nowhere.")
    print("| Set | Ages | Seeds | Fixed | Root share | Share of fixed | Fine-root upkeep | Growth respiration | Budget for building | Paid for new length | Budget not used | Wood gained | Fine-root stock | Share of the root carbon that became wood | Root carbon gone, % of fixed | Shoot carbon not used, % of fixed |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for lo, hi in WINDOWS:
            rows = [(r["new"][y].get("root_ledger") or {}) for r in runs.values() for y in range(lo, hi + 1) if y in r["new"]]
            rows = [x for x in rows if x]
            if not rows:
                continue
            m = lambda k: _mean(x.get(k, 0.0) for x in rows)
            gone = m("budget_kg") - m("wood_gain_kg")
            unspent = _mean(_unspent_kg(r, y) for r in runs.values() for y in range(lo, hi + 1) if y in r["new"])
            print(f"| `{label}` | {lo}-{hi} | {len(runs)} | {m('fixed_kg'):.1f} | {m('root_share_kg'):.2f} | {100.0 * m('root_share_kg') / max(m('fixed_kg'), 1e-9):.1f} % | {m('fine_maint_kg'):.2f} | {m('growth_resp_kg'):.2f} | {m('budget_kg'):.2f} | "
                  f"{m('paid_for_length_kg'):.2f} | {m('budget_kg') - m('paid_for_length_kg'):.2f} | {m('wood_gain_kg'):.3f} | {m('fine_kg'):.2f} | {100.0 * m('wood_gain_kg') / max(m('root_share_kg'), 1e-9):.1f} % | {100.0 * gone / max(m('fixed_kg'), 1e-9):.1f} | {100.0 * unspent / max(m('fixed_kg'), 1e-9):.1f} |")
    # the paid ledger, when the carbon roots are on
    for label in labels:
        runs = _load(label)
        keys = ("fine_upkeep", "fine_build", "new_root_wood", "rings", "wood_respiration", "rest")
        if not any("paid" in (y.get("root_ledger") or {}) for r in runs.values() for y in r["new"].values()):
            continue
        print(f"\nWhat `{label}` paid for, kg a year, and where the carbon use efficiency goes when the unresolved rest isn't counted as growth.  Varik Table 6: soil autotrophic respiration 3.2-5.5 t C/ha/yr, understorey included.")
        print("| Ages | Seeds | Root share | Fine-root upkeep | Fine roots built | New root wood | Rings | Wood's growth respiration | Unresolved rest | Rest, % of fixed | Rings wanted, share got | Model's CUE | Without the rest | Respired or unresolved below ground, t C/ha/yr at the stand's stems |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for lo, hi in WINDOWS:
            rows = [(r["new"][y]["root_ledger"], r["per_year"][y]) for r in runs.values() for y in range(lo, hi + 1) if y in r["new"] and r["new"][y].get("root_ledger", {}).get("paid")]
            if not rows:
                continue
            p = lambda k: _mean(x[0]["paid"].get(k, 0.0) for x in rows)
            fixed = _mean(x[0]["fixed_kg"] for x in rows)
            cue = _mean(float((x[1].get("carbon") or {}).get("cue", 0.0)) * x[0]["fixed_kg"] for x in rows) / max(fixed, 1e-9)
            # 0.48 g C per g (species file, leaf_costs.carbon_fraction); fine roots' growth respiration is 0.25 / 1.25 of what they cost
            stems = _mean(_stems(x[1]["height_m"]) for x in rows)
            flux = (p("fine_upkeep") + 0.2 * p("fine_build") + p("wood_respiration") + p("rest")) * 0.48 * stems / 1000.0
            print(f"| {lo}-{hi} | {len(runs)} | {_mean(x[0]['root_share_kg'] for x in rows):.2f} | " + " | ".join(f"{p(k):.2f}" for k in keys) + f" | {100.0 * p('rest') / max(fixed, 1e-9):.1f} | {p('rings') / max(p('rings_wanted'), 1e-9):.2f} | {cue:.3f} | {cue - p('rest') / 1.25 / max(fixed, 1e-9):.3f} | {flux:.2f} |")


def mass(labels: list) -> None:
    print("Root wood against published equations at each tree's own stem diameter and height.  Means over seeds.")
    print("Model mass: volume x the roots' density.  Stem wood from tools/tree_table.py.  Repola's stump is above- and below-ground, 16 cm high on average; Petersson as in trees.json, not read at source.")
    print("Varik: 21 % of above-ground wood, from one 32-year tree, here on the model's wood without its bark.  Kalliokoski Fig. 5: M = 0.0421 D2 kg and L = D^1.7734 m for each of the model's own roots, without the stump.")
    print("| Set | Age | Seeds | Root wood, all (kg) | Of it the stump below ground (kg) | Over 5 mm (kg) | Over 1 cm (kg) | Repola stump + over 1 cm (kg) | Petersson over 5 mm + stump (kg) | Varik (kg) | Kalliokoski roots alone (kg) | All / Repola | Stem wood (kg) | Root / stem | Repola / stem | Root length (m) | Kalliokoski's length (m) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for age in AGES:
            rows = []
            for r in runs.values():
                s = r["snap"].get(age)
                if not s or "root_arch" not in s:
                    continue
                a = s["root_arch"]
                py = r["per_year"][age]
                dbh = (py.get("dbh_cm") or 0.0) * OVER_BARK
                h = py["height_m"]
                if dbh <= 0.0 or h <= 0.0:
                    continue    # not yet at breast height: the equations want a diameter
                rep = repola_below(dbh, h)
                prox = a["proximal"]
                rows.append({"all": a["total_kg"], "ge5": a["mass_kg"]["5_10"] + a["mass_kg"]["10_50"] + a["mass_kg"]["ge50"], "ge10": a["mass_kg"]["10_50"] + a["mass_kg"]["ge50"],
                             "rep": rep["stump"] + rep["roots"], "pet": petersson_below(dbh), "stem": s["stem_kg"], "len": a["total_m"], "var": 0.21 * (s["stem_kg"] + s["branch_kg"]),
                             "k08": 0.0421 * sum(p["d_cm"] ** 2 for p in prox), "k08_len": sum(p["d_cm"] ** 1.7734 for p in prox), "stump": a.get("stump_kg", 0.0)})
            if not rows:
                continue
            m = lambda k: _mean(x[k] for x in rows)
            print(f"| `{label}` | {age} | {len(rows)} | {m('all'):.1f} | {m('stump'):.1f} | {m('ge5'):.1f} | {m('ge10'):.1f} | {m('rep'):.1f} | {m('pet'):.1f} | {m('var'):.1f} | {m('k08'):.1f} | {_mean(x['all'] / x['rep'] for x in rows):.2f} | {m('stem'):.0f} | {_mean(x['all'] / x['stem'] for x in rows):.3f} | {_mean(x['rep'] / x['stem'] for x in rows):.3f} | {m('len'):.0f} | {m('k08_len'):.0f} |")
    print("\nShare of the coarse-root mass by size (Varik 2014, 32-year stand, one tree: stump 35 %, over 10 mm 41 %, 5-10 mm 9 %, 2-5 mm 9 %; without the stump 63, 14, 14 %)")
    print("| Set | Age | Seeds | Under 2 mm | 2-5 mm | 5-10 mm | 10-50 mm | Over 50 mm |")
    print("|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for age in (50, 60):
            rows = [r["snap"][age]["root_arch"] for r in runs.values() if age in r["snap"] and "root_arch" in r["snap"][age]]
            if not rows:
                continue
            f = lambda k: _mean(100.0 * x["mass_kg"][k] / max(x["total_kg"], 1e-9) for x in rows)
            print(f"| `{label}` | {age} | {len(rows)} | {f('lt2'):.0f} % | {f('2_5'):.0f} % | {f('5_10'):.0f} % | {f('10_50'):.0f} % | {f('ge50'):.0f} % |")


def form(labels: list) -> None:
    print("Proximal roots.  Published: Kalliokoski 2008, silver birch, mature MT, age 48, stump 30 cm: 25 (SD 8) proximal roots, mean d 5.0 cm (SD 2.9), mean insertion depth 35 cm (SD 12), Sum d2 / D0^2 = 0.88, radial extension mean of maxima 11.6 m, largest 20.5 m.")
    print("Laitakari 1934 p. 182: 7-12 dominant main roots (base at least 20 % of the thickest's) in most trees, 6-17 in all; thickest 68-87 % of DBH its widest way.")
    print("| Set | Age | Seeds | Stem base, wood (cm) | Stump, Repola's dS (cm) | Roots at the collar | Dominant | Mean d (cm) | SD of d (cm) | Thickest six d (cm) | Sum d2 / stump^2 | Mean depth at insertion (m) | Reach, max (m) | Depth, max (m) | Mean depth along roots (m) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for age in (20, 30, 50, 60):
            rows = [r["snap"][age]["root_arch"] for r in runs.values() if age in r["snap"] and r["snap"][age].get("root_arch", {}).get("proximal")]
            if not rows:
                continue
            top = [_mean(x["proximal"][i]["d_cm"] if len(x["proximal"]) > i else 0.0 for x in rows) for i in range(6)]
            print(f"| `{label}` | {age} | {len(rows)} | {_mean(x['d0_cm'] for x in rows):.1f} | {_mean(x.get('stump_d_cm', x['d0_cm']) for x in rows):.1f} | {_mean(x['proximal_n'] for x in rows):.1f} | {_mean(x.get('dominant_n', 0) for x in rows):.1f} | "
                  f"{_mean(_mean(p['d_cm'] for p in x['proximal']) for x in rows):.1f} | {_mean(statistics.pstdev(p['d_cm'] for p in x['proximal']) for x in rows):.1f} | {', '.join(f'{v:.1f}' for v in top)} | {_mean(x.get('rel_sum_stump', x['rel_sum_d2']) for x in rows):.2f} | "
                  f"{_mean(_mean(p['depth_m'] for p in x['proximal']) for x in rows):.2f} | {_mean(x['reach_max_m'] for x in rows):.1f} | {_mean(x['depth_max_m'] for x in rows):.2f} | {_mean(x['depth_mean_m'] for x in rows):.2f} |")
    print("\nTaper along the six thickest roots: radius over base radius.  Published main axes (Kalliokoski Eq. 2, Table 7), mature MT: 0.74 at 0.25 m, 0.65 at 0.5 m, 0.48 at 1 m, 0.32 at 2 m, 0.17 at 5 m; pole MT: 0.63, 0.47, 0.33, 0.22, 0.13")
    print("| Set | Age | Seeds | 0.25 m | 0.5 m | 1 m | 2 m | 5 m |")
    print("|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for age in (30, 50, 60):
            ratios = []
            for r in runs.values():
                s = r["snap"].get(age)
                if not s or "root_arch" not in s:
                    continue
                for p in s["root_arch"]["proximal"][:6]:
                    if p["d_cm"] > 0:
                        ratios.append([200.0 * x / p["d_cm"] for x in p["r"]])
            if ratios:
                print(f"| `{label}` | {age} | {len({*runs})} | " + " | ".join(f"{_mean(x[i] for x in ratios):.2f}" for i in range(5)) + " |")
    print("\nThickest diameter of any root at 3 m (cm).  Laitakari 1934 p. 186: none fully 5 cm across its widest way, even on large trees.")
    print("| Set | Age | Seeds | Mean of the seeds' thickest | Largest seed |")
    print("|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for age in (50, 60):
            tops = [max((200.0 * p.get("r3", 0.0) for p in r["snap"][age]["root_arch"]["proximal"]), default=0.0) for r in runs.values() if age in r["snap"] and "root_arch" in r["snap"][age]]
            if tops:
                print(f"| `{label}` | {age} | {len(tops)} | {_mean(tops):.1f} | {max(tops):.1f} |")


def split(labels: list) -> None:
    print("Production a year over the five years to each age, kg of dry matter, as share of the tree's total: stem and branch wood kept (shed wood not counted), leaves made, root wood kept, fine roots made.")
    print("Published shares of tree production: Aosaar 2016 age 10: stem wood 49.5, bark 4.3, twigs and branches 6.7, leaves 21.6, stump and coarse roots 11.0, fine roots 6.8 %.  Varik 2014 Table 6, by carbon, at 13, 32, 45 years: leafless above ground 58, 56, 61; leaf litter 23, 23, 16; coarse roots 12, 10, 12; fine roots 7, 11, 11 %.")
    print("| Set | Age | Seeds | Stem wood (kg/yr) | Branches | Leaves | Root wood | Fine roots | Stem % | Branches % | Leaves % | Root wood % | Fine roots % | Root wood / above-ground wood gain |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for age in (30, 40, 50, 60):
            rows = []
            for r in runs.values():
                a, b = r["snap"].get(age - 5), r["snap"].get(age)
                if not a or not b or "root_arch" not in b:
                    continue
                stem = (b["stem_kg"] - a["stem_kg"]) / 5.0
                branch = (b["branch_kg"] - a["branch_kg"]) / 5.0
                years = [r["new"][y].get("root_ledger") or {} for y in range(age - 4, age + 1) if y in r["new"]]
                leaf = _mean(x.get("leaf_kg", 0.0) for x in years)
                root = (b["root_arch"]["total_kg"] - a["root_arch"]["total_kg"]) / 5.0
                turnover = 0.66
                fine = _mean(x.get("paid", {}).get("fine_build", 0.0) / 1.25 for x in years) or turnover * _mean(x.get("fine_kg", 0.0) for x in years)
                rows.append(dict(stem=stem, branch=branch, leaf=leaf, root=root, fine=fine))
            if not rows:
                continue
            m = lambda k: _mean(x[k] for x in rows)
            tot = m("stem") + m("branch") + m("leaf") + m("root") + m("fine")
            print(f"| `{label}` | {age} | {len(rows)} | {m('stem'):.2f} | {m('branch'):.2f} | {m('leaf'):.2f} | {m('root'):.2f} | {m('fine'):.2f} | {100 * m('stem') / tot:.0f} | {100 * m('branch') / tot:.0f} | {100 * m('leaf') / tot:.0f} | {100 * m('root') / tot:.0f} | {100 * m('fine') / tot:.0f} | {m('root') / max(m('stem') + m('branch'), 1e-9):.2f} |")


def anchor(labels: list) -> None:
    print("What treegen/damage.py reads.  Critical moment: Krisans 2022's 101 kN m per m3 of stem x rooting depth x asymmetry, the one uprooting uses.  Resistance from the plate and roots: Coutts 1986's form, numbers only.  Empirical: Krisans 2022, 25-38 kN m per m3 of H x DBH2, the species file's 31 here.  Plate radius: nothing published for birch found; Danjon 2005's taper zone on pine is 2.2 x DBH, the game's estimate for spruce 6-14 x DBH.")
    print("| Set | Age | Seeds | Plate radius (m) | Per DBH, over bark | Plate depth (m) | Soil's part (kN m) | Resistance from plate and roots (kN m) | Empirical H DBH2 (kN m) | Critical moment, mean (kN m) | Weakest wind direction (kN m) | Rooting depth (m) | Asymmetry factor, lowest-highest |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for label in labels:
        runs = _load(label)
        for age in (30, 50, 60):
            rows = [(r["snap"][age]["root_arch"]["anchorage"], r["per_year"][age]) for r in runs.values() if age in r["snap"] and "anchorage" in r["snap"][age].get("root_arch", {})]
            if not rows:
                continue
            m = lambda k: _mean(x[0].get(k) or 0.0 for x in rows)
            per_dbh = _mean((x[0].get("plate_radius_m") or 0.0) / max((x[1].get("dbh_cm") or 1.0) * OVER_BARK / 100.0, 1e-9) for x in rows)
            lo, hi = _mean((x[0].get("asymmetry_factor_range") or [0.0, 0.0])[0] for x in rows), _mean((x[0].get("asymmetry_factor_range") or [0.0, 0.0])[1] for x in rows)
            print(f"| `{label}` | {age} | {len(rows)} | {m('plate_radius_m'):.2f} | {per_dbh:.1f} | {m('plate_depth_m'):.2f} | {m('soil_weight_knm'):.1f} | {m('resistance_knm'):.1f} | {m('empirical_knm'):.1f} | {m('critical_knm'):.1f} | {m('critical_min_knm'):.1f} | {m('rooting_depth_m'):.2f} | {lo:.2f}-{hi:.2f} |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("ledger", "mass", "form", "anchor", "split"))
    ap.add_argument("labels", nargs="+")
    a = ap.parse_args(argv)
    {"ledger": ledger, "mass": mass, "form": form, "anchor": anchor, "split": split}[a.what](a.labels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
