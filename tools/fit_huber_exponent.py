"""Fit pipe_model.huber_radius_exponent: b in HV(r) = HV0 (r / r_tip)^b, the
whole wood cross-section per unit of leaf area beyond (birch has no distinct
heartwood), to young and older silver birch together, both at breast height.

- Konopka et al. 2023 (Plants 12:1607), natural regeneration up to 15 y:
  LA = 2.37 m2 (D0 / 50 mm)^1.851 (their exponent, scaled to their stated
  2.37 m2 at D0 = 50 mm); DBH = -6.627 + 0.611 D0 (mm).  D0 50-100 mm.
- Repola 2008 (Silva Fennica 42:605), Eq. 12, DBH 11-26 cm:
  ln(foliage kg) = -29.566 + 33.372 dS / (dS + 2), dS = 2 + 1.25 DBH (cm),
  bias-corrected by exp(0.077 / 2); leaf area at SLA 15 m2/kg (Uri et al.
  2007).
- Marklund 1988 (Sweden) has no foliage function for birch, so it cannot be
  used here.

Each dataset carries equal weight; HV0 = hydraulics.huber_value (1.24e-4) at
r_tip = pipe_model.tip_radius (1 mm) anchors the curve.

    python tools/fit_huber_exponent.py
"""
import numpy as np

HV0, R_TIP = 1.24e-4, 0.001


def datasets():
    young, old = [], []
    for d0 in (50, 75, 100):                    # mm; trees of ~3-10 m
        la = 2.37 * (d0 / 50.0) ** 1.851
        r = (-6.627 + 0.611 * d0) / 2000.0       # breast-height radius, m
        young.append((r, np.pi * r * r / la, la))
    for dbh in (11, 15, 20, 26):                # cm
        ds = 2 + 1.25 * dbh
        la = np.exp(-29.566 + 33.372 * ds / (ds + 2)) * np.exp(0.077 / 2) * 15.0
        r = dbh / 200.0
        old.append((r, np.pi * r * r / la, la))
    return {"Konopka et al. 2023 (young)": young, "Repola 2008 (DBH 11-26 cm)": old}


def main():
    pts = datasets()
    num = den = 0.0
    for p in pts.values():
        w = 1.0 / len(p)
        for r, ratio, _ in p:
            x, y = np.log(r / R_TIP), np.log(ratio / HV0)
            num += w * x * y
            den += w * x * x
    b = num / den
    print(f"b = {b:.3f}")
    for name, p in pts.items():
        print(name)
        for r, ratio, la in p:
            print(f"  DBH {r * 200:5.1f} cm  leaf area {la:6.1f} m2  wood/leaf area {ratio:.2e}"
                  f"  fit {HV0 * (r / R_TIP) ** b:.2e}")


if __name__ == "__main__":
    main()
