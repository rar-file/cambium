"""How the mesher places leaves along a twig, measured on grown trees, with leaves.on_shoots off and on.

Orders count from the stem as the mesher draws it (a replaced leader is still the stem).  A twig is an axis with no
living axis of its own.  Overlap: on sample twigs, the share of the blades' area seen side on that another blade of the
same twig hides.  Fill: how much of the crown's outline leaves cover, side on and from above.  Nothing here changes the
tree.  With --close, also a view of a few twigs in the game's own mesh, off and on.

    python tools/leaf_placement.py --label node_x --seeds 3,5,7 --ages 50,60 --sets cases/crown2.txt --close 5
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

E = ROOT / "out" / "bench" / "ensemble"


def axis_orders(T, pos, r_wood, alive, stub_share: float) -> tuple:
    """Each node's axis as the mesher draws the stem, and each axis's order from the stem (the stem is 0)."""
    from treegen import mesh as meshlib

    view = meshlib.continue_trunk(SimpleNamespace(n=T.n, pos=pos, parent=T.parent, axis=T.axis, is_lateral=T.is_lateral, order=T.order, birth=T.birth, death=T.death, depth=T.depth), alive, r_wood, stub_share)
    axis = np.asarray(view.axis[: T.n])
    parent = np.asarray(T.parent[: T.n])
    order = {}
    for i in np.nonzero(alive)[0]:             # a parent comes before its children
        a = int(axis[i])
        if a in order:
            continue
        p = int(parent[i])
        order[a] = 0 if a == 0 or p < 0 else order.get(int(axis[p]), 0) + 1
    return axis, order


def twig_table(T, pos, r_wood, alive, per_node: np.ndarray, area: np.ndarray, is_spur: np.ndarray, stub_share: float) -> tuple:
    """Axes that carry leaves, by order from the stem, and the twigs among them."""
    axis, order = axis_orders(T, pos, r_wood, alive, stub_share)
    parent = np.asarray(T.parent[: T.n])
    idx = np.nonzero(alive)[0]
    seg = np.zeros(T.n)
    has = idx[parent[idx] >= 0]
    seg[has] = np.linalg.norm(pos[has] - pos[parent[has]], axis=1)
    same = has[axis[parent[has]] == axis[has]]
    length, spurs, leaf_m2, leaf_n, kids = {}, {}, {}, {}, set()
    for i in idx:
        a = int(axis[i])
        spurs[a] = spurs.get(a, 0) + int(is_spur[i])
        leaf_m2[a] = leaf_m2.get(a, 0.0) + float(per_node[i] * area[i])
        leaf_n[a] = leaf_n.get(a, 0) + int(per_node[i])
        length.setdefault(a, 0.0)
    for i in same:
        length[int(axis[i])] += float(seg[i])
    for i in has[axis[parent[has]] != axis[has]]:
        kids.add(int(axis[parent[i]]))
    total = sum(leaf_m2.values())
    rows = {}
    for o in sorted(set(order.values())):
        ax = [a for a, v in order.items() if v == o and leaf_n.get(a, 0) > 0 and length.get(a, 0.0) > 0.0]
        if ax:
            sum_len = sum(length[a] for a in ax)
            rows[str(o)] = {"axes": len(ax), "median_m": round(float(np.median([length[a] for a in ax])), 2), "short_shoots_per_m": round(sum(spurs[a] for a in ax) / sum_len, 1),
                            "leaf_m2_per_m": round(sum(leaf_m2[a] for a in ax) / sum_len, 3), "leaves_per_m": round(sum(leaf_n[a] for a in ax) / sum_len, 1), "share_of_leaf_area": round(sum(leaf_m2[a] for a in ax) / total, 3)}
    twigs = [a for a, v in order.items() if a not in kids and v > 0 and leaf_n.get(a, 0) > 0 and length.get(a, 0.0) > 0.0]
    sum_len = sum(length[a] for a in twigs)
    tw = {"axes": len(twigs), "median_m": round(float(np.median([length[a] for a in twigs])), 2), "short_shoots_per_m": round(sum(spurs[a] for a in twigs) / sum_len, 1),
          "leaf_m2_per_m": round(sum(leaf_m2[a] for a in twigs) / sum_len, 3), "leaves_per_m": round(sum(leaf_n[a] for a in twigs) / sum_len, 1), "share_of_leaf_area": round(sum(leaf_m2[a] for a in twigs) / total, 3),
          "orders": {str(o): sum(1 for a in twigs if order[a] == o) for o in sorted({order[a] for a in twigs})}}
    return rows, tw, axis, twigs


def blade_points(leaves, which: np.ndarray, per_side: int) -> tuple:
    """Points evenly over each blade's diamond, of the blade's own area: (points, the blade each is on)."""
    t = (np.arange(per_side) + 0.5) / per_side
    tt, ss = np.meshgrid(t, 2.0 * t - 1.0, indexing="ij")
    tt, ss = tt.ravel(), ss.ravel()
    w0 = 0.34
    half = np.where(tt < w0, tt / w0, (1.0 - tt) / (1.0 - w0))
    keep = np.abs(ss) <= half
    tt, ss = tt[keep], ss[keep]
    a, c, b = leaves.along[which], leaves.across[which], leaves.base[which]
    L = np.sqrt(2.0 * leaves.area[which] * 1.32)
    W = L / 1.32
    P = b[:, None, :] + a[:, None, :] * (L[:, None] * tt)[..., None] + c[:, None, :] * (0.5 * W[:, None] * ss)[..., None]
    return P.reshape(-1, 3), np.repeat(np.arange(len(which)), len(tt))


def twig_overlap(leaves, axis_of_leaf: np.ndarray, twigs: list, rng, cell: float = 0.002, sample: int = 150) -> dict:
    """Side on, on sample twigs: how much of the blades' area another blade of the same twig hides, how far the leaves reach out from the twig, and how wide the twig's leaves look per metre."""
    pick = [a for a in twigs if (axis_of_leaf == a).sum() >= 8]
    if not pick:
        return {}
    pick = list(rng.permutation(pick)[: sample])
    overlap, reach, widths = [], [], []
    for a in pick:
        which = np.nonzero(axis_of_leaf == a)[0]
        P, _ = blade_points(leaves, which, 26)
        centre = leaves.pos_node[which]
        reach.append(float(np.percentile(np.linalg.norm(leaves.base[which] + leaves.along[which] * leaves.length[which, None] * 0.5 - centre, axis=1), 80)))
        for turn in rng.uniform(0.0, np.pi, 3):
            view = np.array([np.cos(turn), np.sin(turn), 0.0])
            right = np.array([-np.sin(turn), np.cos(turn), 0.0])
            grid = np.stack([np.floor(P @ right / cell), np.floor(P[:, 2] / cell)], 1).astype(np.int64)
            seen = len(np.unique(grid, axis=0))
            ideal_points = P.shape[0] / len(which)
            per_blade = np.array_split(grid, len(which))
            each = sum(len(np.unique(g, axis=0)) for g in per_blade)
            overlap.append(1.0 - seen / max(each, 1))
            rows = np.unique(grid[:, 1])
            widths.append(seen * cell * cell / max(len(rows) * cell, 1e-6))
            del view, ideal_points
    return {"twigs": len(pick), "overlap_share": round(float(np.mean(overlap)), 3), "reach_m": round(float(np.mean(reach)), 3), "seen_width_m": round(float(np.mean(widths)), 3)}


def crown_fill(leaves, rng, cell: float = 0.03) -> dict:
    """How much of the crown's outline leaves cover: side on, and from above."""
    which = rng.permutation(len(leaves.node))[: 400000]
    P, _ = blade_points(leaves, which, 7)
    out = []
    for turn in (0.0, 0.8, 1.6, 2.4):
        right = np.array([-np.sin(turn), np.cos(turn), 0.0])
        g = np.stack([np.floor(P @ right / cell), np.floor(P[:, 2] / cell)], 1).astype(np.int64)
        g = np.unique(g, axis=0)
        total = 0
        for z in np.unique(g[:, 1]):
            x = g[g[:, 1] == z, 0]
            total += int(x.max() - x.min() + 1)
        out.append(len(g) / max(total, 1))
    g = np.unique(np.floor(P[:, :2] / cell).astype(np.int64), axis=0)
    total = sum(int(g[g[:, 1] == y, 0].max() - g[g[:, 1] == y, 0].min() + 1) for y in np.unique(g[:, 1]))
    return {"side_on": round(float(np.mean(out)), 3), "from_above": round(len(g) / max(total, 1), 3)}


def measure(model, sp, raw, snap, age: int, seed: int) -> dict:
    import game_export as ge
    from treegen import appearance as ap
    from treegen import game_unreal as gu

    T = model.tree
    pos, r_wood = ge.shoot_arrays(model, age)
    alive = (T.birth[: T.n] <= age) & ((T.death[: T.n] < 0) | (T.death[: T.n] > age))
    look = gu.unreal_look(ap.load_look(raw))
    stub = ap.stem_stub_share({**look, "bark": {**look["bark"], "uneven_top": {**look["bark"]["uneven_top"], "strength": 1.0}}})
    height = float(model.stats[age]["height_m"])
    out = {"seed": seed, "age": age, "height_m": round(height, 2)}
    res = {}
    for name, strength in (("off", 0.0), ("on", 1.0)):
        lk = copy.deepcopy(look)
        lk["leaves"]["on_shoots"]["strength"] = strength
        leaves = ap.leaf_instances(lk, sp, snap, pos, r_wood, age, 1.0)
        z_rel = np.clip(pos[leaves.node, 2] / max(height, 1e-3), 0.0, 1.0)
        leaves = gu.hang_leaves(leaves, z_rel, lk["game"]["unreal"]["leaf"])
        leaves.pos_node = pos[leaves.node]
        res[name] = leaves
    off, on = res["off"], res["on"]
    assert np.array_equal(off.node, on.node) and np.array_equal(off.area, on.area)
    per_node = np.bincount(off.node, minlength=T.n).astype(float)
    area = np.zeros(T.n)
    np.add.at(area, off.node, off.area)
    area = area / np.maximum(per_node, 1.0)
    spur = np.asarray(snap.is_spur[: T.n]) & alive
    new = (np.asarray(T.birth[: T.n]) == age) & alive & ~spur
    # what's on a node
    counts = {"short_shoot_leaves_mean": round(float(per_node[spur & (per_node > 0)].mean()), 2) if (spur & (per_node > 0)).any() else None,
              "short_shoot_share_with": {str(k): round(float((per_node[spur] == k).mean()), 3) for k in range(0, 6)},
              "new_long_node_leaves_mean": round(float(per_node[new].mean()), 2) if new.any() else None,
              "new_long_node_share_with": {str(k): round(float((per_node[new] == k).mean()), 3) for k in range(0, 6)} if new.any() else None,
              "short_shoots": int(spur.sum()), "new_long_nodes": int(new.sum()),
              "leaves": int(len(off.node)), "leaf_area_m2": round(float(off.area.sum()), 3), "model_leaf_area_m2": model.stats[age]["leaf_area_m2"], "model_leaves_reference_units": model.stats[age]["leaves"]}
    out["on_nodes"] = counts
    out["leaf_size_cm2"] = {"median": round(float(np.median(off.area)) * 1e4, 1), "p10": round(float(np.percentile(off.area, 10)) * 1e4, 1), "p90": round(float(np.percentile(off.area, 90)) * 1e4, 1)}
    # the twigs, by order from the stem
    rows, tw, axis, twigs = twig_table(T, pos, r_wood, alive, per_node, area, spur, stub)
    out["by_order"], out["twigs"] = rows, tw
    rng = np.random.default_rng(seed + age)
    for name, leaves in res.items():
        r = r_wood[np.minimum(leaves.node, len(r_wood) - 1)]
        stand = np.linalg.norm(leaves.base - leaves.pos_node, axis=1) - r
        slope = np.degrees(np.arcsin(np.clip(-leaves.along[:, 2], -1.0, 1.0)))
        az = np.arctan2(leaves.along[:, 1], leaves.along[:, 0])
        # pairs of a node's leaves within 30 degrees of each other, which is where they lie on each other
        starts = np.r_[0, np.nonzero(np.diff(leaves.node))[0] + 1]
        close, pairs = 0, 0
        for s, e in zip(starts, np.r_[starts[1:], len(az)]):
            if e - s > 1:
                gaps = np.abs((az[s:e, None] - az[s:e][None, :] + np.pi) % (2.0 * np.pi) - np.pi)[np.triu_indices(e - s, 1)]
                close += int((gaps < np.radians(30.0)).sum())
                pairs += len(gaps)
        isp = spur[leaves.node]
        placed = {"stand_off_short_shoot_mm": [round(float(np.percentile(stand[isp], q)) * 1e3, 1) for q in (10, 50, 90)],
                  "stand_off_long_node_mm": [round(float(np.percentile(stand[~isp], q)) * 1e3, 1) for q in (10, 50, 90)],
                  "slope_before_curl_deg": [round(float(np.percentile(slope, q)), 1) for q in (10, 50, 90)], "pairs_within_30_deg": round(close / max(pairs, 1), 3)}
        placed["twig"] = twig_overlap(leaves, axis[leaves.node], twigs, np.random.default_rng(seed + age + 1))
        placed["crown_fill"] = crown_fill(leaves, np.random.default_rng(seed + age + 2))
        out[name] = placed
    return out


def one(seed: int, sets: list, ages: list, stand: bool) -> list:
    import game_export as ge

    model, sp, raw, snaps = ge.grow_with_leaves("betula_pendula", seed, ages, "sweden_open_field", stand, sets)
    return [measure(model, sp, raw, snaps[a], a, seed) for a in ages]


def close_views(seed: int, sets: list, age: int, stand: bool, out: Path, res: int) -> None:
    """A few twigs in the game's own mesh, leaves as they were and as they are now, the same camera."""
    import game_export as ge
    from treegen import look_render as lr

    folder = out / f"tmp_close_{seed}"
    state = folder / "state.pkl"
    panels = []
    for name, strength in (("before: on no shoot", 0), ("after: on their shoots", 1)):
        sub = folder / str(strength)
        a = argparse.Namespace(species="betula_pendula", environment="sweden_open_field", seed=seed, ages=str(age), seasons="summer", out=str(sub), stand=stand, set=list(sets), budget=[], target="unreal",
                               look=["bark.uneven_top.strength=1", f"game.unreal.leaf.on_shoots={strength}"], state=str(state), levels="")
        ge.main_export(a)
        doc = json.loads((sub / "game_manifest.json").read_text(encoding="utf-8"))
        s = doc["stages"][0]
        prims = lr.load_glb_primitives(sub / s["seasons"]["summer"]["lod0"]["file"])
        gz = np.array([0.0, 0.0, float(s["origin"]["ground_in_file_m"])], np.float32)
        for p in prims:
            p.V = p.V - gz
        H = float(s["height_m"])
        leaf = next(p for p in prims if p.name == "leaves")
        # the crown's nearest side, at the same place in both: from the off version
        if strength == 0:
            V = leaf.V[::7]
            band = V[(V[:, 2] > 0.62 * H) & (V[:, 2] < 0.72 * H)]
            depth = band @ ge.CAM
            front = band[depth > np.percentile(depth, 96.0)]
            tgt = np.median(front, axis=0)
        eye = tgt + ge.CAM * 2.0 + np.array([0.0, 0.0, -0.25])
        lights = lr.Lights(prims, ge.sun_for_camera(), res=4096, sky_res=640, sky_dirs=8, focus=(tgt, 6.0))
        panels.append(ge._label(lr.render(prims, lr.View(eye, tgt, res, res, fov_deg=34.0), lights, ss=2), f"seed {seed}, age {age}: {name}", 22))
        del prims, leaf
    ge._save(ge._row(panels), out / f"twigs_s{seed}_{age}.png")
    shutil.rmtree(folder, ignore_errors=True)


def main(argv=None) -> int:
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap_.add_argument("--label", required=True)
    ap_.add_argument("--seeds", default="3,5,7")
    ap_.add_argument("--ages", default="50,60")
    ap_.add_argument("--open", action="store_true")
    ap_.add_argument("--close", type=int, default=None, help="also a close view of this seed's twigs, at the last age")
    ap_.add_argument("--res", type=int, default=900)
    ap_.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap_.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    a = ap_.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    seeds = [int(x) for x in a.seeds.split(",")]
    ages = [int(x) for x in a.ages.split(",")]
    out = E / a.label
    out.mkdir(parents=True, exist_ok=True)
    if seeds and seeds != [0]:
        with ProcessPoolExecutor(min(int(os.environ.get("ORIGIN_MAX_WORKERS", "2")), len(seeds))) as ex:
            rows = [r for many in ex.map(one, seeds, [a.set] * len(seeds), [ages] * len(seeds), [not a.open] * len(seeds)) for r in many]
        (out / "leaf_placement.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
        for r in rows:
            print(json.dumps({k: r[k] for k in ("seed", "age", "height_m", "leaf_size_cm2", "on_nodes", "twigs")}), flush=True)
            print(json.dumps({"by_order": r["by_order"]}), flush=True)
            print(json.dumps({"off": r["off"]}), flush=True)
            print(json.dumps({"on": r["on"]}), flush=True)
    if a.close is not None:
        close_views(a.close, a.set, max(ages), not a.open, out, a.res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
