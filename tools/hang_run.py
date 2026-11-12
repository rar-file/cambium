"""Grow trees and measure how much they hang at set ages, two ways: from the geometry (tools/hang_measure.py) and
from a leafless picture of the tree (tools/hang_render.py, read by tools/hang_photo.py, the same code that reads the
reference photos).  It only reads the model: tests/test_hang_measure.py.

    python tools/hang_run.py run --label node_hang_stand --seeds 10 [--first-seed 1] [--open] [--years 60]
                                 [--ages 10,20,30,50,60] [--pictures 1] [--set key=json ...]
    python tools/hang_run.py table LABEL [LABEL ...]      # means over seeds, (lowest-highest), age by age
    python tools/hang_run.py matched LABEL [LABEL ...]    # the model against each reference photo, read through that photo's window
    python tools/hang_run.py closer BEFORE AFTER          # is one set closer to the photos than another?  H5 is never ranked alone
    python tools/hang_run.py json LABEL [LABEL ...]       # the same numbers, seed by seed, as one JSON

A tree is grown as tools/tree_table.py grows it (lean, the default species and site), so a seed gives the tree it
gives everywhere else.  Writes out/bench/ensemble/<label>/<seed>/hang.json; with --pictures N the first N seeds also
keep their leafless pictures.

Against a photo, the model is never read whole.  A photo is read only inside its boxes, which often cut the lower
crown, where the model's most upright wood hangs.  So for each reference photo of the tree's kind (solitary photos for
open-grown trees, groups and edges for stand trees) the model is drawn as many pixels tall as the photo's tree and
read through the photo's own window (read_in_window).  The whole-tree reading is kept beside it.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import Job, run_batch  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
AGES = (10, 20, 30, 50, 60)
PEAK_GB = 2.5
PHOTO_KIND = {"open": "solitary", "stand": "group or edge"}     # which reference photos a tree is compared with
CAMERAS = (1.0, 2.0)     # a ground camera this many tree heights from the stem: the photos' own distances aren't known


def photos_for(mode: str) -> dict:
    """The reference photos a tree grown this way is compared with: each one's window (its boxes in tree heights) and
    how soft and grainy it was measured to be.  Numbers only; the photos aren't needed."""
    import hang_photo

    frames = json.loads(hang_photo.FRAMES.read_text(encoding="utf-8"))["photos"]
    numbers = json.loads(hang_photo.NUMBERS.read_text(encoding="utf-8"))["photos"] if hang_photo.NUMBERS.exists() else {}
    out = {}
    for name, frame in frames.items():
        window = hang_photo.window_of(frame)
        if window is not None and frame.get("kind") == PHOTO_KIND[mode]:
            out[Path(name).stem] = {"window": window, "camera": (numbers.get(name) or {}).get("camera") or {}}
    return out


def read_in_window(grey, info: dict, window: dict, mirror: bool = False, full: bool = True) -> dict:
    """The one way a model picture is read against a photo: through the photo's window, laid along the model's own stem
    line by the function that lays it on the photo (hang_photo.window_mask)."""
    import numpy as np

    import hang_photo

    roi = hang_photo.window_mask(grey.shape, window, (info["base_x"], info["base_y"]), (info["top_x"], info["top_y"]), mirror)
    if not roi.any():
        return {"near_vertical_share": None, "fine_line_px": 0.0}
    return hang_photo.measure(grey.astype(np.float64) / 255.0, roi, info["base_y"], info["top_y"], full)


def _short(m: dict) -> dict:
    """A reading without its long lists."""
    out = {k: m.get(k) for k in ("near_vertical_share", "near_vertical_share_strict", "near_level_share", "fine_line_px")}
    if "tips" in m:
        o = m.get("outline") or {}
        out.update({"tips": m["tips"], "hanging_run": m.get("hanging_run"), "fringe_low_at": m.get("fringe_low_at"),
                    "outline": {"width_over_height": o.get("width_over_height"), "widest_at": o.get("widest_at")}})
    return out


def matched(p0, p1, r, g, photo: dict, seed: int = 0) -> dict:
    """A model tree against one reference photo: drawn as many pixels tall as the photo's tree and read through the
    photo's window, on each side of the tree in each of the two views (four readings).

    window           the level view from far away, every measure
    whole            the same pictures read whole: what the window leaves out, at the same scale
    as_that_photo    the pictures made as soft and grainy as the photo was measured to be, then read through the window
    from_the_ground  the tree drawn as a person on the ground sees it, 1 and 2 tree heights from the stem, the same way
    twin             the geometry's own near-vertical share of the wood inside the window, and how much of it points down
    copy_reads       how soft and grainy the photo-like copy reads by the function that read the photo (east view)"""
    import numpy as np

    import hang_measure
    import hang_photo
    import hang_render

    window, camera = photo["window"], photo["camera"]
    foot, _ = hang_measure.foot_and_top(g)
    tree_px = int(round(window["tree_height_px"]))
    out = {"tree_px": tree_px, "window": [], "whole": [], "as_that_photo": [], "from_the_ground": {f"{c:g}x": [] for c in CAMERAS}}
    for view in hang_render.VIEWS:
        grey, info = hang_render.draw(p0, p1, r, view, tree_px, None, foot)
        out["whole"].append(_short(hang_photo.measure(grey.astype(np.float64) / 255.0, None, info["base_y"], info["top_y"], full=False)))
        soft = hang_render.as_photo(grey, camera, seed)
        for mirror in (False, True):
            out["window"].append({"view": view, "mirror": mirror, **_short(read_in_window(grey, info, window, mirror))})
            out["as_that_photo"].append(_short(read_in_window(soft, info, window, mirror, full=False)))
        if "copy_reads" not in out:
            roi = hang_photo.window_mask(soft.shape, window, (info["base_x"], info["base_y"]), (info["top_x"], info["top_y"]))
            out["copy_reads"] = hang_photo.sharpness(soft.astype(np.float64) / 255.0, roi) if roi.any() else {}
            out["px_per_m"] = info["px_per_m"]
        for c in CAMERAS:
            grey, info = hang_render.draw(p0, p1, r, view, tree_px, c, foot)
            for mirror in (False, True):
                out["from_the_ground"][f"{c:g}x"].append(_short(read_in_window(grey, info, window, mirror, full=False)))
    out["twin"] = hang_measure.side_view(g, hang_photo.SEEN_PX / out["px_per_m"], window)
    return out


def at_age(model, g, picture_dir, year: int, photos: dict | None = None) -> dict:
    import numpy as np

    import hang_measure
    import hang_photo
    import hang_render
    from treegen.growth import HANGING_DZ

    T, s = model.tree, model.stats[-1]
    n = T.n
    p0, p1, r = hang_render.segments(g)
    pictures, info = {}, {}
    for view in hang_render.VIEWS:
        grey, info = hang_render.draw(p0, p1, r, view)
        pictures[view] = hang_photo.measure(grey.astype(np.float64) / 255.0, None, info["base_y"], info["top_y"])
        # the same picture after what a camera does to it (hang_render.like_a_photo): does the reading hold?
        photo = hang_photo.measure(hang_render.like_a_photo(grey, year).astype(np.float64) / 255.0, None, info["base_y"], info["top_y"])
        pictures[view]["as_a_photo"] = {k: photo.get(k) for k in ("near_vertical_share", "near_vertical_share_strict", "near_level_share", "fine_line_px", "tips")}
        if picture_dir is not None:
            hang_render.save(grey, picture_dir / f"leafless_{view}_age{year:02d}.png")
    geo = hang_measure.measures(g, hang_photo.SEEN_PX / info["px_per_m"])
    # against each reference photo of this tree's kind: the same part of the tree, at the photo's own scale
    if photos is None:
        photos = photos_for("stand" if model.stand else "open")
    against = {name: matched(p0, p1, r, g, photo, year) for name, photo in photos.items()}
    # the engine's own rule and its own run lengths, beside the ones measured here
    alive = T.death[:n] < 0
    engine = alive & (T.dir[:n, 2] < HANGING_DZ) & ~g.stem
    engine[0] = False
    run = model.hanging_runs()
    tips = alive & (T.main_child[:n] < 0)
    tips[0] = False
    check = {"branch_internodes": int((alive & (g.parent >= 0) & ~g.stem).sum()), "rules_differ_on": int((engine != hang_measure.hangs(g)).sum()),
             "engine_longest_run_m": float(run[tips].max()) if tips.any() else 0.0}
    return {"stats": {k: s.get(k) for k in ("height_m", "dbh_cm", "crown_width_m", "leaf_area_m2", "leaves", "living_internodes", "lai", "crown_ratio")},
            "px_per_m": info["px_per_m"], "geometry": geo, "picture": pictures, "matched": against, "check": check}


def one(seed: int, sets: list, out: Path, years: int, stand: bool, ages: tuple, keep_pictures: bool) -> int:
    import hang_measure
    from treegen import checkpoint
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species, run_manifest

    t0 = time.time()
    species, environment = "betula_pendula", "sweden_open_field"
    sp, _ = load_species(species)
    checkpoint.set_values(sp, sets)
    env_p, _ = load_environment(environment)
    model = GrowthModel(sp, make_environment(env_p), seed, stand=stand, soil=make_soil(env_p), lean=True)
    out.mkdir(parents=True, exist_ok=True)
    photos = photos_for("stand" if stand else "open")
    share, rows = {}, {}
    for year in range(1, years + 1):
        model.step()
        g = hang_measure.from_model(model)
        share[year] = round(hang_measure.leaf_share(g), 5)
        if year in ages:
            rows[year] = at_age(model, g, out if keep_pictures else None, year, photos)
    result = {"seed": seed, "mode": "stand" if stand else "open", "scenario": list(sets), "ages": rows,
              "leaves_on_hanging_share_by_age": share, "H6_first_age_over_10pct": hang_measure.first_age_over(share),
              "H6_first_age_staying_over_10pct": hang_measure.first_age_staying_over(share), "seconds": round(time.time() - t0, 1)}
    (out / "hang.json").write_text(json.dumps(result, default=float), encoding="utf-8")
    meta = {"species_file": species, "environment": environment, "mode": result["mode"], "seed": seed, "generator": "tools/hang_run.py"}
    meta["run_manifest"], meta["options"] = run_manifest(species, environment, sp)
    meta["run_manifest"].update({"resumed_from": None, "scenario": list(sets)})
    (out / "manifest.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return 0


def run(label: str, seeds: int, first: int, sets: list, years: int, stand: bool, ages: str, pictures: int) -> int:
    folder = E / label
    extra = [x for v in sets for x in ("--set", v)] + ([] if stand else ["--open"])
    jobs = [Job(f"seed {s}", [sys.executable, str(Path(__file__).resolve()), "one", "--seed", str(s), "--years", str(years), "--ages", ages,
                              "--out", str(folder / str(s)), *(["--keep-pictures"] if s < first + pictures else []), *extra],
                folder / str(s) / "manifest.json") for s in range(first, first + seeds)]
    return run_batch(jobs, PEAK_GB, log=folder / "runs.csv")


def load(label: str) -> dict:
    out = {}
    for f in sorted((E / label).glob("*/hang.json"), key=lambda p: int(p.parent.name)):
        out[int(f.parent.name)] = json.loads(f.read_text(encoding="utf-8"))
    return out


def _dig(row, path: str):
    for key in path.split("."):
        if row is None:
            return None
        row = row.get(key)
    return row


def _picture(row: dict, path: str):
    """A picture measure: the mean of the two views."""
    v = [_dig(row["picture"][view], path) for view in row["picture"]]
    v = [x for x in v if x is not None]
    return statistics.fmean(v) if v else None


def _against(row: dict, photo: str, which: str, path: str):
    """A measure of the model against one photo: the mean over its readings (two views, the window on either side).
    which: window, whole, as_that_photo, from_the_ground.1x (or 2x); or twin and copy_reads, which are single."""
    block = _dig(row.get("matched", {}).get(photo), which)
    if isinstance(block, dict):
        return _dig(block, path)
    v = [_dig(reading, path) for reading in block or []]
    v = [x for x in v if x is not None]
    return statistics.fmean(v) if v else None


# what the tables show: (heading, where it is, decimals, from the picture?)
GEOMETRY = (("Height (m)", "stats.height_m", 1), ("H1 hanging share of branch length", "geometry.H1_hanging_share_of_branch_length.all", 2),
            ("under 5 mm", "geometry.H1_hanging_share_of_branch_length.under_5mm.share", 2), ("5-10 mm", "geometry.H1_hanging_share_of_branch_length.5_10mm.share", 2),
            ("10-20 mm", "geometry.H1_hanging_share_of_branch_length.10_20mm.share", 2), ("over 20 mm", "geometry.H1_hanging_share_of_branch_length.over_20mm.share", 2),
            ("H2 leaves on hanging wood", "geometry.H2_leaves_on_hanging_share", 2),
            ("H3 run over height, mean", "geometry.H3_hanging_run.mean_over_height", 3), ("p90", "geometry.H3_hanging_run.p90_over_height", 3),
            ("longest", "geometry.H3_hanging_run.longest_over_height", 3), ("mean (m)", "geometry.H3_hanging_run.mean_m", 2),
            ("p90 (m)", "geometry.H3_hanging_run.p90_m", 2), ("longest (m)", "geometry.H3_hanging_run.longest_m", 2),
            ("H4 ends per spray", "geometry.H4_sprays.ends_per_spray", 2), ("single strands", "geometry.H4_sprays.single_strand_share", 2),
            ("longest path, share of spray length", "geometry.H4_sprays.longest_path_share_of_spray_length", 2),
            ("H4 twigs' own sprays: ends", "geometry.H4_sprays.starting_under_5mm.ends_per_spray", 2),
            ("single strands", "geometry.H4_sprays.starting_under_5mm.single_strand_share", 2),
            ("longest path share", "geometry.H4_sprays.starting_under_5mm.longest_path_share_of_spray_length", 2),
            ("H5 twin: near vertical, wood that shows", "geometry.H5_side_view.wood_wide_enough_to_show.near_vertical_share", 2),
            ("of which down", "geometry.H5_side_view.wood_wide_enough_to_show.of_which_down", 2),
            ("H7 width over height", "geometry.H7_outline.width_over_height", 2), ("widest at", "geometry.H7_outline.widest_at", 2),
            ("Hanging wood held at the ground (m)", "geometry.hanging_held_at_ground_m", 1))
PICTURE = (("Near vertical", "near_vertical_share", 3), ("strict", "near_vertical_share_strict", 3), ("as a photo", "as_a_photo.near_vertical_share", 3),
           ("Near level", "near_level_share", 3), ("Tips told", "tips.told", 0), ("down", "tips.down_share", 2), ("up", "tips.up_share", 2),
           ("as a photo: told", "as_a_photo.tips.told", 0), ("down", "as_a_photo.tips.down_share", 2), ("up", "as_a_photo.tips.up_share", 2),
           ("Run over height, mean", "hanging_run.mean_over_height", 3), ("p90", "hanging_run.p90_over_height", 3), ("longest", "hanging_run.longest_over_height", 3),
           ("Width over height", "outline.width_over_height", 2), ("widest at", "outline.widest_at", 2), ("Fringe reaches down to", "fringe_low_at", 2),
           ("Fine line (px)", "fine_line_px", 0))
# against one photo: (heading, which reading, where it is, decimals)
AGAINST = (("Model in the photo's window", "window", "near_vertical_share", 3), ("strict", "window", "near_vertical_share_strict", 3),
           ("Whole tree, same scale", "whole", "near_vertical_share", 3),
           ("In window, as soft and grainy as the photo", "as_that_photo", "near_vertical_share", 3),
           ("In window, from the ground, 1 height away", "from_the_ground.1x", "near_vertical_share", 3),
           ("2 heights away", "from_the_ground.2x", "near_vertical_share", 3),
           ("Twin in window", "twin", "near_vertical_share", 2), ("of which down", "twin", "of_which_down", 2), ("seen (m)", "twin", "seen_m", 0),
           ("Near level", "window", "near_level_share", 3), ("Tips told", "window", "tips.told", 0), ("down", "window", "tips.down_share", 2), ("up", "window", "tips.up_share", 2),
           ("Run over height, p90", "window", "hanging_run.p90_over_height", 3),
           ("Width over height", "window", "outline.width_over_height", 2), ("widest at", "window", "outline.widest_at", 2),
           ("Fine line in window (px)", "window", "fine_line_px", 0), ("Copy's blur (px)", "copy_reads", "blur_sigma_px", 2), ("Copy's grain", "copy_reads", "grain_share_of_contrast", 4))


def _cell(values: list, places: int) -> str:
    v = [x for x in values if x is not None]
    if not v:
        return "-"
    return f"{statistics.fmean(v):.{places}f} ({min(v):.{places}f}-{max(v):.{places}f})"


def table(labels: list) -> None:
    for title, columns, getter in (("From the geometry", GEOMETRY, _dig), ("From the leafless picture, the whole tree at 1,200 px, mean of two views", PICTURE, _picture)):
        print(f"\n{title}. Means over seeds, (lowest-highest).\n")
        print("| Set | Age | Seeds | " + " | ".join(c[0] for c in columns) + " |")
        print("|---" * (len(columns) + 3) + "|")
        for label in labels:
            runs = load(label)
            for age in sorted({int(a) for r in runs.values() for a in r["ages"]}):
                rows = [r["ages"][str(age)] for r in runs.values() if str(age) in r["ages"]]
                print(f"| `{label}` | {age} | {len(rows)} | " + " | ".join(_cell([getter(row, c[1]) for row in rows], c[2]) for c in columns) + " |")
    import hang_measure

    # does the picture follow the geometry?  Tree by tree and age by age: the picture's near-vertical share against its twin from the nodes
    pairs = [(_picture(row, "near_vertical_share"), _dig(row, "geometry.H5_side_view.wood_wide_enough_to_show.near_vertical_share"))
             for label in labels for r in load(label).values() for row in r["ages"].values()]
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    if len(pairs) >= 3:
        print(f"\nPicture against geometry, {len(pairs)} trees-at-an-age: the picture's near-vertical share and its twin from the nodes correlate at "
              f"r = {statistics.correlation([a for a, _ in pairs], [b for _, b in pairs]):.2f}; the picture reads {statistics.fmean(a - b for a, b in pairs):+.2f} on average.")
    print("\nH6, the first age at which a tenth of the leaves sit on hanging wood, and the first age from which they do every year; and the check that this tool's rule and the engine's agree.\n")
    print("| Set | Seeds | H6 first age | H6 from then on | Leaves on hanging wood at 5, 8, 10, 12, 15, 20 | Internodes where the two rules differ | Longest run, engine's (m), at the last age |")
    print("|---|---|---|---|---|---|---|")
    for label in labels:
        runs = load(label)
        if not runs:
            continue
        series = [r["leaves_on_hanging_share_by_age"] for r in runs.values()]
        by = ", ".join(f"{statistics.fmean(s[str(a)] for s in series if str(a) in s):.2f}" for a in (5, 8, 10, 12, 15, 20) if any(str(a) in s for s in series))
        differ = sum(row["check"]["rules_differ_on"] for r in runs.values() for row in r["ages"].values())
        last = [r["ages"][max(r["ages"], key=int)]["check"]["engine_longest_run_m"] for r in runs.values()]
        print(f"| `{label}` | {len(runs)} | {_cell([hang_measure.first_age_over(s) for s in series], 1)} | {_cell([hang_measure.first_age_staying_over(s) for s in series], 1)} | "
              f"{by} | {differ} | {_cell(last, 2)} |")


def matched_table(labels: list) -> None:
    """The model against each reference photo of its kind, read through that photo's window at that photo's scale."""
    import hang_photo

    numbers = json.loads(hang_photo.NUMBERS.read_text(encoding="utf-8"))["photos"] if hang_photo.NUMBERS.exists() else {}
    reads = {Path(name).stem: r for name, r in numbers.items()}
    print("\nThe model against each photo, read through the photo's own window, the tree drawn as tall as the photo's. Means over seeds, (lowest-highest); "
          "each seed is the mean of two views with the window laid on either side.\n")
    print("| Set | Photo | Tree (px) | Photo reads | Age | Seeds | Model less photo | " + " | ".join(c[0] for c in AGAINST) + " | Whole tree at 1,200 px |")
    print("|---" * (len(AGAINST) + 8) + "|")
    for label in labels:
        runs = load(label)
        photos = sorted({p for r in runs.values() for row in r["ages"].values() for p in row.get("matched", {})})
        for photo in photos:
            real = (reads.get(photo) or {}).get("near_vertical_share")
            for age in sorted({int(a) for r in runs.values() for a in r["ages"]}):
                rows = [r["ages"][str(age)] for r in runs.values() if str(age) in r["ages"]]
                inside = [_against(row, photo, "window", "near_vertical_share") for row in rows]
                gap = "-" if real is None else f"{statistics.fmean(x for x in inside if x is not None) - real:+.2f}"
                print(f"| `{label}` | {photo} | {rows[0]['matched'][photo]['tree_px']} | {'-' if real is None else f'{real:.3f}'} | {age} | {len(rows)} | {gap} | "
                      + " | ".join(_cell([_against(row, photo, c[1], c[2]) for row in rows], c[3]) for c in AGAINST)
                      + f" | {_cell([_picture(row, 'near_vertical_share') for row in rows], 3)} |")


def h5_inputs(rows: list, photo: str) -> dict:
    """What hang_measure.closer_on_h5 reads, for one photo at one age: means over the seeds' rows."""
    def mean(values):
        v = [x for x in values if x is not None]
        return statistics.fmean(v) if v else None

    return {"near_vertical": mean(_against(row, photo, "window", "near_vertical_share") for row in rows),
            "twin": mean(_against(row, photo, "twin", "near_vertical_share") for row in rows),
            "of_which_down": mean(_against(row, photo, "twin", "of_which_down") for row in rows),
            "seen_m": mean(_against(row, photo, "twin", "seen_m") for row in rows),
            "hanging_share": mean(_dig(row, "geometry.H1_hanging_share_of_branch_length.all") for row in rows)}


def closer_table(before: str, after: str) -> None:
    """Is the set `after` closer to the photos than `before`, photo by photo and age by age?  The rule is
    hang_measure.closer_on_h5: the picture's near-vertical share is never ranked alone."""
    import hang_measure
    import hang_photo

    numbers = json.loads(hang_photo.NUMBERS.read_text(encoding="utf-8"))["photos"]
    a, b = load(before), load(after)
    seeds = sorted(set(a) & set(b))
    mode = sorted({r["mode"] for r in a.values()} | {r["mode"] for r in b.values()})
    if len(mode) != 1 or not seeds:
        raise SystemExit("the two sets must be grown the same way (open or stand) and share seeds")
    reads = [r["near_vertical_share"] for r in numbers.values() if r["kind"] == PHOTO_KIND[mode[0]]]
    photos = (min(reads), max(reads))
    print(f"\n`{after}` against `{before}`, {len(seeds)} seeds in both. The photos' range for {PHOTO_KIND[mode[0]]} trees: {photos[0]:.2f}-{photos[1]:.2f}. "
          "Closer only if all four hold.\n")
    print("| Photo | Age | In window: before | after | Nearer the photos | H1: before | after | Less wood hangs | Upright wood pointing down: before | after | Less of it | "
          "Upright wood pointing up: before | after | in metres: before | after | No more of it | Closer |")
    print("|---" * 17 + "|")
    for photo in sorted({p for r in a.values() for row in r["ages"].values() for p in row.get("matched", {})}):
        for age in sorted({int(x) for r in a.values() for x in r["ages"]} & {int(x) for r in b.values() for x in r["ages"]}):
            x = h5_inputs([a[s]["ages"][str(age)] for s in seeds if str(age) in a[s]["ages"]], photo)
            y = h5_inputs([b[s]["ages"][str(age)] for s in seeds if str(age) in b[s]["ages"]], photo)
            if any(v is None for v in (*x.values(), *y.values())):
                continue
            v = hang_measure.closer_on_h5(x, y, photos)
            f = v["figures"]
            yes = lambda t: "yes" if t else "no"      # noqa: E731
            print(f"| {photo} | {age} | {x['near_vertical']:.3f} | {y['near_vertical']:.3f} | {yes(v['nearer_the_photos'])} | {x['hanging_share']:.2f} | {y['hanging_share']:.2f} | "
                  f"{yes(v['less_wood_hangs'])} | {f['upright_pointing_down_share'][0]:.3f} | {f['upright_pointing_down_share'][1]:.3f} | {yes(v['less_upright_wood_points_down'])} | "
                  f"{f['upright_pointing_up_share'][0]:.3f} | {f['upright_pointing_up_share'][1]:.3f} | {f['upright_pointing_up_m'][0]:.1f} | {f['upright_pointing_up_m'][1]:.1f} | "
                  f"{yes(v['no_more_upright_wood_points_up'])} | {yes(v['closer'])} |")


def as_json(labels: list) -> dict:
    """Seed by seed, the columns the tables show, and nothing else."""
    import hang_measure

    out = {}
    for label in labels:
        runs = load(label)
        out[label] = {"seeds": sorted(runs), "mode": sorted({r["mode"] for r in runs.values()}), "scenario": sorted({json.dumps(r["scenario"]) for r in runs.values()}),
                      "H6_first_age_over_10pct": {str(s): hang_measure.first_age_over(r["leaves_on_hanging_share_by_age"]) for s, r in runs.items()},
                      "H6_first_age_staying_over_10pct": {str(s): hang_measure.first_age_staying_over(r["leaves_on_hanging_share_by_age"]) for s, r in runs.items()},
                      "leaves_on_hanging_share_by_age": {str(s): r["leaves_on_hanging_share_by_age"] for s, r in runs.items()}, "ages": {}}
        for age in sorted({int(a) for r in runs.values() for a in r["ages"]}):
            rows = {s: r["ages"][str(age)] for s, r in runs.items() if str(age) in r["ages"]}
            photos = sorted({p for row in rows.values() for p in row.get("matched", {})})
            out[label]["ages"][str(age)] = {
                "geometry": {c[1]: {str(s): _dig(row, c[1]) for s, row in rows.items()} for c in GEOMETRY},
                "picture": {c[1]: {str(s): _picture(row, c[1]) for s, row in rows.items()} for c in PICTURE},
                "against_photo": {photo: {f"{c[1]}.{c[2]}": {str(s): _against(row, photo, c[1], c[2]) for s, row in rows.items()} for c in AGAINST} for photo in photos}}
    return out


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("run", "one", "table", "matched", "closer", "json"))
    ap.add_argument("labels", nargs="*")
    ap.add_argument("--label")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--ages", default=",".join(str(a) for a in AGES))
    ap.add_argument("--open", action="store_true", help="grow in the open, no neighbours")
    ap.add_argument("--pictures", type=int, default=1, help="run: how many seeds keep their leafless pictures")
    ap.add_argument("--keep-pictures", action="store_true", help="one: keep this seed's leafless pictures")
    ap.add_argument("--out")
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args(argv)
    if a.what == "one":
        return one(a.seed, a.set, Path(a.out), a.years, not a.open, tuple(int(x) for x in a.ages.split(",") if x.strip()), a.keep_pictures)
    if a.what == "run":
        return run(a.label, a.seeds, a.first_seed, a.set, a.years, not a.open, a.ages, a.pictures)
    if a.what == "table":
        table(a.labels)
    elif a.what == "matched":
        matched_table(a.labels)
    elif a.what == "closer":
        closer_table(*a.labels)
    else:
        def short(x):
            if isinstance(x, dict):
                return {k: short(v) for k, v in x.items()}
            if isinstance(x, list):
                return [short(v) for v in x]
            return round(x, 4) if isinstance(x, float) else x

        # one line a set and an age, so the file stays small and still reads
        print("{")
        sets = short(as_json(a.labels))
        for i, (label, body) in enumerate(sets.items()):
            ages = body.pop("ages")
            print(f' {json.dumps(label)}: {{')
            for key, value in body.items():
                print(f'  {json.dumps(key)}: {json.dumps(value, separators=(",", ":"))},')
            print('  "ages": {')
            print(",\n".join(f'   {json.dumps(age)}: {json.dumps(row, separators=(",", ":"))}' for age, row in ages.items()))
            print("  }\n }" + ("," if i < len(sets) - 1 else ""))
        print("}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
