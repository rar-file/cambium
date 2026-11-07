"""Why a limb's bark shows hoops, and how far it steps from one part of a limb to the next.

The branch atlas had one column to each circumference class, holding the mean bark of all the parts in the class, and a
face read its class's column by its radius.  So colour jumped wherever a limb crossed a class's edge.  This measures the
jump along each limb, nodes in order from its base, for that way and for columns by level of white (bark.uneven_top.limbs).
With --close, also the game's mesh of a few limbs, as it was and as it is now, the same cameras.

    python tools/limb_bark.py --label node_x --seeds 3,5,7 --ages 50,60 --sets cases/crown2.txt --close 5
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

E = ROOT / "out" / "bench" / "ensemble"


def measure(model, raw, age: int, seed: int) -> dict:
    import game_export as ge
    from treegen import appearance as ap
    from treegen import game_unreal as gu

    T = model.tree
    look = gu.unreal_look(ap.load_look(raw))
    pos, r_wood = ge.shoot_arrays(model, age)
    st = model.stats[age]
    dbh_ob = ap.over_bark_dbh_cm(look, st["dbh_cm"])
    alive = (T.birth[: T.n] <= age) & ((T.death[: T.n] < 0) | (T.death[: T.n] > age))
    idx = np.nonzero(alive)[0]
    part_age = age - np.asarray(T.birth[: T.n], float)
    state = ap.part_state(look, part_age[idx], 2.0 * r_wood[idx], pos[idx, 2], float(st["height_m"]), dbh_ob)
    names = [s["name"] for s in look["bark"]["stages"]]
    white = np.zeros(T.n)
    white[idx] = state["weights"][names.index("papery")]
    d_ob = np.zeros(T.n)
    d_ob[idx] = state["diameter_m"]
    # over bark, as the mesher has it
    classes = np.asarray(look["bark"]["branch_circumference_m"], float)
    edges = np.sqrt(classes[1:] * classes[:-1])
    cl = np.searchsorted(edges, np.pi * d_ob)
    parent = np.asarray(T.parent[: T.n])
    axis = np.asarray(T.axis[: T.n])
    seg = np.zeros(T.n)
    has = idx[parent[idx] >= 0]
    seg[has] = np.linalg.norm(pos[has] - pos[parent[has]], axis=1)
    # the old way: each class's column holds the area-weighted mean white of its parts
    area = np.pi * d_ob * seg
    mean_white = np.array([float((white[idx] * area[idx])[cl[idx] == k].sum() / max(area[idx][cl[idx] == k].sum(), 1e-12)) for k in range(len(classes))])
    step = float(look["bark"]["uneven_top"]["limbs"]["level_step"])
    # what a rule of whichever says white first, thickness or the plain 4-10 years of age, would whiten: thin parts past 10 years
    branch = idx[axis[idx] != 0]
    thin_old = float(area[branch][(d_ob[branch] < 0.025) & (part_age[branch] >= 10.0)].sum() / max(area[branch][d_ob[branch] < 0.025].sum(), 1e-12))
    thick_young = float(area[branch][(d_ob[branch] >= 0.05) & (part_age[branch] < 10.0)].sum() / max(area[branch][d_ob[branch] >= 0.05].sum(), 1e-12))
    limbs, crossings, reversals, widen, old_jump, new_jump = 0, [], [], [], [], []
    for a in np.unique(axis[idx]):
        nodes = idx[axis[idx] == a]
        if a == 0 or len(nodes) < 4 or d_ob[nodes].max() < 0.025:
            continue
        nodes = nodes[np.argsort(T.depth[nodes])]
        limbs += 1
        c = cl[nodes]
        crossings.append(int((np.diff(c) != 0).sum()))
        reversals.append(int((np.diff(c) > 0).sum()))
        widen.append(float((np.diff(d_ob[nodes]) > 0.0002).mean()))
        old_jump.append(float(np.abs(np.diff(mean_white[c])).max()))
        new_jump.append(float(np.abs(np.diff(np.rint(white[nodes] / step) * step)).max()))
    return {"seed": seed, "age": age, "thin_parts_past_10_years_share": round(thin_old, 3), "thick_parts_under_10_years_share": round(thick_young, 3), "by_class": [{"round_m": float(classes[k]), "d_ob_cm": [round(float((edges[k - 1] if k else 0.0) / np.pi * 100.0), 1), round(float((edges[k] if k < len(edges) else 1.0) / np.pi * 100.0), 1)],
                                                    "white_in_column": round(float(mean_white[k]), 3),
                                                    "white_of_its_parts_p5_p95": [round(float(np.percentile(white[idx][cl[idx] == k], q)), 3) for q in (5, 95)] if (cl[idx] == k).any() else None} for k in range(len(classes))],
            "limbs": limbs, "class_crossings_mean": round(float(np.mean(crossings)), 2), "limbs_that_go_back_up_a_class": round(float(np.mean(np.array(reversals) > 0)), 3),
            "share_of_steps_thicker_going_out": round(float(np.mean(widen)), 3), "largest_white_jump_old_p50_p95": [round(float(np.percentile(old_jump, q)), 3) for q in (50, 95)],
            "largest_white_jump_new_p50_p95": [round(float(np.percentile(new_jump, q)), 3) for q in (50, 95)]}


def one(seed: int, sets: list, ages: list, stand: bool) -> list:
    import game_export as ge

    model, _, raw, _ = ge.grow_with_leaves("betula_pendula", seed, ages, "sweden_open_field", stand, sets)
    return [measure(model, raw, a, seed) for a in ages]


def close_views(seed: int, sets: list, ages: list, stand: bool, out: Path, res: int, before: list | None = None, name: str = "limbs") -> None:
    """The same frame as tools/leaf_placement.py's twig view, then a limb close to, with its leaves off.
    ``before``: look values for the 'before' panels; without it, before is one column to a circumference."""
    import game_export as ge
    from treegen import look_render as lr

    folder = out / f"tmp_close_{seed}"
    state = folder / "state.pkl"
    last = max(ages)
    rows = {}
    tgt, limb_tgt = None, None
    if before is None:
        runs = (("before", ["bark.uneven_top.limbs.level_step=0"], last), ("after", [], last), ("after", [], min(ages)))
    else:
        runs = (("before", before, last), ("after", [], last), ("before", before, min(ages)), ("after", [], min(ages)))
    for k, (label, extra, age) in enumerate(runs):
        sub = folder / f"{k}_{age}"
        a = argparse.Namespace(species="betula_pendula", environment="sweden_open_field", seed=seed, ages=str(age) if state.exists() else ",".join(str(x) for x in ages), seasons="summer", out=str(sub), stand=stand, set=list(sets), budget=[], target="unreal",
                               look=["bark.uneven_top.strength=1"] + list(extra), state=str(state), levels="")
        ge.main_export(a)
        doc = json.loads((sub / "game_manifest.json").read_text(encoding="utf-8"))
        s = next(x for x in doc["stages"] if x["age"] == age)
        prims = lr.load_glb_primitives(sub / s["seasons"]["summer"]["lod0"]["file"])
        gz = np.array([0.0, 0.0, float(s["origin"]["ground_in_file_m"])], np.float32)
        for p in prims:
            p.V = p.V - gz
        H = float(s["height_m"])
        leaf = next(p for p in prims if p.name == "leaves")
        if tgt is None:
            V = leaf.V[::7]
            band = V[(V[:, 2] > 0.62 * H) & (V[:, 2] < 0.72 * H)]
            depth = band @ ge.CAM
            tgt = np.median(band[depth > np.percentile(depth, 96.0)], axis=0)
            wood = next(p for p in prims if p.name == "branches")
            W = wood.V[::3]
            near = W[(W[:, 2] > 0.5 * H) & (W[:, 2] < 0.8 * H)]
            d = near @ ge.CAM
            limb_tgt = np.median(near[d > np.percentile(d, 90.0)], axis=0)
        eye = tgt + ge.CAM * 2.0 + np.array([0.0, 0.0, -0.25])
        lights = lr.Lights(prims, ge.sun_for_camera(), res=4096, sky_res=640, sky_dirs=8, focus=(tgt, 6.0))
        whole = ge._label(lr.render(prims, lr.View(eye, tgt, res, res, fov_deg=34.0), lights, ss=2), f"seed {seed}, age {age}: {label}", 22)
        woods = ge.wood_only(prims)
        eye2 = limb_tgt + ge.CAM * 3.0 + np.array([0.0, 0.0, -0.5])
        lights2 = lr.Lights(woods, ge.sun_for_camera(), res=4096, sky_res=640, sky_dirs=8, focus=(limb_tgt, 6.0))
        bare = ge._label(lr.render(woods, lr.View(eye2, limb_tgt, res, res, fov_deg=34.0), lights2, ss=2), f"no leaves: {label}, age {age}", 22)
        rows[k] = (whole, bare)
        del prims, woods, leaf
    keys = list(rows)
    ge._save(np.concatenate([ge._row([rows[k][0] for k in keys]), ge._row([rows[k][1] for k in keys])], axis=0), out / f"{name}_s{seed}.png")
    shutil.rmtree(folder, ignore_errors=True)


def main(argv=None) -> int:
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap_.add_argument("--label", required=True)
    ap_.add_argument("--seeds", default="3,5,7")
    ap_.add_argument("--ages", default="50,60")
    ap_.add_argument("--open", action="store_true")
    ap_.add_argument("--close", type=int, default=None, help="also the close views of this seed")
    ap_.add_argument("--res", type=int, default=800)
    ap_.add_argument("--before", action="append", default=None, metavar="KEY=JSON", help="look values for the close views' 'before'")
    ap_.add_argument("--name", default="limbs", help="the close views' file name")
    ap_.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap_.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    a = ap_.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    seeds = [int(x) for x in a.seeds.split(",")]
    ages = [int(x) for x in a.ages.split(",")]
    out = E / a.label
    out.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(min(int(os.environ.get("ORIGIN_MAX_WORKERS", "2")), len(seeds))) as ex:
        rows = [r for many in ex.map(one, seeds, [a.set] * len(seeds), [ages] * len(seeds), [not a.open] * len(seeds)) for r in many]
    (out / "limb_bark.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for r in rows:
        print(json.dumps(r), flush=True)
    if a.close is not None:
        close_views(a.close, a.set, ages, not a.open, out, a.res, a.before, a.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
