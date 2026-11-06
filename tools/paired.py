"""Compare an option with the baseline on the same seeds (PROTOCOL.md section 4).

An effect only counts if the mean paired difference is larger than 2 standard errors of
that difference.  Pairing means the same seed in both ensembles; because the model is
chaotic it reduces the noise only partly, and the standard error here is what's actually
left.  With many metrics and ages, some will pass 2 standard errors by chance alone, so a
lone pass among many is a reason to look further, not a result.

    python tools/paired.py out/bench/ensemble/base out/bench/ensemble/option
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

AGES = (10, 20, 30, 50, 60)
METRICS = ("height_m", "dbh_cm", "leaf_area_m2", "lai", "crown_ratio", "subcanopy_diffuse_light_pct")


def load(folder: Path) -> dict:
    """seed -> {year: stats}."""
    out = {}
    for d in Path(folder).glob("*_stand"):
        per_year = json.loads((d / "stats.json").read_text(encoding="utf-8"))["per_year"]
        out[int(d.name.split("_")[0])] = {r["year"]: r for r in per_year}
    return out


def paired_difference(base: list, option: list) -> dict | None:
    """Mean option - base, its standard error, and whether the effect counts.  None if
    there are fewer than 2 pairs."""
    if len(base) != len(option):
        raise ValueError("paired lists differ in length")
    if len(base) < 2:
        return None
    d = [b - a for a, b in zip(base, option)]
    mean = statistics.fmean(d)
    se = statistics.stdev(d) / len(d) ** 0.5
    return {"n": len(d), "base_mean": statistics.fmean(base), "mean": mean, "se": se,
            "ratio": abs(mean) / se if se > 0 else (0.0 if mean == 0 else float("inf")),
            "counts": abs(mean) > 2.0 * se}


def band_distance(x: float, lo: float, hi: float) -> float:
    """How far a value is outside its band; 0 inside it."""
    return max(lo - x, 0.0, x - hi)


def band_move(base: list, option: list, lo: float, hi: float) -> dict | None:
    """The adoption gate's question (PROTOCOL.md section 9): did the ensemble mean move
    towards its band or away from it, by more than 2 standard errors of the paired difference?
    A verdict is the ensemble mean against the band, so that's what's measured, not each seed.
    "closer" and "further" mean the distance changed and the effect counts; moves that stay
    inside the band change no distance and are "no change"."""
    r = paired_difference(base, option)
    if r is None:
        return None
    d_base = band_distance(statistics.fmean(base), lo, hi)
    d_option = band_distance(statistics.fmean(option), lo, hi)
    moved = "no change"
    if r["counts"] and d_option != d_base:
        moved = "closer" if d_option < d_base else "further"
    return {**r, "lo": lo, "hi": hi, "distance_base": d_base, "distance_option": d_option, "moved": moved}


def compare(base: dict, option: dict, ages=AGES, metrics=METRICS) -> list:
    seeds = sorted(set(base) & set(option))
    rows = []
    for age in ages:
        for m in metrics:
            pairs = [(base[s][age][m], option[s][age][m]) for s in seeds
                     if age in base[s] and age in option[s] and base[s][age].get(m) is not None and option[s][age].get(m) is not None]
            r = paired_difference([p[0] for p in pairs], [p[1] for p in pairs])
            if r:
                rows.append({"age": age, "metric": m, **r})
    return rows


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("base")
    ap.add_argument("option")
    a = ap.parse_args()
    base, option = load(Path(a.base)), load(Path(a.option))
    missing = sorted(set(base) ^ set(option))
    print(f"{len(set(base) & set(option))} paired seeds" + (f"; left out, in one only: {missing}" if missing else ""))
    print("\n| Age | Metric | Baseline mean | Option - baseline | Standard error | Difference / SE | Counts (over 2 SE)? |")
    print("|---|---|---|---|---|---|---|")
    for r in compare(base, option):
        print(f"| {r['age']} | {r['metric']} | {r['base_mean']:.3f} | {r['mean']:+.3f} | {r['se']:.3f} | {r['ratio']:.1f} | {'yes' if r['counts'] else 'no'} |")


if __name__ == "__main__":
    main()
