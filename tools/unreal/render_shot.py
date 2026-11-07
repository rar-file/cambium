"""Inside Unreal: stand trees on a plain ground in sunlight and take pictures of them.

Runs under ``tools/unreal_test.py render``.  The light copies the game's sky actor (AWorldClock): the sun
at 120,000 lux and 0.53 degrees wide, a sky atmosphere, a sky light (empty here: see "fill_lux"), thin fog, Lumen and
virtual shadow maps from the project's settings.  No clouds, no moving time, a fixed exposure, and none
of the game's world around the tree; the report says so.

The job names ``actors`` (id, mesh, at, yaw, scale, seat_sink_m), ``shots`` (name, at, look_at, fov, and
what to change first: set_mesh, set_material, mpc, dynamic_mesh), ``sun`` (pitch, yaw, lux), ``ev100``,
``size``, ``ground`` (a colour map, or none), ``warmup``, ``warmup_seconds`` and ``out``.
"""
import json
import os
import time
import traceback

import unreal

JOB = json.load(open(os.environ["TREEGEN_UE_JOB"], encoding="utf-8"))
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
# editor subsystems can be missing in a commandlet; the older library does the same work
level_lib = unreal.EditorLevelLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem) or level_lib
report = {"shots": [], "actors": [], "notes": []}


def log(message):
    unreal.log(f"[treegen] {message}")


def save():
    with open(JOB["results"], "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)


def vec(v):
    return unreal.Vector(float(v[0]), float(v[1]), float(v[2]))


def spawn(cls, at=(0, 0, 0), rot=(0, 0, 0)):
    return actors.spawn_actor_from_class(cls, vec(at), unreal.Rotator(pitch=float(rot[0]), yaw=float(rot[1]), roll=float(rot[2])))


def ground_material(path):
    """The ground's colour map repeating by world position, so any plane is the same."""
    name = "M_TestGround"
    folder = "/Game/T"
    full = f"{folder}/{name}"
    if eal.does_asset_exist(full):
        return unreal.load_asset(full)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    world = mel.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -800, 0)
    mask = mel.create_material_expression(material, unreal.MaterialExpressionComponentMask, -600, 0)
    for k, v in (("r", True), ("g", True), ("b", False), ("a", False)):
        mask.set_editor_property(k, v)
    mel.connect_material_expressions(world, "", mask, "")
    div = mel.create_material_expression(material, unreal.MaterialExpressionDivide, -400, 0)
    div.set_editor_property("const_b", float(JOB.get("ground_tile_cm", 200.0)))
    mel.connect_material_expressions(mask, "", div, "A")
    if path:
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", path)
        task.set_editor_property("destination_path", folder)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("replace_existing", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = unreal.load_asset(f"{folder}/{os.path.splitext(os.path.basename(path))[0]}")
        sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -200, 0)
        sample.set_editor_property("texture", texture)
        mel.connect_material_expressions(div, "", sample, "UVs")
        gain = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, 0, 0)
        gain.set_editor_property("const_b", float(JOB.get("ground_gain", 0.45)))
        mel.connect_material_expressions(sample, "RGB", gain, "A")
        mel.connect_material_property(gain, "", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        colour = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -200, 0)
        colour.set_editor_property("constant", unreal.LinearColor(0.09, 0.08, 0.05, 1.0))
        mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -200, 300)
    rough.set_editor_property("r", 0.9)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    eal.save_asset(full, only_if_is_dirty=False)
    return material


def build_scene():
    unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    sun_cfg = JOB.get("sun", {})
    sun = spawn(unreal.DirectionalLight, (0, 0, 2000), (float(sun_cfg.get("pitch", -45.0)), float(sun_cfg.get("yaw", 135.0)), 0.0))
    light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    light.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_editor_property("intensity", float(sun_cfg.get("lux", 120000.0)))
    light.set_editor_property("atmosphere_sun_light", True)
    light.set_editor_property("light_source_angle", 0.53)
    light.set_editor_property("contact_shadow_length", 30.0)
    light.set_editor_property("contact_shadow_length_in_ws", True)
    spawn(unreal.SkyAtmosphere)
    sky = spawn(unreal.SkyLight)
    skyc = sky.get_component_by_class(unreal.SkyLightComponent)
    skyc.set_editor_property("real_time_capture", bool(JOB.get("real_time_sky", True)))
    skyc.set_mobility(unreal.ComponentMobility.MOVABLE)
    # the renderer takes these when the light registers; a commandlet doesn't tick, so make it register again
    skyc.set_visibility(False)
    skyc.set_visibility(True)
    # A scene capture can't update a real-time sky light (ReflectionEnvironmentRealTimeCapture.cpp,
    # AllocateAndCaptureFrameSkyEnvMap), and these pictures are only scene captures, so their shade has no
    # sky in it.  "fill_lux": stand-ins for what's missing, shadowless light straight down and straight up, lux
    for lux, pitch in zip(JOB.get("fill_lux", ()), (-90.0, 90.0)):
        fill = spawn(unreal.DirectionalLight, (0, 0, 2000), (pitch, 0.0, 0.0))
        lc = fill.get_component_by_class(unreal.DirectionalLightComponent)
        lc.set_mobility(unreal.ComponentMobility.MOVABLE)
        lc.set_editor_property("intensity", float(lux))
        lc.set_editor_property("cast_shadows", False)
        lc.set_editor_property("atmosphere_sun_light", False)
        lc.set_editor_property("forward_shading_priority", 1 if pitch < 0.0 else 2)
    fog = spawn(unreal.ExponentialHeightFog)
    fogc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fogc.set_editor_property("fog_density", 0.003)
    fogc.set_editor_property("fog_height_falloff", 0.2)
    plane = spawn(unreal.StaticMeshActor)
    smc = plane.static_mesh_component
    smc.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane.Plane"))
    smc.set_world_scale3d(vec((800.0, 800.0, 1.0)))
    smc.set_material(0, ground_material(JOB.get("ground")))
    return sky


PLACED = {}


def place_trees():
    for a in JOB["actors"]:
        mesh = unreal.load_asset(a["mesh"])
        if mesh is None:
            report["notes"].append(f"no mesh {a['mesh']}")
            continue
        at = list(a.get("at", (0, 0, 0)))
        box = mesh.get_bounding_box()
        if a.get("seat_sink_m") is not None:
            # as the game seats a tree: its lowest point at the ground, less the rule's sink
            at[2] += -box.min.z - float(a["seat_sink_m"]) * 100.0
        actor = spawn(unreal.StaticMeshActor, at, (0, float(a.get("yaw", 0.0)), 0))
        smc = actor.static_mesh_component
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        smc.set_static_mesh(mesh)
        if a.get("scale"):
            smc.set_world_scale3d(vec((a["scale"], a["scale"], a["scale"])))
        PLACED[a["id"]] = smc
        report["actors"].append({"id": a["id"], "mesh": a["mesh"], "triangles": mesh.get_num_triangles(0), "bounds_z_cm": [box.min.z, box.max.z],
                                 "materials": [m.get_name() if m else None for m in smc.get_materials()]})
    save()


def capture_rig(world, w, h):
    rt = unreal.RenderingLibrary.create_render_target2d(world, int(w), int(h), unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB, unreal.LinearColor(0, 0, 0, 1), False)
    actor = spawn(unreal.SceneCapture2D)
    c = actor.capture_component2d
    c.set_editor_property("texture_target", rt)
    c.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    c.set_editor_property("capture_every_frame", False)
    c.set_editor_property("capture_on_movement", False)
    c.set_editor_property("always_persist_rendering_state", True)
    pp = c.get_editor_property("post_process_settings")
    ev = float(JOB.get("ev100", 14.0))
    for key, value in (("override_auto_exposure_method", True), ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL), ("override_auto_exposure_apply_physical_camera_exposure", True),
                       ("auto_exposure_apply_physical_camera_exposure", True), ("override_camera_iso", True), ("camera_iso", 100.0), ("override_camera_shutter_speed", True),
                       ("camera_shutter_speed", 2.0 ** ev / 16.0 ** 2 * 1.0), ("override_depth_of_field_fstop", True), ("depth_of_field_fstop", 16.0), ("override_motion_blur_amount", True), ("motion_blur_amount", 0.0)):
        pp.set_editor_property(key, value)
    c.set_editor_property("post_process_settings", pp)
    c.set_editor_property("post_process_blend_weight", 1.0)
    return actor, c, rt


def before_shot(world, shot):
    """What a game would change while it runs: a tree's whole mesh, a slot's material, the day."""
    for change in shot.get("set_mesh", []):
        t0 = time.time()
        PLACED[change["actor"]].set_static_mesh(unreal.load_asset(change["mesh"]))
        report.setdefault("swaps", []).append({"to": change["mesh"], "seconds": round(time.time() - t0, 3)})
    for change in shot.get("set_material", []):
        smc = PLACED[change["actor"]]
        material = unreal.load_asset(change["material"])
        for i, m in enumerate(smc.get_materials()):
            if m is not None and change["slot_has"] in m.get_name():
                smc.set_material(i, material)
    for change in shot.get("mpc", []):
        unreal.MaterialLibrary.set_scalar_parameter_value(world, unreal.load_asset(change["path"]), change["name"], float(change["value"]))
    for change in shot.get("dynamic_mesh", []):
        t0 = time.time()
        actor = spawn(unreal.DynamicMeshActor, change.get("at", (0, 0, 0)))
        comp = actor.get_component_by_class(unreal.DynamicMeshComponent)
        opts = unreal.GeometryScriptCopyMeshFromAssetOptions()
        lod = unreal.GeometryScriptMeshReadLOD()
        lod.set_editor_property("lod_type", unreal.GeometryScriptLODType.SOURCE_MODEL)
        mesh = unreal.load_asset(change["mesh"])
        unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh, comp.get_dynamic_mesh(), opts, lod)
        mats = [s_.get_editor_property("material_interface") for s_ in mesh.get_editor_property("static_materials")]
        comp.configure_material_set(mats)
        report.setdefault("dynamic_meshes", []).append({"from": change["mesh"], "seconds": round(time.time() - t0, 3), "triangles": comp.get_dynamic_mesh().get_triangle_count()})
    save()


def look_at(frm, to):
    return unreal.MathLibrary.find_look_at_rotation(vec(frm), vec(to))


class Run:
    """One step per engine tick.  Streaming (Nanite pages, mips), the sky light's capture and Lumen's
    history all need real frames, which a commandlet never has: this runs in the editor with no window,
    and draws while it ticks."""

    def __init__(self):
        self.step = self.start
        self.busy = False
        self.handle = None
        self.left = list(JOB["shots"])
        self.done = False
        self.t0 = time.time()

    def tick(self, _delta):
        # a slow step can tick the editor again from inside it
        if self.done or self.busy:
            return
        self.busy = True
        try:
            self.step()
        except Exception as error:
            report["error"] = str(error)
            report["trace"] = traceback.format_exc()[-1500:]
            self.finish()
        self.busy = False

    def finish(self):
        self.done = True
        save()
        log("done")
        if self.handle is not None:
            unreal.unregister_slate_post_tick_callback(self.handle)
        unreal.SystemLibrary.quit_editor()

    def start(self):
        build_scene()
        place_trees()
        self.world = (unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem) or level_lib).get_editor_world()
        report["world"] = str(self.world)
        os.makedirs(JOB["out"], exist_ok=True)
        w0, h0 = JOB.get("size", (1600, 1000))
        self.actor, self.c, self.rt = capture_rig(self.world, w0, h0)
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        log("scene ready")
        self.step = self.next_shot

    def next_shot(self):
        if not self.left:
            self.finish()
            return
        self.shot = self.left.pop(0)
        before_shot(self.world, self.shot)
        self.actor.set_actor_location_and_rotation(vec(self.shot["at"]), look_at(self.shot["at"], self.shot["look_at"]), False, False)
        self.c.set_editor_property("fov_angle", float(self.shot.get("fov", 50.0)))
        self.frames = 0
        self.t_shot = time.time()
        self.step = self.draw

    def draw(self):
        self.c.capture_scene()
        self.frames += 1
        want, seconds = int(JOB.get("warmup", 120)), float(JOB.get("warmup_seconds", 12.0))
        if self.frames % 30 == 10:
            unreal.AutomationLibrary.finish_loading_before_screenshot()
        if self.frames >= want and time.time() - self.t_shot >= seconds:
            name = self.shot["name"] + ".png"
            unreal.RenderingLibrary.export_render_target(self.world, self.rt, JOB["out"], name)
            report["shots"].append({"name": self.shot["name"], "file": os.path.join(JOB["out"], name), "frames": self.frames, "seconds": round(time.time() - self.t_shot, 1)})
            log(f"shot {self.shot['name']}: {self.frames} frames")
            save()
            self.step = self.next_shot


run = Run()
run.handle = unreal.register_slate_post_tick_callback(run.tick)
