"""Grow a tree and write its meshes, growth timeline, stats and previews.

    python cli.py --species betula_pendula --seed 1 --years 60           # open-grown
    python cli.py --species betula_pendula --seed 1 --years 60 --stand   # in a stand

Output goes to out/<seed>/ (open) or out/<seed>_stand/ (stand):

* hero meshes (full detail): tree.glb, tree_roots.glb, tree_pruned.glb and
  tree.usdc (+ tree_parts/, loaded as payloads);
* reduced meshes (twigs below a radius threshold dropped, < 10 % of the hero
  triangles): tree_reduced.glb, tree_reduced_roots.glb, tree_reduced.usdc;
* timeline.json (header) + timeline.npz (arrays), stats.json, manifest.json
  (file sizes, triangle counts, runtime and peak memory), previews/.

Meshes are built and written a chunk at a time, so the tree is never in
memory as one mesh.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from treegen import export, mesh, preview
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel
from treegen.params import ROOT, load_environment, load_species
from treegen.reference import reference_block

CROWN_ATTRS = ["birth_year", "death_year", "branch_order", "radius", "node_id"]
ROOT_ATTRS = CROWN_ATTRS + ["depth_below_ground"]
ROOT_COLOR = (0.45, 0.33, 0.22)


def peak_memory_mb() -> float:
    """Peak resident memory of this process so far (MB)."""
    if sys.platform == "win32":
        import ctypes
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        k32 = ctypes.WinDLL("kernel32")
        k32.GetCurrentProcess.restype = wt.HANDLE
        f = k32.K32GetProcessMemoryInfo
        f.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
        f.restype = wt.BOOL
        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        f(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return round(c.PeakWorkingSetSize / 2**20, 1)
    import resource
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(r / (2**20 if sys.platform == "darwin" else 2**10), 1)


def grow(species: str, seed: int, years: int, environment: str, stand: bool = False, verbose: bool = False):
    sp, _ = load_species(species)
    env_p, _ = load_environment(environment)
    model = GrowthModel(sp, make_environment(env_p), seed, stand=stand, soil=make_soil(env_p))
    model.run(years, verbose=verbose)
    return model, sp


def anchorage_numbers(model, sp):
    if model.roots is None:
        return None
    s = model.stats[-1]
    T = model.tree
    trunk = T.trunk_chain(model.leader_axes)
    vol = float((np.pi * T.radius[trunk[1:]] ** 2 * T.length[trunk[1:]]).sum())
    stem_mass = vol * float(sp.mechanics.wood_density)
    return model.roots.anchorage(sp.anchorage, s["height_m"], s["dbh_cm"], stem_mass, vol)


# -- skeletons ----------------------------------------------------------------
def skeleton(model, age: int | None = None):
    """Crown + roots as one skeleton (``mesh.combine_with_roots``) at the end
    of ``age`` (default: final year).  Returns (skel, radius, is_root, orig)."""
    T, R = model.tree, model.roots.tree
    if age is None or age >= model.year:
        alive = T.death[: T.n] < 0
        ralive = R.death[: R.n] < 0
        rs, rr = T.radius[: T.n], R.radius[: R.n]
        shoot = T
    else:
        n = len(model.radius_history[age])
        alive = np.zeros(T.n, bool)
        alive[:n] = (T.birth[:n] <= age) & ((T.death[:n] < 0) | (T.death[:n] > age))
        rs = np.zeros(T.n)
        rs[:n] = model.radius_history[age].astype(np.float64)
        pos = T.pos[: T.n].copy()
        pos[: len(preview._positions_at(model, age))] = preview._positions_at(model, age)
        shoot = SimpleNamespace(n=T.n, pos=pos, parent=T.parent, axis=T.axis, is_lateral=T.is_lateral, order=T.order,
                                birth=T.birth, death=T.death, depth=T.depth)
        m = len(model.roots.radius_history[age])
        ralive = np.zeros(R.n, bool)
        ralive[:m] = (R.birth[:m] <= age) & ((R.death[:m] < 0) | (R.death[:m] > age))
        rr = np.zeros(R.n)
        rr[:m] = model.roots.radius_history[age].astype(np.float64)
    skel, rad, is_root, orig, _ = mesh.combine_with_roots(shoot, R, rs, rr, alive, ralive)
    return skel, rad, is_root, orig


def stream(skel, select, rad, is_root, orig, sp, sinks, budget):
    """Mesh a skeleton chunk by chunk and hand each chunk's crown and root
    parts to every sink (a callable taking (crown, roots))."""
    trunk = np.asarray(skel.axis[: skel.n]) == 0
    for md in mesh.build_mesh_chunks(skel, select, rad, sp.geometry, budget=budget):
        crown, roots = mesh.split_at_ground(md, is_root, orig, trunk)
        for sink in sinks:
            sink(crown, roots)


def concat(parts):
    """Join chunk meshes into one MeshData (in memory: for tests and small trees)."""
    parts = [p for p in parts if p is not None and len(p.faces)]
    if not parts:
        return None
    off = np.r_[0, np.cumsum([p.n_vertices for p in parts])[:-1]]
    return mesh.MeshData(np.concatenate([p.vertices for p in parts]),
                         np.concatenate([p.faces + o for p, o in zip(parts, off)]),
                         np.concatenate([p.normals for p in parts]),
                         {k: np.concatenate([p.attributes[k] for p in parts]) for k in parts[0].attributes})


def build_meshes(model, sp, budget: float = 400_000):
    """Living crown, shed history and roots as in-memory meshes (built in
    chunks, then joined; use the streaming export for big trees)."""
    skel, rad, is_root, orig = skeleton(model)
    crowns, roots = [], []
    stream(skel, np.ones(skel.n, bool), rad, is_root, orig, sp,
           [lambda c, r: (crowns.append(c), roots.append(r))], budget)
    T = model.tree
    alive = T.death[: T.n] < 0
    dead = ~alive
    dead[0] = False
    pruned = None
    if dead.any():
        last = np.where(alive, model.year, T.death[: T.n] - 1)
        r_last = np.array([model.radius_history[y][i] if i < len(model.radius_history[y]) else 0.0
                           for i, y in enumerate(last.tolist())], dtype=np.float64)
        pruned = concat(mesh.build_mesh_chunks(T, dead, r_last, sp.geometry, budget=budget))
    return concat(crowns), pruned, concat(roots)


def reduced_threshold(skel, rad, is_root, orig, sp, hero_triangles: int, budget: float,
                      target: float = 0.085, limit: float = 0.10) -> float:
    """Radius below which twigs are dropped from the reduced mesh: first
    guess from estimated vertex counts (``target`` of the hero), then raised
    until a dry run of the reduced mesh has fewer than ``limit`` x the hero
    triangles."""
    est = mesh.estimate_vertices(skel, np.ones(skel.n, bool), rad)
    r = rad[: skel.n]
    order = np.argsort(-r)
    cum = np.cumsum(est[order])
    thr = float(r[order][min(int(np.searchsorted(cum, target * cum[-1])), len(order) - 1)])
    for _ in range(12):
        count = [0]
        stream(skel, r >= thr, rad, is_root, orig, sp,
               [lambda c, rt: count.__setitem__(0, count[0] + len(c.faces) + len(rt.faces))], budget)
        if count[0] < limit * hero_triangles:
            break
        thr *= 1.15
    return thr


# -- previews -------------------------------------------------------------------
def tree_view(model, age, res_h=1600):
    """Shaded 3/4 view of the whole tree on a ground plane."""
    s = model.stats[age]
    H = s["height_m"]
    pos = preview._positions_at(model, age)
    n = min(len(pos), len(model.radius_history[age]))
    alive = (model.tree.birth[:n] <= age) & ((model.tree.death[:n] < 0) | (model.tree.death[:n] > age))
    half_w = max(0.6 * float(np.abs(pos[:n][alive, :2]).max()), 0.3 * H)
    r = preview.Rasterizer(np.array([0.0, 0.0, 0.47 * H]), half_w, 0.55 * H, azim=-60, elev=12, res_h=res_h)
    r.add_ground(4.0 * half_w)
    return r


def photo_view(model, age, res_h=1600, eye_height=1.6, distance_per_height=1.3, azim=-60.0):
    """Eye-level perspective view, as a photograph of the whole tree taken
    standing on the ground: camera ``eye_height`` m up, ``distance_per_height``
    tree heights away, aimed at mid-height, portrait frame."""
    H = model.stats[age]["height_m"]
    D = distance_per_height * H
    a = np.radians(azim)
    eye = np.array([D * np.cos(a), D * np.sin(a), eye_height])
    centre = np.array([0.0, 0.0, 0.5 * H])
    half_h = 0.58 * H * float(np.linalg.norm(eye - centre)) / D
    r = preview.Rasterizer(centre, 0.75 * half_h, half_h, azim, 0.0, res_h=res_h, eye=eye)
    r.add_ground(6.0 * H)
    return r


def export_all(model, sp, out: Path, meta: dict, anchorage, renderers: list, budget: float, timings: dict, memory: dict):
    """Hero meshes (with the previews rendered from the same chunks), shed
    history, then the reduced meshes.  Returns mesh statistics."""
    T = model.tree
    info = {}
    t0 = time.time()
    skel, rad, is_root, orig = skeleton(model)
    g_crown = export.GLBWriter(out / "tree.glb", "tree", meta, CROWN_ATTRS)
    g_roots = export.GLBWriter(out / "tree_roots.glb", "roots", meta, ROOT_ATTRS, base_color=(115, 84, 56))
    usd = export.USDWriter(out / "tree.usdc", meta)
    usd.group("Living")
    usd.group("Roots", color=ROOT_COLOR, attrs=_anchorage_attrs(anchorage))

    def write(crown, roots):
        g_crown.add(crown)
        g_roots.add(roots)
        usd.add("Living", crown)
        usd.add("Roots", roots)
    sinks = [write] + [_sink_for(r, kinds) for r, kinds in renderers]
    stream(skel, np.ones(skel.n, bool), rad, is_root, orig, sp, sinks, budget)
    info["hero_crown"] = g_crown.close()
    info["hero_roots"] = g_roots.close()
    # shed branches keep the radius they had in their last living year
    alive = T.death[: T.n] < 0
    dead = ~alive
    dead[0] = False
    if dead.any():
        last = np.where(alive, model.year, T.death[: T.n] - 1)
        r_last = np.zeros(T.n)
        for y in np.unique(last[dead]).tolist():
            idx = np.nonzero(dead & (last == y))[0]
            h = model.radius_history[y]
            ok = idx < len(h)
            r_last[idx[ok]] = h[idx[ok]]
        usd.group("PrunedHistory", hidden=True)
        g_pruned = export.GLBWriter(out / "tree_pruned.glb", "pruned_history", meta, CROWN_ATTRS)
        for md in mesh.build_mesh_chunks(T, dead, r_last, sp.geometry, budget=budget):
            g_pruned.add(md)
            usd.add("PrunedHistory", md)
        info["pruned"] = g_pruned.close()
    info["hero_usd"] = usd.close()
    timings["hero_export_s"] = round(time.time() - t0, 1)
    memory["after_hero_export_mb"] = peak_memory_mb()

    # reduced: drop twigs below a radius threshold; < 10 % of the hero triangles
    t0 = time.time()
    hero_tris = info["hero_crown"]["triangles"] + info["hero_roots"]["triangles"]
    thr = reduced_threshold(skel, rad, is_root, orig, sp, hero_tris, budget)
    g_c = export.GLBWriter(out / "tree_reduced.glb", "tree_reduced", meta, CROWN_ATTRS)
    g_r = export.GLBWriter(out / "tree_reduced_roots.glb", "roots_reduced", meta, ROOT_ATTRS, base_color=(115, 84, 56))
    u = export.USDWriter(out / "tree_reduced.usdc", meta, inline=True)
    u.group("Living")
    u.group("Roots", color=ROOT_COLOR, attrs=_anchorage_attrs(anchorage))

    def write_r(crown, roots):
        g_c.add(crown)
        g_r.add(roots)
        u.add("Living", crown)
        u.add("Roots", roots)
    stream(skel, rad[: skel.n] >= thr, rad, is_root, orig, sp, [write_r], budget)
    rc, rr = g_c.close(), g_r.close()
    u.close()
    ratio = (rc["triangles"] + rr["triangles"]) / max(hero_tris, 1)
    info["reduced"] = {"radius_threshold_m": round(thr, 5), "crown": rc, "roots": rr,
                       "triangle_ratio_to_hero": round(ratio, 4)}
    timings["reduced_export_s"] = round(time.time() - t0, 1)
    memory["after_reduced_export_mb"] = peak_memory_mb()
    return info


def _sink_for(r, kinds):
    """Render sink from a kinds tuple; "root>0.004" = roots of at least that radius."""
    min_r = 0.0
    names = []
    for k in kinds:
        if k.startswith("root>"):
            min_r = float(k[5:])
            k = "root"
        names.append(k)
    return _render_sink(r, tuple(names), min_r)


def _anchorage_attrs(anchorage):
    if not anchorage:
        return {}
    cm = anchorage.get("critical_turning_moment") or {}
    return {
        "anchorage:plateRadiusM": anchorage["plate_radius_m"],
        "anchorage:plateDepthM": anchorage["plate_depth_m"],
        "anchorage:criticalTurningMomentMinKNm": cm.get("min_knm"),
        "anchorage:criticalTurningMomentMeanKNm": cm.get("mean_knm"),
        "anchorage:criticalTurningMomentByWindDirKNm": list((cm.get("by_wind_dir_knm") or {}).values()) or None,
        "anchorage:mainRootBreakingForceKN": [r["breaking_force_edge_kn"] for r in anchorage["main_roots"]],
        "anchorage:mainRootAzimuthDeg": [r["azimuth_deg"] for r in anchorage["main_roots"]],
    }


def _render_sink(r, kinds, min_root_radius: float = 0.0):
    def sink(crown, roots):
        if "shoot" in kinds:
            r.add(crown, "shoot")
        if "root" in kinds and roots is not None and len(roots.faces):
            mask = None
            if min_root_radius > 0.0:
                mask = roots.attributes["radius"][roots.faces[:, 0]] >= min_root_radius
            r.add(roots, "root", face_mask=mask)
    return sink


def preview_renderers(model, out_dir: Path):
    """Renderers fed from the final-year hero chunks: 3/4 view, hanging-twig
    close-up, root-flare close-up.  Returns [(renderer, kinds, file)]."""
    last = model.year
    jobs = [(tree_view(model, last), ("shoot", "root"), out_dir / f"shaded_age{last:02d}.png"),
            (photo_view(model, last), ("shoot",), out_dir / f"photo_age{last:02d}.png")]
    run = model.hanging_runs()
    T = model.tree
    tips = np.nonzero((T.death[: T.n] < 0) & (T.main_child[: T.n] < 0))[0]
    if tips.size and run[tips].max() > 0.3:
        k = tips[np.argmax(run[tips])]
        centre = T.pos[k] + np.array([0.0, 0.0, 0.5 * min(run[k], 2.0)])
        jobs.append((preview.Rasterizer(centre, 1.0, 1.0, azim=-60, elev=5, res_h=1400), ("shoot",),
                     out_dir / f"hanging_twigs_closeup_age{last:02d}.png"))
    if model.roots is not None:
        r0 = float(T.radius[0])
        half = max(8.0 * r0, 0.8)
        # soil removed; fine roots hidden so the structural roots and the
        # flare show
        jobs.append((preview.Rasterizer(np.array([0.0, 0.0, -0.1 * half]), half, 0.7 * half, azim=-50, elev=18,
                                        res_h=1200), ("shoot", "root>0.004"), out_dir / f"root_flare_closeup_age{last:02d}.png"))
    return jobs


def render_age_view(model, sp, age: int, out_dir: Path, budget: float):
    """Shaded 3/4 view at an earlier age, meshed from the stored history."""
    r = tree_view(model, age)
    skel, rad, is_root, orig = skeleton(model, age)
    stream(skel, np.ones(skel.n, bool), rad, is_root, orig, sp, [_render_sink(r, ("shoot", "root"))], budget)
    return preview.save_png(r.image(), out_dir / f"shaded_age{age:02d}.png")


def _sizes(out: Path) -> dict:
    files = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            files[p.name] = round(p.stat().st_size / 2**20, 2)
        elif p.is_dir() and p.name.endswith("_parts"):
            files[p.name + "/"] = round(sum(f.stat().st_size for f in p.iterdir()) / 2**20, 2)
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--species", default="betula_pendula")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--environment", default="sweden_open_field")
    ap.add_argument("--stand", action="store_true", help="grow inside a stand (neighbours as shadow volumes)")
    ap.add_argument("--out", default=str(ROOT / "out"))
    ap.add_argument("--preview-ages", default="5,15,30,60")
    ap.add_argument("--shaded-ages", default="30", help="extra shaded 3/4 views besides the final year")
    ap.add_argument("--chunk-vertices", type=float, default=400_000, help="mesh chunk size (memory vs speed)")
    ap.add_argument("--no-mesh", action="store_true", help="skip the mesh files")
    ap.add_argument("--no-preview", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    out = Path(args.out) / (f"{args.seed}_stand" if args.stand else str(args.seed))
    out.mkdir(parents=True, exist_ok=True)
    timings, memory = {}, {}
    t0 = time.time()
    model, sp = grow(args.species, args.seed, args.years, args.environment, stand=args.stand, verbose=not args.quiet)
    timings["growth_s"] = round(time.time() - t0, 1)
    memory["after_growth_mb"] = peak_memory_mb()
    meta = {
        "species": sp.species.scientific_name,
        "species_file": args.species,
        "environment": args.environment,
        "mode": "stand" if args.stand else "open",
        "seed": args.seed,
        "generator": "treegen 0.4 (Palubicki et al. 2009 self-organising model, roots, hydraulics)",
    }
    t1 = time.time()
    anchorage = anchorage_numbers(model, sp)
    export.write_timeline(out / "timeline.json", model, meta)
    export.write_stats(out / "stats.json", model, meta, reference_block(sp, model.stats), anchorage)
    timings["timeline_stats_s"] = round(time.time() - t1, 1)
    memory["after_timeline_mb"] = peak_memory_mb()
    prev_dir = out / "previews"
    prev_dir.mkdir(parents=True, exist_ok=True)
    renderers = [] if args.no_preview else preview_renderers(model, prev_dir)
    info = {}
    if not args.no_mesh:
        info = export_all(model, sp, out, meta, anchorage, [(r, k) for r, k, _ in renderers],
                          args.chunk_vertices, timings, memory)
    t2 = time.time()
    if not args.no_preview:
        if args.no_mesh:  # previews still need the meshes: stream them without writing
            skel, rad, is_root, orig = skeleton(model)
            stream(skel, np.ones(skel.n, bool), rad, is_root, orig, sp,
                   [_sink_for(r, k) for r, k, _ in renderers], args.chunk_vertices)
        for r, _, f in renderers:
            preview.save_png(r.image(), f)
        del renderers
        for a in [int(x) for x in args.shaded_ages.split(",") if x.strip()]:
            if 0 < a < model.year:
                render_age_view(model, sp, a, prev_dir, args.chunk_vertices)
        ages = [int(a) for a in args.preview_ages.split(",") if a.strip()]
        preview.render_previews(model, ages, prev_dir)
        if model.roots is not None:
            preview.render_roots_side(model, [a for a in (15, 30, 60) if a <= model.year] or [model.year], prev_dir)
            preview.render_roots_top(model, model.year, prev_dir)
    timings["previews_s"] = round(time.time() - t2, 1)
    memory["after_previews_mb"] = peak_memory_mb()
    timings["total_s"] = round(time.time() - t0, 1)
    manifest = {**meta, "timings": timings, "peak_memory": memory, "meshes": info, "files_mb": _sizes(out)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    if not args.quiet:
        s = model.stats[-1]
        print(f"done in {timings['total_s']:.1f}s; peak memory {memory['after_previews_mb']:.0f} MB")
        print(f"final: height {s['height_m']:.2f} m, dbh {s['dbh_cm']} cm, crown {s['crown_width_m']:.2f} m -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
