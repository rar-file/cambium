"""Offline: which natural-plot trees would buckle under their own winter
weight plus the mean Finnish crown snow load (5.35 kg m-2, Lehtonen et al.
2014), and when?  Same Rayleigh estimate as stem_mechanics.py (E 10.7 GPa,
fresh density 900 kg m-3; stem, crown wood, snow on the crown's projected
area).  Positions are stored every 5 tree-years, so each tree is checked at
tree ages 5, 10, ... (dated by plot year).  Growth is as logged: a tree
that would have died does not release light here.
python -I tools/snow_buckling.py <plot dir>"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from treegen.export import Timeline  # noqa: E402

E, RHO, G = 10.7e9, 900.0, 9.81


def factor(tl, st, y, snow):
    s = st[y]
    par = tl["shoot_parent"].astype(np.int64)
    birth, death = tl["shoot_birth_year"], tl["shoot_death_year"]
    alive = (birth <= y) & ((death < 0) | (death > y))
    pos = tl["shoot_position"] if y >= tl.years else tl.positions_at(y)
    r = tl.radius_at(y).astype(float)
    top = np.nonzero(alive)[0][np.argmax(pos[alive, 2])]
    ch = [top]
    while par[ch[-1]] >= 0:
        ch.append(par[ch[-1]])
    ch = np.array(ch[::-1])
    stem = np.zeros(len(par), bool); stem[ch] = True
    H = float(pos[alive, 2].max())
    if H < 2.0:
        return np.inf, H
    L = np.linalg.norm(tl["shoot_position"] - tl["shoot_position"][np.maximum(par, 0)], axis=1); L[0] = 0
    vol = math.pi * r ** 2 * L
    br = alive & ~stem
    zb, mb = pos[br, 2], RHO * vol[br]
    zc, rc = pos[ch, 2], r[ch]
    zs = 0.5 * (zc[1:] + zc[:-1])
    ms = RHO * math.pi * rc[1:] ** 2 * np.linalg.norm(np.diff(pos[ch], axis=0), axis=1)
    cw = s.get("crown_width_m") or 0.0
    msnow = snow * math.pi * (cw / 2) ** 2 * mb / max(mb.sum(), 1e-12)
    grid = np.linspace(0.0, H, 300)
    rz = np.interp(grid, zc, rc)
    EI = E * math.pi * rz ** 4 / 4
    w1 = (math.pi / (2 * H)) * np.sin(math.pi * grid / (2 * H))
    w2 = (math.pi / (2 * H)) ** 2 * np.cos(math.pi * grid / (2 * H))
    # mass above each grid height (cumulative from the top)
    zall = np.concatenate([zs, zb, zb]); mall = np.concatenate([ms, mb, msnow])
    o = np.argsort(zall)[::-1]
    csum = np.cumsum(mall[o]); zsorted = zall[o]
    N = G * np.array([csum[np.searchsorted(-zsorted, -z, side="left") - 1] if (zsorted > z).any() else 0.0 for z in grid])
    return np.trapezoid(EI * w2 ** 2, grid) / max(np.trapezoid(N * w1 ** 2, grid), 1e-30), H


src = Path(sys.argv[1])
pj = json.loads((src / "plot.json").read_text())
area_ha = pj["area_m2"] / 1e4
fail = {}
lam_at = {}
for t in pj["trees"]:
    f = src / f"tree_{t['id']:03d}"
    if not (f / "timeline.json").exists():
        continue
    tl = Timeline(f / "timeline.json")
    st = json.loads((f / "stats.json").read_text())["per_year"]
    g = t["germination"]
    last = (t["removed"] if t["removed"] is not None else 60) - g
    for a in range(5, min(len(st), tl.years + 1, last + 1), 5):
        lam_own, H = factor(tl, st, a, 0.0)
        lam_snow, _ = factor(tl, st, a, 5.35)
        lam_at[(t["id"], a + g)] = (lam_own, lam_snow, H, st[a]["dbh_cm"] or 0.0)
        for key, lam in (("own", lam_own), ("snow", lam_snow)):
            if lam < 1.0 and (t["id"], key) not in fail:
                fail[(t["id"], key)] = a + g
print("| plot year | trees alive (logged) | /ha logged | buckled by now under own weight | /ha left | buckled with mean snow load | /ha left |")
print("|---|---|---|---|---|---|---|")
for Y in (20, 25, 30, 35, 40, 45, 50, 55, 60):
    alive_log = [t for t in pj["trees"] if (t["removed"] is None or t["removed"] > Y) and Y > t["germination"]]
    n_own = sum(1 for t in alive_log if fail.get((t["id"], "own"), 999) <= Y)
    n_snow = sum(1 for t in alive_log if fail.get((t["id"], "snow"), 999) <= Y)
    n = len(alive_log)
    print(f"| {Y} | {n} | {n / area_ha:.0f} | {n_own} | {(n - n_own) / area_ha:.0f} | {n_snow} | {(n - n_snow) / area_ha:.0f} |")
first = sorted(v for (tid, k), v in fail.items() if k == "snow")
print("\nfirst failures with mean snow (plot year): ", first[:15])
fs = [(tid, v) for (tid, k), v in fail.items() if k == "snow"]
fs.sort(key=lambda x: x[1])
for tid, v in fs[:6]:
    lo, ls, H, D = lam_at[(tid, v)]
    print(f"  tree {tid}: fails at plot year {v}: H {H:.1f} m, DBH {D:.1f} cm (wood), H/D {H / max(D / 100, 1e-6):.0f}, factor own {lo:.2f}, with snow {ls:.2f}")
ok = [lam_at[k] for k in lam_at if k[1] in (45, 50, 60)]
