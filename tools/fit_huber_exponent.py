"""Fit pipe_model.huber_radius_exponent: b in HV(r) = HV0 (r / r_tip)^b, the
conducting wood each internode keeps per unit of leaf area beyond, so that
the whole wood cross-section (conducting plus the old wood left by sapwood
turnover) per unit of leaf area matches young and older silver birch, at
breast height.

- Konopka et al. 2023 (Plants 12:1607), natural regeneration up to 15 y:
  LA = 2.37 m2 (D0 / 50 mm)^1.851 (their exponent, scaled to their stated
  2.37 m2 at D0 = 50 mm); DBH = -6.627 + 0.611 D0 (mm).  D0 50-100 mm.
- Repola 2008 (Silva Fennica 42:605), Eq. 12, DBH 11-26 cm:
  ln(foliage kg) = -29.566 + 33.372 dS / (dS + 2), dS = 2 + 1.25 DBH (cm),
  bias-corrected by exp(0.077 / 2); leaf area at SLA 15 m2/kg (Uri et al.
  2007).
- Marklund 1988 (Sweden) has no foliage function for birch, so it cannot be
  used here.

With turnover the old wood depends on each tree's history, so the fit runs
the model: the seed-1 stand tree is grown for each candidate b and its leaf
area is read where its DBH passes each data point.  The data's DBH is over
bark and the model's is wood, so the model's DBH is converted to over bark
first (tools/bark.py, Hansen et al. 2023).  Each dataset carries
equal weight; HV0 = hydraulics.huber_value (1.24e-4) at r_tip =
pipe_model.tip_radius (1 mm) anchors the curve.

    python tools/fit_huber_exponent.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cli  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bark  # noqa: E402


def datasets():
    """(DBH cm, leaf area m2) of each dataset."""
    young, old = [], []
    for d0 in (50, 75, 100):                    # mm; trees of ~3-10 m
        young.append(((-6.627 + 0.611 * d0) / 10.0, 2.37 * (d0 / 50.0) ** 1.851))
    for dbh in (11, 15, 20, 26):                # cm
        ds = 2 + 1.25 * dbh
        old.append((dbh, np.exp(-29.566 + 33.372 * ds / (ds + 2)) * np.exp(0.077 / 2) * 15.0))
    return {"Konopka et al. 2023 (young)": young, "Repola 2008 Eq. 12 (DBH 11-26 cm)": old}


def trajectory(b, seed=1, years=90, dbh_max=27.0):
    """Over-bark DBH (cm) and leaf area (m2) of the stand tree, year by year."""
    sp, _ = cli.load_species("betula_pendula")
    sp.pipe_model.huber_radius_exponent = float(b)
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), seed, stand=True, soil=cli.make_soil(env_p))
    D, LA = [], []
    for _ in range(years):
        m.step()
        s = m.stats[-1]
        D.append(float(bark.dbh_over_bark(s["dbh_cm"] or 0.0)))
        LA.append(s["leaf_area_m2"])
        if D[-1] > dbh_max:
            break
    return np.array(D), np.array(LA)


def leaf_area_at(D, LA, d):
    """The model's leaf area where its DBH first reaches d (log-linear)."""
    k = int(np.argmax(D >= d)) if (D >= d).any() else -1
    if k <= 0:
        return np.nan
    f = (d - D[k - 1]) / max(D[k] - D[k - 1], 1e-9)
    return float(np.exp((1 - f) * np.log(LA[k - 1]) + f * np.log(LA[k])))


def misfit(b, verbose=False):
    D, LA = trajectory(b)
    err = 0.0
    for name, pts in datasets().items():
        e = [np.log(leaf_area_at(D, LA, d) / la) for d, la in pts]
        err += float(np.mean(np.square(e)))
        if verbose:
            print(name)
            for (d, la), x in zip(pts, e):
                r = np.pi * (d / 200.0) ** 2
                print(f"  DBH {d:5.1f} cm  leaf area {la:6.1f} m2 (model {la * np.exp(x):6.1f})"
                      f"  wood/leaf area {r / la:.2e} (model {r / (la * np.exp(x)):.2e})")
    return err


def main():
    grid = np.arange(0.10, 0.551, 0.05)
    errs = []
    for b in grid:
        errs.append(misfit(b))
        print(f"b {b:.2f}: misfit {errs[-1]:.4f}", flush=True)
    k = int(np.nanargmin(errs))
    lo, hi = grid[max(k - 1, 0)], grid[min(k + 1, len(grid) - 1)]
    g = (np.sqrt(5.0) - 1.0) / 2.0
    c, d = hi - g * (hi - lo), lo + g * (hi - lo)
    fc, fd = misfit(c), misfit(d)
    while hi - lo > 0.005:
        if fc < fd:
            hi, d, fd = d, c, fc
            c = hi - g * (hi - lo)
            fc = misfit(c)
        else:
            lo, c, fc = c, d, fd
            d = lo + g * (hi - lo)
            fd = misfit(d)
    b = 0.5 * (lo + hi)
    print(f"b = {b:.3f}")
    misfit(b, verbose=True)


if __name__ == "__main__":
    main()
