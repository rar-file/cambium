"""Inside Unreal: import tree files as a game's script would, and read back what survived.

Runs under tools/unreal_test.py, in the test project only.  The job file names what to import:
    {"imports": [{"file": ..., "dest": "/Game/Test/x", "name": "x", "combine": true, "nanite": false,
                  "materials": true, "voxelize": false}], "vertex_sample": 200000}
Writes a JSON report: per mesh triangles, vertices, sections, UV channels, sampled UV and vertex colour
values, bounds, Nanite settings; per material its parent, blend mode, two-sidedness and textures; per
texture its size, format and colour space.
"""
import json
import os
import sys
import traceback

import unreal

JOB = json.load(open(os.environ["TREEGEN_UE_JOB"], encoding="utf-8"))
sys.path.insert(0, JOB["here"])
from readback import sample_mesh  # noqa: E402

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
report = {"imports": [], "notes": []}


def log(message):
    unreal.log(f"[treegen] {message}")


def options(item):
    pipeline = unreal.InterchangeGenericAssetsPipeline()
    mesh = pipeline.get_editor_property("mesh_pipeline")
    behaviour = unreal.InterchangeCombineStaticMeshesBehavior.ALL if item.get("combine", True) else unreal.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE
    mesh.set_editor_property("combine_static_meshes_behavior", behaviour)
    mesh.set_editor_property("build_nanite", bool(item.get("nanite", False)))
    if not item.get("materials", True):
        for sub, flag in (("material_pipeline", "import_materials"), ("texture_pipeline", "import_textures")):
            pipeline.get_editor_property(sub).set_editor_property(flag, False)
    stack = unreal.InterchangePipelineStackOverride()
    stack.add_pipeline(pipeline)
    return stack


def do_import(item):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", item["file"])
    task.set_editor_property("destination_path", item["dest"])
    if item.get("name"):
        task.set_editor_property("destination_name", item["name"])
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("options", options(item))
    asset_tools.import_asset_tasks([task])
    return [str(p) for p in task.get_editor_property("imported_object_paths")]


def read_texture(path):
    t = unreal.load_asset(path)
    d = {"path": path, "name": t.get_name(), "srgb": bool(t.get_editor_property("srgb")),
         "compression": str(t.get_editor_property("compression_settings")), "flip_green": bool(t.get_editor_property("flip_green_channel")),
         "wrap_x": str(t.get_editor_property("address_x")), "wrap_y": str(t.get_editor_property("address_y"))}
    try:
        d["size"] = [t.blueprint_get_size_x(), t.blueprint_get_size_y()]
    except Exception as error:
        d["size"] = str(error)
    return d


def read_material(m):
    d = {"name": m.get_name(), "class": m.get_class().get_name()}
    try:
        parent = m.get_editor_property("parent")
        d["parent"] = parent.get_path_name() if parent else None
    except Exception:
        d["parent"] = None
    for prop, key in (("blend_mode", "blend_mode"), ("two_sided", "two_sided"), ("shading_model", "shading_model"), ("opacity_mask_clip_value", "clip")):
        try:
            d[key] = str(m.get_editor_property(prop))
        except Exception:
            pass
    try:
        base = m.get_base_material()
        d["base_material"] = base.get_path_name()
        d["base_blend_mode"] = str(base.get_editor_property("blend_mode"))
        d["base_two_sided"] = str(base.get_editor_property("two_sided"))
        d["base_used_with_nanite"] = str(base.get_editor_property("used_with_nanite"))
        d["base_used_with_voxels"] = str(base.get_editor_property("used_with_voxels"))
    except Exception as error:
        d["base_error"] = str(error)
    mel = unreal.MaterialEditingLibrary
    try:
        names = [str(n) for n in mel.get_texture_parameter_names(m)]
        tex = {}
        for n in names:
            v = mel.get_material_instance_texture_parameter_value(m, n)
            if v:
                tex[n] = v.get_name()
        d["textures"] = tex
        d["scalars"] = {str(n): round(mel.get_material_instance_scalar_parameter_value(m, n), 4) for n in mel.get_scalar_parameter_names(m)
                        if any(k in str(n) for k in ("Cutoff", "Factor", "Opacity", "Transmission"))}
    except Exception as error:
        d["param_error"] = str(error)
    return d


def read_mesh(path, limit):
    m = unreal.load_asset(path)
    box = m.get_bounding_box()
    d = {"path": path, "name": m.get_name(), "lods": m.get_num_lods(), "triangles": m.get_num_triangles(0), "sections": m.get_num_sections(0),
         "bounds_cm": {"min": [box.min.x, box.min.y, box.min.z], "max": [box.max.x, box.max.y, box.max.z]}}
    # no editor subsystems in a commandlet
    lib = unreal.EditorStaticMeshLibrary
    d["vertices"] = lib.get_number_verts(m, 0)
    d["uv_channels"] = lib.get_num_uv_channels(m, 0)
    d["has_vertex_colours"] = lib.has_vertex_colors(m)
    nanite = m.get_editor_property("nanite_settings")
    d["nanite"] = {"enabled": bool(nanite.get_editor_property("enabled"))}
    try:
        d["nanite"]["shape_preservation"] = str(nanite.get_editor_property("shape_preservation"))
    except Exception:
        pass
    slots = []
    for slot in m.get_editor_property("static_materials"):
        mi = slot.get_editor_property("material_interface")
        slots.append({"slot": str(slot.get_editor_property("material_slot_name")), "material": read_material(mi) if mi else None})
    d["slots"] = slots
    if limit:
        d["sampled"] = sample_mesh(m, limit)
    return d


def main():
    limit = int(JOB.get("vertex_sample", 0))
    for item in JOB["imports"]:
        log(f"importing {item['file']}")
        entry = {"item": item}
        try:
            imported = do_import(item)
            entry["imported"] = imported
            classes = {}
            for p in eal.list_assets(item["dest"], recursive=True, include_folder=False):
                cls = str(eal.find_asset_data(p).asset_class_path.asset_name)
                classes.setdefault(cls, []).append(p.split(".")[0])
            entry["asset_classes"] = {k: len(v) for k, v in classes.items()}
            meshes = classes.get("StaticMesh", [])
            for p in meshes:
                if item.get("voxelize"):
                    mesh = unreal.load_asset(p)
                    nanite = mesh.get_editor_property("nanite_settings")
                    nanite.set_editor_property("shape_preservation", unreal.NaniteShapePreservation.VOXELIZE)
                    mesh.set_editor_property("nanite_settings", nanite)
                    eal.save_asset(p, only_if_is_dirty=False)
            entry["meshes"] = [read_mesh(p, limit) for p in meshes]
            entry["textures"] = [read_texture(p) for p in classes.get("Texture2D", [])]
            entry["materials_listed"] = classes.get("MaterialInstanceConstant", []) + classes.get("Material", [])
            log(f"{item['file']}: {entry['asset_classes']}")
        except Exception as error:
            entry["error"] = str(error)
            entry["trace"] = traceback.format_exc()[-1500:]
            log(f"FAILED {item['file']}: {error}")
        report["imports"].append(entry)
        with open(JOB["results"], "w", encoding="utf-8") as f:
            json.dump(report, f, indent=1)
    log("done")


main()
