"""The first hang arms: a small factorial over the three twig settings tuned together by eye, grown as single trees and
read with the hang measures (tools/hang_run.py), ranked by a rule written before any run
(reports/design/2026-11-11_hang_arms.md, section 1).  It sets values on the command line only: no code or default changes.

    python tools/hang_arms.py plan                                   # the arms and their settings
    python tools/hang_arms.py run --label node_hang_arms1 --seeds 5  # every arm, open and stand, on the node
    python tools/hang_arms.py tables LABEL --open-baseline node_hang_open3       # the report's tables, and the ranking
    python tools/hang_arms.py json LABEL --open-baseline node_hang_open3         # the same, seed by seed
    python tools/hang_arms.py run --label node_hang3_arms1 --round third        # the third round's four arms (report section 11)
    python tools/hang_arms.py compare node_hang3_arms1 node_hang2_arms1 node_hang_arms1 --open-baseline node_hang_open3 \
        --arms <arms> --against r012_h35_t50,r004p5_h35_t50 --more             # paired tables, and the third round's readings

A tree is grown and measured exactly as tools/hang_run.py grows and measures it; the only addition is that each age's
row also keeps the stand tree's light under the canopy, which the leaf area guard needs.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import hang_run  # noqa: E402

E = hang_run.E
NUMBERS = ROOT / "reference" / "betula_pendula" / "hang_photo_numbers.json"     # the photos' numbers (hang_photo.NUMBERS); no photo needed
RADIUS = (0.012, 0.006, 0.003)      # mechanics.pendulous_radius: today, the value before birch v1, half of that
SHARE = (0.35, 0.3)                 # crown_frame.hanging_share: today, the value it had when the working list first held it
SHOOT = (0.5, 0.4)                  # crown_frame.twig_shoot_max_m: today, the old value the species file names
TODAY = (0.012, 0.35, 0.5)
EXTRA_STATS = ("subcanopy_diffuse_light_pct", "subcanopy_light_pct", "crown_base_height_m", "crown_projected_diameter_m")
COUNTED_AGES = (30, 50, 60)         # the ages the photos of old trees can speak for
REQUIRED_AGES = (50, 60)
LAI_BAND = (3.6, 5.4)               # reference/targets.yaml lai_hagemeier.stand_range
LIGHT_MAX = 19.8                    # reference/targets.yaml subcanopy_light_transmittance, top of the range


def arm_name(radius: float, share: float, shoot: float) -> str:
    mm = round(radius * 1000, 6)
    r = f"{round(mm):03d}" if abs(mm - round(mm)) < 1e-9 else f"{mm:05.1f}".replace(".", "p")     # 0.0045 -> 004p5
    return f"r{r}_h{round(share * 100):02d}_t{round(shoot * 100):02d}"


def _sets(r: float, h: float, t: float) -> list:
    return [f"mechanics.pendulous_radius={r}", f"crown_frame.hanging_share={h}", f"crown_frame.twig_shoot_max_m={t}"]


def arms() -> dict:
    """name -> the --set values, softness radius varying slowest."""
    out = {}
    for r, h, t in itertools.product(RADIUS, SHARE, SHOOT):
        out[arm_name(r, h, t)] = _sets(r, h, t)
    return out


# The second round (report section 9, written before its runs): the radii between 0.006 and 0.003, each with both shoot
# lengths, hanging share held at today's 0.35.  Today's arm and the 0.006 arms are the first round's, reused as controls.
SECOND = tuple(itertools.product((0.0045, 0.004), (0.35,), (0.5, 0.4)))
SECOND_CONTROLS = ("r012_h35_t50", "r006_h35_t50")


def arms_second() -> dict:
    return {arm_name(r, h, t): _sets(r, h, t) for r, h, t in SECOND}


# The third round (report section 11, written before its runs): two radii just softer than 0.0045 (more hang), to see whether the
# photos are bracketed, and the existing switch that lets a twig's shoot end in two buds that can start a long shoot
# (crown_frame.twig_end_buds 2, option J) at 0.0045 and 0.0047.  All at today's share and shoot length.
END_BUDS = "crown_frame.twig_end_buds=2"
THIRD_CONTROLS = ("r012_h35_t50", "r004p5_h35_t50")


def arms_third() -> dict:
    out = {arm_name(r, 0.35, 0.5): _sets(r, 0.35, 0.5) for r in (0.0047, 0.0049)}
    for r in (0.0045, 0.0047):
        out[arm_name(r, 0.35, 0.5) + "_j2"] = _sets(r, 0.35, 0.5) + [END_BUDS]
    return out


def arms_of(which: str = "first") -> dict:
    return {"first": arms, "second": arms_second, "third": arms_third}[which]()


def baseline_name() -> str:
    return arm_name(*TODAY)


# -- growing ---------------------------------------------------------------------------------------------------------------
def _with_light(original):
    def at_age(model, g, picture_dir, year, photos=None):
        row = original(model, g, picture_dir, year, photos)
        s = model.stats[-1]
        row["stats"].update({k: s.get(k) for k in EXTRA_STATS})
        return row
    at_age.keeps_light = True
    return at_age


def one(seed: int, sets: list, out: Path, years: int, stand: bool, ages: tuple, keep_pictures: bool) -> int:
    if not getattr(hang_run.at_age, "keeps_light", False):
        hang_run.at_age = _with_light(hang_run.at_age)
    return hang_run.one(seed, sets, out, years, stand, ages, keep_pictures)


def run(label: str, seeds: int, pictures: int, skip: list, years: int, which: str = "first") -> int:
    from batch import Job, run_batch

    jobs = []
    for name, sets in arms_of(which).items():
        for mode in ("open", "stand"):
            if f"{name}_{mode}" in skip:
                continue
            folder = E / label / f"{name}_{mode}"
            for s in range(1, seeds + 1):
                cmd = [sys.executable, str(Path(__file__).resolve()), "one", "--seed", str(s), "--years", str(years), "--out", str(folder / str(s)),
                       *(["--open"] if mode == "open" else []), *(["--keep-pictures"] if s <= pictures else []), *[x for v in sets for x in ("--set", v)]]
                jobs.append(Job(f"{name} {mode} seed {s}", cmd, folder / str(s) / "manifest.json"))
    return run_batch(jobs, hang_run.PEAK_GB, log=E / label / "runs.csv")


# -- reading -------------------------------------------------------------------------------------------------------------
def load(folder: Path) -> dict:
    out = {}
    for f in sorted(folder.glob("*/hang.json"), key=lambda p: int(p.parent.name)):
        out[int(f.parent.name)] = json.loads(f.read_text(encoding="utf-8"))
    return out


def sets_of(label: str, open_baseline: str | None, seeds: int, which: str = "first") -> dict:
    """(arm, mode) -> {seed: hang.json}.  Today's open arm comes from the baseline's own trees when given."""
    out = {}
    for name in arms_of(which):
        for mode in ("open", "stand"):
            runs = load(E / label / f"{name}_{mode}")
            if not runs and name == baseline_name() and mode == "open" and open_baseline:
                runs = load(E / open_baseline)
            runs = {s: r for s, r in runs.items() if s <= seeds}
            if runs:
                out[(name, mode)] = runs
    return out


def photo_reads() -> dict:
    numbers = json.loads(NUMBERS.read_text(encoding="utf-8"))["photos"]
    return {Path(k).stem: v for k, v in numbers.items()}


def seed_values(runs: dict, age: int, getter) -> dict:
    out = {}
    for s, r in runs.items():
        row = r["ages"].get(str(age))
        v = getter(row) if row is not None else None
        if v is not None:
            out[s] = float(v)
    return out


def in_window(photo: str, path: str = "near_vertical_share", which: str = "window"):
    return lambda row: hang_run._against(row, photo, which, path)


def geo(path: str):
    return lambda row: hang_run._dig(row, path)


def mean_se(v: dict):
    x = list(v.values())
    if not x:
        return None, None
    return statistics.fmean(x), (statistics.stdev(x) / math.sqrt(len(x)) if len(x) > 1 else float("nan"))


# -- the rule (report section 1) -----------------------------------------------------------------------------------------
def toward(base: dict, arm: dict, real: float) -> dict:
    """One measure in one photo's window at one age.  The arm moved toward the photo's figure if the paired change,
    seed by seed, in the direction of the photo exceeds twice its standard error; it passed the photo if its mean is on
    the far side of the photo's figure by more than twice its own standard error."""
    seeds = sorted(set(base) & set(arm))
    if len(seeds) < 2:
        return {"seeds": len(seeds), "moved": None}
    b = statistics.fmean(base[s] for s in seeds)
    a = statistics.fmean(arm[s] for s in seeds)
    sign = 1.0 if b > real else -1.0                       # which way the photo lies from today's model
    d = [sign * (base[s] - arm[s]) for s in seeds]         # positive: moved toward the photo
    move, se = statistics.fmean(d), statistics.stdev(d) / math.sqrt(len(seeds))
    arm_se = statistics.stdev([arm[s] for s in seeds]) / math.sqrt(len(seeds))
    passed = sign * (a - real) < -2.0 * arm_se
    return {"seeds": len(seeds), "before": b, "after": a, "real": real, "gap_before": b - real, "gap_after": a - real,
            "move": move, "se": se, "moved": move > 2.0 * se, "worse": move < -2.0 * se, "passed": passed,
            "better": move > 2.0 * se and not passed}


def guards(stand: dict) -> dict:
    """Stand trees at 50 and 60: mean leaf area index inside the band, mean light under the canopy at most the top."""
    out = {}
    for age in REQUIRED_AGES:
        lai = mean_se(seed_values(stand, age, geo("stats.lai")))[0]
        light = mean_se(seed_values(stand, age, geo("stats.subcanopy_diffuse_light_pct")))[0]
        out[age] = {"lai": lai, "light": light,
                    "holds": lai is not None and light is not None and LAI_BAND[0] <= lai <= LAI_BAND[1] and light <= LIGHT_MAX}
    return out


def judge(sets: dict, name: str) -> dict:
    """An arm against today's, by the rule.  Primary: the near-vertical share in each solitary photo's window, open-grown
    trees, at 30, 50 and 60, with the four-part H5 test; required at 50 and 60, not worse at 30.  Guards: stand trees
    at 50 and 60.  Side: the stand trees against groups and edges, and crown width in the windows."""
    import hang_measure

    base = baseline_name()
    reads = photo_reads()
    out = {"arm": name, "primary": {}, "h5_test": {}, "stand": {}, "width": {}}
    for mode, kind, key in (("open", "solitary", "primary"), ("stand", "group or edge", "stand")):
        if (base, mode) not in sets or (name, mode) not in sets:
            continue
        b, a = sets[(base, mode)], sets[(name, mode)]
        photos = [p for p, v in reads.items() if v["kind"] == kind]
        rng = (min(reads[p]["near_vertical_share"] for p in photos), max(reads[p]["near_vertical_share"] for p in photos))
        for photo in photos:
            for age in COUNTED_AGES:
                out[key][(photo, age)] = toward(seed_values(b, age, in_window(photo)), seed_values(a, age, in_window(photo)), reads[photo]["near_vertical_share"])
                if mode == "open":
                    w = (reads[photo].get("outline") or {}).get("width_over_height")
                    if w is not None:
                        out["width"][(photo, age)] = toward(seed_values(b, age, in_window(photo, "outline.width_over_height")),
                                                            seed_values(a, age, in_window(photo, "outline.width_over_height")), w)
                    seeds = sorted(set(b) & set(a))
                    x = hang_run.h5_inputs([b[s]["ages"][str(age)] for s in seeds], photo)
                    y = hang_run.h5_inputs([a[s]["ages"][str(age)] for s in seeds], photo)
                    if None not in (*x.values(), *y.values()):
                        out["h5_test"][(photo, age)] = hang_measure.closer_on_h5(x, y, rng)
    if (name, "stand") in sets:
        out["guards"] = guards(sets[(name, "stand")])
    prim = out["primary"]
    req = [prim[k] for k in prim if k[1] in REQUIRED_AGES]
    out["better_on_numbers"] = bool(req) and all(c["better"] for c in req) and all(not prim[k]["worse"] for k in prim if k[1] == 30)
    out["h5_test_holds"] = bool(out["h5_test"]) and all(v["closer"] for k, v in out["h5_test"].items() if k[1] in REQUIRED_AGES)
    out["guards_hold"] = "guards" in out and all(g["holds"] for g in out["guards"].values())
    out["better"] = out["better_on_numbers"] and out["h5_test_holds"] and out["guards_hold"]
    return out


def up_rise(sets: dict, name: str) -> dict:
    """Part four of the H5 test seed by seed, which the test itself reads only on the means: the upright wood pointing
    up in the solitary windows at 50 and 60 (share of the wood seen, and metres), the arm less today's, per seed,
    averaged over the six cells.  Returns the mean and standard error of each.  A side reading: the rule is not changed."""
    reads = photo_reads()
    photos = [p for p, v in reads.items() if v["kind"] == "solitary"]
    base, arm = sets.get((baseline_name(), "open")) or {}, sets.get((name, "open")) or {}

    def up(row, photo):
        t = _dig_twin(row, photo)
        return None if t is None else (t["near_vertical_share"] * (1.0 - t["of_which_down"]), t["near_vertical_share"] * (1.0 - t["of_which_down"]) * t["seen_m"])

    share, metres = [], []
    for s in sorted(set(base) & set(arm)):
        d = [(up(arm[s]["ages"][str(a)], p), up(base[s]["ages"][str(a)], p)) for p in photos for a in REQUIRED_AGES]
        if all(x is not None and y is not None for x, y in d):
            share.append(statistics.fmean(x[0] - y[0] for x, y in d))
            metres.append(statistics.fmean(x[1] - y[1] for x, y in d))
    se = lambda v: statistics.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")      # noqa: E731
    return {"share": (statistics.fmean(share), se(share)) if share else (None, None), "metres": (statistics.fmean(metres), se(metres)) if metres else (None, None)}


def _dig_twin(row: dict, photo: str):
    t = (row.get("matched", {}).get(photo) or {}).get("twin")
    return t if t and None not in (t.get("near_vertical_share"), t.get("of_which_down"), t.get("seen_m")) else None


def remaining_gap(sets: dict, name: str) -> dict:
    """Seed by seed, the mean over the solitary photos' windows at 50 and 60 of how far the arm is from each photo,
    the figure arms are ranked on."""
    reads = photo_reads()
    runs = sets.get((name, "open")) or {}
    photos = [p for p, v in reads.items() if v["kind"] == "solitary"]
    out = {}
    for s, r in runs.items():
        gaps = []
        for photo in photos:
            for age in REQUIRED_AGES:
                row = r["ages"].get(str(age))
                v = hang_run._against(row, photo, "window", "near_vertical_share") if row else None
                if v is not None:
                    gaps.append(abs(v - reads[photo]["near_vertical_share"]))
        if len(gaps) == len(photos) * len(REQUIRED_AGES):
            out[s] = statistics.fmean(gaps)
    return out


def rank(sets: dict) -> list:
    """Arms that pass the rule first, then the rest; each group by the remaining gap.  Next to each, whether it is
    separated from the one above it by more than twice the paired standard error."""
    names = [n for n in arms() if (n, "open") in sets]
    verdicts = {n: judge(sets, n) for n in names if n != baseline_name()}
    gaps = {n: remaining_gap(sets, n) for n in names}
    order = sorted(names, key=lambda n: (not (n != baseline_name() and verdicts[n]["better"]), mean_se(gaps[n])[0]))
    out, prev = [], None
    for n in order:
        row = {"arm": n, "gap": mean_se(gaps[n])[0], "gap_se": mean_se(gaps[n])[1], "passes": n != baseline_name() and verdicts[n]["better"]}
        if prev is not None:
            seeds = sorted(set(gaps[prev]) & set(gaps[n]))
            d = [gaps[n][s] - gaps[prev][s] for s in seeds]
            row["vs_above"] = statistics.fmean(d) if d else None
            row["separated_from_above"] = len(d) > 1 and statistics.fmean(d) > 2.0 * statistics.stdev(d) / math.sqrt(len(d))
        out.append(row)
        prev = n
    return out


# -- tables ----------------------------------------------------------------------------------------------------------------
def f(x, p=2):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{p}f}"


def cell(v: dict, p=2) -> str:
    m, se = mean_se(v)
    return "-" if m is None else f"{m:.{p}f} ±{se:.{p}f}"


def tables(label: str, open_baseline: str | None, seeds: int) -> None:
    sets = sets_of(label, open_baseline, seeds)
    reads = photo_reads()
    names = list(arms())
    print("Arms: " + ", ".join(f"{n} ({len(sets.get((n, 'open'), {}))} open, {len(sets.get((n, 'stand'), {}))} stand)" for n in names))
    for mode, kind in (("open", "solitary"), ("stand", "group or edge")):
        photos = [p for p, v in reads.items() if v["kind"] == kind]
        print(f"\nNear-vertical share in each photo's window, {mode}-grown, mean ±SE over seeds; the photo's own reading in the heading.\n")
        print("| Arm | Age | " + " | ".join(f"{p.split('_')[0]} ({reads[p]['near_vertical_share']:.2f})" for p in photos) + " | Mean gap |")
        print("|---" * (len(photos) + 3) + "|")
        for n in names:
            runs = sets.get((n, mode))
            if not runs:
                continue
            for age in (10, 20, 30, 50, 60):
                vals = [seed_values(runs, age, in_window(p)) for p in photos]
                gap = statistics.fmean(mean_se(v)[0] - reads[p]["near_vertical_share"] for v, p in zip(vals, photos)) if all(vals) else None
                print(f"| {n} | {age} | " + " | ".join(cell(v) for v in vals) + f" | {'-' if gap is None else f'{gap:+.2f}'} |")
    print("\nGeometry and size, mean ±SE over seeds.\n")
    cols = (("Height m", "stats.height_m", 1), ("DBH cm", "stats.dbh_cm", 1), ("Crown width m", "stats.crown_width_m", 1),
            ("LAI", "stats.lai", 2), ("Light %", "stats.subcanopy_diffuse_light_pct", 1),
            ("H1 all", "geometry.H1_hanging_share_of_branch_length.all", 2),
            ("H1 10-20 mm", "geometry.H1_hanging_share_of_branch_length.10_20mm.share", 2),
            ("H2 leaves", "geometry.H2_leaves_on_hanging_share", 2),
            ("H3 p90/h", "geometry.H3_hanging_run.p90_over_height", 3), ("H3 longest/h", "geometry.H3_hanging_run.longest_over_height", 3),
            ("H3 longest m", "geometry.H3_hanging_run.longest_m", 1),
            ("H4 twig ends", "geometry.H4_sprays.starting_under_5mm.ends_per_spray", 2),
            ("H7 width/h", "geometry.H7_outline.width_over_height", 2), ("Leaf m2", "stats.leaf_area_m2", 0))
    print("| Arm | Mode | Age | " + " | ".join(c[0] for c in cols) + " |")
    print("|---" * (len(cols) + 3) + "|")
    for n in names:
        for mode in ("open", "stand"):
            runs = sets.get((n, mode))
            if not runs:
                continue
            for age in (10, 20, 30, 50, 60):
                print(f"| {n} | {mode} | {age} | " + " | ".join(cell(seed_values(runs, age, geo(c[1])), c[2]) for c in cols) + " |")
    import hang_measure

    print("\nH6: first age a tenth of the leaves hang, and from which they always do; leaves on hanging wood at 10, 12, 15, 20.\n")
    print("| Arm | Mode | H6 first | H6 from then on | at 10 | 12 | 15 | 20 |")
    print("|---|---|---|---|---|---|---|---|")
    for n in names:
        for mode in ("open", "stand"):
            runs = sets.get((n, mode))
            if not runs:
                continue
            series = [r["leaves_on_hanging_share_by_age"] for r in runs.values()]
            first = [hang_measure.first_age_over(s) for s in series]
            stay = [hang_measure.first_age_staying_over(s) for s in series]
            at = [statistics.fmean(s[str(a)] for s in series if str(a) in s) for a in (10, 12, 15, 20)]
            print(f"| {n} | {mode} | {f(statistics.fmean([x for x in first if x is not None]) if any(x is not None for x in first) else None, 1)} | "
                  f"{f(statistics.fmean([x for x in stay if x is not None]) if any(x is not None for x in stay) else None, 1)} | " + " | ".join(f(x) for x in at) + " |")
    print("\nThe rule, arm by arm against today's (" + baseline_name() + "). Primary cells: open-grown, three solitary windows, at 30, 50, 60.\n")
    print("| Arm | Cells better (50, 60) | Worse at 30 | Passed a photo | H5 four-part test at 50, 60 | Stand cells better (50, 60) | Width cells toward (50, 60) | LAI 50 | 60 | Light 50 | 60 | Guards | Better |")
    print("|---" * 13 + "|")
    for n in names:
        if n == baseline_name() or (n, "open") not in sets:
            continue
        v = judge(sets, n)
        p = v["primary"]
        req = [k for k in p if k[1] in REQUIRED_AGES]
        st = [k for k in v["stand"] if k[1] in REQUIRED_AGES]
        wd = [k for k in v["width"] if k[1] in REQUIRED_AGES]
        h5 = [k for k in v["h5_test"] if k[1] in REQUIRED_AGES]
        g = v.get("guards", {})
        print(f"| {n} | {sum(p[k]['better'] for k in req)}/{len(req)} | {sum(p[k]['worse'] for k in p if k[1] == 30)} | {sum(p[k]['passed'] for k in p)} | "
              f"{sum(v['h5_test'][k]['closer'] for k in h5)}/{len(h5)} | {sum(bool(v['stand'][k].get('better')) for k in st)}/{len(st)} | "
              f"{sum(bool(v['width'][k].get('better')) for k in wd)}/{len(wd)} | "
              + " | ".join(f(g.get(a, {}).get("lai")) for a in REQUIRED_AGES) + " | " + " | ".join(f(g.get(a, {}).get("light"), 1) for a in REQUIRED_AGES)
              + f" | {'hold' if v['guards_hold'] else 'FAIL'} | {'yes' if v['better'] else 'no'} |")
    print("\nThe four-part H5 test at 50 and 60: in how many of the six cells each part holds, and the figures behind the last two (means over the cells).\n")
    print("| Arm | Nearer the photos | Less wood hangs | Less upright wood points down | No more points up | Pointing down: before | after | Pointing up: before | after | in m: before | after | Rise in pointing up, paired by seed: share | m |")
    print("|---" * 13 + "|")
    for n in names:
        if n == baseline_name() or (n, "open") not in sets:
            continue
        h5 = {k: t for k, t in judge(sets, n)["h5_test"].items() if k[1] in REQUIRED_AGES}
        if not h5:
            continue
        rise = up_rise(sets, n)
        parts = ("nearer_the_photos", "less_wood_hangs", "less_upright_wood_points_down", "no_more_upright_wood_points_up")
        fig = lambda key, i: statistics.fmean(t["figures"][key][i] for t in h5.values())      # noqa: E731
        print(f"| {n} | " + " | ".join(f"{sum(t[p] for t in h5.values())}/{len(h5)}" for p in parts) + " | "
              + " | ".join(f"{fig(key, i):.3f}" for key in ("upright_pointing_down_share", "upright_pointing_up_share") for i in (0, 1))
              + f" | {fig('upright_pointing_up_m', 0):.0f} | {fig('upright_pointing_up_m', 1):.0f} | "
              + " | ".join("-" if m is None else f"{m:+.{p}f} ±{e:.{p}f}" for (m, e), p in ((rise["share"], 3), (rise["metres"], 1))) + " |")
    print("\nPaired changes against today's in each solitary window (toward the photo is positive), mean ±SE over seeds.\n")
    print("| Arm | " + " | ".join(f"{p.split('_')[0]} {a}" for p in [q for q, r in reads.items() if r["kind"] == "solitary"] for a in COUNTED_AGES) + " |")
    print("|---" * (1 + 3 * len(COUNTED_AGES)) + "|")
    for n in names:
        if n == baseline_name() or (n, "open") not in sets:
            continue
        v = judge(sets, n)["primary"]
        print(f"| {n} | " + " | ".join(f"{v[k]['move']:+.2f} ±{v[k]['se']:.2f}" if v[k].get("move") is not None else "-" for k in v) + " |")
    print("\nRanking: arms that pass the rule first, then by the mean gap to the solitary photos at 50 and 60.\n")
    print("| Rank | Arm | Mean gap at 50, 60 | ±SE | Passes the rule | Change from the one above | Separated (2 SE, paired) |")
    print("|---|---|---|---|---|---|---|")
    for i, row in enumerate(rank(sets), 1):
        above = "-" if row.get("vs_above") is None else format(row["vs_above"], "+.3f")
        sep = "-" if "separated_from_above" not in row else ("yes" if row["separated_from_above"] else "no")
        print(f"| {i} | {row['arm']} | {f(row['gap'], 3)} | {f(row['gap_se'], 3)} | {'yes' if row['passes'] else 'no'} | {above} | {sep} |")


def as_json(label: str, open_baseline: str | None, seeds: int, which: str = "first") -> dict:
    sets = sets_of(label, open_baseline, seeds, which)
    reads = photo_reads()
    paths = ("stats.height_m", "stats.dbh_cm", "stats.crown_width_m", "stats.lai", "stats.subcanopy_diffuse_light_pct", "stats.leaf_area_m2",
             "geometry.H1_hanging_share_of_branch_length.all", "geometry.H1_hanging_share_of_branch_length.10_20mm.share", "geometry.H2_leaves_on_hanging_share",
             "geometry.H3_hanging_run.p90_over_height", "geometry.H3_hanging_run.longest_over_height", "geometry.H4_sprays.starting_under_5mm.ends_per_spray",
             "geometry.H7_outline.width_over_height")
    out = {"arms": arms_of(which), "today": baseline_name(), "open_baseline_from": open_baseline, "sets": {}}
    for (n, mode), runs in sets.items():
        kind = "solitary" if mode == "open" else "group or edge"
        photos = [p for p, v in reads.items() if v["kind"] == kind]
        body = {}
        for age in (10, 20, 30, 50, 60):
            body[str(age)] = {**{p: {str(s): round(x, 4) for s, x in seed_values(runs, age, geo(p)).items()} for p in paths},
                              **{f"window.{ph}": {str(s): round(x, 4) for s, x in seed_values(runs, age, in_window(ph)).items()} for ph in photos}}
        out["sets"][f"{n}_{mode}"] = body
    return out


# -- comparing across rounds (report sections 4-5 corrections, and section 9) ---------------------------------------------
H1_BANDS = (("all", "all"), ("<5", "under_5mm.share"), ("5-10", "5_10mm.share"), ("10-20", "10_20mm.share"), (">20", "over_20mm.share"))


def gather(labels: list, open_baseline: str | None, seeds: int) -> dict:
    """(arm, mode) -> {seed: hang.json}, for the arms of both rounds, from the first label that holds each."""
    out = {}
    for name in {**arms(), **arms_second(), **arms_third()}:
        for mode in ("open", "stand"):
            runs = {}
            for label in labels:
                runs = load(E / label / f"{name}_{mode}")
                if runs:
                    break
            if not runs and name == baseline_name() and mode == "open" and open_baseline:
                runs = load(E / open_baseline)
            runs = {s: r for s, r in runs.items() if s <= seeds}
            if runs:
                out[(name, mode)] = runs
    return out


def per_seed(runs: dict, fn) -> dict:
    """seed -> fn(tree), dropping seeds where fn gives None."""
    out = {}
    for s, r in runs.items():
        v = fn(r)
        if v is not None:
            out[s] = float(v)
    return out


def windows_mean(kind: str, ages: tuple, path: str = "near_vertical_share", against: str | None = None, signed: bool = True):
    """A tree -> the mean over the photos of one kind and the given ages of a window measure; with `against`, its
    distance from the photo's own reading of that key (signed, or absolute)."""
    reads = photo_reads()
    photos = [p for p, v in reads.items() if v["kind"] == kind]

    def fn(r):
        vals = []
        for p in photos:
            real = None
            if against is not None:
                real = _dig_path(reads[p], against)
                if real is None:
                    continue
            for a in ages:
                row = r["ages"].get(str(a))
                v = hang_run._against(row, p, "window", path) if row else None
                if v is None:
                    return None
                vals.append(v if real is None else ((v - real) if signed else abs(v - real)))
        return statistics.fmean(vals) if vals else None
    return fn


def _dig_path(d: dict, path: str):
    for k in path.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def at(age: int, path: str):
    return lambda r: (hang_run._dig(r["ages"].get(str(age)), path) if r["ages"].get(str(age)) else None)


def paired(a: dict, b: dict) -> tuple:
    """a less b, seed by seed: mean, standard error, number of seeds, and in how many seeds it is positive."""
    seeds = sorted(set(a) & set(b))
    d = [a[s] - b[s] for s in seeds]
    if len(d) < 2:
        return None, None, len(d), None
    return statistics.fmean(d), statistics.stdev(d) / math.sqrt(len(d)), len(d), sum(x > 0 for x in d)


def pm(x: tuple, p: int = 3, sign: bool = True) -> str:
    m, se = x[0], x[1]
    if m is None:
        return "-"
    return f"{m:+.{p}f} ±{se:.{p}f}" if sign else f"{m:.{p}f} ±{se:.{p}f}"


def part_four_two_ways(sets: dict, name: str) -> dict:
    """Part four of the H5 test ("no more upright wood points up") in each solitary cell at 50 and 60, read (a) as
    written, on the seed means (hang_measure.closer_on_h5), and (b) with an allowance: it counts as risen only if the
    paired rise exceeds twice its standard error both as a share of the wood seen and in metres.  (a) is the rule."""
    import hang_measure

    reads = photo_reads()
    photos = [p for p, v in reads.items() if v["kind"] == "solitary"]
    rng = (min(reads[p]["near_vertical_share"] for p in photos), max(reads[p]["near_vertical_share"] for p in photos))
    b, a = sets[(baseline_name(), "open")], sets[(name, "open")]
    seeds = sorted(set(a) & set(b))
    out = {}
    for p in photos:
        for age in REQUIRED_AGES:
            x = hang_run.h5_inputs([b[s]["ages"][str(age)] for s in seeds], p)
            y = hang_run.h5_inputs([a[s]["ages"][str(age)] for s in seeds], p)
            written = hang_measure.closer_on_h5(x, y, rng)
            ups = {}
            for s in seeds:
                tb, ta = _dig_twin(b[s]["ages"][str(age)], p), _dig_twin(a[s]["ages"][str(age)], p)
                if tb and ta:
                    ub, ua = tb["near_vertical_share"] * (1 - tb["of_which_down"]), ta["near_vertical_share"] * (1 - ta["of_which_down"])
                    ups[s] = (ua - ub, ua * ta["seen_m"] - ub * tb["seen_m"])
            sh = [v[0] for v in ups.values()]
            mt = [v[1] for v in ups.values()]
            se = lambda v: statistics.stdev(v) / math.sqrt(len(v))      # noqa: E731
            risen = statistics.fmean(sh) > 2 * se(sh) and statistics.fmean(mt) > 2 * se(mt)
            out[(p, age)] = {"as_written": written["no_more_upright_wood_points_up"], "with_allowance": not risen,
                             "other_three": all(written[k] for k in ("nearer_the_photos", "less_wood_hangs", "less_upright_wood_points_down")),
                             "rise_share": (statistics.fmean(sh), se(sh)), "rise_m": (statistics.fmean(mt), se(mt))}
    return out


def compare(labels: list, open_baseline: str | None, seeds: int, names: list, against: list) -> None:
    """Each arm at 50 and 60, as means ±SE over seeds and as paired differences (arm less control, ±SE, seeds where
    positive) against each control: every measure section 9 names."""
    sets = gather(labels, open_baseline, seeds)
    reads = photo_reads()
    sol = [p for p, v in reads.items() if v["kind"] == "solitary"]
    grp = [p for p, v in reads.items() if v["kind"] == "group or edge"]
    show = [n for n in dict.fromkeys(against + names) if (n, "open") in sets]
    print("Seeds: " + ", ".join(f"{n} {len(sets.get((n, 'open'), {}))} open / {len(sets.get((n, 'stand'), {}))} stand" for n in show))

    def table(title, mode, cols):
        print(f"\n{title}\n")
        print("| Arm | Age | " + " | ".join(c[0] for c in cols) + " |")
        print("|---" * (len(cols) + 2) + "|")
        for n in show:
            if (n, mode) not in sets:
                continue
            for age in REQUIRED_AGES:
                print(f"| {n} | {age} | " + " | ".join(pm(mean_se(per_seed(sets[(n, mode)], c[1](age))), c[2], False) for c in cols) + " |")
        for ctrl in against:
            if (ctrl, mode) not in sets:
                continue
            print(f"\nThe same, paired: arm less {ctrl} (±SE; n of seeds where the arm is higher)\n")
            print("| Arm | Age | " + " | ".join(c[0] for c in cols) + " |")
            print("|---" * (len(cols) + 2) + "|")
            for n in show:
                if n == ctrl or (n, mode) not in sets:
                    continue
                for age in REQUIRED_AGES:
                    cells = []
                    for c in cols:
                        d = paired(per_seed(sets[(n, mode)], c[1](age)), per_seed(sets[(ctrl, mode)], c[1](age)))
                        cells.append("-" if d[0] is None else f"{pm(d, c[2])} ({d[3]}/{d[2]})")
                    print(f"| {n} | {age} | " + " | ".join(cells) + " |")

    def win(p, path="near_vertical_share"):
        return lambda age: (lambda r: hang_run._against(r["ages"].get(str(age)), p, "window", path) if r["ages"].get(str(age)) else None)

    short = lambda p: p.split("_")[0].capitalize()      # noqa: E731
    table("Main measure: near-vertical share in each solitary window, open-grown (photos: "
          + ", ".join(f"{short(p)} {reads[p]['near_vertical_share']:.2f}" for p in sol) + "); gap = mean over the three of the arm less the photo; distance = the same with no sign",
          "open", [(short(p), win(p), 3) for p in sol]
          + [("gap", lambda age: windows_mean("solitary", (age,), against="near_vertical_share"), 3),
             ("distance", lambda age: windows_mean("solitary", (age,), against="near_vertical_share", signed=False), 3)])
    table("Stand windows: near-vertical share, stand-grown (photos: " + ", ".join(f"{short(p)} {reads[p]['near_vertical_share']:.2f}" for p in grp) + ")",
          "stand", [(short(p), win(p), 3) for p in grp]
          + [("gap", lambda age: windows_mean("group or edge", (age,), against="near_vertical_share"), 3),
             ("distance", lambda age: windows_mean("group or edge", (age,), against="near_vertical_share", signed=False), 3)])
    table("Solitary windows, open-grown: near-level share (photos 0.14-0.20) and crown width over height (photos 0.46-0.55), mean of the three; "
          "width distance = mean of |arm less photo|",
          "open", [("near-level", lambda age: windows_mean("solitary", (age,), "near_level_share"), 3),
                   ("near-level, highest window", lambda age: (lambda r: max([v for v in (win(p, "near_level_share")(age)(r) for p in sol) if v is not None], default=None)), 3),
                   ("width/h", lambda age: windows_mean("solitary", (age,), "outline.width_over_height"), 3),
                   ("width distance", lambda age: windows_mean("solitary", (age,), "outline.width_over_height", against="outline.width_over_height", signed=False), 3)])
    for mode in ("open", "stand"):
        table(f"{mode.capitalize()}-grown geometry: H1 (share of branch length that hangs) by wood diameter; H3 hanging run; H4 twig sprays (starting under 5 mm)",
              mode, [(f"H1 {lab}", (lambda k: lambda age: at(age, f"geometry.H1_hanging_share_of_branch_length.{k}"))(k), 2) for lab, k in H1_BANDS]
              + [("H3 p90/h", lambda age: at(age, "geometry.H3_hanging_run.p90_over_height"), 3),
                 ("H3 longest/h", lambda age: at(age, "geometry.H3_hanging_run.longest_over_height"), 3),
                 ("H3 longest m", lambda age: at(age, "geometry.H3_hanging_run.longest_m"), 2),
                 ("H4 ends per spray", lambda age: at(age, "geometry.H4_sprays.starting_under_5mm.ends_per_spray"), 2)])
    table("Stand trees: leaf area index and light under the canopy (%), the guards (3.6-5.4; at most 19.8)",
          "stand", [("LAI", lambda age: at(age, "stats.lai"), 2), ("light %", lambda age: at(age, "stats.subcanopy_diffuse_light_pct"), 2)])
    print("\nThe rule against today's (section 1, as written), and part four two ways.\n")
    print("| Arm | Cells moved toward, not passed (50, 60) | Cells passed | Parts 1-3 of the H5 test | Part four as written (the rule) | Part four with a 2 SE allowance (not the rule) | Guards | Better by the rule |")
    print("|---" * 8 + "|")
    for n in show:
        if n == baseline_name():
            continue
        v = judge(sets, n)
        p = v["primary"]
        req = [k for k in p if k[1] in REQUIRED_AGES]
        two = part_four_two_ways(sets, n)
        print(f"| {n} | {sum(p[k]['better'] for k in req)}/{len(req)} | {sum(p[k]['passed'] for k in req)} | {sum(t['other_three'] for t in two.values())}/{len(two)} | "
              f"{sum(t['as_written'] for t in two.values())}/{len(two)} | {sum(t['with_allowance'] for t in two.values())}/{len(two)} | "
              f"{'hold' if v['guards_hold'] else 'FAIL'} | {'yes' if v['better'] else 'no'} |")
    print("\nPart four cell by cell: the paired rise in upright wood pointing up (share of the wood seen; metres), arm less today's.\n")
    print("| Arm | " + " | ".join(f"{short(p)} {a}" for p in sol for a in REQUIRED_AGES) + " |")
    print("|---" * (1 + len(sol) * len(REQUIRED_AGES)) + "|")
    for n in show:
        if n == baseline_name():
            continue
        two = part_four_two_ways(sets, n)
        print(f"| {n} | " + " | ".join(f"{pm(two[(p, a)]['rise_share'], 3)}; {pm(two[(p, a)]['rise_m'], 1)}" for p in sol for a in REQUIRED_AGES) + " |")


def _table(sets: dict, show: list, against: list, title: str, mode: str, cols: list) -> None:
    """Means ±SE over seeds at 50 and 60, then each control's paired table (arm less control, ±SE, seeds higher)."""
    print(f"\n{title}\n")
    print("| Arm | Age | " + " | ".join(c[0] for c in cols) + " |")
    print("|---" * (len(cols) + 2) + "|")
    for n in show:
        if (n, mode) not in sets:
            continue
        for age in REQUIRED_AGES:
            print(f"| {n} | {age} | " + " | ".join(pm(mean_se(per_seed(sets[(n, mode)], c[1](age))), c[2], False) for c in cols) + " |")
    for ctrl in against:
        if (ctrl, mode) not in sets:
            continue
        print(f"\nThe same, paired: arm less {ctrl} (±SE; n of seeds where the arm is higher)\n")
        print("| Arm | Age | " + " | ".join(c[0] for c in cols) + " |")
        print("|---" * (len(cols) + 2) + "|")
        for n in show:
            if n == ctrl or (n, mode) not in sets:
                continue
            for age in REQUIRED_AGES:
                cells = []
                for c in cols:
                    d = paired(per_seed(sets[(n, mode)], c[1](age)), per_seed(sets[(ctrl, mode)], c[1](age)))
                    cells.append("-" if d[0] is None else f"{pm(d, c[2])} ({d[3]}/{d[2]})")
                print(f"| {n} | {age} | " + " | ".join(cells) + " |")


def compare_more(labels: list, open_baseline: str | None, seeds: int, names: list, against: list) -> None:
    """The third round's readings (report section 11), beside compare's: the main measure read with each photo's own
    blur and grain, the strict and loose readings both ways, every spray's and the twigs' own ends, tips and traced
    run, node counts and run time, and the rule's order by the remaining gap on both readings.  Side readings only:
    the rule (section 1) is unchanged."""
    sets = gather(labels, open_baseline, seeds)
    reads = photo_reads()
    sol = [p for p, v in reads.items() if v["kind"] == "solitary"]
    show = [n for n in dict.fromkeys(against + names) if (n, "open") in sets]
    short = lambda p: p.split("_")[0].capitalize()      # noqa: E731
    lo, hi = min(reads[p]["near_vertical_share"] for p in sol), max(reads[p]["near_vertical_share"] for p in sol)

    def win(p, path="near_vertical_share", which="window"):
        return lambda age: (lambda r: hang_run._against(r["ages"].get(str(age)), p, which, path) if r["ages"].get(str(age)) else None)

    def mean3(which, path="near_vertical_share", against_photo=False, signed=True):
        def by_age(age):
            def fn(r):
                row = r["ages"].get(str(age))
                vals = []
                for p in sol:
                    v = hang_run._against(row, p, which, path) if row else None
                    if v is None:
                        return None
                    real = _dig_path(reads[p], path) if against_photo else None
                    if against_photo and real is None:
                        return None
                    vals.append(v if not against_photo else ((v - real) if signed else abs(v - real)))
                return statistics.fmean(vals)
            return fn
        return by_age

    _table(sets, show, against, "Main measure read with each photo's own blur and grain (as_that_photo), open-grown; gap and distance as in compare",
           "open", [(short(p), win(p, which="as_that_photo"), 3) for p in sol]
           + [("gap", mean3("as_that_photo", against_photo=True), 3), ("distance", mean3("as_that_photo", against_photo=True, signed=False), 3)])
    print("\nInside the photos? Strict: cells (of 3) whose mean is within twice its own seed SE of that photo. Loose: the mean of the three windows inside the photos' "
          f"range ({lo:.3f}-{hi:.3f}). Each cell: mean, and mean less photo.\n")
    print("| Arm | Reading | Age | Strict | Mean of three | Loose | " + " | ".join(short(p) for p in sol) + " |")
    print("|---" * (6 + len(sol)) + "|")
    for n in show:
        for which, lab in (("window", "plain"), ("as_that_photo", "photo's blur")):
            for age in REQUIRED_AGES:
                cells, inside = [], 0
                for p in sol:
                    m, se = mean_se(per_seed(sets[(n, "open")], win(p, which=which)(age)))
                    off = m - reads[p]["near_vertical_share"]
                    inside += abs(off) <= 2 * se
                    cells.append(f"{m:.3f} ({off:+.3f})")
                m3 = mean_se(per_seed(sets[(n, "open")], mean3(which)(age)))
                print(f"| {n} | {lab} | {age} | {inside}/3 | {pm(m3, 3, False)} | {'in' if lo <= m3[0] <= hi else 'out'} | " + " | ".join(cells) + " |")
    for mode in ("open", "stand"):
        _table(sets, show, against, f"{mode.capitalize()}-grown sprays (H4): ends per spray over all sprays, and over the twigs' own (starting under 5 mm), with their single-strand share",
               mode, [("ends, all", lambda age: at(age, "geometry.H4_sprays.ends_per_spray"), 3),
                      ("single, all", lambda age: at(age, "geometry.H4_sprays.single_strand_share"), 3),
                      ("ends, twigs' own", lambda age: at(age, "geometry.H4_sprays.starting_under_5mm.ends_per_spray"), 3),
                      ("single, twigs' own", lambda age: at(age, "geometry.H4_sprays.starting_under_5mm.single_strand_share"), 3),
                      ("sprays, twigs' own", lambda age: at(age, "geometry.H4_sprays.starting_under_5mm.sprays"), 0)])
    side = [(lab, mean3("window", path), 3) for lab, path in (("tips up", "tips.up_share"), ("tips down", "tips.down_share"), ("traced run p90/h", "hanging_run.p90_over_height"))]
    print("\nPhotos, solitary: " + "; ".join(f"{lab} {min(_dig_path(reads[p], path) for p in sol):.3f}-{max(_dig_path(reads[p], path) for p in sol):.3f}"
                                         for lab, path in (("tips up", "tips.up_share"), ("tips down", "tips.down_share"), ("traced run p90/h", "hanging_run.p90_over_height"))))
    _table(sets, show, against, "Side readings in the solitary windows, open-grown, mean of the three (weak; not scored)", "open",
           side + [(f"{lab}, distance", mean3("window", path, True, False), 3) for lab, path in (("tips up", "tips.up_share"), ("tips down", "tips.down_share"))])
    for mode in ("open", "stand"):
        _table(sets, show, against, f"{mode.capitalize()}-grown size: living internodes (nodes), crown width, stem, crown base and crown ratio",
               mode, [("nodes", lambda age: at(age, "stats.living_internodes"), 0), ("crown width m", lambda age: at(age, "stats.crown_width_m"), 2),
                      ("H7 width/h", lambda age: at(age, "geometry.H7_outline.width_over_height"), 3), ("DBH cm", lambda age: at(age, "stats.dbh_cm"), 2),
                      ("crown base m", lambda age: at(age, "stats.crown_base_height_m"), 2), ("crown ratio", lambda age: at(age, "stats.crown_ratio"), 3),
                      ("own LAI", lambda age: at(age, "stats.lai"), 2)])
    print("\nRun time per tree to 60, seconds, mean ±SE over seeds (open / stand), and paired against each control\n")
    for n in show:
        cells = []
        for mode in ("open", "stand"):
            if (n, mode) not in sets:
                continue
            s = per_seed(sets[(n, mode)], lambda r: r.get("seconds"))
            cells.append(f"{mode} {pm(mean_se(s), 0, False)}" + "".join(
                f", less {c} {pm(paired(s, per_seed(sets[(c, mode)], lambda r: r.get('seconds'))), 0)}" for c in against if c != n and (c, mode) in sets))
        print(f"- {n}: " + "; ".join(cells))
    for which, lab in (("window", "plain"), ("as_that_photo", "with each photo's blur")):
        gaps = {}
        for n in show:
            gaps[n] = per_seed(sets[(n, "open")], lambda r, which=which: statistics.fmean(
                abs(hang_run._against(r["ages"][str(a)], p, which, "near_vertical_share") - reads[p]["near_vertical_share"]) for p in sol for a in REQUIRED_AGES))
        order = sorted(show, key=lambda n: mean_se(gaps[n])[0])
        print(f"\nThe rule's order by the remaining gap ({lab}): mean over the six cells of the distance to each photo, seed by seed; "
              "each against the one above, paired (separated if beyond twice its SE)\n")
        print("| Rank | Arm | Remaining gap | Less the one above | Separated |")
        print("|---|---|---|---|---|")
        for i, n in enumerate(order, 1):
            if i == 1:
                print(f"| 1 | {n} | {pm(mean_se(gaps[n]), 4, False)} | - | - |")
                continue
            d = paired(gaps[n], gaps[order[i - 2]])
            print(f"| {i} | {n} | {pm(mean_se(gaps[n]), 4, False)} | {pm(d, 4)} | {'yes' if d[0] > 2 * d[1] else 'no'} |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("plan", "run", "one", "tables", "json", "compare"))
    ap.add_argument("labels", nargs="*")
    ap.add_argument("--label")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--ages", default=",".join(str(a) for a in hang_run.AGES))
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--pictures", type=int, default=1)
    ap.add_argument("--keep-pictures", action="store_true")
    ap.add_argument("--skip", action="append", default=[], help="run: an arm and mode to leave out, as <arm>_<open|stand>")
    ap.add_argument("--open-baseline", help="tables, json: the label whose open-grown trees are today's arm")
    ap.add_argument("--out")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--arms", default="", help="compare: the arms to show, comma-separated (default: the second round's)")
    ap.add_argument("--against", default=",".join(SECOND_CONTROLS), help="compare: the controls, comma-separated")
    ap.add_argument("--round", dest="which", choices=("first", "second", "third"), default="first",
                    help="plan, run, json: the first round's twelve arms, the second round's four (report section 9) or the third's four (section 11)")
    ap.add_argument("--more", action="store_true", help="compare: also the third round's readings (report section 11)")
    a = ap.parse_args(argv)
    if a.what == "plan":
        for n, sets in arms_of(a.which).items():
            print(n, " ".join(sets), "(today)" if n == baseline_name() else "")
        return 0
    if a.what == "one":
        return one(a.seed, a.set, Path(a.out), a.years, not a.open, tuple(int(x) for x in a.ages.split(",") if x.strip()), a.keep_pictures)
    if a.what == "run":
        return run(a.label, a.seeds, a.pictures, a.skip, a.years, a.which)
    if a.what == "compare":
        names, against = [x for x in a.arms.split(",") if x] or list(arms_second()), [x for x in a.against.split(",") if x]
        compare(a.labels, a.open_baseline, a.seeds, names, against)
        if a.more:
            compare_more(a.labels, a.open_baseline, a.seeds, names, against)
    elif a.what == "tables":
        tables(a.labels[0], a.open_baseline, a.seeds)
    else:
        print(json.dumps(as_json(a.labels[0], a.open_baseline, a.seeds, a.which), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
