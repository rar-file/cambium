"""Full renders of grown trees, for judging by eye, with nothing heavy left behind.

One sheet per seed: the whole tree at each age in summer, and the same tree with its leaves taken off.  With --group, also the row of trees tools/crown_group.py
draws, at each age: group.png at the last, group_<age>.png at the others.  Grows and exports through tools/game_export.py (lod0, summer only), renders, and deletes its own .glb files, so a run costs disk only while it runs.

    python tools/crown_look.py --label node_c2x --seeds 3,5,7 --ages 30,60 --open --sets cases/crown_best.txt --set crown_frame.limp_twigs=true
    python tools/crown_look.py --label node_c2x --seeds 3,5,7 --ages 30,60 --group --sets cases/crown_best.txt
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

E = ROOT / "out" / "bench" / "ensemble"


def one(seed: int, sets: list, ages: list, stand: bool, out: Path, res: int) -> str:
    import game_export as ge
    import numpy as np
    from treegen import look_render as lr

    folder = out / f"tmp_s{seed}"
    a = argparse.Namespace(species="betula_pendula", environment="sweden_open_field", seed=seed, ages=",".join(str(x) for x in ages), seasons="summer", out=str(folder),
                           stand=stand, set=list(sets), budget=[], target="generic", look=["bark.uneven_top.strength=1"], state=None, levels="lod0")
    ge.main_export(a)
    doc = json.loads((folder / "game_manifest.json").read_text(encoding="utf-8"))
    (out / f"manifest_s{seed}.json").write_text(json.dumps(doc), encoding="utf-8")
    panels = []
    for s in doc["stages"]:
        age, H = s["age"], s["height_m"]
        prims = lr.load_glb_primitives(folder / f"betula_pendula_age{age:03d}_summer_lod0.glb")
        panels.append(ge._whole_tree(prims, H, res, f"seed {seed}, age {age}: {H:.1f} m, DBH {s['dbh_over_bark_cm']:.1f} cm over bark"))
        panels.append(ge._whole_tree(ge.wood_only(prims), H, res, "no leaves"))
        del prims
    ge._save(ge._row(panels), out / f"look_s{seed}.png")
    return str(folder)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", required=True)
    ap.add_argument("--seeds", default="3,5,7")
    ap.add_argument("--ages", default="30,60")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--group", action="store_true", help="also the row of trees at the last age; keep the seeds few, they repeat")
    ap.add_argument("--res", type=int, default=1100)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON")
    ap.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    a = ap.parse_args(argv)
    if a.sets:
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    seeds = [int(x) for x in a.seeds.split(",")]
    ages = [int(x) for x in a.ages.split(",")]
    workers = min(int(os.environ.get("ORIGIN_MAX_WORKERS", "2")), len(seeds))
    out = E / a.label
    out.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(workers) as ex:
        folders = list(ex.map(one, seeds, [a.set] * len(seeds), [ages] * len(seeds), [not a.open] * len(seeds), [out] * len(seeds), [a.res] * len(seeds)))
    if a.group:
        import crown_group
        for age in ages:
            crown_group.main(folders + ["--age", str(age), "--out", str(out / ("group.png" if age == max(ages) else f"group_{age}.png"))])
    for f in folders:
        shutil.rmtree(f, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
