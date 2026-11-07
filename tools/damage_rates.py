"""How often each cause of damage fired in saved plots, from plot.json's damage_log, against the rates it's meant to give.

    python tools/damage_rates.py out/bench/ensemble/node_dmg_log
    python tools/damage_rates.py out/bench/ensemble/node_dmg_log --events     # also every event's size and fate, by cause

Intended, with sources (species file, reference/betula_pendula/labels.yaml):
- wind: 2.9-3.4 % of birches snapped or uprooted per 5 years, 31-35 % of them uprooted (Kitenberga 2021, trees of 14 cm and over);
- snow: about 2 % broken or uprooted, about 29 % bent, in one severe event at ages 8-15 (Donis 2024, in KNOWN_ISSUES.md, not reopened).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

BINS = ((0, 15), (16, 30), (31, 40), (41, 50), (51, 60), (61, 1000))


def bin_of(year: int) -> tuple:
    return next(b for b in BINS if b[0] <= year <= b[1])


def read(folder: Path) -> list:
    plots = sorted(p for p in folder.iterdir() if (p / "plot.json").exists())
    out = []
    for p in plots:
        doc = json.loads((p / "plot.json").read_text(encoding="utf-8"))
        if doc.get("damage_log"):
            out.append((p.name, doc))
    return out


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder")
    ap.add_argument("--events", action="store_true")
    a = ap.parse_args(argv)
    plots = read(Path(a.folder))
    if not plots:
        print("no damage_log in these plots")
        return 1
    print(f"**{Path(a.folder).name}: {len(plots)} plots.**\n")
    events = [dict(e, plot=name) for name, doc in plots for e in doc["damage_log"]["events"]]
    years = [dict(y, plot=name) for name, doc in plots for y in doc["damage_log"]["years"]]

    print("Causes, all years:\n")
    print("| Cause | Events | Fatal | Top lost | Median DBH cm | Median H/D | Median leaf share taken, tops |")
    print("|---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for cause in sorted({e["cause"] for e in events}):
        c = [e for e in events if e["cause"] == cause]
        tops = [e["took"]["leaf_share"] for e in c if not e["fatal"] and isinstance(e.get("took"), dict)]
        d = [e["dbh_cm"] for e in c if e.get("dbh_cm")]
        hd = [e["hd_over_bark"] for e in c if e.get("hd_over_bark")]
        print(f"| {cause} | {len(c)} | {sum(e['fatal'] for e in c)} | {len(tops)} | {np.median(d):.1f} | {np.median(hd):.2f} | "
              f"{np.median(tops) if tops else float('nan'):.2f} |")

    print("\nWind, by plot age.  Rate per 5 years = damage per tree of 14 cm and over, per year, x 5 (intended 2.9-3.4 %):\n")
    print("| Age | Storms | Trees at risk, mean | Expected hits | Hits | Uprooted | Fatal | Per storm % | Per 5 years % |")
    print("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for lo, hi in BINS:
        ys = [y for y in years if lo <= y["year"] <= hi]
        storms = [y for y in ys if y["storm"]]
        hits = [e for e in events if lo <= e["year"] <= hi and e["cause"].startswith("wind")]
        if not ys:
            continue
        risk = sum(y["wind_at_risk"] for y in storms)
        # trees at risk in the years without a storm, where the log has them
        all_risk = sum(y.get("stems_over_min", y["wind_at_risk"]) for y in ys) if all("stems_over_min" in y for y in ys) else None
        per_storm = 100.0 * len(hits) / risk if risk else float("nan")
        if all_risk:
            per5 = 100.0 * len(hits) / all_risk * 5.0
        else:
            per5 = per_storm * 5.0 * len(storms) / len(ys)
        print(f"| {lo}-{hi} | {len(storms)} | {risk / max(len(storms), 1):.0f} | {sum(y['wind_expected'] for y in storms):.1f} | {len(hits)} | "
              f"{sum(e['uprooted'] for e in hits)} | {sum(e['fatal'] for e in hits)} | {per_storm:.1f} | {per5:.2f} |")

    print("\nSnow, by plot age.  Severe = load of 45 kg/m2 and over (intended about 2 % failed and 29 % bent at ages 8-15):\n")
    print("| Age | Events | Severe | Trees, mean | Failed % | Failed %, severe | Bent % | Bent %, severe | Fatal % | Tops lost % |")
    print("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for lo, hi in ((8, 15), *BINS[1:]):
        ys = [y for y in years if lo <= y["year"] <= hi and y["snow_load_kg_m2"] > 0.0]
        if not ys:
            continue

        def share(rows, test):
            at = sum(y["snow_at_risk"] for y in rows)
            n = sum(1 for y in rows for e in events if e["plot"] == y["plot"] and e["year"] == y["year"] and test(e))
            return 100.0 * n / at if at else float("nan")

        sev = [y for y in ys if y["snow_load_kg_m2"] >= 45.0]
        failed = lambda e: e["cause"] in ("snow snap", "snow uproot")
        bent = lambda e: e["cause"] == "snow bend"
        fatal = lambda e: e["cause"].startswith("snow") and e["fatal"]
        tops = lambda e: e["cause"] == "snow snap" and not e["fatal"]
        print(f"| {lo}-{hi} | {len(ys)} | {len(sev)} | {np.mean([y['snow_at_risk'] for y in ys]):.0f} | {share(ys, failed):.1f} | {share(sev, failed):.1f} | "
              f"{share(ys, bent):.1f} | {share(sev, bent):.1f} | {share(ys, fatal):.1f} | {share(ys, tops):.1f} |")

    print("\nStorms that took anything, and the gap fraction the year before, the year after and three years after:\n")
    print("| Plot | Year | Trees at risk | Hits | Fatal | Gap before | Gap after | Gap 3 years on |")
    print("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for name, doc in plots:
        gap = {s["year"]: s.get("gap_fraction") for s in doc.get("stats", [])}
        for y in doc["damage_log"]["years"]:
            hits = [e for e in doc["damage_log"]["events"] if e["year"] == y["year"] and e["cause"].startswith("wind")]
            if hits:
                print(f"| {name} | {y['year']} | {y['wind_at_risk']} | {len(hits)} | {sum(e['fatal'] for e in hits)} | "
                      f"{gap.get(y['year'] - 1)} | {gap.get(y['year'] + 1)} | {gap.get(y['year'] + 3)} |")

    worst = sorted(years, key=lambda y: -y["fatal"])[:8]
    print("\nThe worst years:\n")
    print("| Plot | Year | Storm | Snow kg/m2 | Trees | Events | Fatal | Share dead |")
    print("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for y in worst:
        print(f"| {y['plot']} | {y['year']} | {'yes' if y['storm'] else ''} | {y['snow_load_kg_m2']:.0f} | {y['trees']} | {y['events']} | {y['fatal']} | "
              f"{100.0 * y['fatal'] / max(y['trees'], 1):.0f} % |")

    if a.events:
        print("\nEvery event:\n")
        for e in events:
            print(json.dumps({k: v for k, v in e.items() if k != "plate"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
