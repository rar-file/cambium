"""Where the time and memory go (campaign P0, step 2).  Measures only: timers wrap
the model's functions from outside, and the run prints a digest of its output so
you can check that measuring changed nothing.

    python tools/profile_run.py tree --years 60
    python tools/profile_run.py plot --start-trees 25 --years 20
    python tools/profile_run.py mesh --years 30
    python tools/profile_run.py tree --years 60 --cprofile     # also the top functions

Time: seconds per simulated year by component, each function's own time only, so
nothing is counted twice.  Memory: the 10 largest things in the model at the year
memory peaks, found by walking the model's attributes; for a mesh export, the 10
source lines holding the most memory at the export's peak (tracemalloc, which slows
the export, so read its time from a run without it).  Results go to out/bench/p0/.

These are heavy runs for plots and mesh exports (PROTOCOL.md section 6).
"""
from __future__ import annotations

import argparse
import cProfile
import functools
import io
import json
import pstats
import sys
import time
import tracemalloc
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

OUT = ROOT / "out" / "bench" / "p0"
REPORT_AGES = (10, 20, 30, 40, 50, 60)


class Clock:
    """Each wrapped function's own time, by component; time in functions it calls
    goes to their components instead."""

    def __init__(self):
        self.totals = defaultdict(float)
        self.calls = defaultdict(int)
        self._stack = []

    def wrap(self, fn, component):
        @functools.wraps(fn)
        def timed(*args, **kwargs):
            t0 = time.perf_counter()
            self._stack.append(0.0)
            try:
                return fn(*args, **kwargs)
            finally:
                dt = time.perf_counter() - t0
                inner = self._stack.pop()
                self.totals[component] += dt - inner
                self.calls[component] += 1
                if self._stack:
                    self._stack[-1] += dt
        return timed

    def patch(self, owner, name, component):
        setattr(owner, name, self.wrap(getattr(owner, name), component))


def instrument(clock: Clock):
    import cli
    from treegen import export, hydraulics, mechanics
    from treegen.growth import GrowthModel
    from treegen.light import LightField, ShadowPropagation
    from treegen.plot import Plot
    from treegen.roots import RootSystem, SharedSoil

    table = {
        "light": [(ShadowPropagation, "compute"), (ShadowPropagation, "own_shade"), (GrowthModel, "light_sources"),
                  (GrowthModel, "wood_sources"), (GrowthModel, "_stand_cell"), (GrowthModel, "_crown_light_asymmetry"),
                  (GrowthModel, "_herb_factor"), (LightField, "exposure"), (LightField, "sample"),
                  (LightField, "optimal_direction"), (LightField, "relative_light_at_heights"),
                  (LightField, "diffuse_light_at_heights")],
        "water": [(hydraulics, "solve"), (RootSystem, "update_uptake"), (GrowthModel, "_fine_root_mass"),
                  (RootSystem, "availability_field"), (SharedSoil, "update")],
        "carbon solve": [(GrowthModel, "_growth_factor"), (GrowthModel, "_leaf_costs")],
        "shoot growth": [(GrowthModel, "_grow_shoots"), (GrowthModel, "_shed"), (GrowthModel, "_reiterate"),
                         (GrowthModel, "_leader_damage")],
        "rings": [(GrowthModel, "_update_radii"), (GrowthModel, "_stress_area"), (GrowthModel, "_wind_load_scale")],
        "mechanics": [(mechanics, "bend_and_correct")],
        "roots": [(RootSystem, "step"), (RootSystem, "update_radii")],
        "stats": [(GrowthModel, "measure"), (Plot, "measure")],
        "rest of the year step": [(GrowthModel, "step"), (GrowthModel, "_finish_year"), (Plot, "step")],
        "mesh export": [(cli, "export_all")],
        "file writing": [(export, "write_timeline"), (export, "write_stats"), (export.GLBWriter, "add"),
                         (export.GLBWriter, "close"), (export.USDWriter, "add"), (export.USDWriter, "close"),
                         (GrowthModel, "spill_history"), (Plot, "checkpoint")],
    }
    for component, targets in table.items():
        for owner, name in targets:
            clock.patch(owner, name, component)


def working_set_mb() -> float:
    import cli
    if sys.platform != "win32":
        return cli.peak_memory_mb()
    import ctypes
    import ctypes.wintypes as wt

    from batch import _PMC
    k32 = ctypes.WinDLL("kernel32")
    k32.GetCurrentProcess.restype = wt.HANDLE
    f = k32.K32GetProcessMemoryInfo
    f.argtypes = [wt.HANDLE, ctypes.POINTER(_PMC), wt.DWORD]
    f.restype = wt.BOOL
    c = _PMC()
    c.cb = ctypes.sizeof(_PMC)
    f(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return c.WorkingSetSize / 2 ** 20


def memory_by_attribute(root, name: str) -> dict:
    """Bytes by attribute path under an object, with list and dict positions merged
    (trees[*].tree.pos).  An array viewed from several places counts once."""
    sizes = defaultdict(int)
    seen = set()

    def visit(o, path):
        if id(o) in seen:
            return
        if isinstance(o, np.ndarray):
            base = o
            while isinstance(base.base, np.ndarray):
                base = base.base
            if id(base) not in seen:
                seen.add(id(base))
                sizes[path] += int(base.nbytes)
            seen.add(id(o))
            return
        if o is None or isinstance(o, (bool, type)) or callable(o):
            return
        seen.add(id(o))
        if isinstance(o, (int, float, str, bytes, np.generic)):
            sizes[path] += sys.getsizeof(o)
        elif isinstance(o, dict):
            sizes[path] += sys.getsizeof(o)
            for k, v in o.items():
                visit(v, f"{path}[*]" if not isinstance(k, str) or k.isdigit() else f"{path}.{k}")
        elif isinstance(o, (list, tuple, set, frozenset)):
            sizes[path] += sys.getsizeof(o)
            for v in o:
                visit(v, f"{path}[*]")
        elif isinstance(o, SimpleNamespace) or hasattr(o, "__dict__"):
            for k, v in vars(o).items():
                visit(v, f"{path}.{k}")
        else:
            sizes[path] += sys.getsizeof(o)

    visit(root, name)
    return dict(sizes)


def top_entries(sizes: dict, n: int = 10) -> list:
    return [{"what": k, "mb": round(v / 2 ** 20, 2)} for k, v in sorted(sizes.items(), key=lambda kv: -kv[1])[:n]]


class Run:
    def __init__(self, clock):
        self.clock = clock
        self.rows = {}
        self.last = {}
        self.peak = {"mb": 0.0, "year": None, "top": [], "model_mb": 0.0}

    def after_year(self, year, root, name):
        now = dict(self.clock.totals)
        self.rows[year] = {k: now.get(k, 0.0) - self.last.get(k, 0.0) for k in now}
        self.last = now
        ws = working_set_mb()
        if ws > self.peak["mb"]:
            sizes = memory_by_attribute(root, name)
            self.peak = {"mb": round(ws, 1), "year": year, "top": top_entries(sizes),
                         "model_mb": round(sum(sizes.values()) / 2 ** 20, 1)}


def report(case: str, run: Run, extra: dict, years: int, seconds: float):
    comps = sorted(run.clock.totals, key=lambda k: -run.clock.totals[k])
    total = sum(run.clock.totals.values())
    lines = [f"# Profile: {case}, {years} years, {seconds:.1f} s", "",
             "| Component | Seconds | Share |", "|---|---|---|"]
    for c in comps:
        lines.append(f"| {c} | {run.clock.totals[c]:.2f} | {100 * run.clock.totals[c] / max(total, 1e-9):.1f} % |")
    ages = [a for a in REPORT_AGES if a in run.rows]
    if ages:
        lines += ["", "**Seconds in that one simulated year:**", "", "| Component | " + " | ".join(str(a) for a in ages) + " |",
                  "|---|" + "---|" * len(ages)]
        for c in comps:
            lines.append(f"| {c} | " + " | ".join(f"{run.rows[a].get(c, 0.0):.3f}" for a in ages) + " |")
    lines += ["", f"**Memory at its peak, year {run.peak['year']}: {run.peak['mb']} MB in the process, "
              f"{run.peak['model_mb']} MB found in the model's attributes:**", "", "| What | MB |", "|---|---|"]
    lines += [f"| {t['what']} | {t['mb']} |" for t in run.peak["top"]]
    if extra.get("export_top"):
        lines += ["", f"**Mesh export, at its peak of {extra['export_peak_mb']} MB traced:**", "", "| Source line | MB |", "|---|---|"]
        lines += [f"| {t['what']} | {t['mb']} |" for t in extra["export_top"]]
    if extra.get("digest"):
        lines += ["", f"Output digest: `{extra['digest']}`"]
    if extra.get("cprofile"):
        lines += ["", "```", extra["cprofile"], "```"]
    text = "\n".join(lines) + "\n"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"profile_{case}.md").write_text(text, encoding="utf-8")
    doc = {"case": case, "years": years, "seconds": seconds, "totals": dict(run.clock.totals),
           "per_year": {str(k): v for k, v in run.rows.items()}, "peak": run.peak,
           **{k: v for k, v in extra.items() if k != "cprofile"}}
    (OUT / f"profile_{case}.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(text)


def profile_export(model, sp, folder: Path) -> dict:
    """Export the meshes under tracemalloc, keeping the snapshot at the highest point."""
    import cli
    from treegen import export

    best = {"mb": 0.0, "snap": None}

    def note():
        cur, _ = tracemalloc.get_traced_memory()
        if cur / 2 ** 20 > best["mb"] + 20.0:
            best["mb"] = cur / 2 ** 20
            best["snap"] = tracemalloc.take_snapshot()

    add = export.GLBWriter.add

    def add_noted(self, *a, **k):
        out = add(self, *a, **k)
        note()
        return out

    export.GLBWriter.add = add_noted
    meta = {"species": sp.species.scientific_name, "seed": model.seed}
    anchorage = cli.anchorage_numbers(model, sp)
    tracemalloc.start()
    cli.export_all(model, sp, folder, meta, anchorage, [], 400_000, {}, {})
    tracemalloc.stop()
    export.GLBWriter.add = add
    top = []
    if best["snap"] is not None:
        for s in best["snap"].statistics("lineno")[:10]:
            f = s.traceback[0]
            top.append({"what": f"{Path(f.filename).name}:{f.lineno}", "mb": round(s.size / 2 ** 20, 2)})
    return {"export_peak_mb": round(best["mb"], 1), "export_top": top}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("case", choices=["tree", "plot", "mesh"])
    ap.add_argument("--years", type=int, default=None)
    ap.add_argument("--start-trees", type=int, default=25)
    ap.add_argument("--cprofile", action="store_true")
    a = ap.parse_args()

    import cli
    from sensitivity_screen import output_digest
    from treegen.growth import GrowthModel
    from treegen.plot import Plot

    years = a.years or {"tree": 60, "plot": 20, "mesh": 30}[a.case]
    clock = Clock()
    instrument(clock)
    run = Run(clock)
    sp, _ = cli.load_species("betula_pendula")
    env_p, _ = cli.load_environment("sweden_open_field")
    extra = {}
    prof = cProfile.Profile() if a.cprofile else None
    if prof:
        prof.enable()
    t0 = time.time()
    folder = OUT / f"work_{a.case}"
    folder.mkdir(parents=True, exist_ok=True)
    if a.case == "plot":
        stages = sorted(sp.stand.thinning, key=lambda s: float(s.from_height_m))
        n_final = a.start_trees * float(stages[-1].stems_per_ha) / float(stages[0].stems_per_ha)
        plot = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), n_final, 1, "natural")
        for _ in range(years):
            plot.step()
            run.after_year(plot.year, plot, "plot")
            if plot.year % 5 == 0 and plot.year < years:   # as tools/plot.py does
                plot.checkpoint(folder)
    else:
        model = GrowthModel(sp, cli.make_environment(env_p), 1, stand=True, soil=cli.make_soil(env_p))
        for _ in range(years):
            model.step()
            run.after_year(model.year, model, "model")
        extra["digest"] = output_digest(model)
        if a.case == "mesh":
            extra.update(profile_export(model, sp, folder))
    seconds = time.time() - t0
    if prof:
        prof.disable()
        buf = io.StringIO()
        pstats.Stats(prof, stream=buf).sort_stats("tottime").print_stats(25)
        extra["cprofile"] = buf.getvalue()
    report(a.case, run, extra, years, seconds)


if __name__ == "__main__":
    main()
