"""The example tree's meshes and renders (PROTOCOL.md section 9; the maintainer, 2026-11-06).

A render has to show the tree the scores came from.  The same seed grown on another chip is
a different tree, so the meshes are made where the ensemble ran, and only drawn elsewhere.
An ensemble's trees are lean and keep no history, so the seed is grown again in full, and
its scored outputs must equal the ensemble's run before anything is exported.

    # on the machine that ran the ensemble
    python tools/example_tree.py export --seed 5 --ages 10,30,60 --out out/bench/ensemble/example_5 \
        --check out/bench/ensemble/base_trees/5_stand
    # copy the folder here, then
    python tools/example_tree.py render out/bench/ensemble/example_5 --png reports/renders/M1_example.png

Mesh exports are heavy runs (PROTOCOL.md section 6): one at a time, on the main PC too.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def differences(ours: list, theirs: list) -> list:
    """Every scored yearly value that differs between this run and the other.  A lean run
    leaves out what nothing scores (branch counts, hanging twigs, root detail), so those
    aren't compared."""
    from treegen.runhash import SCORED_KEYS

    out = []
    if len(ours) != len(theirs):
        out.append(f"{len(ours)} years here, {len(theirs)} there")
    for a, b in zip(ours, theirs):
        for key in SCORED_KEYS:
            if a.get(key) != b.get(key):
                out.append(f"year {b.get('year')}: {key}: {a.get(key)!r} here, {b.get(key)!r} there")
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_ages(seed: int, ages: list, out: Path, check: Path | None, species: str, environment: str, scenario: list, budget: float) -> None:
    import cli
    from treegen import export

    other = None
    if check is not None:
        other = json.loads((check / "stats.json").read_text(encoding="utf-8"))  # fails here, before the long run
    out.mkdir(parents=True, exist_ok=True)
    model, sp = cli.grow(species, seed, max(ages), environment, stand=True, scenario=scenario)
    meta = {"species": sp.species.scientific_name, "species_file": species, "environment": environment, "mode": "stand", "seed": seed,
            "generator": "treegen 0.4, tools/example_tree.py"}
    meta["run_manifest"], meta["options"] = cli.run_manifest(species, environment, sp)
    meta["run_manifest"]["scenario"] = list(scenario)
    export.write_stats(out / "stats.json", model, meta, cli.reference_block(sp, model.stats), cli.anchorage_numbers(model, sp))
    if other is not None:
        ours = json.loads((out / "stats.json").read_text(encoding="utf-8"))
        wrong = differences(ours["per_year"], other["per_year"])
        if ours["run_manifest"].get("machine") != other["run_manifest"].get("machine"):
            wrong.append(f"grown on another machine: {ours['run_manifest'].get('machine')} here, {other['run_manifest'].get('machine')} there")
        if wrong:
            print(f"NOT THE SAME TREE as {check}: {len(wrong)} differences, nothing exported", file=sys.stderr)
            print("\n".join(wrong[:10]), file=sys.stderr)
            sys.exit(1)
        print(f"same tree as {check}: every scored value identical in all {len(other['per_year'])} years", flush=True)
    summary = {"seed": seed, "checked_against": None if check is None else check.as_posix(),
               "checked_stats_sha256": None if check is None else sha256(check / "stats.json"),
               "machine": meta["run_manifest"].get("machine"), "code": meta["run_manifest"].get("git_commit"), "ages": {}}
    for age in ages:
        g_crown = export.GLBWriter(out / f"tree_age{age:02d}.glb", f"tree_age{age}", meta, cli.CROWN_ATTRS)
        g_roots = export.GLBWriter(out / f"roots_age{age:02d}.glb", f"roots_age{age}", meta, cli.ROOT_ATTRS, base_color=(115, 84, 56))

        def write(crown, roots):
            g_crown.add(crown)
            g_roots.add(roots)

        skel, rad, is_root, orig = cli.skeleton(model, age)
        cli.stream(skel, np.ones(skel.n, bool), rad, is_root, orig, sp, [write], budget)
        crown_info, root_info = g_crown.close(), g_roots.close()
        s = model.stats[age]
        summary["ages"][str(age)] = {"height_m": s["height_m"], "dbh_cm": s["dbh_cm"], "leaf_area_m2": s.get("leaf_area_m2"), "crown": crown_info, "roots": root_info,
                                     "crown_sha256": sha256(out / f"tree_age{age:02d}.glb"), "roots_sha256": sha256(out / f"roots_age{age:02d}.glb")}
        print(f"age {age}: height {s['height_m']:.2f} m, DBH {s['dbh_cm']:.1f} cm, crown {crown_info}, peak {cli.peak_memory_mb():.0f} MB", flush=True)
    (out / "example.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


def load_mesh(path: Path):
    """A GLB written by this project, back in the model's axes, with the radius the renderer colours by."""
    import trimesh

    from treegen.mesh import MeshData

    scene = trimesh.load(path, process=False)
    g = list(scene.geometry.values())[0] if hasattr(scene, "geometry") else scene
    v, n = np.asarray(g.vertices, float), np.asarray(g.vertex_normals, float)
    return MeshData(np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1), np.asarray(g.faces),
                    np.stack([n[:, 0], -n[:, 2], n[:, 1]], 1),
                    {"radius": np.asarray(g.vertex_attributes["_RADIUS"], float).ravel()})


def render(folder: Path, png: Path, res_h: int) -> None:
    import bark
    from PIL import Image, ImageDraw, ImageFont
    from treegen import preview

    info = json.loads((folder / "example.json").read_text(encoding="utf-8"))
    ages = sorted(int(a) for a in info["ages"])
    H = info["ages"][str(ages[-1])]["height_m"]
    D = 1.3 * H
    az = np.radians(-60.0)
    eye = np.array([D * np.cos(az), D * np.sin(az), 1.6])
    centre = np.array([0.0, 0.0, 0.5 * H])
    half_h = 0.58 * H * float(np.linalg.norm(eye - centre)) / D
    panels = []
    for age in ages:
        r = preview.Rasterizer(centre, 0.75 * half_h, half_h, -60.0, 0.0, res_h=res_h, eye=eye)
        r.add_ground(6.0 * H)
        r.add(load_mesh(folder / f"tree_age{age:02d}.glb"), "shoot")
        roots = folder / f"roots_age{age:02d}.glb"
        if roots.exists() and roots.stat().st_size > 2000:
            r.add(load_mesh(roots), "root")
        panels.append((Image.fromarray(np.asarray(r.image())), age))
    gap, band = 20, 90
    sheet = Image.new("RGB", (sum(p[0].width for p in panels) + gap * (len(panels) - 1), max(p[0].height for p in panels) + band), (252, 252, 251))
    try:
        font = ImageFont.truetype("arial.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(sheet)
    x = 0
    for img, age in panels:
        s = info["ages"][str(age)]
        sheet.paste(img, (x, band))
        draw.text((x + 20, 25), f"age {age}: {s['height_m']:.1f} m tall, DBH {float(bark.dbh_over_bark(s['dbh_cm'])):.1f} cm over bark",
                  fill=(11, 11, 11), font=font)
        x += img.width + gap
    png.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(png)
    print(f"{png} {sheet.size}; seed {info['seed']}, grown on {info.get('machine')}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    e = sub.add_parser("export")
    e.add_argument("--seed", type=int, required=True)
    e.add_argument("--ages", default="10,30,60")
    e.add_argument("--out", required=True)
    e.add_argument("--check", default=None, help="the ensemble's folder for this seed: its scored outputs must match")
    e.add_argument("--species", default="betula_pendula")
    e.add_argument("--environment", default="sweden_open_field")
    e.add_argument("--set", action="append", default=[], help="the same values the ensemble ran with")
    e.add_argument("--chunk-vertices", type=float, default=400_000)
    r = sub.add_parser("render")
    r.add_argument("folder")
    r.add_argument("--png", required=True)
    r.add_argument("--res", type=int, default=1600)
    a = ap.parse_args(argv)
    if a.command == "export":
        export_ages(a.seed, [int(x) for x in a.ages.split(",")], Path(a.out), Path(a.check) if a.check else None,
                    a.species, a.environment, a.set, a.chunk_vertices)
    else:
        render(Path(a.folder), Path(a.png), a.res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
