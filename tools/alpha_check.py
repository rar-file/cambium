"""The carbon the model fixes per m2 of leaf, against the figure alpha = 4.8 was
derived from in commit c3fd2dc (phase 22).

That derivation, from Aosaar et al. 2016 Table 4 (p. 8), 10-year-old stand: tree
NPP 13.02 Mg/ha/yr, leaves 2.81 Mg/ha; with SLA 15 m2/kg (Uri et al. 2007, as the
species file cites it), 0.48 g C/g and CUE 0.45, GPP per m2 of leaf is
13.02e6 * 0.48 / 0.45 / 1e4 / (2.81e3 * 15 / 1e4) = 330 g C/m2/yr, or 1080 model
units at 0.305 g C per unit.  Reads saved outputs only.

    python tools/alpha_check.py out/bench/p40_default_v3/1_stand
"""
import json
import sys
from pathlib import Path

G_C_PER_UNIT = 0.305  # species file, resource.leaf_costs comment


def derivation():
    npp_g_m2 = 13.02e6 * 0.48 / 1e4
    gpp_g_m2 = npp_g_m2 / 0.45
    lai = 2.81e3 * 15.0 / 1e4
    return npp_g_m2, gpp_g_m2, lai, gpp_g_m2 / lai, gpp_g_m2 / lai / G_C_PER_UNIT


def main():
    n, g, l, gl, u = derivation()
    print(f"Derivation: NPP {n:.0f} g C/m2/yr, GPP {g:.0f}, LAI {l:.2f}, {gl:.0f} g C per m2 of leaf, {u:.0f} model units")
    run = Path(sys.argv[1])
    st = json.loads((run / "stats.json").read_text())["per_year"]
    print("| age | leaf area (m2) | LAI | carbon fixed (units) | units per m2 of leaf | g C per m2 of leaf | ratio to the derivation |")
    print("|---|---|---|---|---|---|---|")
    for age in (10, 16, 20, 30, 40, 50, 60):
        r = next((x for x in st if x["year"] == age), None)
        if r is None:
            continue
        fixed = r["carbon"].get("fixed")
        la = r["leaf_area_m2"]
        per = fixed / la if fixed and la else None
        print(f"| {age} | {la:.1f} | {r['lai']:.2f} | {fixed:.0f} | {per:.0f} | {per * G_C_PER_UNIT:.0f} | {per / u:.2f} |")


if __name__ == "__main__":
    main()
