"""Published growth figures used to sanity-check a simulated tree.

* Height: Swedish birch site-index model of Eriksson, Johansson & Kiviste
  (1997), Scand. J. For. Res. 12:149-156 (Hossfeld IV difference form; ages
  are breast-height ages; coefficients as implemented in the R package
  'forester', function Eriksson_1997_height_trajectory_Sweden_Birch).
* Crown diameter of open-grown silver birch from DBH: Hemery, Savill & Pryor
  (2005), For. Ecol. Manage. 215:285-294 (linear fit to the published table).

All numbers live in the ``reference`` block of the species YAML.
"""
from __future__ import annotations


def eriksson_1997_height(h50: float, age_bh: float, asi: float, beta: float, b2: float, ref_age: float = 50.0) -> float:
    d = beta / asi ** b2
    r = ((h50 - 1.3 - d) ** 2 + 4.0 * beta * (h50 - 1.3) / ref_age ** b2) ** 0.5
    return (h50 - 1.3 + d + r) / (2.0 + 4.0 * beta * age_bh ** (-b2) / (h50 - 1.3 - d + r)) + 1.3


def reference_block(species, stats: list) -> dict:
    ref = species.reference
    hr = ref.height
    cr = ref.crown
    rows = []
    for s in stats:
        t = s["year"]
        age_bh = t - hr.years_to_breast_height
        lo = hi = None
        if age_bh >= 1:
            lo = eriksson_1997_height(hr.site_index_low, age_bh, hr.asi, hr.beta, hr.b2)
            hi = eriksson_1997_height(hr.site_index_high, age_bh, hr.asi, hr.beta, hr.b2)
        crown_ref = None
        if s["dbh_cm"] is not None:
            crown_ref = cr.intercept_m + cr.slope_m_per_m * s["dbh_cm"] / 100.0
        rows.append({
            "year": t,
            "height_low_m": None if lo is None else round(lo, 2),
            "height_high_m": None if hi is None else round(hi, 2),
            "height_extrapolated": bool(age_bh < 10),
            "crown_diameter_from_dbh_m": None if crown_ref is None else round(crown_ref, 2),
        })
    final = stats[-1]
    fr = rows[-1]
    checks = {
        "final_year": final["year"],
        "height_m": final["height_m"],
        "height_band_m": [fr["height_low_m"], fr["height_high_m"]],
        "height_in_band": None if fr["height_low_m"] is None else bool(fr["height_low_m"] <= final["height_m"] <= fr["height_high_m"]),
        "dbh_cm": final["dbh_cm"],
        "dbh_open_grown_band_cm": list(ref.dbh.open_grown_band_cm),
        "dbh_band_age": ref.dbh.band_age,
        "crown_width_m": final["crown_width_m"],
        "crown_diameter_from_dbh_m": fr["crown_diameter_from_dbh_m"],
        "crown_to_reference_ratio": None if not fr["crown_diameter_from_dbh_m"] else round(final["crown_width_m"] / fr["crown_diameter_from_dbh_m"], 3),
    }
    return {
        "sources": {
            "height": "Eriksson, Johansson & Kiviste 1997, Scand. J. For. Res. 12:149-156 (Swedish birch site index)",
            "crown": "Hemery, Savill & Pryor 2005, For. Ecol. Manage. 215:285-294 (open-grown Betula pendula)",
            "dbh": "Hynynen et al. 2010 Forestry 83:103-119; crown-released target trees, Forests 12(5):599 (2021)",
        },
        "site_index_h50_bh_m": [hr.site_index_low, hr.site_index_high],
        "years_to_breast_height": hr.years_to_breast_height,
        "per_year": rows,
        "final_checks": checks,
    }
