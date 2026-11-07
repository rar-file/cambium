"""Export a tree for a game: .glb files with PBR textures, three levels of detail, stage by stage.

    # one tree at these ages; a file per age, season and level, and game_manifest.json
    python tools/game_export.py export --seed 5 --ages 5,15,30,60,100 --seasons summer,autumn --out out/game/seed5

    # budgets are settings; override them here or in the species file (appearance.game)
    python tools/game_export.py export --seed 5 --ages 30 --budget lod1=8000 --out out/game/test

    # for the game in Unreal 5.8: its folders, wind data and materials (docs/unreal.md)
    python tools/game_export.py export --target unreal --seed 5 --ages 15,60 --seasons summer --out out/game/unreal

    # sheets for looking at it, drawn from the exported files
    python tools/game_export.py render out/game/seed5 --prefix reports/renders/look_

    # read every .glb through the check again; where each look value comes from
    python tools/game_export.py check out/game/seed5
    python tools/game_export.py values

Growth isn't touched: the tree is grown year by year as cli.py grows it, and only read between years.
Without --stand the tree grows in the open, with it in a stand (as tools/example_tree.py does).
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import cli  # noqa: E402
from treegen import appearance as ap  # noqa: E402
from treegen import checkpoint, game, mesh, preview  # noqa: E402
from treegen import look_render as lr  # noqa: E402
from treegen import textures as tx  # noqa: E402
from treegen.environment import make_environment, make_soil  # noqa: E402
from treegen.export import GameGLB, validate_glb  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402
from treegen.params import load_environment, load_species  # noqa: E402

DEFAULT_SEASONS = ("summer",)


def grow_with_leaves(species: str, seed: int, ages: list, environment: str, stand: bool, scenario: list):
    """Grow the tree, reading its leaves at the end of each age asked for.  The same steps as
    ``cli.grow``, so the same tree."""
    sp, raw = load_species(species)
    checkpoint.set_values(sp, scenario)
    env_p, _ = load_environment(environment)
    model = GrowthModel(sp, make_environment(env_p), seed, stand=stand, soil=make_soil(env_p))
    snaps = {}
    for age in sorted(ages):
        while model.year < age:
            model.step()
        snaps[age] = ap.leaf_snapshot(model, age)
    model.run(0)
    return model, sp, raw, snaps


def shoot_arrays(model, age: int) -> tuple:
    """Positions and wood radii of the crown's nodes at the end of ``age``."""
    T = model.tree
    pos = T.pos[: T.n].copy()
    kf = preview._positions_at(model, age)
    pos[: len(kf)] = kf
    r = np.zeros(T.n)
    h = model.radius_history[age]
    r[: len(h)] = h
    return pos, r


def export_stage(model, sp, look: dict, tiles: list, age: int, snap: ap.LeafSnapshot, out: Path, seasons: list, slug: str, meta: dict, log=print) -> dict:
    """All levels of one age, for each season.  Wood is baked once and shared between seasons."""
    t0 = time.time()
    gcfg_full = look["game"]["full_mesh"]
    T = model.tree
    st = model.stats[age]
    height, dbh_w = float(st["height_m"]), st["dbh_cm"]
    skel, rad, is_root, orig = cli.skeleton(model, age)
    pos, r_wood = shoot_arrays(model, age)
    n = skel.n
    part_age = age - np.asarray(skel.birth[:n], float)
    z = np.asarray(skel.pos[:n, 2], float)
    rad_ob = np.asarray(rad[:n], float).copy()
    rad_ob = ap.add_bark_radius(look, rad_ob, part_age, z, np.asarray(is_root[:n]), height, dbh_w)
    settings0 = mesh.MeshSettings(ring_attributes=True, stem_sides_by_radius=True, sides_allowed=tuple(gcfg_full["sides_allowed"]))
    crown0 = game.crown_mesh(skel, np.ones(n, bool), rad_ob, is_root, orig, sp.geometry, settings0)
    wood = game.WoodParts(look, tiles, age, height, dbh_w, T.birth[: T.n], r_wood)
    wood.tree_seed = int(meta["seed"])
    game.bake_wood(wood, crown0, T, pos, model.radius_history)
    arrays0 = game.wood_arrays(wood, crown0, relief=True)
    log(f"age {age}: H {height:.1f} m, wood {len(crown0.faces)} triangles, baked in {time.time() - t0:.1f} s")

    gcfg = look["game"]
    lods = {lod["name"]: lod for lod in gcfg["lods"]}
    jpeg = int(gcfg["jpeg_quality"])
    seed = int(gcfg["texture_seed"])
    # leaves
    blade0 = tx.leaf_blade(look, seed + 500)
    fill = blade0["fill"]
    leaves = ap.leaf_instances(look, sp, snap, pos, r_wood, age, fill)
    strips_tex = tx.strip_texture(look, seed + 600)
    # the reduced wood, shared between seasons
    lod1 = next((v for v in lods.values() if v["kind"] == "reduced"), None)
    arrays1, wood1_tris, thr = None, 0, None
    if lod1 is not None:
        rm = gcfg["reduced_mesh"]
        settings1 = mesh.MeshSettings(edge_target=rm["edge_target"], sides_allowed=tuple(rm["sides_allowed"]), ring_spacing_factor=rm["ring_spacing_factor"],
                                      min_ring_spacing=rm["min_ring_spacing"], max_ring_spacing=rm["max_ring_spacing"], max_turn_deg=rm["max_turn_deg"], ring_attributes=True, stem_sides_by_radius=True)
        wood_budget = int(float(lod1["budget"]) * float(lod1["wood_share"]))
        thr = game.reduced_radius_threshold(skel, rad_ob, is_root, orig, sp.geometry, settings1, wood_budget)
        crown1 = game.crown_mesh(skel, game.reduced_selection(skel, rad_ob, thr), rad_ob, is_root, orig, sp.geometry, settings1)
        arrays1 = game.wood_arrays(wood, crown1)
        wood1_tris = len(crown1.faces)
    strips = ap.peel_strips(look, pos, T.parent[: T.n], r_wood, T.birth[: T.n], (T.birth[: T.n] <= age) & ((T.death[: T.n] < 0) | (T.death[: T.n] > age)),
                            age, height, ap.over_bark_dbh_cm(look, dbh_w))
    crown_centre = np.array([0.0, 0.0, 0.62 * height])
    out_stage = {"age": age, "height_m": height, "dbh_wood_cm": dbh_w, "dbh_over_bark_cm": round(ap.over_bark_dbh_cm(look, dbh_w), 2),
                 "model_leaves_reference_units": st["leaves"], "model_leaf_area_m2": st["leaf_area_m2"], "exported_leaves": int(len(leaves.node)),
                 "exported_leaf_area_m2": round(float(leaves.area.sum()), 3), "peel_strips": 0 if strips is None else strips.count, "seasons": {}}
    days = look["leaves"]["season"]["days"]
    for season in seasons:
        files = {}
        ll = None if season == "winter" else game.leaf_look(look, leaves, float(days[season]))
        for lname, lod in lods.items():
            path = out / f"{slug}_age{age:03d}_{season}_{lname}.glb"
            lmeta = {**meta, "age": age, "season": season, "level": lname, "height_m": height, "dbh_over_bark_cm": out_stage["dbh_over_bark_cm"]}
            glb = GameGLB(path, path.stem, lmeta)
            if lod["kind"] == "far":
                near = out / f"{slug}_age{age:03d}_{season}_{next(iter(lods))}.glb"
                game.far_cards(look, near, lod, glb, jpeg)
                parts = {"far_cards": glb.triangles}
            else:
                arrays = arrays0 if lod["kind"] == "full" else arrays1
                game.add_wood(glb, wood, arrays, jpeg, float(lod["stem_texture_scale"]), float(lod["atlas_scale"]))
                parts = {"wood": glb.triangles}
                if lod.get("peel_strips") and strips is not None:
                    game.add_strips(glb, look, strips, strips_tex)
                    parts["bark_strips"] = glb.triangles - parts["wood"]
                if ll is not None and len(leaves.node):
                    tri0 = glb.triangles
                    blade = tx.leaf_blade(look, seed + 500, game._turning(ll["mean_chlorophyll"], look["leaves"]["interveinal_lead"]))
                    if lod["leaf_kind"] == "blades":
                        m = game._leaf_material(glb, "leaf_blade", blade, ll, jpeg)
                        a = game.blades_arrays(look, leaves, ll)
                        glb.add_mesh("leaves", m, a["V"], a["N"], a["F"], a["UV"], a["T"], colour=a["colour"], attributes={"NODE_ID": a["node"], "LEAF_SUN": a["sun"], "LEAF_TURN": a["turn"]})
                    else:
                        cards_tex = tx.leaf_card_atlas(look, blade, seed + 700)
                        target = max((int(lod["budget"]) - glb.triangles) // 2, 1)
                        a = game.leaf_cards(look, leaves, ll, target, cards_tex["coverage"], cards_tex["grid"], crown_centre)
                        if a is not None:
                            m = game._leaf_material(glb, "leaf_card", cards_tex, ll, jpeg)
                            glb.add_mesh("leaf_cards", m, a["V"], a["N"], a["F"], a["UV"], a["T"], colour=a["colour"])
                            parts["leaf_area_represented_m2"] = round(a["represented_area"], 3)
                    parts["leaves"] = glb.triangles - tri0
            info = glb.write()
            info.update(parts=parts, budget=lod.get("budget"), within_budget=lod.get("budget") is None or info["triangles"] <= int(lod["budget"]), file=path.name)
            files[lname] = info
        out_stage["seasons"][season] = files
        tri = ", ".join(f"{k} {v['triangles']}" for k, v in files.items())
        log(f"age {age} {season}: {tri}; {time.time() - t0:.1f} s")
    if thr is not None:
        out_stage["reduced_thinnest_wood_radius_m"] = round(float(thr), 5)
    return out_stage


def check_files(folder: Path, log=print) -> list:
    """Every .glb and .gltf read through the validator here and loaded by trimesh; the triangle counts
    must agree.  Raises on the first problem."""
    import trimesh

    results = []
    for path in sorted(folder.glob("*.glb")) + sorted(folder.rglob("*.gltf")):
        info = validate_glb(path)
        scene = trimesh.load(path, process=False)
        geoms = scene.geometry.values() if hasattr(scene, "geometry") else [scene]
        tris = sum(len(g.faces) for g in geoms)
        if tris != info["triangles"]:
            raise ValueError(f"{path.name}: {info['triangles']} triangles here, {tris} in trimesh")
        results.append({"file": path.name, **info})
    log(f"{len(results)} files checked: all read through the validator and loaded by trimesh, with the same triangle counts")
    return results


def stem_map(path: Path) -> np.ndarray:
    """The stem's colour map from a near-level file, as light 0-1."""
    return (_image_of(path, "bark_stem_base") @ np.array([0.2126, 0.7152, 0.0722], np.float32)) / 255.0


def continuity(folder: Path, stages: list, slug: str, look: dict) -> list:
    """Each stage against the next, in the stem's lowest zone, where a texture row is the same place
    at every age: how alike the pattern is (correlation, 1 = the same) and how far the light moved."""
    out = []
    zone = float(look["bark"]["stem_rows"][0][1])
    for a, b in zip(stages[:-1], stages[1:]):
        sa, sb = next(iter(a["seasons"])), next(iter(b["seasons"]))
        first_a, first_b = next(iter(a["seasons"][sa].values()))["file"], next(iter(b["seasons"][sb].values()))["file"]
        ma, mb = stem_map(folder / first_a), stem_map(folder / first_b)
        if a["height_m"] <= look["bark"]["stem_rows"][0][0] or ma.shape != mb.shape:
            continue
        n = int(zone * ma.shape[0])
        x, y = ma[:n].ravel(), mb[:n].ravel()
        out.append({"from_age": a["age"], "to_age": b["age"], "pattern_correlation": round(float(np.corrcoef(x, y)[0, 1]), 3),
                    "mean_light_change": round(float(np.abs(x.mean() - y.mean())), 3)})
    return out


def main_export(a) -> int:
    ages = sorted(int(x) for x in a.ages.split(","))
    seasons = [s.strip() for s in a.seasons.split(",") if s.strip()]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    state = Path(a.state) if a.state else None
    if state is not None and state.exists():
        with open(state, "rb") as f:
            saved = pickle.load(f)
        model, snaps = saved["model"], saved["snaps"]
        sp, raw = load_species(a.species)
        print(f"reusing {state}: age {model.year}", flush=True)
    else:
        model, sp, raw, snaps = grow_with_leaves(a.species, a.seed, ages, a.environment, a.stand, a.set)
        if state is not None:
            state.parent.mkdir(parents=True, exist_ok=True)
            with open(state, "wb") as f:
                pickle.dump({"model": model, "snaps": snaps}, f, protocol=pickle.HIGHEST_PROTOCOL)
    look = ap.load_look(raw)
    if getattr(a, "levels", None):
        look["game"]["lods"] = [lod for lod in look["game"]["lods"] if lod["name"] in a.levels.split(",")]
    for item in a.budget:
        name, val = item.split("=")
        for lod in look["game"]["lods"]:
            if lod["name"] == name:
                lod["budget"] = None if val.lower() == "none" else int(val)
    for item in getattr(a, "look", None) or []:
        key, val = item.split("=", 1)
        parts = key.split(".")
        d = look
        for part in parts[:-1]:
            d = d[part]
        if parts[-1] not in d:
            raise KeyError(f"no such look value: {key}")
        d[parts[-1]] = json.loads(val)
    if getattr(a, "target", "generic") == "unreal":
        return export_unreal(a, model, sp, look, snaps, ages, seasons, out)
    slug = Path(a.species).stem
    meta = {"species": sp.species.scientific_name, "species_file": a.species, "environment": a.environment, "seed": a.seed, "mode": "stand" if a.stand else "open",
            "generator": "treegen tools/game_export.py"}
    meta["run_manifest"], _ = cli.run_manifest(a.species, a.environment, sp)
    t0 = time.time()
    tiles = tx.make_tiles(look)
    print(f"bark tiles made in {time.time() - t0:.1f} s; {', '.join(t.name for t in tiles)}", flush=True)
    stages = []
    for age in ages:
        if age > model.year:
            print(f"age {age}: the tree stopped at {model.year}", flush=True)
            continue
        stages.append(export_stage(model, sp, look, tiles, age, snaps[age], out, seasons, slug, meta, log=lambda s: print(s, flush=True)))
    checks = check_files(out)
    doc = {
        "continuity": continuity(out, stages, slug, look),
        "format": "treegen.game/1",
        **meta,
        "units": {"length": "m", "up_axis": "Y (glTF)", "ground": "y = 0, stem base at the origin"},
        "levels": look["game"]["lods"],
        "stages": stages,
        "checks": checks,
        "needs": ENGINE_NOTES,
    }
    (out / "game_manifest.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"done in {time.time() - t0:.0f} s -> {out}")
    return 0


def export_unreal(a, model, sp, look: dict, snaps: dict, ages: list, seasons: list, out: Path) -> int:
    """For the game: its folders, names, wind data and material setup (treegen/game_unreal.py)."""
    from treegen import game_unreal as gu

    look = gu.unreal_look(look)
    asset = look["game"]["unreal"]["asset"]
    meta = {"species": sp.species.scientific_name, "species_file": a.species, "environment": a.environment, "seed": a.seed, "mode": "stand" if a.stand else "open",
            "generator": "treegen tools/game_export.py --target unreal"}
    t0 = time.time()
    tiles = tx.make_tiles(look)
    gains = gu.scale_tiles_to_albedo(look, tiles)
    print(f"bark tiles made in {time.time() - t0:.1f} s; scaled to measured brightness: {gains}", flush=True)

    def skeleton(m, age):
        skel, rad, is_root, orig = cli.skeleton(m, age)
        pos, r_wood = shoot_arrays(m, age)
        return skel, rad, is_root, orig, pos, r_wood

    ctx = {"look": look, "model": model, "sp": sp, "out": out, "asset": asset, "meta": meta, "tiles": tiles, "snaps": snaps, "seed": a.seed, "skeleton": skeleton}
    stages = []
    for age in ages:
        if age > model.year:
            print(f"age {age}: the tree stopped at {model.year}", flush=True)
            continue
        stages.append(gu.export_stage(ctx, age, seasons, log=lambda s: print(s, flush=True)))
    checks = check_files(out)
    fragments = gu.write_fragments(out, asset, stages, float(look["game"]["unreal"]["roots"]["surface_depth_m"]))
    doc = {"format": "treegen.game.unreal/1", **meta, "target": "unreal", "asset": asset, "bark_gains": gains, "color0": gu.COLOR0, "uv_layout": gu.UV_LAYOUT,
           "units": {"length": "m in the file; Unreal's import makes cm", "up_axis": "Y (glTF), (x, z, -y) of the model's frame, as the game's plants"},
           "levels": look["game"]["lods"], "stages": stages, "checks": checks, "fragments": fragments}
    (out / "game_manifest.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"done in {time.time() - t0:.0f} s -> {out}")
    return 0


ENGINE_NOTES = {
    "core": "glTF 2.0 PBR metallic-roughness, 32-bit indices, embedded PNG and JPEG textures, tangents supplied.",
    "vertex_colour": "branches and leaves multiply base colour by COLOR_0 (16-bit, linear). The material must use vertex colour, or branches go one colour.",
    "alpha": "leaves, cards and bark strips are alphaMode MASK at cutoff 0.5; strips carry their opacity in COLOR_0 alpha, which multiplies the texture's before the cutoff.",
    "two_sided": "leaves and cards are doubleSided: shade the back as well as the front. Bark strips are two one-sided sheets.",
    "optional_extension": "KHR_materials_diffuse_transmission on leaves gives light through them. Not required: without it the base colour alone holds the brightness of a leaf lit from both sides.",
    "extras": "bark materials name a height map in extras.heightTexture, range in metres in extras.heightRange_m, for parallax or displacement if the engine has it. Not a glTF core slot, so an importer ignores it.",
    "custom_attributes": "_NODE_ID (same id for the same part at every age), _RADIUS, _LEAF_SUN, _LEAF_TURN (days later or earlier than the tree's average to colour). Optional.",
    "levels": "one file per level; wire them to the engine's LOD group by file name. lod2 is alpha test on one-sided sheets back to back; meant for distance, because close up its crossed cards show. Don't let lod2 cast shadows from its cards: they fall on each other. Use lod1's, or a blob.",
    "stages": "same tree at each age, same origin, same ids. Swap at a distance or cross-fade (dither) between stages.",
}


# -- sheets ---------------------------------------------------------------------------------------
def _label(img: np.ndarray, text: str, size: int = 26):
    from PIL import Image, ImageDraw, ImageFont

    im = Image.fromarray(img)
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(im)
    x, y = 12, 10
    box = d.textbbox((x, y), text, font=font)
    d.rectangle([box[0] - 6, box[1] - 4, box[2] + 6, box[3] + 4], fill=(255, 255, 255))
    d.text((x, y), text, fill=(12, 12, 12), font=font)
    return np.asarray(im)


def _row(images: list, gap: int = 12) -> np.ndarray:
    h = max(i.shape[0] for i in images)
    w = sum(i.shape[1] for i in images) + gap * (len(images) - 1)
    sheet = np.full((h, w, 3), 252, np.uint8)
    x = 0
    for i in images:
        sheet[: i.shape[0], x:x + i.shape[1]] = i
        x += i.shape[1] + gap
    return sheet


def _save(a: np.ndarray, path: Path):
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a).save(path)
    print(path, a.shape, flush=True)


CAMERA_AZ = np.radians(-60.0)
CAM = np.array([np.cos(CAMERA_AZ), np.sin(CAMERA_AZ), 0.0])


def sun_for_camera(az_offset_deg: float = 55.0, elev_deg: float = 42.0) -> np.ndarray:
    a = CAMERA_AZ + np.radians(az_offset_deg)
    e = np.radians(elev_deg)
    return np.array([np.cos(a) * np.cos(e), np.sin(a) * np.cos(e), np.sin(e)])


def wood_only(prims: list) -> list:
    return [p for p in prims if p.name not in ("leaves", "leaf_cards")]


def bark_shots(prims: list, height: float, stage_label: str, res: int) -> tuple:
    """Lower stem, and two close-ups, with no leaves, so the bark can be judged."""
    wood = wood_only(prims)
    scene = wood + [lr.make_ground(max(8.0, height))]
    lights = lr.Lights(scene, sun_for_camera(), res=4096, sky_res=512, sky_dirs=6)
    # lower stem: the first 3.2 m
    span = min(3.2, max(height * 0.8, 1.2))
    d = 3.0 * span / 3.2 + 0.5
    tgt = np.array([0.0, 0.0, span * 0.5])
    fov = 2.0 * np.degrees(np.arctan(0.5 * span * 1.04 / d))
    stem = lr.render(scene, lr.View(tgt + CAM * d, tgt, int(res * 0.62), res, fov_deg=fov), lights, ss=2)
    stem = _label(stem, f"{stage_label}: lower {span:.1f} m")
    panels = {"stem": stem}
    # close-ups: a palm's distance at breast height, and near the ground
    closes = []
    for z_c, name in ((1.3, "at 1.3 m"), (0.3, "at 0.3 m"), (min(6.0, height * 0.55), f"at {min(6.0, height * 0.55):.1f} m")):
        if z_c > height:
            continue
        tgt = np.array([0.0, 0.0, z_c])
        d = 0.72
        # the stem alone casts here: the shadows of twigs would only get in the way of judging bark
        near = lr.Lights([p for p in wood if p.name != "branches"], sun_for_camera(), res=3072, sky_res=1024, sky_dirs=8, focus=(tgt, 4.0))
        im = lr.render(wood, lr.View(tgt + CAM * d, tgt, res // 2, res // 2, fov_deg=33.0), near, ss=2)
        closes.append(_label(im, f"{stage_label} {name}", 20))
    panels["close"] = closes
    return panels, lights


def _image_of(path: Path, name: str) -> np.ndarray:
    """A texture out of a .glb, as RGB uint8."""
    import io

    from PIL import Image

    from treegen.export import read_glb

    doc, blob = read_glb(path)
    img = next(i for i in doc["images"] if i["name"] == name)
    view = doc["bufferViews"][img["bufferView"]]
    return np.asarray(Image.open(io.BytesIO(blob[view["byteOffset"]:view["byteOffset"] + view["byteLength"]])).convert("RGB"))


def _whole_tree(prims: list, H: float, res: int, label: str) -> np.ndarray:
    for p in prims:
        if p.name == "far_cards":      # crossed cards would throw their shadows on each other
            p.no_cast = True
    scene = prims + [lr.make_ground(4.0 * H)]
    lights = lr.Lights(scene, sun_for_camera(), res=4096, sky_res=640, sky_dirs=8)
    tgt = np.array([0.0, 0.0, 0.5 * H])
    eye = CAM * 1.3 * H + np.array([0.0, 0.0, 1.6])
    fov = 2.0 * np.degrees(np.arctan(0.56 * H / np.linalg.norm(eye - tgt)))
    return _label(lr.render(scene, lr.View(eye, tgt, int(res * 0.72), res, fov_deg=fov), lights, ss=2), label)


def _busy_leaves(prims: list, H: float) -> np.ndarray:
    """A spot of the crown on the camera's side, where there are plenty of leaves to look at."""
    leaf = next((p for p in prims if p.name in ("leaves", "leaf_cards")), None)
    if leaf is None:
        return np.array([0.0, 0.0, 0.7 * H])
    V = leaf.V[::4]
    near = V[(V @ CAM) > np.percentile(V @ CAM, 70.0)]
    return np.median(near, axis=0)


def render_unreal(folder: Path, doc: dict, prefix: str, res: int, sel: list) -> int:
    """The Unreal target's files in this project's own renderer: each stage whole, its foot on the
    ground, and all its roots with the ground taken away."""
    whole, feet, under = [], [], []
    for s in doc["stages"]:
        if s["age"] not in sel:
            continue
        age, H = s["age"], s["height_m"]
        season = "summer" if "summer" in s["seasons"] else next(iter(s["seasons"]))
        near = s["seasons"][season]["lod0"]
        prims = lr.load_glb_primitives(folder / near["file"])
        rt = s["roots"]
        # stand everything on the ground: the file's origin is below the tree
        gz = np.array([0.0, 0.0, float(s["origin"]["ground_in_file_m"])], np.float32)
        for p in prims:
            p.V = p.V - gz
        whole.append(_whole_tree(prims, H, res, f"age {age}: {H:.1f} m, {near['triangles']:,} triangles"))
        wood = wood_only(prims)
        # the foot, seen from where a person stands
        scene = wood + [lr.make_ground(max(8.0, H))]
        lights = lr.Lights(scene, sun_for_camera(), res=4096, sky_res=640, sky_dirs=8, focus=(np.array([0.0, 0.0, 0.2]), 6.0))
        r = near["trunk"]["trunk_r_cm"] / 100.0
        tgt = np.array([0.0, 0.0, 0.1 + r])
        eye = tgt + CAM * (1.1 + 5.0 * r) + np.array([0.0, 0.0, 0.7])
        feet.append(_label(lr.render(scene, lr.View(eye, tgt, res, int(res * 0.72), fov_deg=38.0), lights, ss=2),
                           f"age {age}: the foot; {rt['showing']['roots']} roots show, out to {rt['showing']['reach_m']:.1f} m", 20))
        # the roots, with no ground
        below = lr.load_glb_primitives(folder / rt["files"]["lod0"]["file"]) if "lod0" in rt["files"] else []
        for p in below:
            p.V = p.V - gz
        all_wood = wood + below
        lights2 = lr.Lights(all_wood, sun_for_camera(), res=4096, sky_res=512, sky_dirs=6)
        spread = float(rt["spread_m"])
        tgt = np.array([0.0, 0.0, 0.1])
        eye = tgt + CAM * (2.2 * spread + 1.0) + np.array([0.0, 0.0, 0.12 * spread])
        fov = 2.0 * np.degrees(np.arctan((0.62 * spread + 0.3) / np.linalg.norm(eye - tgt)))
        under.append(_label(lr.render(all_wood, lr.View(eye, tgt, res, int(res * 0.5), fov_deg=fov), lights2, ss=2),
                            f"age {age}: every root, no ground. {rt['length_m']:.0f} m long, {rt['deepest_m']:.2f} m deep, {spread:.1f} m out; {rt['files'].get('lod0', {}).get('triangles', 0):,} triangles below ground", 18))
        del prims, below
    _save(_row(whole), Path(prefix + "unreal_ages_whole.png"))
    _save(np.concatenate(feet, axis=0), Path(prefix + "roots_foot.png"))
    _save(np.concatenate(under, axis=0), Path(prefix + "roots_all.png"))
    return 0


def main_render(a) -> int:
    folder = Path(a.folder)
    doc = json.loads((folder / "game_manifest.json").read_text(encoding="utf-8"))
    prefix = str(a.prefix)
    if doc.get("target") == "unreal":
        return render_unreal(folder, doc, prefix, int(a.res), [int(x) for x in a.ages.split(",")] if a.ages else [t["age"] for t in doc["stages"]])
    res = int(a.res)
    slug = Path(doc["species_file"]).stem
    sel = [int(x) for x in a.ages.split(",")] if a.ages else [s["age"] for s in doc["stages"]]
    stages = [s for s in doc["stages"] if s["age"] in sel]
    only = a.only.split(",")
    whole, stems, closes = [], [], []
    for s in stages:
        age, H = s["age"], s["height_m"]
        season = "summer" if "summer" in s["seasons"] else next(iter(s["seasons"]))
        prims = lr.load_glb_primitives(folder / f"{slug}_age{age:03d}_{season}_lod0.glb")
        label = f"age {age}"
        if "stem" in only or "close" in only:
            panels, _ = bark_shots(prims, H, label, res)
            stems.append(panels["stem"])
            closes.append(panels["close"])
        if "whole" in only:
            whole.append(_whole_tree(prims, H, res, f"{label}, {season}: {H:.1f} m, DBH {s['dbh_over_bark_cm']:.1f} cm over bark"))
        del prims
    if whole:
        _save(_row(whole), Path(prefix + "ages_whole.png"))
    if stems and "stem" in only:
        _save(_row(stems), Path(prefix + "bark_stems.png"))
    if closes and "close" in only:
        rows = [np.concatenate([c[k] if k < len(c) else np.full_like(c[0], 252) for c in closes], axis=1) for k in range(max(len(c) for c in closes))]
        _save(np.concatenate(rows, axis=0), Path(prefix + "bark_closeups.png"))
    # leaves through the year, and against the light
    if "leaves" in only:
        pick = next((s for s in stages if s["age"] == 30 and len(s["seasons"]) > 1), None) or next((s for s in stages if len(s["seasons"]) > 1), stages[0])
        age, H = pick["age"], pick["height_m"]
        shots_front, shots_back, shots_close = [], [], []
        order = [x for x in ("spring", "summer", "early_autumn", "autumn") if x in pick["seasons"]]
        focus = None
        lights = None
        for season in order:
            prims = lr.load_glb_primitives(folder / f"{slug}_age{age:03d}_{season}_lod0.glb")
            focus = _busy_leaves(prims, H) if focus is None else focus
            if lights is None:
                lights = lr.Lights(prims, sun_for_camera(), res=4096, sky_res=640, sky_dirs=8)
                lights_back = lr.Lights(prims, sun_for_camera(165.0, 38.0), res=4096, sky_res=640, sky_dirs=8)
            eye = focus + CAM * 2.4 + np.array([0.0, 0.0, -0.5])
            front = lr.render(prims, lr.View(eye, focus, res * 3 // 5, res * 3 // 5, fov_deg=44.0), lights, ss=3)
            back = lr.render(prims, lr.View(eye, focus, res * 3 // 5, res * 3 // 5, fov_deg=44.0), lights_back, ss=3)
            shots_front.append(_label(front, f"age {age}, {season}, sun behind the viewer", 20))
            shots_back.append(_label(back, "against the sun: light through the leaves", 20))
            eye = focus + CAM * 0.75 + np.array([0.0, 0.0, -0.2])
            shots_close.append(_label(lr.render(prims, lr.View(eye, focus, res * 3 // 5, res * 3 // 5, fov_deg=38.0), lights, ss=3), f"{season}, close", 20))
        if shots_front:
            _save(np.concatenate([_row(shots_front), _row(shots_back), _row(shots_close)], axis=0), Path(prefix + "leaves_season.png"))
    # the levels of detail, side by side
    if "lods" in only:
        pick = next((s for s in stages if s["age"] == 60), stages[-1])
        age, H = pick["age"], pick["height_m"]
        season = "summer" if "summer" in pick["seasons"] else next(iter(pick["seasons"]))
        panels = []
        for lname, info in pick["seasons"][season].items():
            prims = lr.load_glb_primitives(folder / info["file"])
            panels.append(_whole_tree(prims, H, res, f"age {age}, {lname}: {info['triangles']:,} triangles, {info['file_mb']:.1f} MB"))
        _save(_row(panels), Path(prefix + "lods.png"))
    # the stem's own texture by age, and one age's maps
    if "maps" in only:
        from PIL import Image

        strips = []
        for s in stages:
            season = next(iter(s["seasons"]))
            first = next(iter(s["seasons"][season].values()))["file"]
            # row 0 is the ground; flip so the ground is at the bottom
            arr = _image_of(folder / first, "bark_stem_base")[::-1]
            strips.append(_label(np.asarray(Image.fromarray(arr).resize((300, 1000), Image.LANCZOS)), f"age {s['age']}", 20))
        _save(_row(strips), Path(prefix + "stem_textures.png"))
        pick = next((s for s in stages if s["age"] == 60), stages[-1])
        season = next(iter(pick["seasons"]))
        first = next(iter(pick["seasons"][season].values()))["file"]
        panels = []
        for name, title in (("bark_stem_base", "colour"), ("bark_stem_normal", "normal"), ("bark_stem_orm", "occlusion, roughness"), ("bark_stem_height", "height")):
            arr = _image_of(folder / first, name)[::-1][-1400:]
            panels.append(_label(np.asarray(Image.fromarray(arr).resize((420, 840), Image.LANCZOS)), f"age {pick['age']}, lowest part of the stem: {title}", 16))
        _save(_row(panels), Path(prefix + "stem_maps.png"))
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap_.add_subparsers(dest="command", required=True)
    e = sub.add_parser("export")
    e.add_argument("--species", default="betula_pendula")
    e.add_argument("--environment", default="sweden_open_field")
    e.add_argument("--seed", type=int, default=5)
    e.add_argument("--ages", default="5,15,30,60,100")
    e.add_argument("--seasons", default=",".join(DEFAULT_SEASONS), help="any of spring, summer, early_autumn, autumn, winter")
    e.add_argument("--out", required=True)
    e.add_argument("--stand", action="store_true", default=True)
    e.add_argument("--open", dest="stand", action="store_false", help="grow in the open, not in a stand")
    e.add_argument("--set", action="append", default=[], metavar="KEY=JSON", help="growth values, from the start of the run")
    e.add_argument("--sets", help="a file of KEY=JSON lines, read before --set")
    e.add_argument("--budget", action="append", default=[], metavar="LEVEL=TRIANGLES", help="e.g. lod1=8000; 'none' for no limit")
    e.add_argument("--target", choices=("generic", "unreal"), default="generic", help="unreal: what the game reads (docs/unreal.md); generic: a self-contained .glb for any engine")
    e.add_argument("--look", action="append", default=[], metavar="KEY=JSON", help="change a value in the appearance block for this export, e.g. bark.stem_texture_px=[512,2048]")
    e.add_argument("--state", default=None, help="keep the grown tree in this file, and reuse it if it's there")
    e.add_argument("--levels", default="", help="only these levels, e.g. lod0; all if left out")
    r = sub.add_parser("render")
    r.add_argument("folder")
    r.add_argument("--prefix", default="reports/renders/look_")
    r.add_argument("--res", type=int, default=1100)
    r.add_argument("--ages", default="")
    r.add_argument("--only", default="whole,stem,close,leaves,lods,maps")
    c = sub.add_parser("check")
    c.add_argument("folder")
    v = sub.add_parser("values", help="where each look value comes from: SOURCE, DERIVED or TUNED")
    v.add_argument("--species", default="betula_pendula")
    a = ap_.parse_args()
    if getattr(a, "sets", None):
        a.set = Path(a.sets).read_text(encoding="utf-8").split() + a.set
    if a.command == "export":
        return main_export(a)
    if a.command == "render":
        return main_render(a)
    if a.command == "values":
        for key, text in ap.load_look(load_species(a.species)[1])["provenance"].items():
            print(f"{key}: {text}")
        return 0
    check_files(Path(a.folder))
    return 0


if __name__ == "__main__":
    sys.exit(main())
