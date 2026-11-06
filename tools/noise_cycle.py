"""INFO for M3: does the chaos come from the every-other-year shoot pattern?

The maintainer's lead (2026-11-06): the tiny-change moves flip sign with age (leaf area +28 % at
30, -13 % at 50, +11 % at 60), which looks like the same up-and-down cycle shifted in time
rather than different trees.  Reruns the noise test's cases keeping every year, then asks:
does divergence start at the first strong alternating year, do the runs show the same
alternation out of step, and is the divergence mostly the fast cycle or a slow drift?

    python tools/noise_cycle.py --out out/bench/noise_cycle          # runs, then analyses
    python tools/noise_cycle.py --out out/bench/noise_cycle --analyse

The alternation rule and the split into fast and slow parts are this tool's own, for a
diagnosis.  Its results aren't targets.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import Job, run_batch  # noqa: E402

PARAMETERS = ("resource.alpha", "resource.gravimorphism", "light.extinction_coefficient", "resource.apical_dominance")
STEPS = 7


def child(path: str | None, factor: float, years: int, result: Path) -> None:
    import cli
    from sensitivity_screen import apply_change
    from treegen.growth import GrowthModel
    from treegen.runhash import scored_digest

    sp, _ = cli.load_species("betula_pendula")
    if path:
        apply_change(sp, path, factor)
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), 1, stand=True, soil=cli.make_soil(env_p), lean=True)
    for _ in range(years):
        m.step()
    T = m.tree
    birth = T.birth[:T.n]
    lengths = T.length[:T.n]
    # shoot length made each year: all internodes born that year, shed or not
    new_length = np.bincount(birth, weights=lengths, minlength=years + 1)[:years + 1]
    out = {"digest": scored_digest(m),
           "year": [s["year"] for s in m.stats],
           "height_m": [s["height_m"] for s in m.stats],
           "leaf_area_m2": [s["leaf_area_m2"] for s in m.stats],
           "dbh_cm": [s["dbh_cm"] or 0.0 for s in m.stats],
           "fixed": [s["carbon"].get("fixed", 0.0) if s.get("carbon") else 0.0 for s in m.stats],
           "new_length_m": [float(x) for x in new_length]}
    result.write_text(json.dumps(out))


def first_alternating_year(x: np.ndarray, first: int = 5, run: int = 4, strength: float = 0.5) -> int | None:
    """First year starting `run` straight up-down swings, each at least `strength` times the
    local mean: a plain rule for where the see-saw becomes strong."""
    for y in range(first, len(x) - run):
        d = np.diff(x[y:y + run + 1])
        local = np.mean(x[y:y + run + 1])
        if local > 0 and np.all(d[:-1] * d[1:] < 0) and np.all(np.abs(d) >= strength * local):
            return y
    return None


def first_year_above(a: np.ndarray, b: np.ndarray, pct: float, first: int = 1) -> int | None:
    """First year from which a and b differ by more than pct percent."""
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.abs(a / b - 1.0) * 100.0
    for y in range(first, len(a)):
        if np.isfinite(d[y]) and d[y] > pct:
            return y
    return None


def smooth(x: np.ndarray) -> np.ndarray:
    """Centred 4-year mean (weights 1/8, 1/4, 1/4, 1/4, 1/8), which cancels a 2-year swing
    exactly, where a plain 5-year mean would leave a fifth of it.  Shortened at the ends."""
    w = np.array([0.125, 0.25, 0.25, 0.25, 0.125])
    out = np.empty(len(x))
    for i in range(len(x)):
        lo, hi = max(0, i - 2), min(len(x), i + 3)
        k = w[lo - i + 2:hi - i + 2]
        out[i] = float(np.sum(x[lo:hi] * k) / np.sum(k))
    return out


def fast_share(diff: np.ndarray) -> float:
    """Share of a difference's variance in its fast part, what's left after a 4-year mean."""
    slow = smooth(diff)
    fast = diff - slow
    total = float(np.sum(diff ** 2))
    return float(np.sum(fast ** 2)) / total if total > 0 else 0.0


def best_lag(a: np.ndarray, b: np.ndarray, max_lag: int = 3) -> tuple:
    """Correlation of two series' fast parts at lag 0, and the lag that correlates best."""
    fa, fb = a - smooth(a), b - smooth(b)

    def corr(k):
        x, y = (fa[k:], fb[:len(fb) - k]) if k >= 0 else (fa[:k], fb[-k:])
        return float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else 0.0

    lags = {k: corr(k) for k in range(-max_lag, max_lag + 1)}
    k = max(lags, key=lambda q: lags[q])
    return lags[0], k, lags[k]


def analyse(out: Path) -> str:
    base = json.loads((out / "baseline.json").read_text())
    runs = {f.stem: json.loads(f.read_text()) for f in sorted(out.glob("*__*.json"))}
    series = "new_length_m"
    arr = {k: np.array(base[k], float) for k in ("leaf_area_m2", "height_m", "fixed", series)}
    onset = first_alternating_year(arr[series])
    lines = ["# Is the chaos the every-other-year pattern? (INFO for M3)", "",
             f"{len(runs)} runs, seed 1, a parameter changed by 1 to {STEPS} parts in a million, against the default, every year kept.", "",
             f"**The default's first strong alternating year** (4 straight up-down swings, each at least half the local mean, in shoot length made per year): {onset}.", ""]
    rows, shares, lag0s, best, peak_same, onset_rows = [], [], [], [], [], []
    for name, r in runs.items():
        la = np.array(r["leaf_area_m2"], float)
        nl = np.array(r[series], float)
        y01 = first_year_above(la, arr["leaf_area_m2"], 0.1)
        y1 = first_year_above(la, arr["leaf_area_m2"], 1.0)
        y5 = first_year_above(la, arr["leaf_area_m2"], 5.0)
        alt = first_alternating_year(nl)
        onset_rows.append((y01, y1, y5, alt))
        w = slice(20, None)
        shares.append(fast_share((la - arr["leaf_area_m2"])[w]))
        c0, k, ck = best_lag(nl[w], arr[series][w])
        lag0s.append(c0)
        best.append((k, ck))
        # the same years up, or out of step: agreement of the swing's direction
        d1, d0 = np.diff(nl[w]), np.diff(arr[series][w])
        peak_same.append(float(np.mean(np.sign(d1) == np.sign(d0))))
    def med(v):
        v = [x for x in v if x is not None]
        return statistics.median(v) if v else None
    lines += ["| Year divergence passes... | Earliest | Median | Latest | Runs reaching it |", "|---|---|---|---|---|"]
    for i, label in enumerate(("0.1 % in leaf area", "1 %", "5 %")):
        v = [o[i] for o in onset_rows if o[i] is not None]
        lines.append(f"| {label} | {min(v) if v else '-'} | {med(v)} | {max(v) if v else '-'} | {len(v)} of {len(onset_rows)} |")
    alts = [o[3] for o in onset_rows if o[3] is not None]
    lines += ["", f"First strong alternating year in the changed runs: {min(alts) if alts else '-'} to {max(alts) if alts else '-'}, median {med(alts)}; default {onset}.", ""]
    lags = [b[0] for b in best]
    lines += ["**From age 20 on:**", "",
              f"- Direction of the yearly swing in shoot length agrees with the default in {100 * statistics.fmean(peak_same):.0f} % of years (50 % would be chance).",
              f"- Correlation of the fast swings with the default, at no shift: median {statistics.median(lag0s):+.2f}.",
              f"- Best shift of up to 3 years: median correlation {statistics.median([b[1] for b in best]):+.2f}; shifts of "
              + ", ".join(f"{k}: {lags.count(k)}" for k in sorted(set(lags))) + ".",
              f"- Share of the leaf-area divergence that's fast (gone after a 4-year mean): median {100 * statistics.median(shares):.0f} %, "
              f"{100 * min(shares):.0f}-{100 * max(shares):.0f} %.", ""]
    lines += ["**What a 4-year mean does to the spread between these runs (SD of % difference from the default):**", "",
              "| Age | Metric | One year | 4-year mean |", "|---|---|---|---|"]
    for age in (30, 50, 60):
        for k in ("leaf_area_m2", "height_m", "dbh_cm", "fixed"):
            b1, b5 = np.array(base[k], float), smooth(np.array(base[k], float))
            one, five = [], []
            for r in runs.values():
                x = np.array(r[k], float)
                if b1[age] > 0:
                    one.append(100.0 * (x[age] / b1[age] - 1.0))
                    five.append(100.0 * (smooth(x)[age] / b5[age] - 1.0))
            lines.append(f"| {age} | {k} | {statistics.stdev(one):.2f} | {statistics.stdev(five):.2f} |")
    lines += ["", "**Default, every year: shoot length made (m), leaf area (m2):**", "",
              "| Year | Shoot length | Leaf area | Height increment (m) |", "|---|---|---|---|"]
    h = arr["height_m"]
    for y in range(max(1, (onset or 10) - 4), min(len(h), (onset or 10) + 21)):
        lines.append(f"| {y} | {arr[series][y]:.1f} | {arr['leaf_area_m2'][y]:.1f} | {h[y] - h[y - 1]:.2f} |")
    return "\n".join(lines) + "\n"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="out/bench/noise_cycle")
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--child", nargs=3, default=None, help="internal: parameter, factor, result")
    a = ap.parse_args()
    if a.child:
        child(a.child[0] or None, float(a.child[1]), a.years, Path(a.child[2]))
        return
    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    if not a.analyse:
        me = str(Path(__file__).resolve())
        jobs = [Job("baseline", [sys.executable, me, "--child", "", "1.0", str(out / "baseline.json"), "--years", str(a.years)], out / "baseline.json")]
        for p in PARAMETERS:
            for k in range(1, STEPS + 1):
                target = out / f"{p}__{k}.json"
                jobs.append(Job(f"{p} step {k}", [sys.executable, me, "--child", p, repr(1.0 + k * 1e-6), str(target), "--years", str(a.years)], target))
        code = run_batch(jobs, 0.6, log=out / "runs.csv")
        if code:
            sys.exit(code)
    text = analyse(out)
    (out / "noise_cycle.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
