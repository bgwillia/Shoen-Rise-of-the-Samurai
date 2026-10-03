"""Import modular HarborShipyard01 with the established rural FBX workflow.

SHOEN_HARBORSHIPYARD_CAPTURE=1 captures two rendered editor views of its saved map.
SHOEN_HARBORSHIPYARD_VIEW=1 opens that saved map at its exterior review camera.
"""
import json
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/HarborShipyard01"
OUT = ROOT / "artifacts/harborshipyard01"
DEST = "/Game/Art/Buildings/Maritime/HarborShipyard01"
SM_DEST = "/Game/Art/Buildings/Craft/Smithy01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
SOURCE_MAP = "/Game/Art/Buildings/Production/LumberCharcoal01/Review/LumberCharcoal01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/HarborShipyard01_Settlement"
YARD_POSITION = (3200.0, 5600.0, 0.0)
report = {"asset": "HarborShipyard01", "imported": False}


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


def import_mesh(source_name, destination_name, materials, collision=False):
    source = ART / "Exports" / source_name
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
                       "destination_name": destination_name, "automated": True,
                       "replace_existing": True, "replace_existing_settings": True,
                       "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    require(task.imported_object_paths, "FBX import failed: " + source_name)
    mesh = asset(DEST + "/" + destination_name)
    slots = [str(item.get_editor_property("material_slot_name"))
             for item in mesh.get_editor_property("static_materials")]
    require(slots and all(slot in materials for slot in slots), "Unexpected slots: " + repr(slots))
    for index, slot in enumerate(slots):
        mesh.set_material(index, materials[slot])
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    require(editor.remove_collisions(mesh), "Could not clear collision: " + destination_name)
    if collision:
        require(editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX) >= 0,
                "Could not add box collision: " + destination_name)
    require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False),
            "Could not save " + destination_name)
    bounds = mesh.get_bounds()
    report.setdefault("meshes", []).append({
        "asset": mesh.get_path_name(), "source": str(source), "material_slots": slots,
        "simple_collision": "box" if collision else "none", "bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
        "bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]})
    return mesh


def main():
    materials = {"SH01_" + family: asset(SH_DEST + "/M_SH01_" + family)
                 for family in ("Thatch", "Timber", "Plaster", "Stone", "Iron")}
    materials["RH01_Rope"] = asset(SH_DEST + "/M_SH01_Rope")
    materials["SM01_Water"] = asset(SM_DEST + "/M_SM01_Water")
    materials["FC01_Dirt"] = asset("/Game/Art/Buildings/Agriculture/FarmCompound01/M_FC01_Dirt")
    materials["SM01_Charcoal"] = asset(SM_DEST + "/M_SM01_Charcoal")
    assembly = json.loads((ART / "Exports/assembly.json").read_text())
    instances = assembly["instances"] if isinstance(assembly, dict) else assembly
    names = sorted({item["mesh"] for item in instances})
    for extra in ["HS01_CoastalWater", "HS01_CoastalVerge"]:
        names.append(extra)
        instances.append(dict(mesh=extra,name=extra,location=[0,0,0]))
    # Open shelter and pens retain their clear entrances; only solid exterior
    # pieces receive inexpensive query boxes. No gameplay navigation is authored.
    collision_modules = {"HS01_LumberStacks", "HS01_LogPile", "HS01_WorkBench", "Dock_Straight_01", "Dock_End_01", "ShipyardWinch_01", "MooringPost_01", "WorkBoat_01", "Slipway_01"}
    meshes = {name: import_mesh(name + ".fbx", "SM_" + name, materials,
                               collision=name in collision_modules) for name in names}
    import_mesh("HarborShipyard_01.fbx", "SM_HarborShipyard_01", materials, collision=True)
    import_mesh("ShipyardShed_01.fbx", "SM_ShipyardShed_01", materials, collision=True)
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
    require(world is not None, "Could not load existing Manor settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for previous in list(actors.get_all_level_actors()):
        if previous.actor_has_tag("HarborShipyard01"):
            actors.destroy_actor(previous)
    placed_modules = []
    for item in instances:
        x, y, z = item["location"]
        location = (YARD_POSITION[0] + x * 100, YARD_POSITION[1] - y * 100,
                    YARD_POSITION[2] + z * 100)
        yaw = -item.get("rotation_degrees", 0)
        actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*location),
                                             u.Rotator(pitch=0, yaw=yaw, roll=0))
        require(actor is not None, "Could not place " + item["name"])
        actor.set_actor_label("HarborShipyard_01 - " + item["name"])
        actor.set_folder_path("SettlementArt/HarborShipyard_01")
        placed_modules.append(actor)
        actor.tags = [u.Name("HarborShipyard01"), u.Name("SettlementArt")]
        actor.set_actor_scale3d(u.Vector(*item.get("scale", [1, 1, 1])))
        component = actor.static_mesh_component
        component.set_mobility(u.ComponentMobility.STATIC)
        component.set_static_mesh(meshes[item["mesh"]])
        component.set_collision_profile_name("BlockAllDynamic")
        component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY if item["mesh"] in collision_modules
                                        else u.CollisionEnabled.NO_COLLISION)
        report.setdefault("placements", []).append({"name": item["name"], "mesh": item["mesh"],
                                                   "position_cm": location, "yaw": yaw})
    grouping = u.ActorGroupingUtils.get()
    require(grouping is not None, "Missing native actor grouping utility")
    group = grouping.group_actors(placed_modules)
    require(group is not None, "Could not group HarborShipyard_01 modules")
    group.set_actor_label("HarborShipyard_01")
    group.set_folder_path("SettlementArt/HarborShipyard_01")
    group.tags = [u.Name("HarborShipyard01"), u.Name("SettlementArt")]
    actors.clear_actor_selection_set()
    # Simple authored coastline: saved with this separate art review map.
    for label, location, scale, material in [
        ("Harbor coastal land", (0,-2200,-65), (260,164,1.2), asset("/Game/Art/Buildings/Agriculture/FarmCompound01/M_FC01_Dirt")),
        ("Harbor distant sea", (0,16000,-103), (300,200,.10), materials["SM01_Water"])]:
        ground = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*location), u.Rotator())
        ground.set_actor_label(label)
        ground.tags = [u.Name("HarborShipyard01")]
        ground.static_mesh_component.set_static_mesh(asset("/Engine/BasicShapes/Cube"))
        ground.static_mesh_component.set_material(0, material)
        ground.set_actor_scale3d(u.Vector(*scale))
    key = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0,0,1500),u.Rotator(pitch=-42,yaw=-35,roll=0))
    key.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    key.light_component.set_intensity(2.4)
    sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(),u.Rotator())
    sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type",u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_cubemap(asset("/Engine/MapTemplates/Sky/DaylightAmbientCubemap"))
    sky.light_component.set_intensity(.9)
    camera, target = u.Vector(700, 8000, 1150), u.Vector(3200, 5850, 100)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(
        camera, u.MathLibrary.find_look_at_rotation(camera, target))
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save lumber charcoal settlement map")
    report.update(imported=True, map=SETTLEMENT_MAP, source_map=SOURCE_MAP,
                  position_cm=YARD_POSITION, group="HarborShipyard_01")
    write_report("unreal-import.json", report)
    u.log("HARBORSHIPYARD_YARD_01_IMPORTED " + SETTLEMENT_MAP)


def review_scene():
    require("-nullrhi" not in u.SystemLibrary.get_command_line().lower(), "Review needs rendering")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Missing lumber charcoal settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for existing in actors.get_all_level_actors():
        if isinstance(existing, (u.DirectionalLight, u.SkyLight)):
            existing.light_component.set_visibility(False)
    # The gameplay scene creates these at BeginPlay; editor review needs temporary
    # equivalents. Nothing below is saved into this map or the existing settlement.
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
    sky.light_component.set_intensity(1.1)
    views = (("three-quarter", (700, 8000, 1150), (3200, 5850, 100), 44.),
             ("settlement", (7300, 11200, 4800), (2300, 2900, 100), 49.))
    cameras = {}
    for name, location, target, fov in views:
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location),
            u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*target)))
        camera.set_actor_label("HarborShipyard review - " + name)
        camera.camera_component.set_field_of_view(fov)
        camera.camera_component.set_editor_property("aspect_ratio", 4. / 3.)
        exposure = camera.camera_component.get_editor_property("post_process_settings")
        for prop, value in (("override_auto_exposure_method", True),
                            ("auto_exposure_method", u.AutoExposureMethod.AEM_MANUAL),
                            ("override_auto_exposure_apply_physical_camera_exposure", True),
                            ("auto_exposure_apply_physical_camera_exposure", False),
                            ("override_auto_exposure_bias", True), ("auto_exposure_bias", 1.5)):
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
    u.EditorLevelLibrary.pilot_level_actor(camera)
    u.log("HARBORSHIPYARD_YARD_01_VIEW_READY " + SETTLEMENT_MAP)


def capture():
    views, cameras = review_scene()
    OUT.mkdir(parents=True, exist_ok=True)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6,
             "start": time.monotonic(), "results": []}

    def tick(_delta):
        try:
            require(time.monotonic() - state["start"] < 120, "LumberCharcoal screenshot timed out")
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
                    1600, 1200, str(path), camera=cameras[name], delay=1.)
                require(state["task"] is not None and state["task"].is_valid_task(), "Screenshot request failed")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            write_report("capture.json", {"rendered": False, "error": traceback.format_exc()})
            u.log_error(traceback.format_exc())
            u.SystemLibrary.quit_editor()
    state["handle"] = u.register_slate_post_tick_callback(tick)


def ready(_delta):
    u.unregister_slate_post_tick_callback(READY_HANDLE)
    try:
        if os.environ.get("SHOEN_HARBORSHIPYARD_VIEW") == "1":
            show()
        elif os.environ.get("SHOEN_HARBORSHIPYARD_CAPTURE") == "1":
            capture()
        else:
            main()
            if os.environ.get("SHOEN_HARBORSHIPYARD_IMPORT_CAPTURE") == "1":capture()
    except Exception:
        write_report("error.json", {"error":traceback.format_exc()})
        u.log_error(traceback.format_exc())
        u.SystemLibrary.quit_editor()
u.EditorPythonScripting.set_keep_python_script_alive(True)
READY_HANDLE=u.register_slate_post_tick_callback(ready)
