"""Import Manor_01 and place its modular exterior in the existing settlement.

SHOEN_MANOR_CAPTURE=1 takes the two actual rendered Unreal editor views.
"""
import json
import math
import os
from pathlib import Path
import re
import runpy
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/Manor01"
OUT = ROOT / "artifacts/manor01"
DEST = "/Game/Art/Buildings/Administration/Manor01"
RC_DEST = "/Game/Art/Buildings/Military/RetainerCompound01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
MK_DEST = "/Game/Art/Buildings/Commerce/Market01"
SOURCE_MAP = RC_DEST + "/Review/RetainerCompound01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/Manor01_Settlement"
# The manor fronts the central village lane; existing buildings keep their sites.
COMPOUND_POSITION = (-750.0, 2350.0, 0.0)
COMPOUND_YAW = 180.0
EXPORT_NAMES = (
    "Manor_01", "Manor_MainHall_01", "ManorGate_01", "ManorWall_Straight_01",
    "ManorWall_Corner_01", "ManorSideBuilding_01", "MN01_Veranda",
    "MN01_GardenElements", "MN01_Banners", "MN01_StoneBase", "MN01_Steps",
    "MN01_MainRoof", "ManorWall_Plaster_01", "MN01_GroundApron", "StoneLantern_01",
)
BOX_MODULES = {"ManorWall_Straight_01", "ManorWall_Plaster_01", "MN01_StoneBase", "MN01_Steps"}
# Local metres; only substantial exterior volumes receive collision.
POST_BOXES = {
    "Manor_MainHall_01": [(0, 0, 2.085, 9.3, 5.6, 2.73)],
    "ManorSideBuilding_01": [(0, 0, 1.465, 3.1, 3.7, 2.31)],
    "ManorGate_01": (
        [(x, 0, .17, .52, .58, .34) for x in (-1.72, 1.72)]
        + [(x, 0, 1.605, .28, .30, 2.73) for x in (-1.72, 1.72)]
        + [(x, .785, 1.41, .15, 1.41, 2.34) for x in (-1.72, 1.72)]
    ),
    "ManorWall_Corner_01": [(.5, 0, 1.10, 1.18, .60, 2.20),
                              (0, .5, 1.10, .60, 1.18, 2.20)],
}
report = {"asset": "Manor01", "imported": False}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def asset(path):
    value = u.load_asset(path)
    require(value is not None, "Missing asset: " + path)
    return value


def map_filename(path):
    return str(Path(u.Paths.project_content_dir()) / (path.removeprefix("/Game/") + ".umap"))


def write_report(name, payload):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, indent=2) + "\n")


def instances_from(path):
    assembly = json.loads(path.read_text())
    return assembly["instances"] if isinstance(assembly, dict) else assembly


def import_mesh(name, materials):
    source = ART / "Exports" / (name + ".fbx")
    require(source.is_file(), "Missing FBX: " + str(source))
    options = u.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_as_skeletal = False
    options.mesh_type_to_import = u.FBXImportType.FBXIT_STATIC_MESH
    options.import_mesh = True
    options.import_animations = False
    options.import_materials = False
    options.import_textures = False
    options.create_physics_asset = False
    data = options.static_mesh_import_data
    for key, value in {"convert_scene": False, "convert_scene_unit": True,
                       "force_front_x_axis": False, "combine_meshes": True,
                       "auto_generate_collision": False, "generate_lightmap_u_vs": False}.items():
        data.set_editor_property(key, value)
    data.normal_import_method = u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    data.vertex_color_import_option = u.VertexColorImportOption.REPLACE
    task = u.AssetImportTask()
    for key, value in {"filename": str(source), "destination_path": DEST,
                       "destination_name": "SM_" + name, "automated": True,
                       "replace_existing": True, "replace_existing_settings": True,
                       "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    require(task.imported_object_paths, "FBX import failed: " + name)
    mesh = asset(DEST + "/SM_" + name)
    slots = [str(item.get_editor_property("material_slot_name"))
             for item in mesh.get_editor_property("static_materials")]
    base_slots = [re.sub(r"[._]\d{3}$", "", slot) for slot in slots]
    require(slots and all(slot in materials for slot in base_slots), "Unexpected slots: " + repr(slots))
    for index, slot in enumerate(base_slots):
        mesh.set_material(index, materials[slot])
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    require(editor.remove_collisions(mesh), "Could not clear collision: " + name)
    collision = "none"
    if name in BOX_MODULES or name in POST_BOXES:
        require(editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX) >= 0,
                "Could not create simple collision: " + name)
        collision = "box"
    if name in POST_BOXES:
        body = mesh.get_editor_property("body_setup")
        geometry = body.get_editor_property("agg_geom")
        box_type = type(geometry.get_editor_property("box_elems")[0])
        boxes = []
        for x, y, z, width, depth, height in POST_BOXES[name]:
            box = box_type()
            box.set_editor_property("center", u.Vector(x * 100, -y * 100, z * 100))
            box.set_editor_property("rotation", u.Rotator())
            for key, value in (("x", width), ("y", depth), ("z", height)):
                box.set_editor_property(key, value * 100)
            boxes.append(box)
        geometry.set_editor_property("box_elems", boxes)
        body.set_editor_property("agg_geom", geometry)
        collision = str(len(boxes)) + " simple exterior boxes; porch and open gaps clear"
    require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), "Could not save " + name)
    bounds = mesh.get_bounds()
    report.setdefault("meshes", []).append({
        "asset": mesh.get_path_name(), "source": str(source), "material_slots": slots,
        "simple_collision": collision, "bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
        "bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]})
    return mesh


def main():
    # Preserve the earlier Retainer source. Its current import already strips
    # Blender's duplicated material suffixes and completes the existing context.
    source_map = SOURCE_MAP
    if not Path(map_filename(source_map)).is_file():
        try:
            runpy.run_path(str(ROOT / "SourceArt/Buildings/RetainerCompound01/Scripts/import_unreal.py"))
        except Exception:
            report["context_warning"] = traceback.format_exc()
            u.log_warning("Existing Retainer import failed; keeping the Market settlement context: "
                          + report["context_warning"])
            source_map = MK_DEST + "/Review/Market01_Settlement"
    if not Path(map_filename(source_map)).is_file():
        report.setdefault("context_warning", "Retainer import did not produce its settlement map")
        u.log_warning(report["context_warning"])
        source_map = MK_DEST + "/Review/Market01_Settlement"
    require(Path(map_filename(source_map)).is_file(), "Missing existing settlement context")
    materials = {"SH01_" + family: asset(SH_DEST + "/M_SH01_" + family)
                 for family in ("Thatch", "Timber", "Plaster", "Stone", "Iron")}
    materials["RH01_Rope"] = asset(SH_DEST + "/M_SH01_Rope")
    materials["FC01_Dirt"] = (u.load_asset(RC_DEST + "/M_RC01_Dirt")
        or asset("/Game/Art/Buildings/Agriculture/FarmCompound01/M_FC01_Dirt"))
    for family in ("Cloth", "Ink", "Leaf"):
        materials["MK01_" + family] = asset(MK_DEST + "/M_MK01_" + family)
    instances = instances_from(ART / "Exports/assembly.json")
    names = set(EXPORT_NAMES) | {item["mesh"] for item in instances}
    meshes = {name: import_mesh(name, materials) for name in sorted(names)}
    # Manor_01 is the combined reusable asset. Render the modular assembly once.
    instances = [item for item in instances if item["mesh"] != "Manor_01"]
    require(instances, "Manor assembly contains no modular pieces")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(source_map))
    require(world is not None, "Could not load the existing settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for previous in list(actors.get_all_level_actors()):
        if previous.actor_has_tag("Manor01"):
            actors.destroy_actor(previous)
    angle = math.radians(COMPOUND_YAW)
    cosine, sine = math.cos(angle), math.sin(angle)
    for item in instances:
        x, y, z = item["location"]
        local_x, local_y = x * 100, -y * 100
        position = (COMPOUND_POSITION[0] + local_x * cosine - local_y * sine,
                    COMPOUND_POSITION[1] + local_x * sine + local_y * cosine,
                    COMPOUND_POSITION[2] + z * 100)
        yaw = COMPOUND_YAW - item.get("rotation_degrees", 0)
        actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*position),
                                             u.Rotator(pitch=0, yaw=yaw, roll=0))
        require(actor is not None, "Could not place " + item["name"])
        actor.set_actor_label("Manor_01 - " + item["name"])
        actor.set_folder_path("SettlementArt/Manor01")
        actor.tags = [u.Name("Manor01"), u.Name("SettlementArt")]
        actor.set_actor_scale3d(u.Vector(*item.get("scale", [1, 1, 1])))
        component = actor.static_mesh_component
        component.set_mobility(u.ComponentMobility.STATIC)
        component.set_static_mesh(meshes[item["mesh"]])
        collision = item["mesh"] in BOX_MODULES or item["mesh"] in POST_BOXES
        component.set_collision_profile_name("BlockAllDynamic")
        component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY if collision else u.CollisionEnabled.NO_COLLISION)
        report.setdefault("placements", []).append({"name": item["name"], "mesh": item["mesh"],
                                                    "position_cm": position, "yaw": yaw})
    # Reposition the existing non-gameplay scale reference next to the entrance.
    for placed in actors.get_all_level_actors():
        if placed.actor_has_tag("RuralHouse01ScaleFigure"):
            placed.set_actor_location(u.Vector(COMPOUND_POSITION[0] + 230, COMPOUND_POSITION[1] - 830, 0), False, False)
    actors.clear_actor_selection_set()
    camera, target = u.Vector(-3100, -250, 1700), u.Vector(-750, 2370, 220)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(
        camera, u.MathLibrary.find_look_at_rotation(camera, target))
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save manor settlement")
    report.update(imported=True, map=SETTLEMENT_MAP, source_map=source_map,
                  position_cm=COMPOUND_POSITION, yaw=COMPOUND_YAW,
                  assembly_policy="Modular pieces placed once; combined Manor_01 retained as reusable asset")
    write_report("unreal-import.json", report)
    u.log("MANOR_01_IMPORTED " + SETTLEMENT_MAP)


def review_scene():
    require("-nullrhi" not in u.SystemLibrary.get_command_line().lower(), "Review needs rendering")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Missing manor settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for existing in actors.get_all_level_actors():
        if isinstance(existing, (u.DirectionalLight, u.SkyLight)):
            existing.light_component.set_visibility(False)
    # The gameplay scene creates these at BeginPlay; editor review needs temporary
    # equivalents. Nothing below is saved into this map or the existing settlement.
    ground = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -9), u.Rotator())
    ground.set_actor_label("Manor review - temporary terrain")
    ground.static_mesh_component.set_static_mesh(asset("/Engine/BasicShapes/Cube"))
    ground.static_mesh_component.set_material(0, asset("/Game/Art/Buildings/Craft/Smithy01/M_SM01_ReviewEarth"))
    ground.set_actor_scale3d(u.Vector(1500, 1500, .15))
    key = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 1500),
                                       u.Rotator(pitch=-42, yaw=-35, roll=0))
    key.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    key.light_component.set_intensity(2.4)
    key.light_component.set_editor_property("atmosphere_sun_light", True)
    atmosphere = actors.spawn_actor_from_class(u.SkyAtmosphere, u.Vector(), u.Rotator())
    key.light_component.set_editor_property("dynamic_shadow_distance_movable_light", 10000.)
    key.light_component.set_editor_property("dynamic_shadow_cascades", 4)
    sky = actors.spawn_actor_from_class(u.SkyLight, u.Vector(), u.Rotator())
    sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type", u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_cubemap(asset("/Engine/MapTemplates/Sky/DaylightAmbientCubemap"))
    sky.light_component.set_intensity(1.05)
    fill = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 1000),
                                        u.Rotator(pitch=-26, yaw=135, roll=0))
    fill.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    fill.light_component.set_intensity(.42)
    fill.light_component.set_editor_property("cast_shadows", False)

    views = (("three-quarter", (-3000, -650, 1220), (-750, 2370, 240), 40.),
             ("settlement", (-4300, -5000, 6200), (-150, 900, 120), 50.))
    cameras = {}
    for name, location, target, fov in views:
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location),
            u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*target)))
        camera.set_actor_label("Manor review - " + name)
        camera.camera_component.set_field_of_view(fov)
        camera.camera_component.set_editor_property("aspect_ratio", 20. / 13.)
        exposure = camera.camera_component.get_editor_property("post_process_settings")
        for prop, value in (("override_auto_exposure_method", True),
                            ("auto_exposure_method", u.AutoExposureMethod.AEM_MANUAL),
                            ("override_auto_exposure_apply_physical_camera_exposure", True),
                            ("auto_exposure_apply_physical_camera_exposure", False),
                            ("override_auto_exposure_bias", True), ("auto_exposure_bias", 1.2)):
            exposure.set_editor_property(prop, value)
        camera.camera_component.set_editor_property("post_process_settings", exposure)
        camera.camera_component.set_editor_property("post_process_blend_weight", 1.)
        cameras[name] = camera
    actors.clear_actor_selection_set()
    u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    u.EditorPythonScripting.set_keep_python_script_alive(True)
    return views, cameras


def show():
    views, cameras = review_scene()
    camera = cameras["three-quarter"]
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(
        camera.get_actor_location(), camera.get_actor_rotation())
    u.get_editor_subsystem(u.LevelEditorSubsystem).pilot_level_actor(camera)
    u.log("MANOR_01_VIEW_READY " + SETTLEMENT_MAP)


def capture():
    views, cameras = review_scene()
    OUT.mkdir(parents=True, exist_ok=True)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6,
             "start": time.monotonic(), "results": []}

    def tick(_delta):
        try:
            require(time.monotonic() - state["start"] < 120, "Manor screenshot timed out")
            if state["task"] is not None:
                if not state["task"].is_task_done():
                    return
                name = views[state["index"]][0]
                path = OUT / ("unreal-" + name + ".png")
                require(path.is_file() and path.stat().st_size > 0, "Missing screenshot " + str(path))
                state["results"].append(str(path))
                state.update(task=None, index=state["index"] + 1, next=time.monotonic() + 3)
            if state["index"] == len(views):
                u.unregister_slate_post_tick_callback(state["handle"])
                write_report("capture.json", {"rendered": True, "map": SETTLEMENT_MAP,
                    "mode": "Metal editor; existing settlement layout; temporary review lighting",
                    "captures": state["results"]})
                u.SystemLibrary.quit_editor()
                return
            if time.monotonic() >= state["next"]:
                name = views[state["index"]][0]
                path = OUT / ("unreal-" + name + ".png")
                if path.exists():
                    path.unlink()
                state["task"] = u.AutomationLibrary.take_high_res_screenshot(
                    2000, 1300, str(path), camera=cameras[name], delay=1.)
                require(state["task"] is not None and state["task"].is_valid_task(), "Screenshot request failed")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            write_report("capture.json", {"rendered": False, "error": traceback.format_exc()})
            u.log_error(traceback.format_exc())
            u.SystemLibrary.quit_editor()
    state["handle"] = u.register_slate_post_tick_callback(tick)


try:
    if os.environ.get("SHOEN_MANOR_VIEW") == "1":
        show()
    elif os.environ.get("SHOEN_MANOR_CAPTURE") == "1":
        capture()
    else:
        main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report("unreal-import.json", report)
    raise
