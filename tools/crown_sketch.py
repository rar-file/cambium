"""A quick side view of grown trees, wood alone and wood with leaves, for judging limbs and crown shape before a full render.

No meshes, no textures: every living internode is a line as wide as its wood, every leafy node a dot.  Light on disk and quick, so it can be run
on every attempt; the real look is still tools/game_export.py.  It only reads the model.  Also writes the limbs' sizes as limbs_s<seed>.json.

    python tools/crown_sketch.py --label node_c2x --seeds 3,5,7 --ages 30,50,60 --open --set crown_frame.enabled=true ...
"""
from __future__ import annotations

import numpy as np
import argparse
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

E = ROOT / "out" / "bench" / "ensemble"
WOOD = (58, 46, 40)
THICK = (150, 140, 128)
LEAF = (74, 112, 52)
SKY = (236, 240, 244)


def limb_table(model) -> dict:
    """Each limb's base diameter (cm), length along its axis (m), and leaf area (m2) beyond it, largest first."""
    import numpy as np

    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    on = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    limbs = np.nonzero(alive & T.is_lateral[:n] & ~on & on[np.maximum(T.parent[:n], 0)])[0]
    leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
    la = T.basipetal(T.levels(alive), leaves) * float(model.light.leaf_area)
    length = np.bincount(T.axis[:n][alive], weights=T.length[:n][alive], minlength=int(T.axis[:n].max()) + 1)
    rows = sorted(((round(200.0 * float(T.radius[i]), 2), round(float(length[T.axis[i]]), 2), round(float(la[i]), 2), round(float(T.pos[T.parent[i], 2]), 2)) for i in limbs), reverse=True)
    # where the branch wood is, kg, by the thickness of the wood: under 1, 1-2, 2-5, over 5 cm
    vol = np.where(alive & ~on, math.pi * T.radius[:n] ** 2 * T.length[:n], 0.0) * 530.0
    d = 200.0 * T.radius[:n]
    by_d = [round(float(vol[(d >= a) & (d < b)].sum()), 1) for a, b in ((0.0, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 1e9))]
    metres = [round(float(np.where(alive & ~on, T.length[:n], 0.0)[(d >= a) & (d < b)].sum()), 0) for a, b in ((0.0, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 1e9))]
    return {"age": int(model.year), "height_m": float(model.stats[-1]["height_m"]), "dbh_cm": model.stats[-1]["dbh_cm"], "limbs": rows, "wood_by_d": by_d, "metres_by_d": metres}


def foliage_table(model) -> dict:
    """Where the leaves are, and how twigs start and live.  Orders count from the stem as it is now: a replacement leader is stem, so T.order can't be used.  A limb is an axis off the stem, a twig an axis off a limb.
    Places: how far out a leaf stands against the crown's radius at its own height (a crown that tapers has few leaves far out at its top for that reason alone), and how far out a twig starts along its own limb."""
    import numpy as np

    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    on = np.isin(T.axis[:n], np.fromiter(model.leader_axes, np.int64))
    la = np.where(alive, T.leaves[:n], 0.0).astype(float) * float(model.light.leaf_area)
    length = np.where(alive, T.length[:n], 0.0)
    par = T.parent[:n]
    # every node once made, dead ones included, by parent before child: node numbers grow outward
    rel = np.zeros(n, np.int64)
    limb_of = np.full(n, -1, np.int64)
    twig_of = np.full(n, -1, np.int64)
    lat = T.is_lateral[:n]
    for i in range(1, n):
        pi = par[i]
        if on[i]:
            continue
        rel[i] = rel[pi] + (1 if (lat[i] or on[pi]) else 0)
        limb_of[i] = i if on[pi] else limb_of[pi]
        twig_of[i] = i if (rel[i] == 2 and lat[i] and rel[pi] == 1) else twig_of[pi]
    order = np.minimum(rel, 5)
    spur = alive & (T.lat[:n] == 2)
    out = {"la_m2": round(float(la.sum()), 1), "by_order": {}, "by_wood_age": {}}
    for k in range(6):
        hit = order == k
        m = float(length[hit].sum())
        nodes = int((hit & alive).sum())
        out["by_order"][k] = {"metres": round(m, 1), "la_m2": round(float(la[hit].sum()), 1), "la_per_m": round(float(la[hit].sum()) / max(m, 1e-9), 3), "spurs_per_m": round(float((spur & hit).sum()) / max(m, 1e-9), 2),
                              "axes": int(np.unique(T.axis[:n][hit & alive]).size), "nodes_per_m": round(nodes / max(m, 1e-9), 1), "spur_share": round(float((spur & hit).sum()) / max(nodes, 1), 3)}
    age = int(model.year) - T.birth[:n]
    for name, lo, hi in (("0-2", 0, 3), ("3-5", 3, 6), ("6-10", 6, 11), ("11-20", 11, 21), ("21+", 21, 10000)):
        hit = (age >= lo) & (age < hi)
        m = float(length[hit].sum())
        limb_axis = order == 1
        mb = float(length[hit & limb_axis].sum())
        out["by_wood_age"][name] = {"metres": round(m, 1), "la_m2": round(float(la[hit].sum()), 1), "la_per_m": round(float(la[hit].sum()) / max(m, 1e-9), 3), "limb_axis_metres": round(mb, 1),
                                    "limb_axis_spurs_per_m": round(float((spur & hit & limb_axis).sum()) / max(mb, 1e-9), 2)}
    stem = np.nonzero(on & alive)[0]
    r = np.hypot(T.pos[:n, 0] - np.interp(T.pos[:n, 2], *_sorted_xy(T, stem, 0)), T.pos[:n, 1] - np.interp(T.pos[:n, 2], *_sorted_xy(T, stem, 1)))
    leafy = la > 0.0
    H = float(T.pos[:n, 2][alive].max())
    band = np.clip((T.pos[:n, 2] / H * 20).astype(np.int64), 0, 19)
    rlocal = np.ones(n)
    for b in range(20):
        hit = leafy & (band == b)
        if hit.sum() >= 20:
            rlocal[band == b] = max(float(np.percentile(r[hit], 95)), 1e-3)
    rr = r / rlocal
    q = np.zeros(n)
    dg = model.diag
    q[np.minimum(dg["term_nodes"], n - 1)] = dg["Qterm"]
    q[np.minimum(dg["lat_nodes"], n - 1)] = dg["Qlat"]
    out["by_radius_at_height"] = {}
    for name, lo, hi, plan in (("0-25", 0.0, 0.25, 0.0625), ("25-50", 0.25, 0.5, 0.1875), ("50-75", 0.5, 0.75, 0.3125), ("75-100", 0.75, 1.0, 0.4375), ("beyond", 1.0, 99.0, 0.0)):
        hit = leafy & (rr >= lo) & (rr < hi)
        lit = hit & (q > 0.0)
        out["by_radius_at_height"][name] = {"share": round(float(la[hit].sum()) / max(float(la.sum()), 1e-9), 3), "plan": plan, "light": round(float(np.average(q[lit], weights=la[lit])), 3) if lit.any() else 0.0}
    # how far each limb reaches, then where along it each twig starts
    limb_reach = np.zeros(n)
    limb_nodes = limb_of >= 0
    np.maximum.at(limb_reach, limb_of[limb_nodes & (rel == 1)], r[limb_nodes & (rel == 1)])
    twigs = np.nonzero((twig_of == np.arange(n)))[0]
    start = r[par[twigs]] / np.maximum(limb_reach[limb_of[twigs]], 1e-3)
    now = int(model.year)
    live_leaf = np.bincount(twig_of[(twig_of >= 0) & leafy], weights=la[(twig_of >= 0) & leafy], minlength=n)
    live_light = np.bincount(twig_of[(twig_of >= 0) & leafy], weights=(la * q)[(twig_of >= 0) & leafy], minlength=n)
    rows = {}
    for name, lo, hi in (("inner third", -1.0, 1.0 / 3.0), ("middle third", 1.0 / 3.0, 2.0 / 3.0), ("outer third", 2.0 / 3.0, 99.0)):
        hit = twigs[(start >= lo) & (start < hi)]
        live = hit[alive[hit]]
        dead = hit[~alive[hit]]
        life = T.death[dead] - T.birth[dead]
        rows[name] = {"born": int(hit.size), "alive": int(live.size), "dead": int(dead.size), "median_life_of_dead": round(float(np.median(life)), 1) if dead.size else 0.0, "median_age_of_live": round(float(np.median(now - T.birth[live])), 1) if live.size else 0.0,
                      "la_m2": round(float(live_leaf[live].sum()), 1), "la_per_live_twig": round(float(live_leaf[live].mean()), 3) if live.size else 0.0, "light": round(float(live_light[live].sum() / max(live_leaf[live].sum(), 1e-9)), 3)}
    out["twigs_by_start"] = rows
    out["limbs_alive"] = int((alive & (limb_of == np.arange(n))).sum())
    out["limb_reach_median_m"] = round(float(np.median(limb_reach[(limb_of == np.arange(n)) & alive])), 2) if (alive & (limb_of == np.arange(n))).any() else 0.0
    axes = T.axis[:n]
    tw = alive & (order >= 2)
    lens = np.bincount(axes[tw], weights=length[tw]) if tw.any() else np.zeros(1)
    lens = lens[lens > 0.0]
    out["twig_axis_len_m"] = {"n": int(lens.size), "median": round(float(np.median(lens)), 2) if lens.size else 0.0, "p90": round(float(np.percentile(lens, 90)), 2) if lens.size else 0.0}
    return out


def _sorted_xy(T, stem, c):
    order = np.argsort(T.pos[stem, 2])
    return T.pos[stem, 2][order], T.pos[stem, c][order]


def draw(model, ppm: float, leaves: bool, label: str, width_m: float, height_m: float):
    import numpy as np
    from PIL import Image, ImageDraw

    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    ss = 2
    w, h = int(width_m * ppm * ss), int(height_m * ppm * ss)
    im = Image.new("RGB", (w, h), SKY)
    d = ImageDraw.Draw(im)
    P = T.pos[:n]
    u = 0.5 * w + P[:, 0] * ppm * ss
    v = h - P[:, 2] * ppm * ss
    idx = np.nonzero(alive & (T.parent[:n] >= 0))[0]
    # thin first, so thick wood lies on top
    idx = idx[np.argsort(T.radius[idx])]
    par = T.parent[idx]
    if leaves:
        leafy = np.nonzero(alive & (T.leaves[:n] > 0))[0]
        rr = 0.04 * ppm * ss
        for i in leafy.tolist():
            d.ellipse((u[i] - rr, v[i] - rr, u[i] + rr, v[i] + rr), fill=LEAF)
    for i, p in zip(idx.tolist(), par.tolist()):
        r = float(T.radius[i])
        if leaves and r < 0.004:
            continue
        width = max(1, int(round(2.0 * r * ppm * ss * 1.5)))
        c = THICK if r > 0.015 else WOOD
        d.line((u[p], v[p], u[i], v[i]), fill=c, width=width)
    d.text((6, 6), label, fill=(0, 0, 0))
    return im.resize((w // ss, h // ss), Image.LANCZOS)


def one(seed: int, sets: list, ages: list, stand: bool, out: Path) -> str:
    import numpy as np
    from PIL import Image

    from treegen import checkpoint
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    sp, _ = load_species("betula_pendula")
    checkpoint.set_values(sp, sets)
    env_p, _ = load_environment("sweden_open_field")
    model = GrowthModel(sp, make_environment(env_p), seed, stand=stand, soil=make_soil(env_p), lean=True)
    panels, tables = [], []
    for year in range(1, max(ages) + 1):
        model.step()
        if year in ages:
            s = model.stats[-1]
            d = s["dbh_cm"] or 0.0
            tag = f"seed {seed} age {year}: {s['height_m']:.1f} m, dbh {d:.1f} wood, width {s['crown_width_m']:.1f}, LA {s['leaf_area_m2']:.0f}, CR {s.get('crown_ratio') or 0.0:.2f}"
            ppm = 28.0
            panels.append(draw(model, ppm, False, tag, 16.0, 26.0))
            panels.append(draw(model, ppm, True, "", 16.0, 26.0))
            tables.append({**limb_table(model), "foliage": foliage_table(model)})
    W = sum(p.size[0] for p in panels)
    H = max(p.size[1] for p in panels)
    im = Image.new("RGB", (W, H), (255, 255, 255))
    x = 0
    for p in panels:
        im.paste(p, (x, 0))
        x += p.size[0]
    out.mkdir(parents=True, exist_ok=True)
    im.save(out / f"sketch_s{seed}.png", optimize=True)
    (out / f"limbs_s{seed}.json").write_text(json.dumps(tables), encoding="utf-8")
    return f"seed {seed} done"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", required=True)
    ap.add_argument("--seeds", default="3,5,7")
    ap.add_argument("--ages", default="30,60")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    a = ap.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    seeds = [int(x) for x in a.seeds.split(",")]
    ages = [int(x) for x in a.ages.split(",")]
    workers = min(int(os.environ.get("ORIGIN_MAX_WORKERS", "2")), len(seeds))
    out = E / a.label
    with ProcessPoolExecutor(workers) as ex:
        for msg in ex.map(one, seeds, [a.set] * len(seeds), [ages] * len(seeds), [not a.open] * len(seeds), [out] * len(seeds)):
            print(msg, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
