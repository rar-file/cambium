"""A quick side view of grown trees, wood alone and wood with leaves, for judging limbs and crown shape before a full render.

No meshes, no textures: every living internode is a line as wide as its wood, every leafy node a dot.  Light on disk and quick, so it can be run
on every attempt; the real look is still tools/game_export.py.  It only reads the model.  Also writes the limbs' sizes as limbs_s<seed>.json.

    python tools/crown_sketch.py --label node_c2x --seeds 3,5,7 --ages 30,50,60 --open --set crown_frame.enabled=true ...
"""
from __future__ import annotations

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
    return {"age": int(model.year), "height_m": float(model.stats[-1]["height_m"]), "dbh_cm": model.stats[-1]["dbh_cm"], "limbs": rows}


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
        rr = 0.055 * ppm * ss
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
            panels.append(draw(model, ppm, False, tag, 17.0, 27.0))
            panels.append(draw(model, ppm, True, "", 17.0, 27.0))
            tables.append(limb_table(model))
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
    a = ap.parse_args(argv)
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
