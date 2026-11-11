"""Inside Unreal: the game's own scripts pick up an export, unchanged, in the test project.

Runs under ``tools/unreal_test.py route``, which first copies what's needed into the test project's
GameScripts and SourceArt folders.  Nothing in the game's folder is opened.  In order:
  * M_Surface and M_Foliage, by the game's build_master;
  * each file named, by the game's import_world_assets.py (Interchange, Combine All, Nanite on);
  * an instance per slot, by the game's instances_stage; then what its set_tree_looks.py does for a birch.
Then it reads back what the tree has, as tools/unreal/import_check.py does.
"""
import json
import os
import sys
import traceback

import unreal

JOB = json.load(open(os.environ["TREEGEN_UE_JOB"], encoding="utf-8"))
sys.path.insert(0, JOB["here"])
from readback import sample_mesh  # noqa: E402

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SCRIPTS = os.path.join(PROJECT, "GameScripts")
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
report = {"steps": [], "imports": []}


def log(message):
    unreal.log(f"[treegen] {message}")


def step(name, ok=True, **more):
    report["steps"].append({"step": name, "ok": ok, **more})
    log(f"{name}: {'ok' if ok else 'FAILED'} {more if more else ''}")
    with open(JOB["results"], "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)


def load_materials():
    """The game's build_materials.py without its last line, which runs everything."""
    path = os.path.join(SCRIPTS, "build_materials.py")
    source = open(path, encoding="utf-8").read()
    head, _, tail = source.rpartition("main()")
    assert not tail.strip()
    # the one line docs/unreal.md asks of the game, for the season master only (SEASON stays None otherwise)
    line = "        normal_out = rounded_normal(material, normal_out)\n"
    assert head.count(line) == 1
    head = head.replace(line, line + "        colour_out = SEASON(material, colour, colour_out) if SEASON else colour_out\n")
    ns = {"__name__": "game_build_materials", "__file__": path, "SEASON": None}
    exec(compile(head, path, "exec"), ns)
    return ns


def masters(ns):
    _, surface, _, _ = ns["slot_textures"]("bark_debris_01", "bark_debris_01")
    moss = os.path.join(PROJECT, "SourceArt", "ambientCG", "Moss001", "Moss001_diff_2k.jpg")
    surface = dict(surface, ground_moss=ns["import_texture"](moss, f"{ns['SURFACE_ROOT']}/Moss001", "diff"))
    _, foliage, _, _ = ns["slot_textures"]("fern_02", "fern_02")
    ns["build_master"]("M_Surface", False, surface)
    ns["build_master"]("M_Foliage", True, foliage)


def season_master(ns, cfg):
    """M_FoliageSeason: M_Foliage with the live season, and an instance of it for one leaf slot."""
    example = {}
    path = os.path.join(JOB["here"], "season_example.py")
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), example)
    example["make_collection"](float(cfg.get("day", 200.0)))
    ns["SEASON"] = lambda material, colour, colour_out: example["season_colour"](material, colour, colour_out, cfg)
    _, foliage, _, _ = ns["slot_textures"]("fern_02", "fern_02")
    ns["build_master"]("M_FoliageSeason", True, foliage)
    ns["SEASON"] = None


def season_instances(ns, cfg):
    master = unreal.load_asset(f"{ns['MATERIAL_ROOT']}/M_FoliageSeason")
    for asset, slot in cfg["slots"]:
        old = unreal.load_asset(f"/Game/World/PolyHaven/{asset}/Mat/MI_{slot}")
        textures = {k: mel.get_material_instance_texture_parameter_value(old, k) for k in ("BaseColor", "Normal", "Roughness")}
        ns["make_instance"](f"MI_{slot}_season", f"/Game/World/PolyHaven/{asset}/Mat", master, textures, {"OpacityFromColourAlpha": True},
                            {k: mel.get_material_instance_scalar_parameter_value(old, k) for k in ("WindHeightCm", "WindIntensity", "WindSpeed")})


def scan_bark(cfg):
    """Our wood under the game's own scan: our bake keeps the rough base, and above it the scan wraps
    round each part on UV1 (M_Surface's UpperBark).  New instances; the bake's stay as they are."""
    asset, source = cfg["asset"], cfg["scan_asset"]
    tex = f"/Game/World/PolyHaven/{source}/Tex/{source}_bark"
    surface = unreal.load_asset("/Game/World/Materials/M_Surface")
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for slot, start, blend in cfg["slots"]:
        folder = f"/Game/World/PolyHaven/{asset}/Mat"
        name = f"MI_{slot}_scan"
        if eal.does_asset_exist(f"{folder}/{name}"):
            eal.delete_asset(f"{folder}/{name}")
        old = unreal.load_asset(f"{folder}/MI_{slot}")
        mi = tools.create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, surface)
        for param in ("BaseColor", "Normal", "Roughness"):
            mel.set_material_instance_texture_parameter_value(mi, param, mel.get_material_instance_texture_parameter_value(old, param))
        for param, kind in (("BarkColor", "diff"), ("BarkNormal", "nor_gl"), ("BarkRoughness", "rough")):
            mel.set_material_instance_texture_parameter_value(mi, param, unreal.load_asset(f"{tex}_{kind}_2k"))
        mel.set_material_instance_static_switch_parameter_value(mi, "UpperBark", True)
        for param, value in (("BarkStartCm", start), ("BarkBlendCm", blend), ("BarkGain", cfg["bark_gain"]), ("WindHeightCm", cfg["wind"][0]), ("WindIntensity", cfg["wind"][1]), ("WindSpeed", cfg["wind"][2])):
            mel.set_material_instance_scalar_parameter_value(mi, param, float(value))
        mel.update_material_instance(mi)
        eal.save_asset(f"{folder}/{name}", only_if_is_dirty=False)


def through_gain(gain):
    """On the test project's copy of M_Foliage only: the share of a leaf's colour that light takes passing
    through it, for showing what docs/unreal.md's addition 7 would do.  The game's script fixes it at 0.25."""
    path = "/Game/World/Materials/M_Foliage"
    material = unreal.load_asset(path)
    node = unreal.MaterialEditingLibrary.get_material_property_input_node(material, unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    node.set_editor_property("const_b", float(gain))
    unreal.MaterialEditingLibrary.recompile_material(material)
    eal.save_asset(path, only_if_is_dirty=False)


def static_displacement(cfg):
    """Epic's build-time alternative to relief in the mesh, for comparing: Nanite Static Displacement
    Mapping, driven by a height map on one material slot."""
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", cfg["height_file"])
    task.set_editor_property("destination_path", "/Game/T")
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    name = os.path.splitext(os.path.basename(cfg["height_file"]))[0]
    tex = unreal.load_asset(f"/Game/T/{name}")
    tex.set_editor_property("srgb", False)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_WRAP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    eal.save_asset(f"/Game/T/{name}", only_if_is_dirty=False)
    mesh = unreal.load_asset(cfg["mesh"])
    nanite = mesh.get_editor_property("nanite_settings")
    entry = unreal.MeshDisplacementMap()
    entry.set_editor_property("texture", tex)
    entry.set_editor_property("magnitude", float(cfg["magnitude_cm"]))
    entry.set_editor_property("center", float(cfg["center"]))
    nanite.set_editor_property("displacement_uv_channel", 0)
    nanite.set_editor_property("displacement_maps", [entry])
    nanite.set_editor_property("trim_relative_error", float(cfg["trim"]))
    mesh.set_editor_property("nanite_settings", nanite)
    eal.save_asset(cfg["mesh"], only_if_is_dirty=False)


def import_files(files):
    # The game's import script reads <prefix>_FILES and <prefix>_FINISH; set CAMBIUM_GAME_ENV_PREFIX to its prefix.
    prefix = os.environ.get("CAMBIUM_GAME_ENV_PREFIX", "GAME")
    os.environ[prefix + "_FILES"] = ";".join(files)
    os.environ.pop(prefix + "_FINISH", None)
    path = os.path.join(SCRIPTS, "import_world_assets.py")
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), {"__name__": "game_import_world_assets", "__file__": path})


def looks(asset, cfg):
    """As the game's set_tree_looks.py does for its birch; ``cfg`` per slot ending."""
    for path in eal.list_assets(f"/Game/World/PolyHaven/{asset}", recursive=True, include_folder=False):
        if str(eal.find_asset_data(path).asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        path = path.split(".")[0]
        name = path.rsplit("/", 1)[-1].lower()
        instance = unreal.load_asset(path)
        for ending, values in cfg.items():
            if ending not in name:
                continue
            for param, value in values.items():
                if isinstance(value, list):
                    mel.set_material_instance_vector_parameter_value(instance, param, unreal.LinearColor(*value))
                else:
                    mel.set_material_instance_scalar_parameter_value(instance, param, float(value))
        mel.update_material_instance(instance)
        eal.save_asset(path, only_if_is_dirty=False)


def read_material(m):
    d = {"name": m.get_name(), "class": m.get_class().get_name()}
    try:
        parent = m.get_editor_property("parent")
        d["parent"] = parent.get_path_name() if parent else None
        tex = {}
        for n in mel.get_texture_parameter_names(m):
            v = mel.get_material_instance_texture_parameter_value(m, n)
            tex[str(n)] = v.get_name() if v else None
        d["textures"] = {k: v for k, v in tex.items() if k in ("BaseColor", "Normal", "Roughness", "Opacity")}
        d["switches"] = {str(n): bool(mel.get_material_instance_static_switch_parameter_value(m, n)) for n in mel.get_static_switch_parameter_names(m)}
        d["scalars"] = {str(n): round(mel.get_material_instance_scalar_parameter_value(m, n), 4) for n in mel.get_scalar_parameter_names(m)
                        if str(n) in ("ColourGain", "WindIntensity", "WindHeightCm", "WindSpeed", "PlantKitWind", "BranchSway", "FlutterGain", "BarkStartCm", "BarkBlendCm")}
    except Exception as error:
        d["error"] = str(error)
    return d


def read_mesh(path):
    m = unreal.load_asset(path)
    box = m.get_bounding_box()
    lib = unreal.EditorStaticMeshLibrary        # no editor subsystems in a commandlet
    nanite = m.get_editor_property("nanite_settings")
    # a Nanite mesh's render data is its fallback: its triangles, here, are the fallback's
    return {"name": m.get_name(), "source": sample_mesh(m, int(JOB.get("vertex_sample", 20000)), ("source",))["source"], "triangles": m.get_num_triangles(0), "lods": m.get_num_lods(), "sections": m.get_num_sections(0), "vertices": lib.get_number_verts(m, 0),
            "uv_channels": lib.get_num_uv_channels(m, 0), "has_vertex_colours": lib.has_vertex_colors(m),
            "bounds_cm": {"min": [round(box.min.x, 1), round(box.min.y, 1), round(box.min.z, 1)], "max": [round(box.max.x, 1), round(box.max.y, 1), round(box.max.z, 1)]},
            "nanite": {"enabled": bool(nanite.get_editor_property("enabled")), "shape": str(nanite.get_editor_property("shape_preservation"))},
            "slots": [{"slot": str(s.get_editor_property("material_slot_name")), "material": read_material(s.get_editor_property("material_interface")) if s.get_editor_property("material_interface") else None}
                      for s in m.get_editor_property("static_materials")]}


def main():
    ns = load_materials()
    step("the game's script loaded")
    if JOB.get("masters"):
        masters(ns)
        step("masters", materials=[p.split(".")[0] for p in eal.list_assets("/Game/World/Materials", recursive=False, include_folder=False)])
    for f in JOB.get("files", []):
        try:
            import_files([f])
            step("imported", file=os.path.basename(f))
        except Exception as error:
            step("imported", ok=False, file=os.path.basename(f), error=str(error), trace=traceback.format_exc()[-800:])
        unreal.SystemLibrary.collect_garbage()
    for asset, wind in JOB.get("instances", {}).items():
        ns["WIND"][asset] = tuple(wind)
        # a voxel build takes 7-11 GB, by the game's own note: only when the job asks for it, by "voxelize"
        ns["NANITE_SHAPE"].pop(asset, None)
        count = ns["instances_stage"]([asset])
        step("instances", asset=asset, count=count, problems=list(ns.get("problems", []))[:20])
    for asset, cfg in JOB.get("looks", {}).items():
        looks(asset, cfg)
        step("looks", asset=asset)
    if JOB.get("season"):
        season_master(ns, JOB["season"])
        season_instances(ns, JOB["season"])
        step("season master", problems=list(ns.get("problems", []))[:20])
    if JOB.get("scan_bark"):
        scan_bark(JOB["scan_bark"])
        step("our wood under the scan")
    if "through_gain" in JOB:
        through_gain(JOB["through_gain"])
        step("through gain", gain=JOB["through_gain"])
    if JOB.get("static_displacement"):
        static_displacement(JOB["static_displacement"])
        step("static displacement")
    for asset, voxel in JOB.get("voxelize", {}).items():
        for name in voxel:
            path = f"/Game/World/PolyHaven/{asset}/{name}"
            mesh = unreal.load_asset(path)
            nanite = mesh.get_editor_property("nanite_settings")
            nanite.set_editor_property("shape_preservation", unreal.NaniteShapePreservation.VOXELIZE)
            mesh.set_editor_property("nanite_settings", nanite)
            eal.save_asset(path, only_if_is_dirty=False)
            step("voxelized", mesh=name)
            del mesh
            unreal.SystemLibrary.collect_garbage()
    for asset in JOB.get("read", []):
        for p in eal.list_assets(f"/Game/World/PolyHaven/{asset}", recursive=False, include_folder=False):
            if str(eal.find_asset_data(p).asset_class_path.asset_name) == "StaticMesh" and (not JOB.get("read_only") or p.split(".")[0].rsplit("/", 1)[-1] in JOB["read_only"]):
                report["imports"].append(read_mesh(p.split(".")[0]))
                step("read", mesh=p.split(".")[0].rsplit("/", 1)[-1])
                unreal.SystemLibrary.collect_garbage()
    # what the engine's own build came to, from the saved assets, without loading a mesh
    for path in JOB.get("asset_tags", []):
        data = eal.find_asset_data(path)
        step("asset tags", mesh=path.rsplit("/", 1)[-1], **{tag: str(data.get_tag_value(tag)) for tag in ("Triangles", "Vertices", "NaniteTriangles", "NaniteVertices")})
    log("done")


try:
    main()
except Exception as error:
    step("stopped", ok=False, error=str(error), trace=traceback.format_exc()[-1500:])
