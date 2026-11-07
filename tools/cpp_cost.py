"""What a tree-year costs now, by stage, for the C++ port plan (reports/cpp_port_plan.md).  Measures only: timers wrap the model's
functions from outside, nothing in treegen/ changes, and a tree's digest shows that measuring changed nothing.  Server only.

    python tools/cpp_cost.py tree --label node_cpp_t --seed 1 --speed lossless       # a stand tree, lean, to 60
    python tools/cpp_cost.py plot --label node_cpp_p --seed 1 --speed lossless       # 1000 m2, thinning, spread and storms, to 60
    python tools/cpp_cost.py mesh --label node_cpp_m --seed 1 --ages 10,30,50,60     # an exported tree, every level
    python tools/cpp_cost.py hot --label node_cpp_h --seed 1 --at 30,60              # the top functions by their own time
    python tools/cpp_cost.py lines --label node_cpp_l                                # which of treegen's lines a run reaches
    python tools/cpp_cost.py table <folder> [<folder> ...]                           # the plan's tables, from the results

Stages follow the year's own order.  A time goes to the innermost stage on the stack, so tree passes (levels, subtree sums) count
towards whichever stage asked for them.  'compiled' is the part of a stage inside already compiled code (numba kernels, numpy's and
scipy's FFTs, tensordot, the ndimage filters): a C++ port can't gain much there.  The rest is Python and numpy calls.
Results go to out/bench/ensemble/<label>/, where tools/node/fetch.sh looks.
"""
from __future__ import annotations

import argparse
import cProfile
import functools
import json
import pstats
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from profile_run import memory_by_attribute, top_entries  # noqa: E402

BASE = ROOT / "out" / "bench" / "ensemble"
AGES = (10, 20, 30, 40, 50, 60)
PLAN_AGES = (10, 30, 50, 60)

# The settings the verdict plots and damage runs use (node_dmg_fix5): crown, roots and storms on.  Crown 2 will change some of them.
FULL = ["height_driver.enabled=true", "height_driver.ring_share_max=0.5", "stats.limbs_on_leader=true", "pipe_model.heartwood_by_own_foliage=true",
        "pipe_model.branch_sapwood_senescence=0.30", "resource.apical_dominance=0.75", "resource.reiteration.setpoint_angle_deg=20",
        "bud_fate.long_shoot_threshold=5", "bud_fate.short_shoot_light=0.18", "bud_fate.short_shoot_survival_light=0.18",
        "bud_fate.density_control.enabled=true", "bud_fate.density_control.after_growth=true", "bud_fate.density_control.af_zero=1.7",
        "shedding.shade_softness=0.5", "shedding.light_per_leaf_threshold=0.18", "mechanics.pendulous_radius_limb=0.0025", "crown_frame.enabled=true",
        "roots.paid.enabled=true", "geometry.root_flare_min_share=0.5", "roots.lateral_setpoint_deg=92", "roots.lateral_gravitropism_per_m=3.0",
        "damage.enabled=true", "damage.old_age.enabled=true", "damage.wind.enabled=true", "damage.snow.enabled=true"]
LOSSLESS = ["speed.compiled_carbon=true", "speed.compiled_mechanics=true", "speed.light_layers=true", "speed.keep_soil_grids=true",
            "speed.quick_solve=true", "speed.quick_levels=true"]
# not bit-identical: needs the maintainer's approval (reports/speed_research.md)
ROWS_DROP = ["speed.light_rows=true", "speed.drop_dead=true"]
PLOT = ["plot.stand_measures=true", "plot.natural_start.enabled=true", "plot.natural_start.stems_per_ha=16000", "mortality.enabled=true",
        "plot.natural_start.area_m2=1000", "regeneration.spread.enabled=true", "regeneration.spread.repeat_ends=true"]


def settings(a) -> list:
    out = list(FULL) if a.settings == "full" else []
    if a.speed in ("lossless", "rows_drop"):
        out += LOSSLESS
    if a.speed == "rows_drop":
        out += ROWS_DROP
    return out + list(a.set)


def status_mb() -> dict:
    """The process's memory now and at its highest, MB."""
    out = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            out[line[:5]] = int(line.split()[1]) / 1024
    return {"rss_mb": out.get("VmRSS", 0.0), "peak_mb": out.get("VmHWM", 0.0)}


class StageClock:
    """Time goes to the top of a stack of stages.  Inside a tree's step, 'base' is the step's own frame: the year's inline code between
    the functions below, which set_base moves along as the year moves from one stage to the next."""

    def __init__(self):
        self.stack = ["outside"]
        self.base = None
        self.t = time.perf_counter()
        self.by = defaultdict(float)
        self.compiled = defaultdict(float)

    def _tick(self):
        now = time.perf_counter()
        self.by[self.stack[-1]] += now - self.t
        self.t = now

    def push(self, stage):
        self._tick()
        self.stack.append(stage)

    def pop(self):
        self._tick()
        self.stack.pop()

    def set_base(self, stage):
        if self.base is not None:
            self._tick()
            self.stack[self.base] = stage

    def wrap(self, owner, name, stage=None, before=None, after=None):
        fn = getattr(owner, name)

        @functools.wraps(fn)
        def timed(*args, **kwargs):
            if before:
                self.set_base(before)
            if stage:
                self.push(stage)
            try:
                return fn(*args, **kwargs)
            finally:
                if stage:
                    self.pop()
                if after:
                    self.set_base(after)
        setattr(owner, name, timed)

    def wrap_compiled(self, owner, name):
        fn = getattr(owner, name)

        @functools.wraps(fn)
        def timed(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                self.compiled[self.stack[-1]] += time.perf_counter() - t0
        setattr(owner, name, timed)

    def snapshot(self) -> tuple:
        self._tick()
        return dict(self.by), dict(self.compiled)


def instrument(clock: StageClock, per_tree=None) -> None:
    """per_tree: a list that gets (live crown nodes, live root nodes, seconds) for each tree's year, when it's not None."""
    from scipy import fft as sfft

    from treegen import damage, fast, growth, hydraulics, kernels, light as light_mod, mechanics, plot as plot_mod, roots as roots_mod
    from treegen.growth import GrowthModel as G
    from treegen.light import LightField, ShadowPropagation
    from treegen.plot import Plot
    from treegen.roots import RootSystem, SharedSoil

    w = clock.wrap
    # the tree's year, in order
    w(G, "_leader_damage", "damage")
    w(damage, "tree_year", "damage")
    w(G, "light_sources", "light", before="light")
    w(G, "wood_sources", "light")
    w(G, "_stand_cell", "light")
    w(ShadowPropagation, "compute", "light: field")
    w(ShadowPropagation, "own_shade", "light")
    w(LightField, "relative_light_at_heights", "light")
    w(LightField, "diffuse_light_at_heights", "light")
    w(G, "_crown_light_asymmetry", "light", after="shedding")
    w(G, "_fine_root_mass", "water", before="water")
    w(RootSystem, "update_uptake", "water")
    w(G, "conducting_area", "water")
    w(hydraulics, "solve", "water", after="carbon")
    w(G, "_leaf_costs", "carbon", before="carbon")
    w(G, "_growth_factor", "carbon")
    w(G, "_reiterate", "growth: shoots", before="growth: shoots")
    w(G, "_grow_shoots", "growth: shoots")
    w(RootSystem, "step", "roots")
    w(G, "_finish_year", None, before="growth: rings")
    w(G, "_update_radii", "growth: rings")
    w(G, "_update_roots", "roots")
    w(mechanics, "bend_and_correct", "mechanics")
    w(G, "measure", "stats")
    w(RootSystem, "measure", "stats")
    w(growth, "compact", "drop dead")
    # the plot's year
    w(Plot, "step", "plot: other")
    w(Plot, "_starve", "thinning")
    w(Plot, "_die", "thinning")
    w(Plot, "_self_thin", "thinning")
    w(Plot, "_thin", "thinning")
    w(Plot, "_regenerate", "seed spread")
    w(Plot, "measure", "stats")
    w(damage, "plot_year", "damage")
    w(plot_mod, "gap_fraction", "stats")
    w(SharedSoil, "update", "roots")
    w(RootSystem, "absorbing", "roots")

    real_step = G.step

    def timed_step(self):
        t0 = time.perf_counter()
        clock.push("tree: other")
        outer, clock.base = clock.base, len(clock.stack) - 1
        try:
            real_step(self)
        finally:
            clock.pop()
            clock.base = outer
        if per_tree is not None:
            T, R = self.tree, self.roots.tree if self.roots is not None else None
            per_tree.append((int((T.death[: T.n] < 0).sum()), int((R.death[: R.n] < 0).sum()) if R is not None else 0, time.perf_counter() - t0))
    G.step = timed_step

    # what's already compiled
    for owner, name in ((np.fft, "rfft2"), (np.fft, "irfft2"), (sfft, "rfft2"), (sfft, "irfft2"), (np, "tensordot"), (light_mod, "gaussian_filter"),
                        (light_mod, "map_coordinates"), (roots_mod, "gaussian_filter"), (roots_mod, "map_coordinates"),
                        (fast, "sweep_rows"), (fast, "blur_layers"), (fast, "deposit"), (fast, "sample_wrap"), (fast, "carbon_parts"), (fast, "bend_steps"),
                        (fast, "level_order"), (kernels, "basipetal"), (kernels, "compose"), (kernels, "positions"), (kernels, "posture")):
        clock.wrap_compiled(owner, name)

    # bend_steps calls fast.apply_rotation inside numba, so that name must stay the compiled function: only mechanics' own call is timed
    class FastSeenByMechanics:
        def __getattr__(self, name):
            return getattr(fast, name)
    seen = FastSeenByMechanics()
    seen.apply_rotation = fast.apply_rotation
    clock.wrap_compiled(seen, "apply_rotation")
    mechanics.fast = seen


def year_row(now: tuple, last: tuple) -> dict:
    by, comp = now
    b0, c0 = last
    return {"by": {k: v - b0.get(k, 0.0) for k, v in by.items() if k != "outside"}, "compiled": {k: v - c0.get(k, 0.0) for k, v in comp.items()}}


def live_and_single(T) -> tuple:
    """Bytes the node arrays hold: at their capacity, for the nodes in use, for living nodes only, and that in single precision."""
    n = T.n
    alive = int((T.death[:n] < 0).sum())
    node = node32 = 0
    for name in list(T.VEC) + list(T.SCALAR):
        a = getattr(T, name)
        one = a.dtype.itemsize * (a.shape[1] if a.ndim == 2 else 1)
        node += one
        node32 += one // 2 if a.dtype.itemsize == 8 else one
    return {"cap_b": node * T.cap, "used_b": node * n, "live_b": node * alive, "live32_b": node32 * alive, "bytes_per_node": node, "bytes_per_node_32": node32}


def tree_memory(m, name="model") -> dict:
    sizes = memory_by_attribute(m, name)
    place = (f"{name}._field", f"{name}.light", f"{name}._plot_view", f"{name}.roots.field", f"{name}.roots._kept_soil", f"{name}.soil")
    state = {k: v for k, v in sizes.items() if not k.startswith(place)}
    crown = sum(v for k, v in state.items() if k.startswith(f"{name}.tree."))
    roots = sum(v for k, v in state.items() if k.startswith(f"{name}.roots.tree."))
    mb = 2.0 ** 20
    return {"state_mb": sum(state.values()) / mb, "crown_mb": crown / mb, "roots_mb": roots / mb, "other_mb": (sum(state.values()) - crown - roots) / mb,
            "place_mb": (sum(sizes.values()) - sum(state.values())) / mb, "top": top_entries(state, 12), "crown": live_and_single(m.tree),
            "root": live_and_single(m.roots.tree) if m.roots is not None else None}


def load(a):
    import cli
    from treegen import checkpoint

    sp, raw = cli.load_species("betula_pendula")
    return cli, checkpoint, sp, raw


def run_tree(a) -> None:
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    per_tree = None
    clock = None
    if not a.plain:
        clock = StageClock()
        per_tree = None
        instrument(clock, per_tree)
    cli, checkpoint, sp, _ = load(a)
    items = settings(a)
    checkpoint.set_values(sp, items)
    from treegen.growth import GrowthModel
    from treegen.runhash import output_digest

    env_p, _ = cli.load_environment("sweden_open_field")
    t00 = time.perf_counter()
    m = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    rows, mem = {}, {}
    last = clock.snapshot() if clock else None
    for _ in range(a.years):
        t0, c0 = time.perf_counter(), time.process_time()
        m.step()
        wall, cpu = time.perf_counter() - t0, time.process_time() - c0
        T, R = m.tree, m.roots.tree
        row = {"wall": wall, "cpu": cpu, "nodes": int(T.n), "alive": int((T.death[: T.n] < 0).sum()), "root_nodes": int(R.n), "root_alive": int((R.death[: R.n] < 0).sum()),
               "leaves": float(T.leaves[: T.n][T.death[: T.n] < 0].sum()), "height_m": float(m.stats[-1]["height_m"]), **status_mb()}
        field = getattr(m, "_field", None)
        if field is not None:
            row["grid"] = list(field.S.shape)
        if clock:
            now = clock.snapshot()
            row.update(year_row(now, last))
            last = now
        rows[m.year] = row
        if m.year in AGES:
            t1 = time.perf_counter()
            mem[m.year] = tree_memory(m)
            if clock:
                clock._tick()     # the walk isn't the year's
                clock.by["memory walk"] += time.perf_counter() - t1
                last = clock.snapshot()
            print(f"year {m.year}: {wall:.2f} s, {row['alive']} live of {row['nodes']}, state {mem[m.year]['state_mb']:.1f} MB", flush=True)
    doc = {"what": "tree", "label": a.label, "seed": a.seed, "settings": a.settings, "speed": a.speed, "plain": a.plain, "years": a.years, "sets": items,
           "seconds": time.perf_counter() - t00, "digest": output_digest(m), "rows": {str(k): v for k, v in rows.items()}, "memory": {str(k): v for k, v in mem.items()}}
    (out / f"tree_{a.settings}_{a.speed}_s{a.seed}{'_plain' if a.plain else ''}.json").write_text(json.dumps(doc), encoding="utf-8")
    print(f"{a.label}: {doc['seconds']:.1f} s, digest {doc['digest']}", flush=True)


def plot_memory(plot) -> dict:
    sizes = memory_by_attribute(plot, "plot")
    trees = [plot.trees[k] for k in plot.alive]
    mb = 2.0 ** 20
    # the plot's light and soil are reached through the first tree that holds them, so go by what a path names
    shared = (".light", "._field", "._plot_view", ".soil", ".roots.field", ".roots._kept_soil", ".environment")
    place = sum(v for k, v in sizes.items() if not k.startswith("plot.trees[*]") or any(s in k for s in shared))
    crown = sum(v for k, v in sizes.items() if k.startswith("plot.trees[*].tree."))
    roots = sum(v for k, v in sizes.items() if k.startswith("plot.trees[*].roots.tree."))
    other = sum(sizes.values()) - place - crown - roots
    used = live = live32 = 0
    for m in trees:
        for T in (m.tree, m.roots.tree):
            s = live_and_single(T)
            used += s["used_b"]
            live += s["live_b"]
            live32 += s["live32_b"]
    n = max(len(trees), 1)
    top = [t for t in top_entries(sizes, 40)]
    return {"trees": len(trees), "crown_mb": crown / mb / n, "roots_mb": roots / mb / n, "other_mb": other / mb / n, "state_mb": (crown + roots + other) / mb / n,
            "used_mb": used / mb / n, "live_mb": live / mb / n, "live32_mb": live32 / mb / n, "place_mb": place / mb, "top": top[:16]}


def run_plot(a) -> None:
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    per_tree: list = []
    clock = StageClock()
    instrument(clock, per_tree)
    cli, checkpoint, sp, _ = load(a)
    items = settings(a) + PLOT
    checkpoint.set_values(sp, items)
    from treegen.light import ShadowPropagation
    from treegen.plot import Plot

    shapes = {}
    compute = ShadowPropagation.compute

    def noted(self, *args, **kwargs):
        f = compute(self, *args, **kwargs)
        shapes["last"] = list(f.S.shape)
        return f
    ShadowPropagation.compute = noted
    env_p, _ = cli.load_environment("sweden_open_field")
    t00 = time.perf_counter()
    plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), seed=a.seed, mode="natural", lean=True)
    plot.enable_regeneration()
    rows, mem = {}, {}
    last = clock.snapshot()
    prof_at = {int(x) for x in a.profile_at.split(",") if x.strip()}
    hot = {}
    while plot.year < a.years and plot.alive:
        del per_tree[:]
        t0, c0 = time.perf_counter(), time.process_time()
        prof = cProfile.Profile() if plot.year + 1 in prof_at else None
        if prof:
            prof.enable()
        plot.step()
        if prof:
            prof.disable()
            hot[plot.year] = top_functions(prof, 40)
        wall, cpu = time.perf_counter() - t0, time.process_time() - c0
        trees = [plot.trees[k] for k in plot.alive]
        now = clock.snapshot()
        row = {"wall": wall, "cpu": cpu, "profiled": bool(prof), "stepped": len(per_tree), "trees": len(trees), "ever": len(plot.trees), "tree_steps_s": sum(p[2] for p in per_tree),
               "nodes": sum(int(m.tree.n) for m in trees), "alive": sum(int((m.tree.death[: m.tree.n] < 0).sum()) for m in trees),
               "root_nodes": sum(int(m.roots.tree.n) for m in trees), "root_alive": sum(int((m.roots.tree.death[: m.roots.tree.n] < 0).sum()) for m in trees),
               "grid": shapes.get("last"), "stats": {k: plot.stats[-1].get(k) for k in ("stems_per_ha", "basal_area_ob_m2_ha", "top_height_m", "lai", "new_trees", "recruits_alive")},
               **status_mb(), **year_row(now, last)}
        last = now
        if plot.year in AGES:
            t1 = time.perf_counter()
            mem[plot.year] = plot_memory(plot)
            row["per_tree"] = [[p[0], p[1], round(p[2], 4)] for p in per_tree]
            clock._tick()
            clock.by["memory walk"] += time.perf_counter() - t1
            last = clock.snapshot()
        rows[plot.year] = row
        print(f"year {plot.year}: {wall:.1f} s, {len(trees)} trees, {row['alive']} live nodes, {row['rss_mb']:.0f} MB, grid {row['grid']}", flush=True)
        write_plot(out, a, items, t00, rows, mem, hot, plot)
    write_plot(out, a, items, t00, rows, mem, hot, plot)
    print(f"{a.label}: {time.perf_counter() - t00:.0f} s", flush=True)


def write_plot(out, a, items, t00, rows, mem, hot, plot) -> None:
    doc = {"what": "plot", "label": a.label, "seed": a.seed, "settings": a.settings, "speed": a.speed, "sets": items, "years": a.years, "area_m2": plot.area,
           "seconds": time.perf_counter() - t00, "rows": {str(k): v for k, v in rows.items()}, "memory": {str(k): v for k, v in mem.items()},
           "hot": {str(k): v for k, v in hot.items()}}
    tmp = out / f"plot_{a.settings}_{a.speed}_s{a.seed}.json.tmp"
    tmp.write_text(json.dumps(doc), encoding="utf-8")
    tmp.replace(out / f"plot_{a.settings}_{a.speed}_s{a.seed}.json")


def top_functions(prof, n: int) -> list:
    st = pstats.Stats(prof)
    rows = []
    for (fn, line, name), (cc, nc, tt, ct, _) in st.stats.items():
        rows.append({"where": f"{Path(fn).name}:{line}", "name": name, "calls": nc, "own_s": round(tt, 4), "with_callees_s": round(ct, 4)})
    rows.sort(key=lambda r: -r["own_s"])
    return rows[:n]


def run_hot(a) -> None:
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    cli, checkpoint, sp, _ = load(a)
    checkpoint.set_values(sp, settings(a))
    from treegen.growth import GrowthModel

    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    at = {int(x) for x in a.at.split(",")}
    res = {}
    for _ in range(max(at)):
        if m.year + 1 in at:
            prof = cProfile.Profile()
            prof.enable()
            m.step()
            prof.disable()
            res[m.year] = top_functions(prof, 40)
        else:
            m.step()
    (out / f"hot_{a.settings}_{a.speed}_s{a.seed}.json").write_text(json.dumps(res), encoding="utf-8")


def run_mesh(a) -> None:
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    work = out / "tmp_export"
    import cli
    from game_export import grow_with_leaves, shoot_arrays
    from treegen import appearance as ap
    from treegen import game, game_unreal as gu
    from treegen import textures as tx
    from treegen.export import GameGLB

    ages = sorted(int(x) for x in a.ages.split(","))
    t0 = time.perf_counter()
    model, sp, raw, snaps = grow_with_leaves("betula_pendula", a.seed, ages, "sweden_open_field", True, settings(a))
    grow_s = time.perf_counter() - t0
    print(f"grown in {grow_s:.1f} s, {status_mb()}", flush=True)
    look = gu.unreal_look(ap.load_look(raw))
    if a.lod1_budget:
        for lod in look["game"]["lods"]:
            if lod["name"] == "lod1":
                lod["budget"] = int(a.lod1_budget)
    t0 = time.perf_counter()
    tiles = tx.make_tiles(look)
    gu.scale_tiles_to_albedo(look, tiles)
    tiles_s = time.perf_counter() - t0
    asset = look["game"]["unreal"]["asset"]

    def skeleton(m, age):
        skel, rad, is_root, orig = cli.skeleton(m, age)
        pos, r_wood = shoot_arrays(m, age)
        return skel, rad, is_root, orig, pos, r_wood

    clock = StageClock()
    w = clock.wrap
    level = {"tree_meshes": 0, "wood_arrays": 0}
    real_meshes, real_arrays = gu.tree_meshes, game.wood_arrays

    def meshes(*args, **kwargs):
        name = "wood tube, nearest" if level["tree_meshes"] == 0 else "wood tube, lod1"
        level["tree_meshes"] += 1
        clock.push(name)
        try:
            return real_meshes(*args, **kwargs)
        finally:
            clock.pop()

    def arrays(*args, **kwargs):
        name = "wood arrays, nearest" if level["wood_arrays"] == 0 else "wood arrays, lod1"
        level["wood_arrays"] += 1
        clock.push(name)
        try:
            return real_arrays(*args, **kwargs)
        finally:
            clock.pop()
    gu.tree_meshes, game.wood_arrays = meshes, arrays
    for owner, name, stage in ((game, "bake_wood", "bark bake"), (gu, "_bark_maps", "maps to PNG"), (gu.Maps, "write", "maps to PNG"), (gu, "blade_mesh", "leaf blades"),
                               (gu, "card_mesh", "leaf cards, lod1"), (ap, "leaf_instances", "leaf instances"), (ap, "peel_strips", "bark strips"), (gu, "shape_stem", "stem relief"),
                               (gu, "stem_edges", "stem relief"), (gu, "root_atlas", "root bake"), (gu, "leaf_atlas", "atlases"), (gu, "card_atlas", "atlases"), (gu, "strip_atlas", "atlases"),
                               (game, "far_sheets", "far sheets, lod2"), (GameGLB, "write_gltf", "file writing"), (GameGLB, "add_mesh", "file writing"), (gu, "export_stage", "export: other")):
        w(owner, name, stage)
    rows = {}
    for age in ages:
        if age > model.year:
            continue
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        level["tree_meshes"] = level["wood_arrays"] = 0
        ctx = {"look": look, "model": model, "sp": sp, "out": work, "asset": asset, "meta": {"species": "betula_pendula", "seed": a.seed}, "tiles": tiles, "snaps": snaps, "seed": a.seed, "skeleton": skeleton}
        last = clock.snapshot()
        t0 = time.perf_counter()
        stage = gu.export_stage(ctx, age, ["summer"], log=lambda s: print(s, flush=True))
        wall = time.perf_counter() - t0
        now = clock.snapshot()
        files = stage["seasons"]["summer"]
        sizes = {p.name: p.stat().st_size for p in work.rglob("*") if p.is_file()}
        rows[age] = {"wall": wall, **status_mb(), **year_row(now, last), "disk_mb": sum(sizes.values()) / 2 ** 20,
                     "levels": {k: {"triangles": v["triangles"], "vertices": v.get("vertices"), "file_mb": v.get("file_mb"), "parts": v.get("parts")} for k, v in files.items()},
                     "leaves": stage["exported_leaves"],
                     "gltf_mb": sum(v for k, v in sizes.items() if k.endswith((".gltf", ".bin"))) / 2 ** 20, "png_mb": sum(v for k, v in sizes.items() if k.endswith(".png")) / 2 ** 20,
                     "nodes": int(model.tree.n), "alive_at_end": int((model.tree.death[: model.tree.n] < 0).sum())}
        print(f"age {age}: {wall:.1f} s, {rows[age]['levels']}, disk {rows[age]['disk_mb']:.0f} MB, peak {rows[age]['peak_mb']:.0f} MB", flush=True)
        name = f"mesh_s{a.seed}" + (f"_lod1_{a.lod1_budget}" if a.lod1_budget else "")
        (out / f"{name}.json").write_text(json.dumps({"what": "mesh", "seed": a.seed, "lod1_budget": a.lod1_budget or 16000, "grow_s": grow_s, "tiles_s": tiles_s,
                                                     "rows": {str(k): v for k, v in rows.items()}}), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)


def run_lines(a) -> None:
    """Which of treegen's lines a tree and a small plot reach, on these settings.  sys.monitoring, each line once, so it costs little.
    A line not reached may still be needed: storms are rare, and a small run won't take every branch."""
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    pkg = str(ROOT / "treegen")
    seen = defaultdict(set)
    mon = sys.monitoring
    tool = mon.COVERAGE_ID
    mon.use_tool_id(tool, "cpp_cost")

    def on_line(code, line):
        if code.co_filename.startswith(pkg):
            seen[code.co_filename].add(line)
        return mon.DISABLE
    mon.register_callback(tool, mon.events.LINE, on_line)
    mon.set_events(tool, mon.events.LINE)
    cli, checkpoint, sp, raw = load(a)
    import copy

    from treegen.growth import GrowthModel
    from treegen.plot import Plot
    from treegen import species_schema as schema

    env_p, _ = cli.load_environment("sweden_open_field")
    sp0 = copy.deepcopy(sp)
    checkpoint.set_values(sp, settings(a))
    m = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    for _ in range(a.years):
        m.step()
    sp2 = sp0
    items = settings(a) + [x for x in PLOT if not x.startswith("plot.natural_start.area_m2")] + ["plot.natural_start.area_m2=200"]
    checkpoint.set_values(sp2, items)
    plot = Plot(sp2, cli.make_environment(env_p), lambda: cli.make_soil(env_p), seed=a.seed, mode="natural", lean=True)
    plot.enable_regeneration()
    while plot.year < a.years and plot.alive:
        plot.step()
    mon.set_events(tool, 0)
    mon.free_tool_id(tool)
    doc = {}

    def code_lines(code, out_set):
        for _, _, ln in code.co_lines():
            if ln:
                out_set.add(ln)
        for c in code.co_consts:
            if hasattr(c, "co_lines"):
                code_lines(c, out_set)

    for p in sorted(Path(pkg).glob("*.py")):
        text = p.read_text(encoding="utf-8")
        lines: set = set()
        code_lines(compile(text, str(p), "exec"), lines)
        hit = seen.get(str(p), set())
        doc[p.name] = {"lines": len(text.splitlines()), "code_lines": len(lines), "reached": len(hit & lines)}
    flat = schema.flatten(raw)
    settings_all = {k: v for k, v in flat.items() if schema.is_setting(k, v)}
    switches = {k: v for k, v in settings_all.items() if isinstance(v, bool)}
    labels = schema.load_labels(ROOT / "reference" / "betula_pendula" / "labels.yaml")
    species_text = (ROOT / "species" / "betula_pendula.yaml").read_text(encoding="utf-8")
    read = schema.read_labels(raw, species_text, labels)
    count = defaultdict(int)
    for k, v in read.items():
        count[getattr(v, "status", v if isinstance(v, str) else v.get("status") if isinstance(v, dict) else str(v))] += 1
    (out / "lines.json").write_text(json.dumps({"modules": doc, "settings_in_file": len(settings_all), "switches": len(switches), "switches_on": sum(1 for v in switches.values() if v),
                                                "in_schema": sum(1 for k in settings_all if k in schema.BY_PATH), "labels": dict(count),
                                                "appearance_settings": sum(1 for k in settings_all if k.startswith("appearance.")),
                                                "growth_settings": sum(1 for k in settings_all if not k.startswith("appearance."))}, indent=1), encoding="utf-8")
    print(json.dumps(doc, indent=0)[:2000], flush=True)


# -- tables ----------------------------------------------------------------------------------------------------------------------
ROW_ORDER = ["light: field", "light", "shedding", "water", "carbon", "growth: shoots", "growth: rings", "mechanics", "roots", "damage", "thinning", "seed spread", "stats", "drop dead", "tree: other", "plot: other"]


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def table_tree(docs: list, title: str) -> str:
    lines = [f"### {title}: {len(docs)} seeds, one server core each, seconds in that one year", "", "| Stage | " + " | ".join(f"Age {a}" for a in PLAN_AGES) + " | Share of the whole run | Of it compiled |", "|---|" + "---|" * (len(PLAN_AGES) + 2)]
    total = defaultdict(float)
    comp = defaultdict(float)
    for d in docs:
        for row in d["rows"].values():
            for k, v in row.get("by", {}).items():
                total[k] += v
            for k, v in row.get("compiled", {}).items():
                comp[k] += v
    whole = sum(total.values()) or 1.0
    for s in ROW_ORDER + sorted(set(total) - set(ROW_ORDER)):
        if s in total and total[s] / whole > 0.0005:
            vals = [_mean([d["rows"][str(a)].get("by", {}).get(s, 0.0) for d in docs if str(a) in d["rows"]]) for a in PLAN_AGES]
            lines.append(f"| {s} | " + " | ".join(f"{v:.3f}" if v is not None else "" for v in vals) + f" | {100 * total[s] / whole:.1f} % | {100 * comp[s] / total[s]:.0f} % |")
    wall = [_mean([d["rows"][str(a)]["wall"] for d in docs if str(a) in d["rows"]]) for a in PLAN_AGES]
    lines.append("| **All, wall** | " + " | ".join(f"**{v:.3f}**" for v in wall) + f" | 100 % | **{100 * sum(comp.values()) / whole:.0f} %** |")
    for key, name in (("alive", "Crown nodes, live"), ("nodes", "Crown nodes, all"), ("root_alive", "Root nodes, live"), ("root_nodes", "Root nodes, all"), ("height_m", "Height, m"), ("rss_mb", "Process now, MB"), ("peak_mb", "Process peak, MB")):
        vals = [_mean([d["rows"][str(a)].get(key) for d in docs if str(a) in d["rows"]]) for a in PLAN_AGES]
        lines.append(f"| {name} | " + " | ".join(f"{v:,.1f}" if key == "height_m" else f"{v:,.0f}" for v in vals) + " | | |")
    lines.append("| Light grid | " + " | ".join("x".join(str(v) for v in docs[0]["rows"][str(a)].get("grid", [])) for a in PLAN_AGES) + " | | |")
    lines.append(f"\nWhole run to 60: {_mean([d['seconds'] for d in docs]):.1f} s a tree; each seed {', '.join(f'{d['seconds']:.1f}' for d in docs)} s. Digests: {', '.join(d['digest'][:12] for d in docs)}.")
    mem = ["", "**Memory per tree, MB:**", "", "| Age | Model state | Crown arrays | Root arrays | Everything else | Arrays, live nodes only | And single precision | Light and soil grids (a place, not a tree) |", "|---|---|---|---|---|---|---|---|"]
    for a in PLAN_AGES:
        ms = [d["memory"][str(a)] for d in docs if str(a) in d["memory"]]
        if ms:
            live = _mean([(m["crown"]["live_b"] + m["root"]["live_b"]) / 2 ** 20 for m in ms])
            l32 = _mean([(m["crown"]["live32_b"] + m["root"]["live32_b"]) / 2 ** 20 for m in ms])
            mem.append(f"| {a} | {_mean([m['state_mb'] for m in ms]):.1f} | {_mean([m['crown_mb'] for m in ms]):.1f} | {_mean([m['roots_mb'] for m in ms]):.1f} | {_mean([m['other_mb'] for m in ms]):.1f} | {live:.1f} | {l32:.1f} | {_mean([m['place_mb'] for m in ms]):.1f} |")
    last = docs[0]["memory"].get("60")
    if last:
        mem.append("\nLargest in the first seed's state at 60, MB: " + ", ".join(f"{t['what'].replace('model.', '')} {t['mb']:.2f}" for t in last["top"]) + f". Bytes per node: {last['crown']['bytes_per_node']}, or {last['crown']['bytes_per_node_32']} in single precision.")
    return "\n".join(lines + mem) + "\n"


def table_plot(docs: list, title: str) -> str:
    lines = [f"### {title}: {len(docs)} plots, one server core each, per tree-year (seconds)", "", "| Stage | " + " | ".join(f"Age {a}" for a in PLAN_AGES) + " | Share of the whole run | Of it compiled |", "|---|" + "---|" * (len(PLAN_AGES) + 2)]
    total = defaultdict(float)
    comp = defaultdict(float)
    for d in docs:
        for row in d["rows"].values():
            if row.get("profiled"):
                continue
            for k, v in row.get("by", {}).items():
                total[k] += v
            for k, v in row.get("compiled", {}).items():
                comp[k] += v
    whole = sum(total.values()) or 1.0

    def per(d, a, s):
        r = d["rows"].get(str(a))
        if not r or not r.get("stepped"):
            return None
        return r["by"].get(s, 0.0) / r["stepped"]
    for s in ROW_ORDER + sorted(set(total) - set(ROW_ORDER)):
        if s in total and total[s] / whole > 0.0005:
            vals = [_mean([per(d, a, s) for d in docs]) for a in PLAN_AGES]
            lines.append(f"| {s} | " + " | ".join(f"{v:.4f}" if v is not None else "" for v in vals) + f" | {100 * total[s] / whole:.1f} % | {100 * comp[s] / total[s]:.0f} % |")
    vals = [_mean([d["rows"][str(a)]["wall"] / max(d["rows"][str(a)]["stepped"], 1) for d in docs if str(a) in d["rows"]]) for a in PLAN_AGES]
    lines.append("| **All, wall** | " + " | ".join(f"**{v:.4f}**" if v is not None else "" for v in vals) + f" | 100 % | **{100 * sum(comp.values()) / whole:.0f} %** |")
    for key, name, fmt in (("wall", "Whole plot's year, s", "{:,.1f}"), ("stepped", "Trees stepped", "{:,.0f}"), ("alive", "Live crown nodes, whole plot", "{:,.0f}"), ("nodes", "All crown nodes, whole plot", "{:,.0f}"), ("root_alive", "Live root nodes, whole plot", "{:,.0f}"), ("rss_mb", "Process now, MB", "{:,.0f}"), ("peak_mb", "Process peak, MB", "{:,.0f}")):
        vs = [_mean([d["rows"][str(a)].get(key) for d in docs if str(a) in d["rows"]]) for a in PLAN_AGES]
        lines.append(f"| {name} | " + " | ".join(fmt.format(v) if v is not None else "" for v in vs) + " | | |")
    lines.append("| Light grid | " + " | ".join("x".join(str(v) for v in (docs[0]["rows"].get(str(a), {}).get("grid") or [])) for a in PLAN_AGES) + " | | |")
    stands = [(k, [d["rows"].get(str(a), {}).get("stats", {}).get(k) for d in docs]) for k, a in ()]
    lines.append("")
    ever = [max(int(r["ever"]) for r in d["rows"].values()) for d in docs]
    tree_years = [sum(int(r["stepped"]) for r in d["rows"].values()) for d in docs]
    # the two years run under cProfile are slow: the per tree-year figure leaves them out
    clean = [(sum(r["wall"] for r in d["rows"].values() if not r.get("profiled")), sum(int(r["stepped"]) for r in d["rows"].values() if not r.get("profiled"))) for d in docs]
    lines.append(f"Whole run: {', '.join(f'{d['seconds']:.0f}' for d in docs)} s; tree-years {tree_years}; trees ever {ever}; seconds per tree-year, profiled years left out: {', '.join(f'{w / max(t, 1):.3f}' for w, t in clean)}.")
    stand = ["", "**The stand:**", "", "| Age | Stems/ha | Basal area, m2/ha | Top height, m | LAI | New trees that year |", "|---|---|---|---|---|---|"]
    for a in PLAN_AGES:
        rs = [d["rows"][str(a)]["stats"] for d in docs if str(a) in d["rows"]]
        if rs:
            stand.append(f"| {a} | {_mean([r.get('stems_per_ha') for r in rs]):,.0f} | {_mean([r.get('basal_area_ob_m2_ha') for r in rs]):.1f} | {_mean([r.get('top_height_m') for r in rs]):.1f} | {_mean([r.get('lai') for r in rs]):.2f} | {_mean([r.get('new_trees') for r in rs]):.0f} |")
    mem = ["", "**Memory per living tree, MB:**", "", "| Age | Trees | Model state | Crown arrays | Root arrays | Everything else | Arrays in use | Arrays, live nodes only | And single precision | Grids and shared, whole plot |", "|---|---|---|---|---|---|---|---|---|---|"]
    for a in PLAN_AGES:
        ms = [d["memory"][str(a)] for d in docs if str(a) in d["memory"]]
        if ms:
            mem.append(f"| {a} | {_mean([m['trees'] for m in ms]):.0f} | {_mean([m['state_mb'] for m in ms]):.2f} | {_mean([m['crown_mb'] for m in ms]):.2f} | {_mean([m['roots_mb'] for m in ms]):.2f} | {_mean([m['other_mb'] for m in ms]):.2f} | {_mean([m['used_mb'] for m in ms]):.2f} | {_mean([m['live_mb'] for m in ms]):.2f} | {_mean([m['live32_mb'] for m in ms]):.2f} | {_mean([m['place_mb'] for m in ms]):.0f} |")
    last = docs[0]["memory"].get("60")
    if last:
        mem.append("\nLargest in the first plot at 60, MB, whole plot: " + ", ".join(f"{t['what'].replace('plot.trees[*].', '')} {t['mb']:.0f}" for t in last["top"]) + ".")
    # what a tree costs by its size, the shared light apart
    fit = ["", "**A tree's own step against its live nodes (crown + roots), least squares at each age, shared light apart:**", "", "| Age | Trees | Seconds at no nodes | Microseconds per live node | Largest tree's step, s |", "|---|---|---|---|---|"]
    for a in PLAN_AGES:
        pts = [p for d in docs for p in d["rows"].get(str(a), {}).get("per_tree", [])]
        if len(pts) > 3:
            x = np.array([p[0] + p[1] for p in pts], float)
            y = np.array([p[2] for p in pts], float)
            b, c = np.polyfit(x, y, 1)
            fit.append(f"| {a} | {len(pts)} | {c:.4f} | {b * 1e6:.1f} | {y.max():.3f} |")
    return "\n".join(lines + stand + mem + fit) + "\n"


def table_mesh(doc: dict) -> str:
    rows = doc["rows"]
    ages = [a for a in map(str, PLAN_AGES) if a in rows]
    stages = sorted({s for a in ages for s in rows[a]["by"]}, key=lambda s: -rows[ages[-1]]["by"].get(s, 0.0))
    lines = [f"### Export of one stand tree, every level, seed {doc['seed']}, lod1 budget {doc.get('lod1_budget', 16000):,}: seconds for that age (grown once in {doc['grow_s']:.0f} s, bark tiles {doc['tiles_s']:.0f} s)", "", "| Part | " + " | ".join(f"Age {a}" for a in ages) + " |", "|---|" + "---|" * len(ages)]
    for s in stages:
        lines.append(f"| {s} | " + " | ".join(f"{rows[a]['by'].get(s, 0.0):.2f}" for a in ages) + " |")
    lines.append("| **All** | " + " | ".join(f"**{rows[a]['wall']:.1f}**" for a in ages) + " |")
    for lv in ("lod0", "lod1", "lod2"):
        lines.append(f"| Triangles, {lv} | " + " | ".join(f"{rows[a]['levels'].get(lv, {}).get('triangles', 0):,}" for a in ages) + " |")
        if any(rows[a]["levels"].get(lv, {}).get("vertices") for a in ages):
            lines.append(f"| Vertices, {lv} | " + " | ".join(f"{rows[a]['levels'].get(lv, {}).get('vertices') or 0:,}" for a in ages) + " |")
            lines.append(f"| File, {lv}, MB | " + " | ".join(f"{rows[a]['levels'].get(lv, {}).get('file_mb') or 0:,.2f}" for a in ages) + " |")
    for key, name in (("gltf_mb", "Mesh files, MB"), ("png_mb", "Texture files, MB"), ("peak_mb", "Process peak so far, MB")):
        lines.append(f"| {name} | " + " | ".join(f"{rows[a][key]:,.0f}" for a in ages) + " |")
    return "\n".join(lines) + "\n"


def table_kernels(rows: list) -> str:
    """Milliseconds, best of a few runs on the same input, and whether the strict C++ gave the same bits."""
    out = []
    for kernel in dict.fromkeys(r["kernel"] for r in rows):
        rs = [r for r in rows if r["kernel"] == kernel]
        keys = list(dict.fromkeys(k for r in rs for k in r["times"]))
        out += [f"### {kernel}: milliseconds", "", "| Age | Size | " + " | ".join(keys) + " | C++ strict against the original, bits |", "|---|---|" + "---|" * (len(keys) + 1)]
        for r in rs:
            b = r["bits"].get("strict", {})

            def word(x):
                if isinstance(x, bool):
                    return "same" if x else "differ"
                if x.get("same_bits"):
                    return "same"
                return f"{x['differ']:,} of {x['of']:,} differ, at most {x['max_rel']:.1e} relative"
            same = word(b) if "same_bits" in b else "; ".join(f"{k} {word(v)}" for k, v in b.items())
            out.append(f"| {r['age']} | " + ", ".join(f"{k} {v}" for k, v in r["size"].items()) + " | " + " | ".join(f"{1000 * r['times'][k]:,.3g}" if k in r["times"] else "" for k in keys) + f" | {same} |")
        out.append("")
    return "\n".join(out) + "\n"


def run_table(a) -> None:
    trees, plots, meshes, hots, lines_doc = defaultdict(list), defaultdict(list), [], [], None
    kernel_rows = []
    plain = []
    chaos = []
    saves = []
    singles = defaultdict(list)
    far_trees, far_plots = [], []
    for folder in a.folders:
        for p in sorted(Path(folder).expanduser().glob("*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            if p.name.startswith("far_tree_"):
                far_trees.append(d)
            elif p.name.startswith("far_plot_"):
                far_plots.append(d)
            elif p.name.startswith("single_"):
                singles[d["arm"]] += d["trees"]
            elif p.name.startswith("chaos_"):
                chaos.append(d)
            elif p.name.startswith("saves_"):
                saves.append(d)
            elif p.name.startswith("kernels_"):
                kernel_rows += d
            elif p.name.startswith("tree_") and d.get("plain"):
                plain.append(d)
            elif p.name.startswith("tree_") and not d.get("plain"):
                trees[f"{d['settings']}, speed {d['speed']}"].append(d)
            elif p.name.startswith("plot_"):
                plots[f"{d['settings']}, speed {d['speed']}"].append(d)
            elif p.name.startswith("mesh_"):
                meshes.append(d)
            elif p.name.startswith("hot_"):
                hots.append((p.name, d))
            elif p.name == "lines.json":
                lines_doc = d
    out = []
    for d in plain:
        out.append(f"Plain run, no timers: {d['settings']}, speed {d['speed']}, seed {d['seed']}: {d['seconds']:.1f} s, digest {d['digest'][:12]}.\n")
    if kernel_rows:
        out.append(table_kernels(kernel_rows))
    for d in chaos:
        out.append(table_chaos(d))
    if saves:
        out.append(table_saves(saves))
    if singles:
        out.append(table_single(singles))
    if far_trees or far_plots:
        out.append(table_far(far_trees, far_plots))
    for k, docs in sorted(trees.items()):
        out.append(table_tree(docs, f"Stand tree, {k}"))
    for k, docs in sorted(plots.items()):
        out.append(table_plot(docs, f"Plot, {k}"))
    for d in meshes:
        out.append(table_mesh(d))
    for name, d in hots:
        for age, rows in d.items():
            out.append(f"### Top functions by own time, {name}, year {age}\n\n| Function | Where | Calls | Own, s |\n|---|---|---|---|\n" + "\n".join(f"| {r['name']} | {r['where']} | {r['calls']:,} | {r['own_s']:.3f} |" for r in rows[:25]) + "\n")
    if lines_doc:
        rows = "\n".join(f"| {k} | {v['lines']:,} | {v['code_lines']:,} | {v['reached']:,} |" for k, v in lines_doc["modules"].items())
        rest = {k: v for k, v in lines_doc.items() if k != "modules"}
        out.append(f"### Lines reached\n\n| Module | Lines | Lines of code | Reached |\n|---|---|---|---|\n{rows}\n\n{json.dumps(rest)}\n")
    from treegen import species_schema as schema
    import yaml

    raw = yaml.safe_load((ROOT / "species" / "betula_pendula.yaml").read_text(encoding="utf-8"))
    flat = schema.flatten(raw)
    out.append(f"### The species file\n\nValues and settings: {len(flat)}; of them in species_schema.py: {sum(1 for k in flat if k in schema.BY_PATH)}; lines in the file: "
               f"{len((ROOT / 'species' / 'betula_pendula.yaml').read_text(encoding='utf-8').splitlines())}. By block: "
               + ", ".join(f"{b} {sum(1 for k in flat if k.split('.')[0] == b)}" for b in raw) + "\n")
    text = "\n".join(out)
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")


def run_chaos(a) -> None:
    """How fast a difference too small to matter spreads: the same seed with resource.alpha changed by a tiny share, year by year.  This is what a port's
    rounding would do, and it sets how long a run of Python and C++ can stay comparable tree for tree."""
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    cli, checkpoint, _, _ = load(a)
    from treegen.growth import GrowthModel

    env_p, _ = cli.load_environment("sweden_open_field")
    keys = ("height_m", "dbh_cm", "leaf_area_m2", "crown_width_m", "lai")
    doc = {}

    def grow(seed, factor):
        sp, _ = cli.load_species("betula_pendula")
        checkpoint.set_values(sp, settings(a))
        sp.resource.alpha = float(sp.resource.alpha) * factor
        m = GrowthModel(sp, cli.make_environment(env_p), seed, stand=True, soil=cli.make_soil(env_p), lean=True)
        rows = []
        for _ in range(a.years):
            m.step()
            T = m.tree
            s = m.stats[-1]
            rows.append({**{k: s.get(k) for k in keys}, "nodes": int(T.n), "alive": int((T.death[: T.n] < 0).sum()), "digest": hash(T.pos[: T.n].tobytes())})
        return rows

    for seed in range(a.seed, a.seed + a.seeds):
        base = grow(seed, 1.0)
        doc[str(seed)] = {"base": base}
        for factor in (1.0 + 1e-15, 1.0 + 1e-12, 1.0 + 1e-6):
            doc[str(seed)][repr(factor)] = grow(seed, factor)
            print(f"seed {seed} x {factor!r} done", flush=True)
        (out / f"chaos_s{a.seed}.json").write_text(json.dumps(doc), encoding="utf-8")


def table_chaos(doc: dict) -> str:
    lines = ["### How fast a tiny change spreads: stand trees, resource.alpha changed by the share shown", "", "| Seed | Change | First year any node's position differs | First year a whole-tree figure differs (as rounded in the stats) | "
             + " | ".join(f"Height, stem, leaf area at {y}, % off" for y in PLAN_AGES) + " |", "|---|---|---|---|" + "---|" * len(PLAN_AGES)]
    for seed, runs in doc.items():
        base = runs["base"]
        for name, rows in runs.items():
            if name == "base":
                continue
            exact = next((i + 1 for i, (r, b) in enumerate(zip(rows, base)) if r["digest"] != b["digest"]), None)
            shown = next((i + 1 for i, (r, b) in enumerate(zip(rows, base)) if any(r[k] != b[k] for k in ("height_m", "dbh_cm", "leaf_area_m2", "crown_width_m"))), None)

            def off(y):
                r, b = rows[y - 1], base[y - 1]
                return ", ".join(f"{100.0 * (r[k] / b[k] - 1.0):+.2f}" if r.get(k) and b.get(k) else "-" for k in ("height_m", "dbh_cm", "leaf_area_m2"))
            lines.append(f"| {seed} | {float(name) - 1.0:.0e} | {exact} | {shown} | " + " | ".join(off(y) for y in PLAN_AGES) + " |")
    return "\n".join(lines) + "\n"


def run_saves(a) -> None:
    """What one tree would cost on disk: the whole state pickled as Python saves it, and the node arrays of living nodes alone, in single precision."""
    import gzip
    import pickle
    import zlib

    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    cli, checkpoint, sp, _ = load(a)
    checkpoint.set_values(sp, settings(a))
    from treegen.growth import GrowthModel

    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    rows = {}
    mb = 2.0 ** 20
    for _ in range(a.years):
        m.step()
        if m.year not in AGES:
            continue
        keep = m._field, getattr(m, "_plot_view", None), m.light, m.roots.field, getattr(m.roots, "_kept_soil", None)
        m._field = m._plot_view = m.light = None
        m.roots.field = None
        m.roots._kept_soil = None
        blob = pickle.dumps(m, protocol=pickle.HIGHEST_PROTOCOL)
        m._field, m._plot_view, m.light, m.roots.field, m.roots._kept_soil = keep
        parts = []
        for T in (m.tree, m.roots.tree):
            alive = T.death[: T.n] < 0
            for name in list(T.VEC) + list(T.SCALAR):
                x = getattr(T, name)[: T.n][alive]
                parts.append((x.astype(np.float32) if x.dtype == np.float64 else x).tobytes())
        raw = b"".join(parts)
        rows[m.year] = {"pickle_mb": len(blob) / mb, "pickle_gz_mb": len(gzip.compress(blob, 1)) / mb, "live32_mb": len(raw) / mb, "live32_z1_mb": len(zlib.compress(raw, 1)) / mb, "live32_z6_mb": len(zlib.compress(raw, 6)) / mb}
        print(m.year, rows[m.year], flush=True)
    (out / f"saves_{a.speed}_s{a.seed}.json").write_text(json.dumps({"seed": a.seed, "speed": a.speed, "rows": {str(k): v for k, v in rows.items()}}), encoding="utf-8")


def table_saves(docs: list) -> str:
    lines = ["### One tree on disk, MB", "", "| Age | Speed | Seed | Whole state, pickled | Pickled, gzip | Living nodes' arrays, single precision | Those, zlib level 1 | Those, zlib level 6 |", "|---|---|---|---|---|---|---|---|"]
    for d in docs:
        for a, r in d["rows"].items():
            if int(a) in PLAN_AGES:
                lines.append(f"| {a} | {d['speed']} | {d['seed']} | {r['pickle_mb']:.1f} | {r['pickle_gz_mb']:.1f} | {r['live32_mb']:.1f} | {r['live32_z1_mb']:.1f} | {r['live32_z6_mb']:.1f} |")
    return "\n".join(lines) + "\n"


SKELETON_RADII = (0.005, 0.01, 0.02)       # m: a limb skeleton keeps living wood at least this thick


def _z(b: bytes) -> int:
    import zlib
    return len(zlib.compress(b, 6))


def far_forms(m, history=None) -> dict:
    """What a tree far from the player could hold to stay itself, in bytes, raw and compressed (zlib 6).  Sums over the arrays as they
    are, written as a C++ port might: these are sizes, not a working far form.

    full: every living node and every dead stub still on living wood (knots), all node arrays, 8-byte numbers as 4, crown and roots.
    skeleton r: the crown's and roots' living wood at least r thick, and the stubs on it, 32 bytes a node (parent, position, radius, sapwood
      area, birth, death, axis), or 19 quantised (position from the parent in mm, radius in 0.02 mm, years as bytes), plus at each point
      where finer wood was left off, the leaf area and bud count beyond it (6 bytes).
    rings: the ring widths of that skeleton, every year of its life, 0.01 mm in 2 bytes (only with the yearly radii, a non-lean tree).
    rest: everything else in the model, pickled with gzip: carbon pools, random streams, the frame's plan, records."""
    import gzip
    import pickle

    from treegen.growth import LAT_DORMANT, LAT_SPUR

    out = {}
    full_parts, counts = [], {}
    keeps = {r: {"plain": [], "quant": [], "summary": 0, "nodes": 0} for r in SKELETON_RADII}
    ring_parts = {r: [] for r in SKELETON_RADII}
    ring_years = {r: 0 for r in SKELETON_RADII}
    for part, T in (("crown", m.tree), ("root", m.roots.tree)):
        n = T.n
        par = T.parent[:n].astype(np.int64)
        alive = T.death[:n] < 0
        scar = ~alive & (par >= 0) & alive[np.maximum(par, 0)]
        held = alive | scar
        counts[part] = {"nodes": int(n), "alive": int(alive.sum()), "stubs": int(scar.sum())}
        for name in list(T.VEC) + list(T.SCALAR):
            x = getattr(T, name)[:n][held]
            full_parts.append((x.astype(np.float32) if x.dtype == np.float64 else x).tobytes())
        r = T.radius[:n]
        # leaf area and buds beyond each node, for the summary where finer wood is left off
        leaves = np.where(alive, T.leaves[:n].astype(np.float64), 0.0) if part == "crown" else np.zeros(n)
        buds = np.where(alive & ((T.term[:n] == 1) | np.isin(T.lat[:n], (LAT_DORMANT, LAT_SPUR))), 1.0, 0.0) if part == "crown" else np.zeros(n)
        acc = np.stack([leaves, buds], 1)
        lv = T.levels(alive)
        acc = T.basipetal(lv, acc) if len(lv) > 1 else acc
        for rk in SKELETON_RADII:
            keep = (alive & (r >= rk)) | (scar & (r[np.maximum(par, 0)] >= rk))
            keep[0] = True
            idx = np.nonzero(keep)[0]
            remap = np.full(n, -1, np.int64)
            remap[idx] = np.arange(len(idx))
            p = np.where(par[idx] >= 0, remap[np.maximum(par[idx], 0)], -1)
            pos = T.pos[:n][idx]
            rel = pos - T.pos[:n][np.maximum(par[idx], 0)]
            birth, death = T.birth[:n][idx], T.death[:n][idx]
            plain = [p.astype(np.int32).tobytes(), pos.astype(np.float32).tobytes(), r[idx].astype(np.float32).tobytes(), T.sap_area[:n][idx].astype(np.float32).tobytes(),
                     birth.astype(np.int16).tobytes(), death.astype(np.int16).tobytes(), T.axis[:n][idx].astype(np.int32).tobytes()]
            quant = [p.astype(np.int32).tobytes(), np.clip(np.round(rel * 1000.0), -32767, 32767).astype(np.int16).tobytes(),
                     np.clip(np.round(r[idx] / 2e-5), 0, 65535).astype(np.uint16).tobytes(),
                     np.clip(np.round(255.0 * T.sap_area[:n][idx] / np.maximum(T.wood_area[:n][idx], 1e-12)), 0, 255).astype(np.uint8).tobytes(),
                     np.clip(birth, 0, 255).astype(np.uint8).tobytes(), np.clip(death, 0, 255).astype(np.uint8).tobytes(), T.axis[:n][idx].astype(np.int32).tobytes()]
            # where living wood was left off: what it carried
            child_off = alive & ~keep & (par >= 0) & keep[np.maximum(par, 0)]
            ends = np.unique(par[child_off])
            summary = 6 * len(ends)
            k = keeps[rk]
            k["plain"] += plain
            k["quant"] += quant
            k["summary"] += summary
            k["nodes"] += len(idx)
            if history is not None and part == "crown":
                years = len(history)
                live_idx = idx[alive[idx]]
                H = np.zeros((years, len(live_idx)), np.float32)
                for y, hr in enumerate(history):
                    ok = live_idx < len(hr)
                    H[y, ok] = hr[live_idx[ok]]
                rings = np.diff(np.vstack([np.zeros((1, len(live_idx)), np.float32), H]), axis=0)
                born = (H > 0)
                vals = np.clip(np.round(rings[born] / 1e-5), 0, 65535).astype(np.uint16)
                ring_parts[rk].append(vals.tobytes())
                ring_years[rk] += int(born.sum())
    raw = b"".join(full_parts)
    out["full"] = {"raw": len(raw), "z": _z(raw)}
    for rk in SKELETON_RADII:
        k = keeps[rk]
        pl, qu = b"".join(k["plain"]), b"".join(k["quant"])
        out[f"skeleton_{rk}"] = {"nodes": k["nodes"], "raw": len(pl) + k["summary"], "z": _z(pl) + k["summary"], "quant_raw": len(qu) + k["summary"], "quant_z": _z(qu) + k["summary"]}
        if history is not None:
            rb = b"".join(ring_parts[rk])
            out[f"rings_{rk}"] = {"node_years": ring_years[rk], "raw": len(rb), "z": _z(rb)}
    # everything else, with the node stores, grids and records left out
    hide = {"tree": None, "light": None, "_field": None, "_plot_view": None, "soil": None, "sp": None, "radius_history": [], "keyframes": {}, "stats": [], "diag": None,
            "_bud_q": None, "_leaf_density": None, "_psi": None, "_r_last": None, "_r_pipe": None, "_ring": None, "_stand_map": None, "_clone_angle": {}}
    keep_m = {k: m.__dict__.get(k) for k in hide if k in m.__dict__}
    rk_ = {k: m.roots.__dict__.get(k) for k in ("tree", "field", "_kept_soil", "radius_history", "soil") if k in m.roots.__dict__}
    try:
        for k in keep_m:
            m.__dict__[k] = hide[k]
        for k in rk_:
            m.roots.__dict__[k] = [] if k == "radius_history" else None
        blob = pickle.dumps(m, protocol=pickle.HIGHEST_PROTOCOL)
    finally:
        m.__dict__.update(keep_m)
        m.roots.__dict__.update(rk_)
    out["rest"] = {"raw": len(blob), "z": len(gzip.compress(blob, 6))}
    out["counts"] = counts
    # bringing the whole state back, Python: decompress the arrays, and load a whole pickled tree
    import zlib
    zb = zlib.compress(raw, 6)
    t0 = time.perf_counter()
    zlib.decompress(zb)
    out["decompress_s"] = time.perf_counter() - t0
    saved = m.__dict__.get("_field"), m.__dict__.get("_plot_view"), m.light
    m._field = m._plot_view = None
    m.light = None
    try:
        whole = pickle.dumps(m, protocol=pickle.HIGHEST_PROTOCOL)
    finally:
        m._field, m._plot_view, m.light = saved
    t0 = time.perf_counter()
    pickle.loads(whole)
    out["unpickle_s"] = time.perf_counter() - t0
    out["pickle_mb"] = len(whole) / 2 ** 20
    return out


def run_far(a) -> None:
    """Far forms of stand trees (non-lean, so their yearly radii give the rings), or of every tree in a plot (lean)."""
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    cli, checkpoint, sp, _ = load(a)
    env_p, _ = cli.load_environment("sweden_open_field")
    if not a.in_plot:
        from treegen.growth import GrowthModel

        checkpoint.set_values(sp, settings(a))
        m = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p))
        rows = {}
        for _ in range(a.years):
            m.step()
            if m.year in AGES:
                rows[str(m.year)] = far_forms(m, m.radius_history)
                print(m.year, json.dumps({k: v for k, v in rows[str(m.year)].items() if k != "counts"})[:400], flush=True)
        (out / f"far_tree_s{a.seed}.json").write_text(json.dumps({"seed": a.seed, "rows": rows}), encoding="utf-8")
        return
    from treegen.plot import Plot

    items = settings(a) + PLOT
    checkpoint.set_values(sp, items)
    plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), seed=a.seed, mode="natural", lean=True)
    plot.enable_regeneration()
    rows = {}
    while plot.year < a.years and plot.alive:
        plot.step()
        if plot.year in AGES:
            per = [far_forms(plot.trees[k]) for k in plot.alive]
            rows[str(plot.year)] = per
            print(plot.year, len(per), flush=True)
            (out / f"far_plot_s{a.seed}.json").write_text(json.dumps({"seed": a.seed, "rows": rows}), encoding="utf-8")


def table_far(trees: list, plots: list) -> str:
    mb = 2.0 ** 20
    lines = []

    def block(title, rows_by_age):
        ls = [f"### {title}", "", "| Form | " + " | ".join(f"Age {a}" for a in PLAN_AGES) + " |", "|---|" + "---|" * len(PLAN_AGES)]
        keys = [("full", "raw", "Full: living nodes and stubs, all arrays, single precision"), ("full", "z", "Full, compressed")]
        for rk in SKELETON_RADII:
            keys += [(f"skeleton_{rk}", "nodes", f"Skeleton >= {rk * 100:g} cm: nodes"), (f"skeleton_{rk}", "raw", f"Skeleton >= {rk * 100:g} cm, 32 bytes a node"),
                     (f"skeleton_{rk}", "quant_z", f"Skeleton >= {rk * 100:g} cm, quantised, compressed")]
            keys += [(f"rings_{rk}", "z", f"Its rings, every year, compressed")]
        keys += [("rest", "z", "Everything else in the model, gzip"), ("pickle_mb", None, "Whole state pickled, MB"), ("unpickle_s", None, "Loading that pickle, s"), ("decompress_s", None, "Decompressing the full arrays, s")]
        for k, sub, name in keys:
            vals = []
            for a_ in PLAN_AGES:
                rs = rows_by_age.get(str(a_), [])
                xs = [(r[k][sub] if sub else r[k]) for r in rs if k in r and (sub is None or sub in r[k])]
                vals.append(_mean(xs))
            if all(v is None for v in vals):
                continue
            if sub in ("raw", "z", "quant_z"):
                ls.append(f"| {name}, MB | " + " | ".join("" if v is None else f"{v / mb:.3f}" for v in vals) + " |")
            elif sub == "nodes":
                ls.append(f"| {name} | " + " | ".join("" if v is None else f"{v:,.0f}" for v in vals) + " |")
            else:
                ls.append(f"| {name} | " + " | ".join("" if v is None else f"{v:.3f}" for v in vals) + " |")
        return ls + [""]

    if trees:
        by = {str(a_): [d["rows"][str(a_)] for d in trees if str(a_) in d["rows"]] for a_ in PLAN_AGES}
        lines += block(f"Far forms of a stand tree, mean of {len(trees)} seeds, per tree", by)
        c = trees[0]["rows"].get("60", {}).get("counts")
        if c:
            lines.append(f"Seed {trees[0]['seed']} at 60: crown {c['crown']['alive']:,} living nodes and {c['crown']['stubs']:,} dead stubs on living wood, of {c['crown']['nodes']:,}; roots {c['root']['alive']:,} living.\n")
    for d in plots:
        lines += block(f"Far forms of the trees in plot {d['seed']}, mean per living tree", d["rows"])
        big = ["| Age | Trees | Largest tree, full, compressed, MB | Largest, skeleton >= 1 cm, quantised, compressed, MB | All trees, full, compressed, MB |", "|---|---|---|---|---|"]
        for a_ in PLAN_AGES:
            rs = d["rows"].get(str(a_))
            if rs:
                big.append(f"| {a_} | {len(rs)} | {max(r['full']['z'] for r in rs) / mb:.2f} | {max(r['skeleton_0.01']['quant_z'] for r in rs) / mb:.3f} | {sum(r['full']['z'] for r in rs) / mb:.1f} |")
        lines += big + [""]
    return "\n".join(lines) + "\n"


SINGLE_KEYS = ("height_m", "dbh_cm", "leaf_area_m2", "crown_width_m", "crown_ratio", "lai", "subcanopy_diffuse_light_pct")


def run_single(a) -> None:
    """Does single precision change the tree?  Stand trees with every 8-byte number in the node arrays as 4, from outside: the model's code is the same, and numpy then
    works in single precision on those arrays.  With no speed settings, since the compiled copies assume doubles.  --set single=1 is this arm; without it, the plain baseline."""
    from treegen.structure import Tree

    single = a.single
    if single:
        for k, dt in list(Tree.SCALAR.items()):
            if dt is np.float64:
                Tree.SCALAR[k] = np.float32
        init = Tree.__init__

        def init32(self, capacity=4096):
            init(self, capacity)
            for k in Tree.VEC:
                setattr(self, k, getattr(self, k).astype(np.float32))
        Tree.__init__ = init32
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    cli, checkpoint, _, _ = load(a)
    from treegen.growth import GrowthModel

    env_p, _ = cli.load_environment("sweden_open_field")
    doc = []
    arm = "single" if single else "double"
    for seed in range(a.seed, a.seed + a.seeds):
        sp, _ = cli.load_species("betula_pendula")
        checkpoint.set_values(sp, settings(a))
        t0 = time.perf_counter()
        m = GrowthModel(sp, cli.make_environment(env_p), seed, stand=True, soil=cli.make_soil(env_p), lean=True)
        rows, mem = {}, {}
        for _ in range(a.years):
            m.step()
            if m.year in AGES:
                rows[str(m.year)] = {k: m.stats[-1].get(k) for k in SINGLE_KEYS}
                mem[str(m.year)] = tree_memory(m)["state_mb"]
        doc.append({"seed": seed, "seconds": time.perf_counter() - t0, "rows": rows, "state_mb": mem, "dtype": str(m.tree.pos.dtype)})
        print(f"{arm} seed {seed}: {doc[-1]['seconds']:.0f} s, {doc[-1]['dtype']}, height at the end {rows[str(a.years)]['height_m'] if str(a.years) in rows else None}, state {mem.get(str(a.years))} MB", flush=True)
        (out / f"single_{arm}_s{a.seed}.json").write_text(json.dumps({"arm": arm, "trees": doc}), encoding="utf-8")


def table_single(docs: dict) -> str:
    d, s = docs.get("double"), docs.get("single")
    if not d or not s:
        return ""
    lines = [f"### Single precision against double, stand trees, no speed settings, {len(d)} and {len(s)} seeds (unpaired: a seed makes a different tree after any change)", "",
             "| Age | Measure | Double, mean | Single, mean | Change, % | z |", "|---|---|---|---|---|---|"]
    for age in map(str, PLAN_AGES):
        for k in SINGLE_KEYS:
            x = [t["rows"][age][k] for t in d if age in t["rows"] and t["rows"][age].get(k) is not None]
            y = [t["rows"][age][k] for t in s if age in t["rows"] and t["rows"][age].get(k) is not None]
            if len(x) > 1 and len(y) > 1:
                mx, my = float(np.mean(x)), float(np.mean(y))
                se = float(np.sqrt(np.var(x, ddof=1) / len(x) + np.var(y, ddof=1) / len(y)))
                lines.append(f"| {age} | {k} | {mx:.3f} | {my:.3f} | {100 * (my / mx - 1) if mx else 0:+.1f} | {(my - mx) / se if se else 0:+.1f} |")
    for name, t in (("double", d), ("single", s)):
        lines.append(f"\n{name}: {_mean([x['seconds'] for x in t]):.0f} s a tree; model state at 50, 60: {_mean([x['state_mb'].get('50') for x in t]):.1f}, {_mean([x['state_mb'].get('60') for x in t]):.1f} MB.")
    return "\n".join(lines) + "\n"


def run_batch(a) -> None:
    import subprocess

    for command in a.commands:
        print(f"RUN {command}", flush=True)
        done = subprocess.run([sys.executable, str(Path(__file__).resolve())] + command.split())
        print(f"exit {done.returncode}: {command}", flush=True)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="what", required=True)
    for name in ("tree", "plot", "mesh", "hot", "lines", "chaos", "saves", "single", "far"):
        p = sub.add_parser(name)
        p.add_argument("--single", action="store_true", help="single: this arm in single precision")
        p.add_argument("--in-plot", action="store_true", help="far: every tree of a plot, not a stand tree")
        p.add_argument("--lod1-budget", type=int, default=None, help="mesh: triangles for lod1")
        p.add_argument("--label", required=True)
        p.add_argument("--seed", type=int, default=1)
        p.add_argument("--seeds", type=int, default=3, help="chaos: how many seeds from --seed")
        p.add_argument("--years", type=int, default=60)
        p.add_argument("--settings", choices=["full", "default"], default="full")
        p.add_argument("--speed", choices=["off", "lossless", "rows_drop"], default="lossless")
        p.add_argument("--plain", action="store_true", help="tree: no timers, for the overhead and the digest")
        p.add_argument("--profile-at", default="35,55", help="plot: years to run under cProfile (left out of the stage totals)")
        p.add_argument("--at", default="30,60", help="hot: years to profile")
        p.add_argument("--ages", default="10,30,50,60", help="mesh")
        p.add_argument("--set", action="append", default=[])
    t = sub.add_parser("table")
    t.add_argument("folders", nargs="+")
    t.add_argument("--out", default=None)
    b = sub.add_parser("batch", help="several of these one after another, each its own process: one core, no overlap")
    b.add_argument("commands", nargs="+")
    a = ap.parse_args()
    {"tree": run_tree, "plot": run_plot, "mesh": run_mesh, "hot": run_hot, "lines": run_lines, "chaos": run_chaos, "saves": run_saves, "single": run_single, "far": run_far, "table": run_table, "batch": run_batch}[a.what](a)


if __name__ == "__main__":
    main()
