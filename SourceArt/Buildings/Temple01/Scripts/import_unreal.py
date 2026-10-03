"""Import Temple_01 and place its modular exterior in the existing settlement.

SHOEN_TEMPLE_CAPTURE=1 takes the two actual rendered Unreal editor views.
"""
import json
import math
import os
from pathlib import Path
import re
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/Temple01"
OUT = ROOT / "artifacts/temple01"
DEST = "/Game/Art/Buildings/Religion/Temple01"
RC_DEST = "/Game/Art/Buildings/Military/RetainerCompound01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
MK_DEST = "/Game/Art/Buildings/Commerce/Market01"
MN_DEST = "/Game/Art/Buildings/Administration/Manor01"
SR_DEST = "/Game/Art/Buildings/Religion/SmallShrine01"
SOURCE_MAPS = ("/Game/Art/Buildings/Production/LumberCharcoal01/Review/LumberCharcoal01_Settlement",
               MN_DEST + "/Review/Manor01_Settlement",
               RC_DEST + "/Review/RetainerCompound01_Settlement")
SETTLEMENT_MAP = DEST + "/Review/Temple01_Settlement"
# The temple sits beyond the existing northern compounds, facing the village.
COMPOUND_POSITION = (-900.0, 5400.0, 0.0)
COMPOUND_YAW = 180.0
EXPORT_NAMES = (
    "Temple_01", "Temple_MainHall_01", "TempleGate_01", "TempleBellPavilion_01",
    "TempleBell_01", "Temple_Railing_01", "Temple_Steps_01", "Temple_Curtains_01",
    "Temple_Fence_01",
)
SHARED_MESHES = {"StoneLantern_01": SR_DEST + "/SM_StoneLantern_01"}
BOX_MODULES = {"Temple_Steps_01", "Temple_Fence_01"}
# Optional assembly collision_boxes supply local metre boxes for open supports.
POST_BOXES = {
    "Temple_MainHall_01": [(0, 0, 2.9, 10.8, 7.6, 3.2)],
    "Temple_Foundation_01": [(0, 0, .4, 13.9, 10.4, .8)],
}
report = {"asset": "Temple01", "imported": False}


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


def cedar_material():
    """Keep the existing timber graph and vertex tint; replace its three maps."""
    textures = {}
    for channel in ("BaseColor", "Normal", "ORM"):
        name = "T_TP01_Cedar_" + channel
        source = ART / "Textures" / ("TP01_Cedar_" + channel + ".png")
        require(source.is_file(), "Missing cedar texture: " + str(source))
        task = u.AssetImportTask()
        for key, value in {"filename": str(source), "destination_path": DEST,
                           "destination_name": name, "automated": True,
                           "replace_existing": True, "replace_existing_settings": True,
                           "save": False}.items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        require(task.imported_object_paths, "Texture import failed: " + name)
        texture = asset(DEST + "/" + name)
        texture.set_editor_property("srgb", channel == "BaseColor")
        if channel == "Normal":
            texture.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP)
            # Derived with the same OpenGL +Y convention as RuralHouse01.
            texture.set_editor_property("flip_green_channel", True)
        elif channel == "ORM":
            texture.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_MASKS)
        require(u.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False),
                "Could not save " + name)
        textures[channel] = texture

    path = DEST + "/M_TP01_Cedar"
    material = u.load_asset(path)
    if material is None:
        material = u.EditorAssetLibrary.duplicate_asset(SH_DEST + "/M_SH01_Timber", path)
    require(material is not None, "Could not copy the shared timber material")
    edit = u.MaterialEditingLibrary
    replaced = set()
    for expression in edit.get_material_expressions(material):
        if not isinstance(expression, u.MaterialExpressionTextureSample):
            continue
        previous = expression.get_editor_property("texture")
        if previous is None:
            continue
        for channel, texture in textures.items():
            if previous.get_name().endswith("_" + channel):
                expression.set_editor_property("texture", texture)
                replaced.add(channel)
                break
    require(replaced == set(textures), "Copied timber graph is missing cedar texture channels")
    require(not list(edit.recompile_material(material)), "Cedar material compile failed")
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False),
            "Could not save cedar material")
    report["cedar_material"] = {"asset": path, "copied_from": SH_DEST + "/M_SH01_Timber",
        "textures": {channel: texture.get_path_name() for channel, texture in textures.items()},
        "base_color": "generated cedar multiplied by existing mesh vertex RGB",
        "normal_xy_strength": .65, "normal_green_flipped": True,
        "roughness_mean": .699, "shared_materials_modified": False}
    return material


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
    source_map = next((path for path in SOURCE_MAPS if Path(map_filename(path)).is_file()), None)
    require(source_map is not None, "Missing existing Manor or Retainer settlement")
    materials = {"SH01_" + family: asset(SH_DEST + "/M_SH01_" + family)
                 for family in ("Thatch", "Timber", "Plaster", "Stone", "Iron")}
    materials["TP01_Cedar"] = cedar_material()
    materials["RH01_Rope"] = asset(SH_DEST + "/M_SH01_Rope")
    materials["FC01_Dirt"] = (u.load_asset(RC_DEST + "/M_RC01_Dirt")
        or asset("/Game/Art/Buildings/Agriculture/FarmCompound01/M_FC01_Dirt"))
    for family in ("Cloth", "Ink", "Leaf"):
        materials["MK01_" + family] = asset(MK_DEST + "/M_MK01_" + family)
    assembly = json.loads((ART / "Exports/assembly.json").read_text())
    instances = assembly["instances"] if isinstance(assembly, dict) else assembly
    if isinstance(assembly, dict):
        POST_BOXES.update(assembly.get("collision_boxes", {}))
    names = set(EXPORT_NAMES) | {item["mesh"] for item in instances}
    meshes = {name: asset(SHARED_MESHES[name]) if name in SHARED_MESHES else import_mesh(name, materials)
              for name in sorted(names)}
    # Temple_01 is the combined reusable asset. Render the modular assembly once.
    instances = [item for item in instances if item["mesh"] != "Temple_01"]
    require(instances, "Temple assembly contains no modular pieces")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(source_map))
    require(world is not None, "Could not load the existing settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for previous in list(actors.get_all_level_actors()):
        if previous.actor_has_tag("Temple01"):
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
        actor.set_actor_label("Temple_01 - " + item["name"])
        actor.set_folder_path("SettlementArt/Temple01")
        actor.tags = [u.Name("Temple01"), u.Name("SettlementArt")]
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
            placed.set_actor_location(u.Vector(COMPOUND_POSITION[0] + 260, COMPOUND_POSITION[1] - 1130, 0), False, False)
    actors.clear_actor_selection_set()
    camera, target = u.Vector(1800, 1900, 1500), u.Vector(-900, 5200, 300)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(
        camera, u.MathLibrary.find_look_at_rotation(camera, target))
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save temple settlement")
    report.update(imported=True, map=SETTLEMENT_MAP, source_map=source_map,
                  position_cm=COMPOUND_POSITION, yaw=COMPOUND_YAW,
                  assembly_policy="Modular pieces placed once; combined Temple_01 retained as reusable asset")
    write_report("unreal-import.json", report)
    u.log("TEMPLE_01_IMPORTED " + SETTLEMENT_MAP)


def review_scene():
    require("-nullrhi" not in u.SystemLibrary.get_command_line().lower(), "Review needs rendering")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Missing temple settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for existing in actors.get_all_level_actors():
        if isinstance(existing, (u.DirectionalLight, u.SkyLight)):
            existing.light_component.set_visibility(False)
    # The gameplay scene creates these at BeginPlay; editor review needs temporary
    # equivalents. Nothing below is saved into this map or the existing settlement.
    ground = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -9), u.Rotator())
    ground.set_actor_label("Temple review - temporary terrain")
    ground.static_mesh_component.set_static_mesh(asset("/Engine/BasicShapes/Cube"))
    ground.static_mesh_component.set_material(0, asset("/Game/Art/Buildings/Craft/Smithy01/M_SM01_ReviewEarth"))
    ground.set_actor_scale3d(u.Vector(1500, 1500, .15))
    key = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 1500),
                                       u.Rotator(pitch=-38, yaw=135, roll=0))
    key.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    key.light_component.set_intensity(2.4)
    key.light_component.set_light_color(u.LinearColor(1., .94, .82, 1.))
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
                                        u.Rotator(pitch=-26, yaw=-45, roll=0))
    fill.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    fill.light_component.set_intensity(.42)
    fill.light_component.set_editor_property("cast_shadows", False)

    views = (("three-quarter", (1800, 1900, 1500), (-900, 5200, 300), 39.),
             ("settlement", (-6500, -7000, 10600), (-100, 2300, 150), 50.))
    cameras = {}
    for name, location, target, fov in views:
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location),
            u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*target)))
        camera.set_actor_label("Temple review - " + name)
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
    u.log("TEMPLE_01_VIEW_READY " + SETTLEMENT_MAP)


def capture():
    views, cameras = review_scene()
    OUT.mkdir(parents=True, exist_ok=True)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6,
             "start": time.monotonic(), "results": []}

    def tick(_delta):
        try:
            require(time.monotonic() - state["start"] < 120, "Temple screenshot timed out")
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
                    2000, 1500, str(path), camera=cameras[name], delay=1.)
                require(state["task"] is not None and state["task"].is_valid_task(), "Screenshot request failed")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            write_report("capture.json", {"rendered": False, "error": traceback.format_exc()})
            u.log_error(traceback.format_exc())
            u.SystemLibrary.quit_editor()
    state["handle"] = u.register_slate_post_tick_callback(tick)


try:
    if os.environ.get("SHOEN_TEMPLE_VIEW") == "1":
        show()
    elif os.environ.get("SHOEN_TEMPLE_CAPTURE") == "1":
        capture()
    else:
        main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report("capture-error.json" if os.environ.get("SHOEN_TEMPLE_CAPTURE") else "unreal-import.json", report)
    raise
