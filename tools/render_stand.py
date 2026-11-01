"""Eye-level stand render framed like a photograph: a level camera 1.6 m up
with a given focal length (px) and horizon row, the hero mesh (every twig)
for every tree out to --max-dist, sky in a measured clear-sky colour.

  python tools/render_stand.py runs <runs dir> <out.png> <winter|summer> [options]
  python tools/render_stand.py plot <plot dir> <out.png> <winter|summer> [options]

runs: single-tree runs <runs dir>/<seed>_stand (or the folders matching
--pattern) placed at random at 450 stems/ha; plot: the trees of a
tools/plot.py run at their own positions.
The patch repeats periodically, each copy turned by its own random angle.
The defaults frame it like the Gullmarsskogen 5 reference photo (Sony
RX100 at 10.4 mm: f = 1513 px at 1280 px width, horizon 1370 px down, from
the farthest stem bases); summer adds plain leaf cards at the short shoots.
Options: --f 1513 --horizon 1370 --width 1280 --height 1802 --max-dist 120"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from treegen import preview  # noqa: E402
from treegen.export import Timeline  # noqa: E402
from treegen.mesh import MeshData  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["runs", "plot"])
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("season", choices=["winter", "summer"])
ap.add_argument("--f", type=float, default=1513.0)
ap.add_argument("--horizon", type=float, default=1370.0)
ap.add_argument("--width", type=int, default=1280)
ap.add_argument("--height", type=int, default=1802)
ap.add_argument("--max-dist", type=float, default=120.0)
ap.add_argument("--n", type=int, default=20)
ap.add_argument("--pattern", default="*_stand", help="runs mode: tree folders to use (e.g. tree_* for a plot's trees)")
ap.add_argument("--density", type=float, default=450.0)
args = ap.parse_args()
src = Path(args.src)
rng = np.random.default_rng(42)

if args.mode == "runs":
    dirs = sorted((d for d in src.glob(args.pattern) if (d / "tree.glb").exists()),
                  key=lambda d: int("".join(ch for ch in d.name if ch.isdigit()) or 0))[: args.n]
    N = len(dirs)
    L = math.sqrt(N * 10000.0 / args.density)
    dmin = 0.6 * math.sqrt(10000.0 / args.density)
    pts = []
    while len(pts) < N:
        q = rng.uniform(-L / 2, L / 2, 2)
        d = np.abs(np.array(pts) - q) if pts else np.zeros((0, 2))
        d = np.minimum(d, L - d)
        if not len(d) or (np.hypot(d[:, 0], d[:, 1]) >= dmin).all():
            pts.append(q)
    pts = np.array(pts)
else:
    pj = json.loads((src / "plot.json").read_text())
    L = float(pj["side_m"])
    live = [t for t in pj["trees"] if t["removed"] is None and (src / f"tree_{t['id']:03d}" / "tree.glb").exists()]
    dirs = [src / f"tree_{t['id']:03d}" for t in live]
    pts = np.array([[t["x"], t["y"]] for t in live])
    N = len(dirs)
print(f"{N} trees, patch {L:.1f} m, {N / (L * L) * 1e4:.0f} stems/ha", flush=True)

# camera: the spot in the near quarter farthest from any stem, 1.6 m up, level, looking +x
allp = np.concatenate([pts + np.array([i * L, j * L]) for i in (-1, 0, 1) for j in (-1, 0, 1)])
gx, gy = np.meshgrid(np.linspace(-L / 2, -L / 4, 21), np.linspace(-L / 4, L / 4, 21))
cand = np.stack([gx.ravel(), gy.ravel()], 1)
dist = np.min(np.linalg.norm(cand[:, None, :] - allp[None, :, :], axis=2), axis=1)
e = cand[np.argmax(dist)]
eye = np.array([e[0], e[1], 1.6])
print(f"camera at {e.round(1)}, nearest stem {dist.max():.1f} m", flush=True)

# a symmetric level frustum with the horizon at the centre, 2 x horizon rows
# tall; the rows below the photo's bottom edge are cropped afterwards
D = 20.0
half_h = D * args.horizon / args.f
half_w = D * (args.width / 2) / args.f
res_h = int(round(2 * args.horizon))
r = preview.Rasterizer(eye + np.array([D, 0.0, 0.0]), half_w, half_h, 0, 0, res_h=res_h, eye=eye)
r.add_ground(args.max_dist + 2 * L)
tan_h = (args.width / 2) / args.f

_cache = {}


def load(d):
    if d not in _cache:
        sc = trimesh.load(d / "tree.glb", process=False)
        g = list(sc.geometry.values())[0] if hasattr(sc, "geometry") else sc
        v = np.asarray(g.vertices, float)
        nrm = np.asarray(g.vertex_normals, float)
        V = np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)
        Nn = np.stack([nrm[:, 0], -nrm[:, 2], nrm[:, 1]], 1)
        rad = np.asarray(g.vertex_attributes["_RADIUS"], float).ravel()
        _cache[d] = (V.astype(np.float32), np.asarray(g.faces), Nn.astype(np.float32), rad.astype(np.float32))
    return _cache[d]


def leaves(d, density, lrng):
    tl = Timeline(d / "timeline.json")
    y = int(tl["shoot_birth_year"].max())
    pos = tl.positions_at(y)
    live = tl["spur_death_year"] < 0
    node = tl["spur_node"][live]
    area = tl["spur_leaf_area_m2"][live].astype(float)
    P, A = [pos[node]] * 3, [area] * 3
    keep = [np.ones(len(node), bool), np.ones(len(node), bool), lrng.random(len(node)) < 0.5]
    new = tl["shoot_birth_year"] == y
    P.append(pos[new])
    A.append(np.where(tl["shoot_leaf_area_m2"][new] > 0, tl["shoot_leaf_area_m2"][new], 0.0015).astype(float))
    keep.append(np.ones(int(new.sum()), bool))
    P = np.concatenate([p[k] for p, k in zip(P, keep)])
    A = np.concatenate([a[k] for a, k in zip(A, keep)])
    if density < 1:
        sel = lrng.random(len(P)) < density
        P, A = P[sel], A[sel] / density
    m = len(P)
    az = lrng.uniform(0, 2 * np.pi, m)
    inc = np.radians(lrng.uniform(30, 70, m))
    u = np.stack([np.cos(az) * np.cos(inc), np.sin(az) * np.cos(inc), -np.sin(inc)], 1)
    w = np.stack([-np.sin(az), np.cos(az), np.zeros(m)], 1)
    Lb = np.sqrt(2.8 * A)
    Wb = Lb / 1.4
    base = P + 0.02 * np.stack([np.cos(az), np.sin(az), np.zeros(m)], 1)
    V = np.stack([base, base + 0.5 * Lb[:, None] * u + 0.5 * Wb[:, None] * w, base + Lb[:, None] * u,
                  base + 0.5 * Lb[:, None] * u - 0.5 * Wb[:, None] * w], 1).reshape(-1, 3)
    i = np.arange(m) * 4
    F = np.concatenate([np.stack([i, i + 1, i + 2], 1), np.stack([i, i + 2, i + 3], 1)])
    F = np.concatenate([F, F[:, ::-1]])
    Nn = np.repeat(np.cross(u, w), 4, axis=0)
    return V, F, Nn


def place(V, Nn, a, off):
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]], np.float32)
    return V @ R.T + np.array([off[0], off[1], 0.0], np.float32), Nn @ R.T


# every tree copy inside the horizontal field of view (plus a crown margin)
n_tiles = int(math.ceil((args.max_dist + L) / L)) + 1
todo = []
for ti in range(-1, n_tiles + 1):
    for tj in range(-n_tiles, n_tiles + 1):
        for k in range(N):
            off = pts[k] + np.array([ti * L, tj * L])
            dx, dy = off[0] - eye[0], off[1] - eye[1]
            if dx < -3.0 or dx > args.max_dist or abs(dy) > tan_h * max(dx, 0.0) + 6.0:
                continue
            todo.append((dx, ti, tj, k, off))
todo.sort(key=lambda t: t[0])
print(f"{len(todo)} tree copies in view to {args.max_dist:.0f} m", flush=True)
trng = np.random.default_rng(7)
for n_done, (dx, ti, tj, k, off) in enumerate(todo):
    a = float(trng.uniform(0, 2 * np.pi)) if (ti, tj) != (0, 0) else float(rng.uniform(0, 2 * np.pi))
    V, F, Nn, rad = load(dirs[k])
    V, Nn = place(V, Nn, a, off)
    r.add(MeshData(V, F, Nn, {"radius": rad}), "shoot")
    if args.season == "summer":
        LV, LF, LN = leaves(dirs[k], 1.0 if dx < 30 else 0.25, np.random.default_rng(n_done))
        LV, LN = place(LV.astype(np.float32), LN.astype(np.float32), a, off)
        r.add(MeshData(LV, LF, LN, {}), "leaf")
    if n_done % 25 == 0:
        print(f"  {n_done} / {len(todo)} drawn (at {dx:.0f} m)", flush=True)

# image with the photo's sky: colour by elevation angle (photo 5, measured)
img = r.img.reshape(r.H, r.W, 3).copy()
empty = ~np.isfinite(r.zbuf.reshape(r.H, r.W))
rows = (np.arange(r.H) + 0.5) / r.ss
elev = np.degrees(np.arctan2(args.horizon - rows, args.f))
ref_e = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 90.0])
ref_c = np.array([[160, 180, 208], [153, 174, 205], [152, 177, 216], [142, 169, 216], [123, 153, 201], [100, 135, 195]]) / 255.0
sky = np.stack([np.interp(elev, ref_e, ref_c[:, c]) for c in range(3)], 1)[:, None, :]
img = np.where(empty[:, :, None], np.broadcast_to(sky, img.shape), img)
img = img.reshape(r.out_h, r.ss, r.out_w, r.ss, 3).mean((1, 3))
img = (np.clip(img, 0, 1) * 255).astype(np.uint8)[: args.height]
preview.save_png(img, args.out)
print(args.out)
