"""Seedlings in steady shade: how much light does a seedling need to live and to grow?

    python tools/shade_trial.py --label node_shade --lights 0.15,0.25,0.4,1.0 --years 12 --set speed.quick_solve=true
    python tools/shade_trial.py --label node_shade --arm soft=shedding.shade_softness=1.0

Each light gets its own small plot of seedlings, far enough apart to shade each other little, under a canopy
that isn't there: every bud's exposure is simply multiplied by that light.  The carbon rule and the hazards act
as in a stand.  Writes table.md and trial.json under out/bench/ensemble/<label>.  It reads the model and changes
nothing in it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import cli  # noqa: E402
from treegen import checkpoint  # noqa: E402
from treegen.plot import Plot  # noqa: E402

BASE = ROOT / "out" / "bench" / "ensemble"
READ_AT = (1, 2, 3, 5, 8, 12, 15, 20)


class ShadedField:
    """A light field with a steady canopy over it: exposure times ``light``."""

    def __init__(self, field, light: float):
        self.f = field
        self.light = float(light)
        self.p, self.S, self.lo, self.periodic = field.p, field.S, field.lo, field.periodic
        self.diffuse_layers = None

    def shadow_at_voxel(self, pos):
        return self.f.shadow_at_voxel(pos) - self.p.C * np.log(self.light)

    def exposure(self, pos, self_weight, own_shade=None):
        return self.f.exposure(pos, self_weight, own_shade) * self.light

    def sample(self, pts):
        return self.f.sample(pts) - self.p.C * np.log(self.light)

    def optimal_direction(self, pos, heading):
        return self.f.optimal_direction(pos, heading)

    def relative_light_at_heights(self, heights):
        return None

    def diffuse_light_at_heights(self, heights):
        return None


def trial(a, light: float, soil: str, items: list, herb: bool) -> dict:
    sp, _ = cli.load_species(a.species)
    checkpoint.set_values(sp, ["plot.stand_measures=true", "plot.natural_start.enabled=true", f"plot.natural_start.stems_per_ha={a.stems}",
                               f"plot.natural_start.area_m2={a.area}", "mortality.enabled=true"] + items)
    env_p, _ = cli.load_environment(a.environment)

    def make_soil():
        s = cli.make_soil(env_p)
        if not herb:
            s.herb_lai = 0.0
        return s

    plot = Plot(sp, cli.make_environment(env_p), make_soil, seed=a.seed, mode="natural", lean=True)
    compute = plot.light.compute
    plot.light.compute = lambda *x, **kw: ShadedField(compute(*x, **kw), light)
    for m in plot.trees:
        m.field_layer_exposed = 0 if soil == "mineral" else None
    n = len(plot.trees)
    rows = {}
    while plot.year < a.years and plot.alive:
        plot.step()
        if plot.year in READ_AT or plot.year == a.years:
            alive = [k for k in plot.alive if plot.trees[k].stats]
            h = [plot.trees[k].stats[-1]["height_m"] for k in alive]
            bal = [plot.trees[k].carbon.get("fixed", 0.0) / max(plot.trees[k].carbon.get("upkeep", 0.0), 1e-12) for k in alive if plot.trees[k].carbon]
            rows[plot.year] = dict(alive=len(plot.alive) / n, height_m=float(np.mean(h)) if h else None, height_max_m=max(h) if h else None,
                                   fixed_over_upkeep=float(np.median(bal)) if bal else None)
    causes = {}
    for x in plot.info:
        if x.get("removed") is not None:
            causes[x.get("cause")] = causes.get(x.get("cause"), 0) + 1
    return dict(light=light, soil=soil, seedlings=n, rows=rows, causes=causes)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", required=True)
    ap.add_argument("--species", default="betula_pendula")
    ap.add_argument("--environment", default="sweden_open_field")
    ap.add_argument("--lights", default="0.10,0.15,0.20,0.25,0.30,0.40,0.60,1.0")
    ap.add_argument("--soils", default="mineral,organic")
    ap.add_argument("--years", type=int, default=12)
    ap.add_argument("--area", type=float, default=1000.0)
    ap.add_argument("--stems", type=float, default=300.0, help="stems/ha: 300 is about 6 m apart")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-herb", action="store_true", help="also run each with no field layer at all")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap.add_argument("--arm", action="append", default=[], metavar="NAME=KEY=JSON;KEY=JSON", help="the whole trial again with these changes")
    a = ap.parse_args()
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    arms = [["V", ""]] + [x.split("=", 1) for x in a.arm]
    results, lines = [], ["| Arm | Soil | Field layer | Light | " + " | ".join(f"Alive, height at {y}" for y in READ_AT if y <= a.years) + " | Fixed over upkeep at 2, 5 | Deaths |",
                          "|---|---|---|---|" + "---|" * (sum(1 for y in READ_AT if y <= a.years) + 2)]
    for name, item in arms:
        items = list(a.set) + [x for x in item.split(";") if x]
        for soil in a.soils.split(","):
            for herb in ([True, False] if a.no_herb else [True]):
                for light in (float(x) for x in a.lights.split(",")):
                    r = trial(a, light, soil, items, herb)
                    r.update(arm=name, herb=herb)
                    results.append(r)
                    cells = []
                    for y in READ_AT:
                        if y > a.years:
                            continue
                        v = r["rows"].get(y)
                        cells.append(f"{v['alive'] * 100:.0f} %, {v['height_m']:.2f} m" if v and v["height_m"] is not None else "0 %")
                    bal = [r["rows"].get(y, {}).get("fixed_over_upkeep") for y in (2, 5)]
                    lines.append(f"| {name} | {soil} | {'yes' if herb else 'no'} | {light:.2f} | " + " | ".join(cells) + " | " +
                                 ", ".join("-" if b is None else f"{b:.2f}" for b in bal) + f" | {r['causes']} |")
                    print(lines[-1], flush=True)
                    (out / "table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
                    (out / "trial.json").write_text(json.dumps(results), encoding="utf-8")
    print("done", flush=True)


if __name__ == "__main__":
    main()
