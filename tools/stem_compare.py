"""Stems of an exported tree or plot against published silver birch, with
the model's wood diameters converted to over bark for every comparison with
field DBH (tools/bark.py; the model itself has no bark).

  - H/D on wood DBH and on over-bark DBH
  - taper: d/DBH along the stem against Hansen et al. 2023 (under bark,
    matched to the model's wood DBH at 1.3 m), form factor, where the extra
    stem wood sits, and the over-bark DBH the model's stem wood would give
    with that taper
  - stem wood and living branches against Repola 2008 (Silva Fennica
    42:605), multivariate model 1, at the over-bark DBH:
      stem wood (Eq. 7): ln y = -4.879 + 9.651 dS/(dS+12) + 1.012 ln h
      living branches (Eq. 9): ln y = -4.152 + 15.874 dS/(dS+16) - 4.407 h/(h+10)
      dS = 2 + 1.25 d; bias corrections exp((0.00263+0.00544)/2) and
      exp((0.02733+0.07662)/2); y kg dry mass; stem wood without bark,
      branches with bark.  Model wood at 530 kg m-3 (basic density), no bark.

The stem is the path from the base to the highest living node.  Plots: the
median (10th-90th percentile) over living trees.

    python tools/stem_compare.py out/bench/p27_stand/1_stand 30,50,60
    python tools/stem_compare.py out/bench/p26_nat 30,50,60 --plot
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import bark  # noqa: E402
from treegen.export import Timeline  # noqa: E402

RHO = 530.0
SEG = [(0.0, 0.1), (0.1, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 1.0)]
REL = (0.1, 0.3, 0.5, 0.7, 0.9)


def repola(d_ob, h):
    ds = 2 + 1.25 * d_ob
    stem = np.exp(-4.879 + 9.651 * ds / (ds + 12) + 1.012 * np.log(h)) * np.exp((0.00263 + 0.00544) / 2)
    br = np.exp(-4.152 + 15.874 * ds / (ds + 16) - 4.407 * h / (h + 10)) * np.exp((0.02733 + 0.07662) / 2)
    return stem, br


def taper_wood_volume(dbh_ob, H, n=801):
    hs = np.linspace(0.0, H, n)
    return float(np.trapezoid(np.pi / 4 * (bark.d_under_bark(hs, dbh_ob, H) / 100) ** 2, hs))


def measure(tl, y, row):
    if not row["dbh_cm"]:
        return None
    par = tl["shoot_parent"].astype(np.int64)
    b, dd = tl["shoot_birth_year"], tl["shoot_death_year"]
    alive = (b <= y) & ((dd < 0) | (dd > y))
    pos = tl["shoot_position"] if y >= tl.years else tl.positions_at(y)
    r = tl.radius_at(y)
    top = np.nonzero(alive)[0][np.argmax(pos[alive, 2])]
    chain = [top]
    while par[chain[-1]] >= 0:
        chain.append(par[chain[-1]])
    chain = np.array(chain[::-1])
    stem = np.zeros(len(par), bool)
    stem[chain] = True
    L = np.linalg.norm(tl["shoot_position"] - tl["shoot_position"][np.maximum(par, 0)], axis=1)
    L[0] = 0.0
    H, dbh = float(row["height_m"]), float(row["dbh_cm"])
    dob = float(bark.dbh_over_bark(dbh))
    z = pos[chain, 2]
    zm = 0.5 * (z[1:] + z[:-1])
    vol = np.pi * r[chain[1:]] ** 2 * np.linalg.norm(np.diff(pos[chain], axis=0), axis=1)
    tob = bark.taper_matched(dbh, H)
    hs = np.linspace(0, H, 2001)
    vt = np.pi / 4 * (bark.d_under_bark(hs, tob, H) / 100) ** 2
    seg_m = np.array([vol[(zm >= a * H) & (zm < c * H)].sum() for a, c in SEG])
    seg_t = np.array([np.trapezoid(vt[(hs >= a * H) & (hs <= c * H)], hs[(hs >= a * H) & (hs <= c * H)]) for a, c in SEG])
    prof = []
    for q in REL:
        k = int(np.argmax(z >= q * H)) if (z >= q * H).any() else len(z) - 1
        prof.append((200 * r[chain[k]] / dbh, float(bark.d_under_bark(q * H, tob, H)) / dbh))
    V = float(vol.sum())
    # the over-bark DBH whose taper-curve wood volume equals the model's
    try:
        d_eq = brentq(lambda x: taper_wood_volume(x, H) - V, 1.0, 90.0)
    except ValueError:
        d_eq = np.nan
    ba = np.pi / 4 * (dbh / 100) ** 2
    st_r, br_r = repola(dob, H)
    vb = np.pi * r ** 2 * L
    return dict(H=H, dbh=dbh, dob=dob, hd=H / (dbh / 100), hd_ob=H / (dob / 100), prof=prof,
                ff=(V / (ba * H), sum(seg_t) / (ba * H)), seg=(seg_m, seg_t), d_eq=d_eq, hd_eq=H / (d_eq / 100),
                stem=(V * RHO, st_r), branch=(float(vb[alive & ~stem].sum() * RHO), br_r))


def summary(v, spread):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if not len(v):
        return "-"
    if spread and len(v) > 1:
        return f"{np.median(v):.2f} ({np.percentile(v, 10):.2f}-{np.percentile(v, 90):.2f})"
    return f"{np.median(v):.2f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src")
    ap.add_argument("years")
    ap.add_argument("--plot", action="store_true", help="src is a plot directory; years are plot years")
    a = ap.parse_args()
    src = Path(a.src)
    out = {}
    for Y in (int(v) for v in a.years.split(",")):
        items = []
        if a.plot:
            pj = json.loads((src / "plot.json").read_text())
            items = [(src / f"tree_{t['id']:03d}", Y - t["germination"]) for t in pj["trees"]
                     if (t["removed"] is None or t["removed"] > Y) and Y > t["germination"]]
        else:
            items = [(src, Y)]
        rows = []
        for f, y in items:
            st = json.loads((f / "stats.json").read_text())["per_year"]
            if y < len(st):
                m = measure(Timeline(f / "timeline.json"), y, st[y])
                if m:
                    rows.append(m)
        out[Y] = rows
    med = lambda rows, f: float(np.median([f(r) for r in rows]))
    sp = a.plot
    print("H/D")
    print("| age | trees | H (m) | DBH wood (cm) | DBH over bark (cm) | H/D on wood DBH | H/D over bark | over-bark DBH with birch taper (cm) | H/D with birch taper, over bark |")
    print("|---|---|---|---|---|---|---|---|---|")
    for Y, rows in out.items():
        d_eq_ob = [r["d_eq"] for r in rows]          # solved over bark already
        hd_eq_ob = [r["hd_eq"] for r in rows]
        print(f"| {Y} | {len(rows)} | {med(rows, lambda r: r['H']):.1f} | {med(rows, lambda r: r['dbh']):.1f} | {med(rows, lambda r: r['dob']):.1f} | "
              f"{summary([r['hd'] for r in rows], sp)} | {summary([r['hd_ob'] for r in rows], sp)} | {summary(d_eq_ob, sp)} | {summary(hd_eq_ob, sp)} |")
    print("\nTaper (wood, under bark): d/DBH at relative height, model / Hansen et al. 2023")
    print("| age | " + " | ".join(f"{q} H" for q in REL) + " | form factor | model / curve volume | excess above 0.3 H |")
    print("|---|" + "---|" * (len(REL) + 3))
    for Y, rows in out.items():
        cells = [f"{med(rows, lambda r: r['prof'][i][0]):.2f} / {med(rows, lambda r: r['prof'][i][1]):.2f}" for i in range(len(REL))]
        ex = med(rows, lambda r: (r["seg"][0][2:] - r["seg"][1][2:]).sum() / max((r["seg"][0] - r["seg"][1]).sum(), 1e-12))
        print(f"| {Y} | " + " | ".join(cells) + f" | {med(rows, lambda r: r['ff'][0]):.2f} / {med(rows, lambda r: r['ff'][1]):.2f} | "
              f"{med(rows, lambda r: r['seg'][0].sum() / r['seg'][1].sum()):.2f} | {ex:.0%} |")
    print("\nWood against Repola 2008 at the over-bark DBH (model / Repola)")
    print("| age | stem wood (kg) | ratio | living branches (kg) | ratio | branch : stem, model / Repola |")
    print("|---|---|---|---|---|---|")
    for Y, rows in out.items():
        print(f"| {Y} | {med(rows, lambda r: r['stem'][0]):.0f} / {med(rows, lambda r: r['stem'][1]):.0f} | {summary([r['stem'][0] / r['stem'][1] for r in rows], sp)} | "
              f"{med(rows, lambda r: r['branch'][0]):.1f} / {med(rows, lambda r: r['branch'][1]):.1f} | {summary([r['branch'][0] / r['branch'][1] for r in rows], sp)} | "
              f"{med(rows, lambda r: r['branch'][0] / r['stem'][0]):.3f} / {med(rows, lambda r: r['branch'][1] / r['stem'][1]):.3f} |")


if __name__ == "__main__":
    main()
