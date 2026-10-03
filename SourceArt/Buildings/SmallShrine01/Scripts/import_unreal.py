"""Import SmallShrine01 using the existing rural FBX/material workflow.

Default: import meshes and add one shrine to a copy of the Smithy settlement map.
SHOEN_SHRINE_CAPTURE=1: capture the exterior and settlement context in the rendered
editor with -ShoenScenario=settlement. No gameplay or shared-material edits.
"""
import json
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/SmallShrine01"
OUT = ROOT / "artifacts/smallshrine01"
DEST = "/Game/Art/Buildings/Religion/SmallShrine01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
SOURCE_MAP = "/Game/Art/Buildings/Agriculture/FarmCompound01/Review/FarmCompound01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/SmallShrine01_Settlement"
SHRINE_POSITION = (50.0, 1000.0, 0.0)
report = {"asset": "SmallShrine01", "imported": False}


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


def simple_material(name, color, roughness, metallic=0.0, emission=None):
    path = DEST + "/M_" + name
    material = u.load_asset(path)
    if material is not None:
        return material
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_" + name, DEST, u.Material, u.MaterialFactoryNew())
    require(material is not None, "Could not create " + name)
    material.set_editor_property("two_sided", True)
    edit = u.MaterialEditingLibrary
    base = edit.create_material_expression(material, u.MaterialExpressionConstant3Vector)
    base.set_editor_property("constant", u.LinearColor(*color, 1.0))
    require(edit.connect_material_property(base, "", u.MaterialProperty.MP_BASE_COLOR),
            "Could not connect " + name + " base color")
    for value, prop in ((roughness, u.MaterialProperty.MP_ROUGHNESS),
                        (metallic, u.MaterialProperty.MP_METALLIC)):
        node = edit.create_material_expression(material, u.MaterialExpressionConstant)
        node.set_editor_property("r", value)
        require(edit.connect_material_property(node, "", prop), "Could not connect " + name)
    if emission is not None:
        node = edit.create_material_expression(material, u.MaterialExpressionConstant3Vector)
        node.set_editor_property("constant", u.LinearColor(*emission, 1.0))
        require(edit.connect_material_property(node, "", u.MaterialProperty.MP_EMISSIVE_COLOR),
                "Could not connect " + name + " emissive color")
    edit.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, True)
    require(not list(edit.recompile_material(material)), "Material compile failed: " + name)
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False),
            "Could not save " + name)
    return material


def import_mesh(source_name, destination_name, materials):
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
    require(editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX) >= 0,
            "Could not add box collision: " + destination_name)
    require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False),
            "Could not save " + destination_name)
    bounds = mesh.get_bounds()
    report.setdefault("meshes", []).append({
        "asset": mesh.get_path_name(), "source": str(source), "material_slots": slots,
        "simple_collision": "box", "bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
        "bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]})
    return mesh


def main():
    materials = {"SH01_" + family: asset(SH_DEST + "/M_SH01_" + family)
                 for family in ("Thatch", "Timber", "Plaster", "Stone", "Iron")}
    materials["RH01_Rope"] = asset(SH_DEST + "/M_SH01_Rope")
    materials["SR01_Paper"] = simple_material("SR01_Paper", (0.72, 0.69, 0.60), 0.95)
    names = ("SmallShrine_01", "Torii_01", "OfferingBox_01", "StoneLantern_01",
             "SR01_Fence_Straight", "SR01_Fence_End", "SR01_Fence_Boundary", "SR01_Banners")
    meshes = {name: import_mesh(name + ".fbx", "SM_" + name, materials) for name in names}
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
    require(world is not None, "Could not load existing Smithy settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for previous in list(actors.get_all_level_actors()):
        if previous.actor_has_tag("SmallShrine01"):
            actors.destroy_actor(previous)

    # Modular placements are authored in Blender meters; the established FBX
    # orientation maps Blender -Y onto Unreal +Y.
    assembly = json.loads((ART / "Exports/assembly.json").read_text())
    instances = assembly["instances"] if isinstance(assembly, dict) else assembly
    for item in instances:
        x, y, z = item["location"]
        location = (SHRINE_POSITION[0] + x * 100, SHRINE_POSITION[1] - y * 100,
                    SHRINE_POSITION[2] + z * 100)
        yaw = -item.get("rotation_degrees", 0)
        actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*location),
                                             u.Rotator(pitch=0, yaw=yaw, roll=0))
        require(actor is not None, "Could not place " + item["name"])
        actor.set_actor_label("SmallShrine_01 - " + item["name"])
        actor.tags = [u.Name("SmallShrine01"), u.Name("SettlementArt")]
        actor.set_actor_scale3d(u.Vector(*item.get("scale", [1, 1, 1])))
        component = actor.static_mesh_component
        component.set_mobility(u.ComponentMobility.STATIC)
        component.set_static_mesh(meshes[item["mesh"]])
        component.set_collision_profile_name("BlockAllDynamic")
        # The Torii's simple asset box must not obstruct its open approach.
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION if item["mesh"] == "Torii_01"
                                        else u.CollisionEnabled.QUERY_ONLY)
        report.setdefault("placements", []).append({"name": item["name"], "mesh": item["mesh"],
                                                   "position_cm": location, "yaw": yaw})
    for placed in actors.get_all_level_actors():
        if placed.actor_has_tag("RuralHouse01ScaleFigure"):
            placed.set_actor_location(u.Vector(SHRINE_POSITION[0] - 340,
                                              SHRINE_POSITION[1] + 300, 0), False, False)
    actors.clear_actor_selection_set()
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    editor.set_level_viewport_camera_info(u.Vector(-810, 2120, 590),
                                         u.Rotator(pitch=-16, yaw=-45, roll=0))
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save shrine settlement map")
    report.update(imported=True, map=SETTLEMENT_MAP, position_cm=SHRINE_POSITION,
                  source_map=SOURCE_MAP, torii_collision="Disabled on placed actor to keep approach open")
    write_report("unreal-import.json", report)
    u.log("SMALL_SHRINE_01_IMPORTED " + SETTLEMENT_MAP)


def review_scene():
    require("-nullrhi" not in u.SystemLibrary.get_command_line().lower(), "Review needs rendering")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Missing shrine settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for existing in actors.get_all_level_actors():
        if isinstance(existing, (u.DirectionalLight, u.SkyLight)):
            existing.light_component.set_visibility(False)
    # The gameplay scene creates these at BeginPlay; editor review needs temporary
    # equivalents. Nothing below is saved into this map or the existing settlement.
    ground = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -9), u.Rotator())
    ground.set_actor_label("Shrine review - temporary terrain")
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
    sky.light_component.set_intensity(.7)
    fill = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 900),
                                        u.Rotator(pitch=-30, yaw=145, roll=0))
    fill.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    fill.light_component.set_intensity(.85)
    fill.light_component.set_editor_property("cast_shadows", False)
    fill.light_component.set_editor_property("light_color", u.Color(211, 225, 255, 255))
    key.light_component.set_editor_property("forward_shading_priority", 2)
    fill.light_component.set_editor_property("forward_shading_priority", 1)

    views = (("three-quarter", (-1050, 2280, 610), (50, 1080, 210), 34.),
             ("settlement", (-950, 4450, 4250), (200, 0, 100), 48.))
    cameras = {}
    for name, location, target, fov in views:
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location),
            u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*target)))
        camera.set_actor_label("Shrine review - " + name)
        camera.camera_component.set_field_of_view(fov)
        camera.camera_component.set_editor_property("aspect_ratio", 4. / 3.)
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
    u.log("FARM_COMPOUND_01_VIEW_READY " + SETTLEMENT_MAP)


def capture():
    views, cameras = review_scene()
    OUT.mkdir(parents=True, exist_ok=True)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6,
             "start": time.monotonic(), "results": []}

    def tick(_delta):
        try:
            require(time.monotonic() - state["start"] < 120, "Shrine screenshot timed out")
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


try:
    if os.environ.get("SHOEN_SHRINE_CAPTURE") == "1":
        capture()
    else:
        main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report("unreal-import.json", report)
    raise
