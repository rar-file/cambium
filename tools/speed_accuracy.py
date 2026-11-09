"""Does a speed setting move the results by more than the noise?  Tree ensembles at ages 50 and 60, and plots.

    python tools/speed_accuracy.py trees node_speed_t_A_base node_speed_t_A_base2 -- node_speed_t_A_rows node_speed_t_A_k26
    python tools/speed_accuracy.py trees node_speed_t_A_base+node_speed_t_A_base2 -- node_speed_t_A_rows+node_speed_t_A_rows2     # draws pooled
    python tools/speed_accuracy.py plots node_speed_p_A_base node_speed_p_A_base2 -- node_speed_p_A_rows

The first label is the baseline; any more before -- are the same settings on fresh seeds, which show what a second draw does by
chance.  Each test set is compared with the first baseline, unpaired: a seed makes a different tree after any change, so its
trees are new draws (the seeds' random numbers are shared, so an unpaired test is if anything too cautious).
z = difference / its standard error.  Over many rows, some |z| above 2 is expected by chance: about 1 in 20.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

E = ROOT / "out" / "bench" / "ensemble"
AGES = (50, 60)
TREE_METRICS = (("Height (m)", lambda r, a: r["per_year"][a]["height_m"], ".2f"),
                ("LAI", lambda r, a: r["per_year"][a]["lai"], ".3f"),
                ("Light (%)", lambda r, a: r["per_year"][a]["subcanopy_diffuse_light_pct"], ".2f"),
                ("Stem wood (kg)", lambda r, a: r["snap"][a]["stem_kg"], ".1f"),
                ("Branch wood (kg)", lambda r, a: r["snap"][a]["branch_kg"], ".1f"),
                ("Crown width (m)", lambda r, a: r["per_year"][a]["crown_width_m"], ".2f"),
                ("Crown ratio", lambda r, a: r["per_year"][a]["crown_ratio"], ".3f"),
                ("Limb angle, low (deg)", lambda r, a: r["snap"][a]["shape"].get("angle_low"), ".1f"),
                ("Limb angle, mid (deg)", lambda r, a: r["snap"][a]["shape"].get("angle_mid"), ".1f"),
                ("Limb angle, upper (deg)", lambda r, a: r["snap"][a]["shape"].get("angle_up"), ".1f"),
                ("Widest at (0 base, 1 top)", lambda r, a: r["snap"][a]["shape"].get("widest_at"), ".3f"),
                ("Crown side fill", lambda r, a: r["snap"][a]["shape"].get("fill"), ".3f"),
                ("Hanging share of leaves", lambda r, a: r["snap"][a]["shape"].get("hang_leaves"), ".3f"),
                ("Branches, count", lambda r, a: r["snap"][a]["branches"], ".1f"),
                ("Mean branch (m)", lambda r, a: r["snap"][a]["mean_branch_m"], ".2f"))
PLOT_METRICS = (("Stems/ha", "stems_ha", ".0f"), ("Mean height (m)", "mean_height_m", ".2f"),
                ("Mean height of the 100 thickest/ha (m; a cross-check, not the approved top height)", "top_height_m", ".2f"),
                ("Basal area (m2/ha)", "basal_area", ".1f"), ("LAI", "lai", ".2f"), ("Light (%)", "light", ".1f"))


def mean_se(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return (xs[0] if xs else float("nan")), float("nan"), len(xs)
    return statistics.fmean(xs), statistics.stdev(xs) / math.sqrt(len(xs)), len(xs)


def compare_row(name, age, base_vals, draws, tests, f):
    m0, s0, n0 = mean_se(base_vals)
    cells = [f"{m0:{f}} +- {s0:{f}} ({n0})"]
    worst = 0.0
    for vals in draws:
        m, s, _ = mean_se(vals)
        z = (m - m0) / math.hypot(s, s0) if math.hypot(s, s0) > 0 else 0.0
        cells.append(f"{m - m0:+{f}} (z {z:+.1f})")
    for vals in tests:
        m, s, n = mean_se(vals)
        z = (m - m0) / math.hypot(s, s0) if math.hypot(s, s0) > 0 else 0.0
        worst = max(worst, abs(z))
        pct = 100.0 * (m - m0) / abs(m0) if m0 else 0.0
        mark = " **" if abs(z) >= 2 else ""
        cells.append(f"{m - m0:+{f}}, {pct:+.1f} % (z {z:+.1f}){mark}")
    print(f"| {name} | {age} | " + " | ".join(cells) + " |")
    return worst


def trees(base, tests):
    from tree_table import load

    def loaded(label):
        # a+b is one set: draws on other seeds, pooled
        out = {}
        for part in label.split("+"):
            out.update(load(part))
        return out

    runs = {label: loaded(label) for label in base + tests}
    head = [f"`{base[0]}`, mean +- SE (seeds)"] + [f"`{x}` minus baseline" for x in base[1:]] + [f"`{x}` minus baseline" for x in tests]
    print("| Metric | Age | " + " | ".join(head) + " |")
    print("|---|---|" + "---|" * len(head))
    over = {t: 0 for t in tests}
    for name, fn, f in TREE_METRICS:
        for age in AGES:
            def vals(label):
                out = []
                for r in runs[label].values():
                    try:
                        if fn(r, age) is not None:
                            out.append(float(fn(r, age)))
                    except (KeyError, TypeError):
                        pass
                return out
            compare_row(name, age, vals(base[0]), [vals(x) for x in base[1:]], [vals(t) for t in tests], f)
            for t in tests:
                m0, s0, _ = mean_se(vals(base[0]))
                m, s, _ = mean_se(vals(t))
                if math.hypot(s, s0) > 0 and abs(m - m0) / math.hypot(s, s0) >= 2:
                    over[t] += 1
    n = len(TREE_METRICS) * len(AGES)
    print(f"\nRows with |z| of 2 or more, of {n} (about {n / 20:.0f} by chance): " + ", ".join(f"`{t}` {v}" for t, v in over.items()))
    for t in tests:
        secs = []
        p = E / t / "runs.csv"
        if p.exists():
            import csv
            for row in csv.DictReader(p.read_text(encoding="utf-8").splitlines()):
                for key in ("seconds", "duration_s", "runtime_s"):
                    if row.get(key):
                        secs.append(float(row[key]))
                        break
        if secs:
            print(f"`{t}`: {statistics.fmean(secs):.0f} s a run, {len(secs)} runs on the node")


def plot_values(label):
    """One row per plot, by age: what tools/stand_table.py reads, with the plot's own LAI, light and height."""
    from stand_table import plot_folders, read_plot

    out = []
    for folder in plot_folders(E / label):
        p = read_plot(folder, AGES)
        by_year = {s["year"]: s for s in p["doc"]["stats"]}
        rows = {}
        for age in AGES:
            s = by_year.get(age, {})
            rows[age] = {**p["rows"].get(age, {}), **{k: s.get(k) for k in ("lai", "subcanopy_diffuse_light_pct", "height_mean_m", "height_max_m", "dbh_mean_cm", "trees")},
                         "runtime_s": p["runtime_s"], "peak_mb": p["peak_mb"]}
        out.append(rows)
    return out


def plots(base, tests):
    all_rows = {label: plot_values(label) for label in base + tests}
    head = [f"`{base[0]}`, mean +- SE (plots)"] + [f"`{x}` minus baseline" for x in base[1:]] + [f"`{x}` minus baseline" for x in tests]
    print("| Measure | Age | " + " | ".join(head) + " |")
    print("|---|---|" + "---|" * len(head))

    def get(label, age, key):
        return [float(p[age][key]) for p in all_rows[label] if p.get(age, {}).get(key) is not None]

    for name, key, f in (("Stems/ha", "stems_per_ha", ".0f"), ("Basal area over bark (m2/ha)", "basal_area_ob_m2_ha", ".1f"), ("Mean height (m)", "height_mean_m", ".2f"),
                         ("Mean height of the 100 thickest/ha (m; a cross-check, not the approved top height)", "top_height_m", ".2f"),
                         ("Tallest (m)", "height_max_m", ".2f"), ("Mean stem, wood (cm)", "dbh_mean_cm", ".2f"),
                         ("LAI", "lai", ".2f"), ("Light (%)", "subcanopy_diffuse_light_pct", ".1f")):
        for age in AGES:
            b = get(base[0], age, key)
            if len(b) >= 2:
                compare_row(name, age, b, [get(x, age, key) for x in base[1:]], [get(t, age, key) for t in tests], f)
    for label in base + tests:
        print(f"`{label}`: mean {statistics.fmean(get(label, 60, 'runtime_s')):.0f} s a plot, peak {statistics.fmean(get(label, 60, 'peak_mb')):.0f} MB")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    what = sys.argv[1]
    rest = sys.argv[2:]
    cut = rest.index("--")
    base, tests = rest[:cut], rest[cut + 1:]
    (trees if what == "trees" else plots)(base, tests)


if __name__ == "__main__":
    main()
