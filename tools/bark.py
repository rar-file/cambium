"""Birch bark thickness and stem taper, for comparisons only (the model has
no bark: its radii are wood, so its DBH is under bark, while field DBH is
over bark).

Hansen, Rahlf, Astrup & Gobakken 2023, Scand. J. For. Res. 38:413-428,
doi:10.1080/02827581.2023.2243821, with the correction
doi:10.1080/02827581.2024.2358467; coefficients for birch (Betula pendula and
B. pubescens, Norwegian NFI trees) as coded in the taperNOR R package 0.2.1:

  double bark thickness (mm) = -0.48552367 + 0.04957885 DBH + 0.84676248 d
      (d, DBH over bark, cm)
  taper, over bark (Kozak 1988 variable-exponent form):
      d = b1 DBH^b2 b3^DBH ((1 - sqrt(z)) / (1 - sqrt(0.2)))^(b4 z^2 + b5 ln(z + 0.001)
          + b6 sqrt(z) + b7 e^z + b8 DBH / H),   z = h / H
"""
import numpy as np
from scipy.optimize import brentq

BARK = (-0.48552367, 0.04957885, 0.84676248)
TAPER = (0.9810885, 0.9936293, 0.9941538, 0.8526987, -0.1819791, 0.4687623, -0.2198294, 0.1591102)


def bark_mm(d_ob, dbh_ob):
    """Double bark thickness (mm) at a point of over-bark diameter d_ob (cm)."""
    b0, b1, b2 = BARK
    return b0 + b1 * np.asarray(dbh_ob, float) + b2 * np.asarray(d_ob, float)


def dbh_over_bark(dbh_ub):
    """Over-bark DBH (cm) of a stem whose wood (under-bark) DBH is dbh_ub.
    At breast height d = DBH, so DBH_ub = DBH_ob - (b0 + (b1 + b2) DBH_ob) / 10."""
    b0, b1, b2 = BARK
    d = np.asarray(dbh_ub, float)
    return np.where(d > 0, (d + b0 / 10.0) / (1.0 - (b1 + b2) / 10.0), 0.0)


def d_over_bark(h, dbh_ob, H):
    """Over-bark diameter (cm) at height h (m) of a birch of DBH dbh_ob (cm,
    over bark) and height H (m)."""
    b1, b2, b3, b4, b5, b6, b7, b8 = TAPER
    z = np.clip(np.asarray(h, float) / H, 0.0, 1.0)
    return b1 * dbh_ob ** b2 * b3 ** dbh_ob * ((1 - np.sqrt(z)) / (1 - np.sqrt(0.2))) ** (
        b4 * z ** 2 + b5 * np.log(z + 0.001) + b6 * np.sqrt(z) + b7 * np.exp(z) + b8 * (dbh_ob / H))


def d_under_bark(h, dbh_ob, H):
    """Under-bark (wood) diameter (cm) along the stem."""
    d = d_over_bark(h, dbh_ob, H)
    return np.maximum(d - bark_mm(d, dbh_ob) / 10.0, 0.0)


def taper_matched(dbh_ub, H):
    """Over-bark DBH of the taper curve whose wood diameter at 1.3 m equals
    dbh_ub (the model's DBH)."""
    return brentq(lambda x: float(d_under_bark(1.3, x, H)) - dbh_ub, dbh_ub * 0.8, dbh_ub * 3.0)
