"""Quick one-at-a-time sensitivity screen of the species file (campaign M1c).

Grows the seed-1 stand tree once with the defaults and once per parameter with
that value changed by a factor, and ranks the parameters by the largest relative
change in height, DBH, leaf area or carbon fixed at ages 30, 50 and 60.  Each run
is its own process; several run at once within the free-memory floor (tools/batch.py,
PROTOCOL.md section 6).  It can be stopped and started again: finished runs are
kept.  Runs are lean (no history, fewer stats; the scored outputs are the same,
tests/test_lean.py) unless --full.  Each new result carries a SHA-256 of the scored
outputs and the final tree, so a run can be shown to be the same however it was launched.

    python tools/sensitivity_screen.py --out out/bench/m1/screen
    python tools/sensitivity_screen.py --out out/bench/m1/screen --factor 0.75
    python tools/sensitivity_screen.py --out DIR --only resource.alpha,baseline --jobs 1
    python tools/sensitivity_screen.py --rank out/bench/m1/screen
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import statistics
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import Job, run_batch  # noqa: E402
from run_cache import Cache, case_key, code_version, plain, settings  # noqa: E402

RUN_PEAK_GB = 0.55  # measured: 464-532 MB in the screen's growth-only runs (peak_mb in the results)
AGES = (30, 50, 60)
METRICS = ("height_m", "dbh_cm", "leaf_area_m2", "fixed")

# Not screened, with the reason.
SKIP_SECTIONS = {
    "species": "names", "reference": "never read by growth", "stats": "output only", "plot": "plot runs only",
    "regeneration": "plot runs only", "geometry": "mesh only", "anchorage": "output only",
    "germination": "option off", "soil_water_balance": "option off", "field_layer_competition": "option off",
}
SKIP_PATHS = {
    "pipe_model.huber_radius_exponent": "not used at stem_theory stage 1 or 2 (treegen/growth.py:1469-1471)",
    "pipe_model.huber_path_exponent": "not used at stem_theory stage 1 or 2 (treegen/growth.py:1469-1471)",
    "pipe_model.huber_path_reference_m": "not used at stem_theory stage 1 or 2 (treegen/growth.py:1469-1471)",
    "roots.uptake_conductance_per_m": "used only when fine_root_uptake is off",
    "mechanics.substeps": "numerical resolution",
    "mechanics.max_rotation_per_step": "numerical guard",
    "light.perception_samples": "numerical resolution",
    "light.horizontal_margin": "numerical guard; a stand cell has no margin",
    "roots.field_margin": "numerical guard",
    "shoot.min_height_above_ground": "numerical guard",
    "shoot.short_shoot_internode_length": "not read by any code",
    "pipe_model.wind_load.wind_speed_m_s": "not used at stem_theory stage 2, which has its own wind speed",
}


def numeric_paths(o, p=""):
    """Dotted paths of every number or list of numbers in the parameter tree."""
    out = []
    items = vars(o).items() if isinstance(o, SimpleNamespace) else o.items() if isinstance(o, dict) else ()
    for k, v in items:
        path = f"{p}.{k}" if p else str(k)
        if isinstance(v, bool) or v is None or isinstance(v, str):
            continue
        if isinstance(v, (int, float)):
            out.append(path)
        elif isinstance(v, (list, tuple)):
            if v and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
                out.append(path)
        elif isinstance(v, (SimpleNamespace, dict)):
            out.extend(numeric_paths(v, path))
    return out


def screened_paths(sp):
    keep, skipped = [], {}
    for path in numeric_paths(sp):
        section = path.split(".")[0]
        if section in SKIP_SECTIONS:
            skipped[path] = SKIP_SECTIONS[section]
        elif path in SKIP_PATHS:
            skipped[path] = SKIP_PATHS[path]
        elif path == "pipe_model.stem_theory.stage":
            skipped[path] = "a selector, not a quantity"
        else:
            keep.append(path)
    return keep, skipped


def scaled(value, factor):
    def one(x):
        y = x * factor
        return int(round(y)) if isinstance(x, int) and not isinstance(x, bool) else y
    return [one(x) for x in value] if isinstance(value, (list, tuple)) else one(value)


def apply_change(sp, path, factor):
    obj = sp
    parts = path.split(".")
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], scaled(getattr(obj, parts[-1]), factor))


def one_run(path: str | None, factor: float, years: int, lean: bool = True, seed: int = 1) -> dict:
    """Grow the tree once in this process and return what the ranking needs."""
    import cli
    from treegen.growth import GrowthModel
    from treegen.runhash import scored_digest

    sp, _ = cli.load_species("betula_pendula")
    if path:
        apply_change(sp, path, factor)
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), seed, stand=True, soil=cli.make_soil(env_p), lean=lean)
    for _ in range(years):
        m.step()
    out = {}
    for s in m.stats:
        if s["year"] in AGES:
            out[str(s["year"])] = {
                "height_m": s["height_m"], "dbh_cm": s["dbh_cm"], "leaf_area_m2": s["leaf_area_m2"],
                "lai": s["lai"], "crown_ratio": s.get("crown_ratio"), "fixed": s["carbon"].get("fixed"),
                "cue": s["carbon"].get("cue"), "diffuse_light_pct": s.get("subcanopy_diffuse_light_pct"),
            }
    out["scored_digest"] = scored_digest(m)
    out["peak_mb"] = cli.peak_memory_mb()
    return out


def result_name(path, factor, seed=None):
    tail = "" if seed is None else f"__s{seed}"
    return f"baseline{tail}.json" if path is None else f"{path}__x{factor:g}{tail}.json"


def key_for(sp, env, path, factor, years, full, code, machine, seed=1) -> str:
    changed = copy.deepcopy(sp)
    if path:
        apply_change(changed, path, factor)
    return case_key("screen", changed, plain(env), seed, years, not full, code=code, machine=machine)


def job_for(out: Path, path, factor, years, full=False, key=None, seed=None) -> Job:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--one", path or "", "--factor", str(1.0 if path is None else factor),
           "--years", str(years), "--seed", str(seed or 1), "--result", str(out / result_name(path, factor, seed))] + (["--full"] if full else [])
    if key:
        cmd += ["--cache-key", key]
    seen = "" if seed is None else f" seed {seed}"
    return Job(f"{path or 'baseline'} x{1.0 if path is None else factor:g}{seen}", cmd, out / result_name(path, factor, seed))


def rank(out: Path):
    """ranking.csv: the largest relative change per parameter over the metrics and
    ages, for whichever factors have run."""
    base = json.loads((out / "baseline.json").read_text())
    rows = []
    for f in sorted(out.glob("*__x*.json")):
        path, factor = f.stem.split("__x")
        res = json.loads(f.read_text())
        worst, where = 0.0, ""
        for age in AGES:
            a, b = base.get(str(age)), res.get(str(age))
            if not a:
                continue
            if not b:
                worst, where = 100.0, f"no output at {age}"
                continue
            for k in METRICS:
                if a[k] and b[k] is not None:
                    d = 100.0 * (b[k] / a[k] - 1.0)
                    if abs(d) > abs(worst):
                        worst, where = d, f"{k} at {age}"
        rows.append({"path": path, "factor": float(factor), "change_pct": worst, "where": where})
    by_path: dict = {}
    for r in rows:
        if r["path"] not in by_path or abs(r["change_pct"]) > abs(by_path[r["path"]]["change_pct"]):
            by_path[r["path"]] = r
    ordered = sorted(by_path.values(), key=lambda r: -abs(r["change_pct"]))
    with open(out / "ranking.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["rank", "path", "factor", "max_change_pct", "where"])
        w.writeheader()
        for i, r in enumerate(ordered, 1):
            w.writerow({"rank": i, "path": r["path"], "factor": r["factor"],
                        "max_change_pct": f"{r['change_pct']:.1f}", "where": r["where"]})
    print(f"{len(ordered)} parameters ranked: {out / 'ranking.csv'}")
    for i, r in enumerate(ordered[:25], 1):
        print(f"{i:3d} {r['path']:55s} x{r['factor']:g} {r['change_pct']:+7.1f} %  {r['where']}")


def rank_paired(out: Path, seeds: int):
    """ranking.csv from several seeds per value, each paired with the baseline on the same
    seed.  Effect: the mean paired change in %.  Noise: its standard error; with few seeds
    one value's own standard error can be small by chance, so the larger of that and the
    typical standard error for that metric and age across all values is used.  A value
    is ranked by its largest effect / noise over METRICS at AGES, and flagged as within the
    noise if that's 2 or less.  With 12 comparisons per value, a lone pass can be chance:
    the top values get rerun at more seeds."""
    base = {s: json.loads((out / result_name(None, 1.0, s)).read_text()) for s in range(1, seeds + 1)}
    moves = {}
    for f in out.glob("*__x*__s*.json"):
        stem, seed = f.stem.rsplit("__s", 1)
        path, factor = stem.split("__x")
        res = json.loads(f.read_text())
        s = int(seed)
        for age in AGES:
            a, b = base[s].get(str(age)), res.get(str(age))
            for k in METRICS:
                if a and b and a.get(k) and b.get(k) is not None:
                    moves.setdefault((path, float(factor), age, k), []).append(100.0 * (b[k] / a[k] - 1.0))
    per_slot = {}
    for (path, factor, age, k), v in moves.items():
        if len(v) >= 2:
            per_slot.setdefault((age, k), []).append(statistics.stdev(v) / len(v) ** 0.5)
    typical = {slot: statistics.median(v) for slot, v in per_slot.items()}
    best = {}
    for (path, factor, age, k), v in moves.items():
        if len(v) < 2:
            continue
        mean = statistics.fmean(v)
        se = max(statistics.stdev(v) / len(v) ** 0.5, typical[(age, k)])
        ratio = abs(mean) / se if se > 0 else 0.0
        if path not in best or ratio > best[path]["ratio"]:
            best[path] = {"path": path, "factor": factor, "effect": mean, "se": se, "ratio": ratio, "where": f"{k} at {age}", "seeds": len(v)}
    ordered = sorted(best.values(), key=lambda r: -r["ratio"])
    with open(out / "ranking.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["rank", "path", "factor", "max_change_pct", "se_pct", "effect_over_noise", "within_noise", "where", "seeds"])
        w.writeheader()
        for i, r in enumerate(ordered, 1):
            w.writerow({"rank": i, "path": r["path"], "factor": r["factor"], "max_change_pct": f"{r['effect']:.2f}", "se_pct": f"{r['se']:.2f}",
                        "effect_over_noise": f"{r['ratio']:.2f}", "within_noise": "yes" if r["ratio"] <= 2.0 else "no", "where": r["where"], "seeds": r["seeds"]})
    inside = sum(1 for r in ordered if r["ratio"] <= 2.0)
    print(f"{len(ordered)} values ranked, {inside} within the noise: {out / 'ranking.csv'}")
    for i, r in enumerate(ordered[:25], 1):
        print(f"{i:3d} {r['path']:52s} {r['effect']:+7.2f} % +- {r['se']:.2f}, ratio {r['ratio']:5.1f}  {r['where']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="out/bench/m1/screen")
    ap.add_argument("--factor", type=float, default=1.25)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1, help="internal: the seed of one run")
    ap.add_argument("--seeds", type=int, default=None, help="several seeds per value, paired with the baseline on the same seed")
    ap.add_argument("--one", default=None, help="internal: one run of this parameter (empty: the baseline)")
    ap.add_argument("--result", default=None, help="internal: where --one writes")
    ap.add_argument("--rank", default=None, help="rank the finished runs in this folder, no runs")
    ap.add_argument("--list", action="store_true", help="print what would be screened, no runs")
    ap.add_argument("--full", action="store_true", help="not lean: keep the history and every yearly stat")
    ap.add_argument("--cache-key", default=None, help="internal: store the result under this key")
    ap.add_argument("--no-cache", action="store_true", help="run every case, even one already finished elsewhere")
    ap.add_argument("--jobs", type=int, default=None, help="runs at once (default: CPU cores - 1, within the memory floor)")
    ap.add_argument("--only", default=None, help="comma-separated parameters, 'baseline' for the baseline: run just these")
    a = ap.parse_args()

    if a.one is not None:
        res = one_run(a.one or None, a.factor, a.years, lean=not a.full, seed=a.seed)
        Path(a.result).write_text(json.dumps(res))
        if a.cache_key:
            Cache().put(a.cache_key, res)
        return
    if a.rank:
        rank_paired(Path(a.rank), a.seeds) if a.seeds else rank(Path(a.rank))
        return

    import cli

    sp, _ = cli.load_species("betula_pendula")
    keep, skipped = screened_paths(copy.deepcopy(sp))
    if a.list:
        print(f"{len(keep)} screened, {len(skipped)} skipped")
        print("\n".join(keep))
        return
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "skipped.json").write_text(json.dumps(skipped, indent=1))
    if a.only:
        chosen = [x.strip() for x in a.only.split(",") if x.strip()]
        unknown = [c for c in chosen if c != "baseline" and c not in keep]
        if unknown:
            sys.exit(f"not screened parameters: {unknown}")
        cases = [None if c == "baseline" else c for c in chosen]
    else:
        cases = [None] + keep
    jobs = []
    cache, reused = Cache(), 0
    env_raw, _ = cli.load_environment("sweden_open_field")
    code, machine = code_version(), settings()
    seed_list = list(range(1, a.seeds + 1)) if a.seeds else [None]
    if a.seeds and None not in cases:
        cases = [None] + cases   # every value is paired with the baseline on the same seed
    for c in cases:
        for seed in seed_list:
            target = out / result_name(c, a.factor, seed)
            key = None
            if not a.no_cache:
                key = key_for(sp, env_raw, c, 1.0 if c is None else a.factor, a.years, a.full, code, machine, seed or 1)
                hit = cache.get(key)
                if hit is not None and not target.exists():
                    target.write_text(json.dumps(hit))
                    reused += 1
            jobs.append(job_for(out, c, a.factor, a.years, a.full, key, seed))
    if reused:
        print(f"{reused} cases reused from out/cache, not rerun", flush=True)
    code = run_batch(jobs, RUN_PEAK_GB, workers=a.jobs, log=out / "runs.csv")
    if code:
        sys.exit(code)
    if a.seeds:
        rank_paired(out, a.seeds)
    elif not a.only:
        rank(out)


if __name__ == "__main__":
    main()
