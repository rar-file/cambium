"""A row of exported trees side by side, from the same .glb files game_export.py writes, for judging a stand tree among neighbours.

A tree grown in a stand is meant to be seen in one: alone on a plain it's a thin crown on a long stem, which is what it is.  So this is the fair
look against a photo of close-planted birches.  Each tree here is one folder's export, turned by a fixed angle, on a jittered grid at the given
spacing.  It only reads the files.  Growth isn't touched.

    python tools/crown_group.py out/bench/ensemble/node_a out/bench/ensemble/node_b --age 60 --spacing 5 --rows 3 --cols 5 --out out/group.png
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from treegen import look_render as lr  # noqa: E402
from game_export import _save, sun_for_camera  # noqa: E402


def placed(prims: list, angle: float, x: float, y: float) -> list:
    """Copies of a tree's meshes, turned about the vertical and moved.  Textures are shared."""
    c, s = np.cos(angle), np.sin(angle)
    out = []
    for p in prims:
        q = copy.copy(p)
        V = p.V.copy()
        V[:, 0], V[:, 1] = c * p.V[:, 0] - s * p.V[:, 1] + x, s * p.V[:, 0] + c * p.V[:, 1] + y
        q.V = V
        N = p.N.copy()
        N[:, 0], N[:, 1] = c * p.N[:, 0] - s * p.N[:, 1], s * p.N[:, 0] + c * p.N[:, 1]
        q.N = N
        if p.T is not None:
            T = p.T.copy()
            T[:, 0], T[:, 1] = c * p.T[:, 0] - s * p.T[:, 1], s * p.T[:, 0] + c * p.T[:, 1]
            q.T = T
        out.append(q)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--age", type=int, default=60)
    ap.add_argument("--season", default="summer")
    ap.add_argument("--spacing", type=float, default=5.0)
    ap.add_argument("--rows", type=int, default=3)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--res", type=int, default=1100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(a.seed)
    loaded = []
    H = 0.0
    for f in a.folders:
        folder = Path(f)
        doc = json.loads((folder / "game_manifest.json").read_text(encoding="utf-8"))
        slug = Path(doc["species_file"]).stem
        stage = next(s for s in doc["stages"] if s["age"] == a.age)
        H = max(H, float(stage["height_m"]))
        prims = lr.load_glb_primitives(folder / f"{slug}_age{a.age:03d}_{a.season}_lod0.glb")
        for p in prims:
            if p.name == "far_cards":
                p.no_cast = True
        loaded.append(prims)
    scene = []
    width = (a.cols - 1) * a.spacing
    for j in range(a.rows):
        for i in range(a.cols):
            x = (i - 0.5 * (a.cols - 1) + (0.5 if j % 2 else 0.0)) * a.spacing + float(rng.normal(0.0, 0.12 * a.spacing))
            y = j * a.spacing * 0.87 + float(rng.normal(0.0, 0.12 * a.spacing))
            scene += placed(loaded[int(rng.integers(len(loaded)))], float(rng.uniform(0.0, 2.0 * np.pi)), x, y)
    scene.append(lr.make_ground(4.0 * H + width))
    lights = lr.Lights(scene, sun_for_camera(), res=4096, sky_res=640, sky_dirs=8)
    tgt = np.array([0.0, 0.5 * a.rows * a.spacing, 0.5 * H])
    eye = np.array([0.0, -1.35 * max(H, width), 1.6])
    dist = float(np.linalg.norm(eye - tgt))
    fov = 2.0 * np.degrees(np.arctan(0.58 * H / dist))
    img = lr.render(scene, lr.View(eye, tgt, int(a.res * 1.25), a.res, fov_deg=fov), lights, ss=2)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    _save(img, Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
