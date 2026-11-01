"""Stem mechanics diagnosis (no model change).  For an exported tree at given
ages:
 1. Buckling under its own weight in winter (leafless), with the crown's wood
    and a crown snow load: Rayleigh estimate for a cantilever column with the
    stem's own EI(z) (wood radius), w = 1 - cos(pi z / 2H):
        lambda = int EI w''^2 dz / int N w'^2 dz,  N(z) = g x mass above z
    lambda < 1: the stem buckles.  E green 10.7 GPa (Finnish silver birch
    14.5 GPa at 12 % [Heraejaervi 2004] x yellow birch's green/12 % ratio
    10.3/13.9 [Wood Handbook FPL-GTR-282, Table 5-3a]); fresh density 900 kg m-3
    (basic 512-530 x (1 + 0.72), sapwood moisture of birches, Table 4-1).
    Snow on the crown's projected area: 5.35 kg m-2 (Finnish mean crown load,
    Lehtonen et al. 2014, Silva Fennica 48:1120) and 30 kg m-2 (wet snow above
    which damage typically occurs, Nykanen et al. 1997, Silva Fennica 31:193),
    put on the crown's wood in proportion to its mass.
 2. Constant-stress (Metzger) stem profile with the model's own crown as the
    wind load (drag in proportion to leaf area, uniform wind):
        M(z) = sum leaf area_i x (z_i - z),  d(z) ~ M(z)^(1/3)
    against the model stem and Hansen et al. 2023 (tools/bark.py), d/DBH.
python -I tools/stem_mechanics.py <tree dir> <ages> [label]"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import bark  # noqa: E402
from treegen.export import Timeline  # noqa: E402

E, RHO, G = 10.7e9, 900.0, 9.81
f = Path(sys.argv[1])
ages = [int(a) for a in sys.argv[2].split(",")]
label = sys.argv[3] if len(sys.argv) > 3 else f.parent.name
tl = Timeline(f / "timeline.json")
st = json.loads((f / "stats.json").read_text())["per_year"]
par = tl["shoot_parent"].astype(np.int64)
birth, death = tl["shoot_birth_year"], tl["shoot_death_year"]
sn, sb, sd, sla = tl["spur_node"].astype(np.int64), tl["spur_birth_year"], tl["spur_death_year"], tl["spur_leaf_area_m2"]
print(f"\n{label}")
print("| age | H (m) | DBH wood / over bark (cm) | H/D over bark | crown width (m) | buckling factor: own weight | + 5.35 kg/m2 snow | + 30 kg/m2 snow | d/DBH at 0.3 / 0.5 / 0.7 H: model | constant stress | birch taper |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for y in ages:
    s = st[y]
    alive = (birth <= y) & ((death < 0) | (death > y))
    pos = tl["shoot_position"] if y >= tl.years else tl.positions_at(y)
    r = tl.radius_at(y).astype(float)
    top = np.nonzero(alive)[0][np.argmax(pos[alive, 2])]
    chain = [top]
    while par[chain[-1]] >= 0:
        chain.append(par[chain[-1]])
    chain = np.array(chain[::-1])
    stem = np.zeros(len(par), bool)
    stem[chain] = True
    H = float(s["height_m"])
    zc = pos[chain, 2]
    rc = r[chain]
    # masses: stem segments and the crown's wood (fresh), by height
    L = np.linalg.norm(tl["shoot_position"] - tl["shoot_position"][np.maximum(par, 0)], axis=1)
    L[0] = 0.0
    vol = math.pi * r ** 2 * L
    br = alive & ~stem
    zb, mb = pos[br, 2], RHO * vol[br]
    zs = 0.5 * (zc[1:] + zc[:-1])
    ms = RHO * math.pi * rc[1:] ** 2 * np.linalg.norm(np.diff(pos[chain], axis=0), axis=1)
    cw = s.get("crown_width_m") or 0.0
    A_c = math.pi * (cw / 2) ** 2
    grid = np.linspace(0.0, H, 400)
    rz = np.interp(grid, zc, rc)
    EI = E * math.pi * rz ** 4 / 4
    w1 = (math.pi / (2 * H)) * np.sin(math.pi * grid / (2 * H))
    w2 = (math.pi / (2 * H)) ** 2 * np.cos(math.pi * grid / (2 * H))
    num = np.trapezoid(EI * w2 ** 2, grid)
    lam = []
    for snow in (0.0, 5.35, 30.0):
        msnow = snow * A_c * mb / max(mb.sum(), 1e-12)
        N = np.array([G * (ms[zs > z].sum() + mb[zb > z].sum() + msnow[zb > z].sum()) for z in grid])
        lam.append(num / np.trapezoid(N * w1 ** 2, grid))
    # constant-stress profile from the leaf area by height
    spur_alive = (sb < y) & ((sd < 0) | (sd > y)) & alive[sn]
    zl = pos[sn[spur_alive], 2]
    al = 2.5 * sla[spur_alive].astype(float)
    M = np.array([(al * np.maximum(zl - z, 0.0)).sum() for z in grid])
    dM = np.cbrt(M)
    k13 = int(np.argmax(grid >= 1.3))
    dbh = float(s["dbh_cm"])
    tob = bark.taper_matched(dbh, H)
    cells_m, cells_c, cells_t = [], [], []
    for q in (0.3, 0.5, 0.7):
        k = int(np.argmax(zc >= q * H))
        cells_m.append(f"{200 * rc[k] / dbh:.2f}")
        cells_c.append(f"{dM[int(np.argmax(grid >= q * H))] / max(dM[k13], 1e-12):.2f}")
        cells_t.append(f"{float(bark.d_under_bark(q * H, tob, H)) / dbh:.2f}")
    dob = float(bark.dbh_over_bark(dbh))
    print(f"| {y} | {H:.1f} | {dbh:.1f} / {dob:.1f} | {H / (dob / 100):.0f} | {cw:.1f} | {lam[0]:.2f} | {lam[1]:.2f} | {lam[2]:.2f} | "
          f"{' / '.join(cells_m)} | {' / '.join(cells_c)} | {' / '.join(cells_t)} |")
