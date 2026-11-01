"""Is the leaf area per DBH mismatch a leaf problem?  Model foliage against
Repola 2008 birch foliage (Eq. 12 from DBH; A6 from DBH and crown ratio:
ln y = -20.856 + 22.320 dS/(dS+2) + 2.819 cr, bias exp((0.0108+0.044)/2)),
at the model's over-bark DBH, ages 30, 50, 60; and young trees against
Konopka et al. 2023 at the stem-base diameter D0 they measured (leaf area
2.37 m2 (D0/50 mm)^1.851; SLA 147 cm2/g).  Model foliage dry mass from the
logged leaf dry mass.  python -I tools/foliage_check.py <tree dir> [plot dir]"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import bark  # noqa: E402
from treegen.export import Timeline  # noqa: E402


def rep12(d):
    ds = 2 + 1.25 * d
    return np.exp(-29.566 + 33.372 * ds / (ds + 2)) * np.exp(0.077 / 2)


def repA6(d, cr):
    ds = 2 + 1.25 * d
    return np.exp(-20.856 + 22.320 * ds / (ds + 2) + 2.819 * cr) * np.exp((0.0108 + 0.044) / 2)


def tree_rows(f, ages):
    tl = Timeline(f / "timeline.json")
    st = json.loads((f / "stats.json").read_text())["per_year"]
    par = tl["shoot_parent"].astype(np.int64); lat = tl["shoot_is_lateral"].astype(bool)
    birth, death = tl["shoot_birth_year"], tl["shoot_death_year"]
    out = {}
    for y in ages:
        if y >= len(st) or not st[y]["dbh_cm"]:
            continue
        alive = (birth <= y) & ((death < 0) | (death > y))
        pos = tl["shoot_position"] if y >= tl.years else tl.positions_at(y)
        r = tl.radius_at(y)
        top = np.nonzero(alive)[0][np.argmax(pos[alive, 2])]
        stem = np.zeros(len(par), bool); k = top
        path = []
        while k >= 0:
            stem[k] = True; path.append(k); k = par[k]
        path = path[::-1]
        limbs = np.nonzero(alive & lat & stem[np.maximum(par, 0)] & (par >= 0))[0]
        H = st[y]["height_m"]
        cr_field = 1 - float(pos[par[limbs], 2].min()) / H if len(limbs) else np.nan
        zb = pos[path, 2]
        d0 = 200 * float(r[path[int(np.argmax(zb >= 0.05))]])
        out[y] = dict(dob=float(bark.dbh_over_bark(st[y]["dbh_cm"])), H=H, la=st[y]["leaf_area_m2"],
                      fol=st[y]["carbon"]["leaf_dm_g"] / 1000.0, cr=st[y]["crown_ratio"] or np.nan, cr_field=cr_field,
                      d0=float(bark.dbh_over_bark(d0)))
    return out


def report(label, rows_by_age):
    print(f"\n{label}: foliage dry mass (kg), model / Repola at the model's over-bark DBH")
    print("| age | trees | DBH over bark (cm) | model LMA (g/m2) | model foliage | Repola Eq. 12 | ratio | A6, model crown ratio | ratio | A6, crown ratio by lowest live limb | ratio |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for y, rows in rows_by_age.items():
        if not rows:
            continue
        g = lambda k: np.array([r[k] for r in rows])
        dob, fol, la = g("dob"), g("fol"), g("la")
        e12, a6m, a6f = rep12(dob), repA6(dob, g("cr")), repA6(dob, g("cr_field"))
        m = lambda v: f"{np.nanmedian(v):.2f}"
        print(f"| {y} | {len(rows)} | {m(dob)} | {np.median(1000 * fol / la):.0f} | {m(fol)} | {m(e12)} | {m(fol / e12)} | {m(a6m)} | {m(fol / a6m)} | {m(a6f)} | {m(fol / a6f)} |")


tree = Path(sys.argv[1])
report(f"stand tree {tree.parent.name}", {y: [r] for y, r in tree_rows(tree, (30, 50, 60)).items()})
# young: where D0 passes 50 / 75 / 100 mm
yr = tree_rows(tree, range(2, 25))
ys = sorted(yr)
print(f"\nyoung stand tree {tree.parent.name} against Konopka et al. 2023 at D0 (over bark)")
print("| D0 (mm) | model age | model leaf area (m2) | Konopka leaf area | ratio | model foliage (kg) | Konopka foliage (kg, SLA 147 cm2/g) | ratio |")
print("|---|---|---|---|---|---|---|---|")
D0 = np.array([10 * yr[y]["d0"] for y in ys]); LA = np.array([yr[y]["la"] for y in ys]); FO = np.array([yr[y]["fol"] for y in ys])
for d in (50, 75, 100):
    k = int(np.argmax(D0 >= d))
    if D0[k] < d:
        continue
    f = (d - D0[k - 1]) / max(D0[k] - D0[k - 1], 1e-9)
    la = (1 - f) * LA[k - 1] + f * LA[k]
    fo = (1 - f) * FO[k - 1] + f * FO[k]
    lk = 2.37 * (d / 50.0) ** 1.851
    print(f"| {d} | {ys[k - 1] + f:.1f} | {la:.1f} | {lk:.1f} | {la / lk:.2f} | {fo:.2f} | {lk / 14.7:.2f} | {fo / (lk / 14.7):.2f} |")
if len(sys.argv) > 2:
    pd = Path(sys.argv[2])
    pj = json.loads((pd / "plot.json").read_text())
    by_age = {y: [] for y in (30, 50, 60)}
    for t in pj["trees"]:
        if t["removed"] is not None:
            continue
        rows = tree_rows(pd / f"tree_{t['id']:03d}", tuple(y - t["germination"] for y in (30, 50, 60)))
        for y in (30, 50, 60):
            a = y - t["germination"]
            if a in rows:
                by_age[y].append(rows[a])
    report(f"natural plot {pd.name} (plot years)", by_age)
