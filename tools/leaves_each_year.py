"""Leaves that come back new each spring (appearance.leaves.each_year): one tree, with the setting off and on.
On is the default since 2026-11-12, so "on" here is a plain export and "off" is the same export with its --timelapse option.

Grows a tree once and writes it at each age asked for, off and on: for the game (the Unreal target, summer), and at the ages of the
pairs as the plain export as well (its near level only).  From those files, in this project's own renderer, one short shoot's leaves at
two ages a year apart, from one camera, off above and on below:

    cluster_plain_*.png          the plain export, the shoot by itself.  Off, its leaves come back exactly as they were; on, each
                                 is on the side of the twig it was on, and hangs anew
    cluster_game_*.png           the game target, the same shoot by itself.  Off, each leaf's droop already shifts a little from year
                                 to year there, because that target draws it by the leaf's place in the tree's list
    in_the_crown_game_*.png      the game target, with the crown round the shoot (left out with --no-crown)
    whole_game_*.png             the game target, the whole tree

The first pair of ages shows a shoot with three leaves a year, the second one with two.  On the grown tree it also counts what a year
changes and what it leaves alone (each_year.json): the leaves on the same node with the same number in both years, in the plain
export's placing and in the game's (how far they turned, how far a blade's base moved against its node, and in the game's mesh the
stalk's start on the bark); each node's leaf area against last year's; how the leaves are tilted; and how many short shoots kept
their number of leaves.
Nothing here changes the tree, and the files it wrote are deleted when it's done.

    python tools/leaves_each_year.py --label node_x --seed 5 --pairs 49-50,59-60 --whole 50,60
"""
from __future__ import annotations

import argparse
import copy
import json
import pickle
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

E = ROOT / "out" / "bench" / "ensemble"
SETTING = (("off", True), ("on", False))      # name, and whether the export is given its time-lapse option
SAID = {"off": "--timelapse (leaves.each_year off)", "on": "the default (leaves.each_year on)"}


def leaf_ids(leaves) -> np.ndarray:
    """Node and number on the node, as one id: the same leaf's place from year to year."""
    return leaves.node * 64 + (np.arange(len(leaves.node)) - np.searchsorted(leaves.node, leaves.node))


def plane_tilt(leaves) -> np.ndarray:
    """How far each blade's plane is tilted off the horizontal, in degrees: the angle between its normal and straight up.  That's what
    the leaf-angle papers measure.  A blade's slope from base to tip is less than this wherever the blade is rolled about its midrib."""
    n = np.cross(leaves.along, leaves.across)
    return np.degrees(np.arccos(np.clip(np.abs(n[:, 2]) / np.maximum(np.linalg.norm(n, axis=1), 1e-12), 0.0, 1.0)))


def spread(v: np.ndarray, limits=None) -> dict:
    """Mean, SD and 5-50-95 % of some angles, and with ``limits`` the share of them outside."""
    out = {"mean": round(float(v.mean()), 2), "sd": round(float(v.std()), 2), "p5_p50_p95": [round(float(np.percentile(v, q)), 1) for q in (5, 50, 95)]}
    if limits is not None:
        out[f"share_outside_{limits[0]:g}_{limits[1]:g}"] = round(float(((v < limits[0]) | (v > limits[1])).mean()), 4)
    return out


def file_angles(leaf, leaves_in_file: int, tip_point: int, stalk_points: int) -> tuple:
    """From an exported file's own leaves, which it holds one after another, in degrees: each midrib's slope from base to tip below the
    horizontal, and the tilt of each blade's plane, the plane its points lie nearest to."""
    per = len(leaf.V) // leaves_in_file
    assert per * leaves_in_file == len(leaf.V)
    V = np.asarray(leaf.V, np.float64).reshape(leaves_in_file, per, 3)
    chord = V[:, tip_point] - V[:, 0]
    chord /= np.maximum(np.linalg.norm(chord, axis=1, keepdims=True), 1e-12)
    # the file holds each leaf's points in the order they were made in: the midrib sets off the way it ends up going
    first = V[:, 1] - V[:, 0]
    first /= np.maximum(np.linalg.norm(first, axis=1, keepdims=True), 1e-12)
    assert tip_point == 1 or float(np.median((first * chord).sum(1))) > 0.9, "the file's leaves aren't laid out as expected"
    P = V[:, :per - stalk_points]
    P = P - P.mean(1, keepdims=True)
    _, vec = np.linalg.eigh(np.einsum("nij,nik->njk", P, P))
    return np.degrees(np.arcsin(np.clip(-chord[:, 2], -1.0, 1.0))), np.degrees(np.arccos(np.clip(np.abs(vec[:, 2, 0]), 0.0, 1.0)))


def on_the_bark(leaves, pos: np.ndarray, r_wood: np.ndarray) -> np.ndarray:
    """Where the game's mesh starts each leaf's stalk, against the leaf's own node: on the bark, on the line from the node to the
    blade's base (treegen/game_unreal.py, export_stage, leaves.twig)."""
    out = leaves.base - pos[leaves.node]
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9) * r_wood[leaves.node][:, None]


def a_year_on(a, b, pos_a: np.ndarray, pos_b: np.ndarray, r_a: np.ndarray, r_b: np.ndarray, stalks: bool) -> dict:
    """The leaves on the same node with the same number in both years: how many hang as they did, how far the rest turned, how
    far the blade's base moved against its own node, and how many kept their size and their days to turn (an old tree turns a
    little earlier each year, 0.04 of a day, which is why that's within a tenth).  With ``stalks``, how far the stalk's start in
    the game's mesh moved as well.  And over the nodes with leaves in both years, each node's leaf area against last year's."""
    _, ia, ib = np.intersect1d(leaf_ids(a), leaf_ids(b), return_indices=True)
    turn = np.degrees(np.arccos(np.clip((a.along[ia] * b.along[ib]).sum(1), -1.0, 1.0)))
    roll = np.degrees(np.arccos(np.clip((a.across[ia] * b.across[ib]).sum(1), -1.0, 1.0)))
    moved = np.linalg.norm((b.base[ib] - pos_b[b.node[ib]]) - (a.base[ia] - pos_a[a.node[ia]]), axis=1) * 1e3
    pct = lambda v, digits=2: [round(float(np.percentile(v, q)), digits) for q in (10, 50, 90)]  # noqa: E731
    out = {"leaves_in_both_years": int(len(ia)), "share_of_this_years": round(len(ia) / max(len(b.node), 1), 3),
           "hang_as_last_year_within_1_deg": round(float(((turn < 1.0) & (roll < 1.0)).mean()), 4), "turned_deg_p10_p50_p90": pct(turn),
           "base_moved_on_its_node_mm_p10_p50_p90": pct(moved), "base_moved_on_its_node_mm_max": round(float(moved.max()), 2),
           "same_size_within_1_pct": round(float((np.abs(b.area[ib] / a.area[ia] - 1.0) < 0.01).mean()), 4),
           "days_to_turn_as_last_year_within_0.1": round(float((np.abs(b.delay[ib] - a.delay[ia]) < 0.1).mean()), 4)}
    if stalks:
        start = np.linalg.norm(on_the_bark(b, pos_b, r_b)[ib] - on_the_bark(a, pos_a, r_a)[ia], axis=1) * 1e3
        out.update({"stalk_start_on_the_bark_moved_mm_p10_p50_p90": pct(start), "stalk_start_on_the_bark_moved_mm_max": round(float(start.max()), 2),
                    "twig_diameter_there_mm_p10_p50_p90": pct(2e3 * r_b[b.node[ib]])})
    n = min(len(pos_a), len(pos_b))
    area_a, area_b = np.bincount(a.node, a.area, len(pos_a))[:n], np.bincount(b.node, b.area, len(pos_b))[:n]
    both = (area_a > 0) & (area_b > 0)
    out.update({"nodes_with_leaves_in_both_years": int(both.sum()), "a_nodes_leaf_area_against_last_years_p10_p50_p90": pct(area_b[both] / area_a[both], 3),
                "tree_leaf_area_m2": [round(float(a.area.sum()), 4), round(float(b.area.sum()), 4)]})
    return out


def placed(model, sp, look: dict, snap, age: int, hang: bool):
    """The leaves of one age: as the plain export places them, or as the game's target hangs them; with the nodes' places and radii."""
    import game_export as ge
    from treegen import appearance as ap
    from treegen import game_unreal as gu

    pos, r_wood = ge.shoot_arrays(model, age)
    leaves = ap.leaf_instances(look, sp, snap, pos, r_wood, age, 1.0)
    if hang:
        z_rel = np.clip(pos[leaves.node, 2] / max(float(model.stats[age]["height_m"]), 1e-3), 0.0, 1.0)
        leaves = gu.hang_leaves(leaves, z_rel, look["game"]["unreal"]["leaf"])
    return leaves, pos, r_wood


def measure(model, sp, raw, snaps: dict, ages: list, pairs: list) -> dict:
    from treegen import appearance as ap
    from treegen import game_unreal as gu

    plain = ap.load_look(raw)
    limits = [float(x) for x in plain["leaves"]["inclination_deg"]]
    looks = {"plain export": (plain, False), "game (Unreal target)": (gu.unreal_look(plain), True)}
    # the plain export's blade is flat from base to tip; the game's mesh curls its blade down from where it starts, so there the
    # file's own numbers (files_angles) are the ones to compare with a measurement
    slope_is = {"plain export": "the blade's, base to tip", "game (Unreal target)": "the blade's where it starts, before the mesh curls it down: see files_angles"}
    out = {"by_age": [], "a_year_on": [], "short_shoots_a_year_on": []}
    got = {}
    for where, (look, hang) in looks.items():
        for name, on in (("off", 0.0), ("on", 1.0)):
            lk = copy.deepcopy(look)
            lk["leaves"]["each_year"] = on
            for age in ages:
                leaves, pos, r_wood = placed(model, sp, lk, snaps[age], age, hang)
                got[where, name, age] = (leaves, pos, r_wood)
                slope = np.degrees(np.arcsin(np.clip(-leaves.along[:, 2], -1.0, 1.0)))
                out["by_age"].append({"where": where, "each_year": name, "age": age, "leaves": int(len(leaves.node)), "leaf_area_m2": round(float(leaves.area.sum()), 4),
                                      "model_leaf_area_m2": model.stats[age]["leaf_area_m2"], "slope_is": slope_is[where], "slope_deg_mean": round(float(slope.mean()), 2),
                                      "slope_deg_sd": round(float(slope.std()), 2), "slope_deg_p5_p50_p95": [round(float(np.percentile(slope, q)), 1) for q in (5, 50, 95)],
                                      "plane_tilt_deg": spread(plane_tilt(leaves), limits),
                                      "leaf_cm2_p5_p50_p95": [round(float(np.percentile(leaves.area, q)) * 1e4, 1) for q in (5, 50, 95)]})
    for age in ages:      # node by node, the setting leaves the count alone
        for where in looks:
            assert np.array_equal(got[where, "off", age][0].node, got[where, "on", age][0].node)
    for a, b in pairs:
        for where, (_, hang) in looks.items():
            for name in ("off", "on"):
                (la, pa, ra), (lb, pb, rb) = got[where, name, a], got[where, name, b]
                out["a_year_on"].append({"where": where, "each_year": name, "from_age": a, "to_age": b, **a_year_on(la, lb, pa, pb, ra, rb, hang)})
        # a short shoot's leaves go on round its spiral as if it had this year's number of leaves every year: how many kept their number
        la, lb = got["plain export", "off", a][0], got["plain export", "off", b][0]
        n = min(len(snaps[a].is_spur), len(snaps[b].is_spur))
        per_a, per_b = np.bincount(la.node, minlength=n)[:n], np.bincount(lb.node, minlength=n)[:n]
        both = snaps[a].is_spur[:n] & snaps[b].is_spur[:n] & (per_a > 0) & (per_b > 0)
        out["short_shoots_a_year_on"].append({"from_age": a, "to_age": b, "with_leaves_in_both_years": int(both.sum()),
                                              "with_the_same_number_of_leaves": round(float((per_a == per_b)[both].mean()), 4) if both.any() else None,
                                              "leaves_a_shoot_mean": [round(float(per_a[both].mean()), 3), round(float(per_b[both].mean()), 3)] if both.any() else None})
    return out


def pick_cluster(model, sp, look: dict, snaps: dict, a: int, b: int, count: int) -> dict:
    """A short shoot with ``count`` leaves in both years, on the camera's side of the crown, that hardly moved, with the least in front of it."""
    import game_export as ge

    (la, pos_a, _), (lb, pos_b, _) = placed(model, sp, look, snaps[a], a, True), placed(model, sp, look, snaps[b], b, True)
    n = min(len(snaps[a].is_spur), len(snaps[b].is_spur))
    per_a, per_b = np.bincount(la.node, minlength=n)[:n], np.bincount(lb.node, minlength=n)[:n]
    H = float(model.stats[a]["height_m"])
    still = np.linalg.norm(pos_b[:n] - pos_a[:n], axis=1) < 0.005
    spur = snaps[a].is_spur[:n] & snaps[b].is_spur[:n] & (per_a > 0) & (per_b > 0)
    band = (pos_a[:n, 2] > 0.45 * H) & (pos_a[:n, 2] < 0.8 * H)
    same = (per_a == count) & (per_b == count)
    for ok in (spur & still & band & same, spur & still & same, spur & still & band, spur & still, spur):
        cand = np.nonzero(ok)[0]
        if cand.size:
            break
    cand = cand[np.argsort(-(pos_a[cand] @ ge.CAM))[:300]]
    bases = np.concatenate([la.base, lb.base])

    def in_the_way(nd):
        rel = bases - pos_a[nd]
        t = rel @ ge.CAM
        return int(((t > -0.10) & (t < 0.6) & (np.linalg.norm(rel - t[:, None] * ge.CAM, axis=1) < 0.13)).sum())

    nd = int(min(cand.tolist(), key=in_the_way))
    target = la.base[la.node == nd].mean(0) + np.array([0.0, 0.0, -0.02])
    return {"node": nd, "target": target, "eye": target + ge.CAM * 0.40 + np.array([0.0, 0.0, 0.06]), "height_m": round(float(pos_a[nd, 2]), 2), "tree_height_m": round(H, 2),
            "leaves": [int(per_a[nd]), int(per_b[nd])], "born": int(snaps[a].birth[nd]), "moved_mm": round(float(np.linalg.norm(pos_b[nd] - pos_a[nd])) * 1e3, 2),
            "leaves_near_the_line_of_sight": in_the_way(nd), "leaf_index": {a: np.nonzero(la.node == nd)[0], b: np.nonzero(lb.node == nd)[0]}}


def only(p, keep: np.ndarray):
    """A part of a mesh: the faces kept, with their vertices."""
    q = copy.copy(p)
    idx = np.unique(p.F[keep])
    q.F = np.searchsorted(idx, p.F[keep])
    for name in ("V", "N", "UV", "T", "C"):
        v = getattr(p, name)
        setattr(q, name, None if v is None else v[idx])
    return q


def alone(prims: list, leaves_in_file: int, cluster: dict, age: int, reach: float = 0.3) -> list:
    """The cluster's own leaves, which the file holds in the order they were made in, and the wood within ``reach`` of it."""
    leaf = next(p for p in prims if p.name == "leaves")
    per = len(leaf.V) // leaves_in_file
    assert per * leaves_in_file == len(leaf.V)
    scene = [only(leaf, np.isin(leaf.F[:, 0] // per, cluster["leaf_index"][age]))]
    for p in prims:
        if p.name in ("stem", "branches"):
            keep = (np.linalg.norm(p.V[p.F] - cluster["target"], axis=2) < reach).all(1)
            if keep.any():
                scene.append(only(p, keep))
    return scene


def close_up(prims: list, leaves_in_file: int, cluster: dict, age: int, res: int, label: str) -> np.ndarray:
    """One short shoot by itself, with the wood near it, from the cluster's own camera."""
    import game_export as ge
    from treegen import look_render as lr

    scene = alone(prims, leaves_in_file, cluster, age)
    lights = lr.Lights(scene, ge.sun_for_camera(), res=2048, sky_res=512, sky_dirs=8, focus=(cluster["target"], 0.45))
    return ge._label(lr.render(scene, lr.View(cluster["eye"], cluster["target"], res, res, fov_deg=32.0), lights, ss=3), label, 20)


def main(argv=None) -> int:
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap_.add_argument("--label", required=True)
    ap_.add_argument("--seed", type=int, default=5)
    ap_.add_argument("--pairs", default="49-50,59-60", help="ages a year apart, to see one cluster at both")
    ap_.add_argument("--whole", default="50,60", help="ages to draw the whole tree at")
    ap_.add_argument("--open", action="store_true", help="grow in the open, not in a stand")
    ap_.add_argument("--res", type=int, default=760)
    ap_.add_argument("--no-crown", action="store_true", help="leave out the in_the_crown sheets")
    ap_.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap_.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    a = ap_.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    pairs = [tuple(int(x) for x in p.split("-")) for p in a.pairs.split(",") if p]
    whole = [int(x) for x in a.whole.split(",") if x]
    ages = sorted({x for p in pairs for x in p} | set(whole))
    out = E / a.label
    folder = out / "tmp"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        return run(a, ages, pairs, whole, out, folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def export(a, folder: Path, name: str, timelapse: bool, ages: list, target: str, levels: str) -> dict:
    """One export of the tree, grown once and kept in the folder; returns its manifest."""
    import game_export as ge

    ge.main_export(argparse.Namespace(species="betula_pendula", environment="sweden_open_field", seed=a.seed, ages=",".join(str(x) for x in ages), seasons="summer",
                                      out=str(folder / name), stand=not a.open, set=list(a.set), budget=[], target=target, look=[], timelapse=timelapse,
                                      state=str(folder / "state.pkl"), levels=levels))
    return json.loads((folder / name / "game_manifest.json").read_text(encoding="utf-8"))


def run(a, ages: list, pairs: list, whole: list, out: Path, folder: Path) -> int:
    import game_export as ge
    from treegen import appearance as ap
    from treegen import game_unreal as gu
    from treegen import look_render as lr
    from treegen.params import load_species

    docs = {name: export(a, folder, name, timelapse, ages, "unreal", "") for name, timelapse in SETTING}
    with open(folder / "state.pkl", "rb") as f:
        saved = pickle.load(f)
    model, snaps = saved["model"], saved["snaps"]
    sp, raw = load_species("betula_pendula")
    result = measure(model, sp, raw, snaps, ages, pairs)
    # what the files themselves say, level by level
    result["files"] = [{"each_year": name, "age": s["age"], "exported_leaves": s["exported_leaves"], "exported_leaf_area_m2": s["exported_leaf_area_m2"], "model_leaf_area_m2": s["model_leaf_area_m2"],
                        **{f"{lname}_{k}": v for lname, info in s["seasons"]["summer"].items() for k, v in (("triangles", info["triangles"]), ("leaf_triangles", info["parts"].get("leaves")),
                                                                                                             ("leaf_area_stood_for_m2", info["parts"].get("leaf_area_represented_m2"))) if v is not None}}
                       for name, doc in docs.items() for s in doc["stages"]]
    look = gu.unreal_look(ap.load_look(raw))
    limits = [float(x) for x in look["leaves"]["inclination_deg"]]
    midrib_points = len(look["game"]["unreal"]["leaf"]["midrib_at"])
    # a shoot with three leaves a year for the first pair, one with two for the next: on a 2/5 spiral they behave differently
    clusters = {p: pick_cluster(model, sp, look, snaps, *p, 3 - i % 2) for i, p in enumerate(pairs)}
    result["clusters"] = [{"ages": list(p), "camera_chosen_in": "the game target's placing", **{k: (np.round(v, 3).tolist() if isinstance(v, np.ndarray) else v) for k, v in c.items() if k != "leaf_index"}}
                          for p, c in clusters.items()]
    result["files_angles"] = []

    def save():
        (out / "each_year.json").write_text(json.dumps(result, indent=1), encoding="utf-8")

    save()
    for key in ("by_age", "a_year_on", "short_shoots_a_year_on", "files", "clusters"):
        for row in result[key]:
            print(json.dumps(row), flush=True)
    del model, saved
    # the plain export, at the ages of the pairs: where a leaf's every draw goes by its node, so off it comes back exactly
    plain_ages = sorted({x for p in pairs for x in p})
    plain, close, crown, far = {}, {}, {}, {}
    for name, timelapse in SETTING:
        doc = export(a, folder, f"plain_{name}", timelapse, plain_ages, "generic", "lod0")
        for s in doc["stages"]:
            age = s["age"]
            prims = lr.load_glb_primitives(folder / f"plain_{name}" / s["seasons"]["summer"]["lod0"]["file"])
            for pair, c in clusters.items():
                if age in pair:
                    plain[pair, name, age] = close_up(prims, int(s["exported_leaves"]), c, age, a.res, f"age {age}, plain export, {SAID[name]}: one short shoot, {len(c['leaf_index'][age])} leaves")
            del prims
        shutil.rmtree(folder / f"plain_{name}", ignore_errors=True)
    for pair in pairs:
        ge._save(np.concatenate([ge._row([plain[pair, name, age] for age in pair]) for name, _ in SETTING], axis=0), out / f"cluster_plain_{pair[0]}_{pair[1]}.png")
    for name, doc in docs.items():
        for s in doc["stages"]:
            age, H = s["age"], s["height_m"]
            prims = lr.load_glb_primitives(folder / name / s["seasons"]["summer"]["lod0"]["file"])
            for p in prims:       # back to the model's own frame, where the cameras are
                p.V = p.V - np.array([0.0, 0.0, float(s["origin"]["model_zero_in_file_m"])], np.float32)
            # how the game's own blades lie, curl and all: the last six points of each leaf are its stalk
            slope, tilt = file_angles(next(p for p in prims if p.name == "leaves"), int(s["exported_leaves"]), midrib_points - 1, 6)
            row = {"where": "game (Unreal target), from its files", "each_year": name, "age": age, "leaves": int(len(slope)), "midrib_slope_base_to_tip_deg": spread(slope),
                   "plane_tilt_deg": spread(tilt, limits)}
            result["files_angles"].append(row)
            print(json.dumps(row), flush=True)
            save()
            for pair, c in clusters.items():
                if age in pair:
                    # the short shoot by itself, with the wood near it; then where it is in the crown, with everything round it
                    close[pair, name, age] = close_up(prims, int(s["exported_leaves"]), c, age, a.res, f"age {age}, game target, {SAID[name]}: one short shoot, {len(c['leaf_index'][age])} leaves")
                    if a.no_crown:
                        continue
                    lights = lr.Lights(prims, ge.sun_for_camera(), res=4096, sky_res=640, sky_dirs=8, focus=(c["target"], 2.5))
                    crown[pair, name, age] = ge._label(lr.render(prims, lr.View(c["eye"], c["target"], a.res, a.res, fov_deg=32.0), lights, ss=3),
                                                       f"age {age}, game target, {SAID[name]}: the same shoot, in the middle", 20)
            if age in whole:
                line = float(s["origin"]["ground_in_file_m"]) - float(s["origin"]["model_zero_in_file_m"])
                for p in prims:   # stood on the ground
                    p.V = p.V - np.array([0.0, 0.0, line], np.float32)
                far[name, age] = ge._whole_tree(prims, H, a.res + 240, f"age {age}, game target, {SAID[name]}: {s['exported_leaves']:,} leaves, {s['exported_leaf_area_m2']:.1f} m2")
            del prims
    for pair in pairs:
        for shots, stem in ((close, "cluster_game"),) + (() if a.no_crown else ((crown, "in_the_crown_game"),)):
            ge._save(np.concatenate([ge._row([shots[pair, name, age] for age in pair]) for name, _ in SETTING], axis=0), out / f"{stem}_{pair[0]}_{pair[1]}.png")
    if whole:
        ge._save(np.concatenate([ge._row([far[name, age] for age in whole]) for name, _ in SETTING], axis=0), out / f"whole_game_{'_'.join(str(x) for x in whole)}.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
