"""Which thick axes are red-brown, and why: thickness or age.  Prints each axis that reaches 3 cm over bark, the stem
first as the mesher draws it (a replacement leader is the stem), with its thickness, part age and white share.

    python tools/limb_probe.py --seed 5 --ages 50,60 --sets cases/crown2.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def main(argv=None) -> int:
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap_.add_argument("--seed", type=int, default=5)
    ap_.add_argument("--ages", default="50,60")
    ap_.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap_.add_argument("--sets")
    a = ap_.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    ages = [int(x) for x in a.ages.split(",")]
    import copy

    import game_export as ge
    from treegen import appearance as ap
    from treegen import game_unreal as gu
    from treegen import mesh as meshlib

    model, _, raw, _ = ge.grow_with_leaves("betula_pendula", a.seed, ages, "sweden_open_field", True, a.set)
    look = gu.unreal_look(ap.load_look(raw))
    old = copy.deepcopy(look)
    old["bark"]["uneven_top"]["stage_ramps"]["papery"]["part_age_years"] = [4.0, 10.0]
    names = [s["name"] for s in look["bark"]["stages"]]
    k = names.index("papery")
    T = model.tree
    for age in ages:
        pos, r_wood = ge.shoot_arrays(model, age)
        st = model.stats[age]
        H, dbh = float(st["height_m"]), ap.over_bark_dbh_cm(look, st["dbh_cm"])
        alive = (T.birth[: T.n] <= age) & ((T.death[: T.n] < 0) | (T.death[: T.n] > age))
        view = meshlib.continue_trunk(SimpleNamespace(n=T.n, pos=pos, parent=T.parent, axis=T.axis, is_lateral=T.is_lateral, order=T.order, birth=T.birth, death=T.death, depth=T.depth),
                                      alive, r_wood, ap.stem_stub_share(look))
        axis = np.asarray(view.axis[: T.n])
        idx = np.nonzero(alive)[0]
        part_age = age - np.asarray(T.birth[: T.n], float)
        now = ap.part_state(look, part_age[idx], 2.0 * r_wood[idx], pos[idx, 2], H, dbh)
        was = ap.part_state(old, part_age[idx], 2.0 * r_wood[idx], pos[idx, 2], H, dbh)
        d = np.zeros(T.n)
        d[idx] = now["diameter_m"]
        w_now, w_was = np.zeros(T.n), np.zeros(T.n)
        w_now[idx], w_was[idx] = now["weights"][k], was["weights"][k]
        print(f"age {age}: height {H:.1f} m")
        print("axis   nodes  z m       d over bark cm  part age yr   white was   white now   (mean over the axis's parts thicker than 3 cm)")
        rows = []
        for ax in np.unique(axis[idx]):
            n = idx[axis[idx] == ax]
            thick = n[d[n] >= 0.03]
            if ax != 0 and not len(thick):
                continue
            if ax == 0:
                thick = n[(d[n] >= 0.03) & (pos[n, 2] > 0.5 * H)]
            rows.append((ax, len(thick), pos[thick, 2].min(), pos[thick, 2].max(), d[thick].min(), d[thick].max(), part_age[thick].min(), part_age[thick].max(), w_was[thick].mean(), w_now[thick].mean()))
        rows.sort(key=lambda r: (r[0] != 0, -r[5]))
        for r in rows[:30]:
            print(f"{'stem' if r[0] == 0 else int(r[0]):>5} {r[1]:6d}  {r[2]:5.1f}-{r[3]:5.1f}  {100 * r[4]:5.1f}-{100 * r[5]:5.1f}     {r[6]:4.0f}-{r[7]:4.0f}     {r[8]:6.2f}      {r[9]:6.2f}", flush=True)
        # the stem's top, as the mesher draws it: thickness, age and white by height
        n = idx[axis[idx] == 0]
        n = n[np.argsort(pos[n, 2])]
        top = n[pos[n, 2] > 0.55 * H]
        print("stem top: z m, d cm, part age, white was, white now")
        for i in top[:: max(len(top) // 12, 1)]:
            print(f"  {pos[i, 2]:5.1f}  {100 * d[i]:5.1f}  {part_age[i]:4.0f}  {w_was[i]:.2f}  {w_now[i]:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
