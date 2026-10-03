"""Import the retainer exterior using the established modular rural FBX workflow.

SHOEN_RETAINER_CAPTURE=1 takes the two actual rendered Unreal editor views.
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
ART = ROOT / "SourceArt/Buildings/RetainerCompound01"
OUT = ROOT / "artifacts/retainercompound01"
DEST = "/Game/Art/Buildings/Military/RetainerCompound01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
MK_DEST = "/Game/Art/Buildings/Commerce/Market01"
SOURCE_MAP = MK_DEST + "/Review/Market01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/RetainerCompound01_Settlement"
COMPOUND_POSITION = (1350.0, 2600.0, 0.0)
# Blender front is -Y; turn the assembled compound to face the village (-Unreal Y).
COMPOUND_YAW = 180.0
BOX_MODULES = {"RetainerFence_Straight_01"}
# Local metres; broad exterior hall and separate supports, never tiny props.
POST_BOXES = {
    "RetainerCompound_01": [(0, 0, 1.25, 5.64, 3.15, 2.5)],
    "RetainerGate_01": [(x, 0, 1.43, .26, .27, 2.60) for x in (-1.47, 1.47)],
    "RetainerFence_Corner_01": [(.5, 0, .775, 1.0, .22, 1.55),
                                  (0, .5, .775, .22, 1.0, 1.55)],
    # Each simple box encloses one .195m support from its spread foot at
    # +/- .8736m, z=.22m to its upper end at +/- .78m, z=4.79m.
    "Watchtower_01": [(x, y, 2.505, .2886, .2886, 4.57)
                       for x in (-.8268, .8268) for y in (-.8268, .8268)],
}
report = {"asset": "RetainerCompound01", "imported": False}


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


def thin_surface_material(source, family):
    """Retain rural PBR maps on the authored thin reed, shingle and ink faces."""
    path = DEST + "/M_RC01_" + family
    material = u.load_asset(path)
    if material is None:
        material = u.EditorAssetLibrary.duplicate_asset(source.get_path_name(), path)
    require(material is not None, "Could not reuse " + family)
    material.set_editor_property("two_sided", True)
    require(not list(u.MaterialEditingLibrary.recompile_material(material)), "Could not compile " + family)
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False), "Could not save " + family)
    return material


def retainer_dirt_material():
    """Retain the village earth palette with close-view grit and authored wear."""
    path = DEST + "/M_RC01_Dirt"
    material = u.load_asset(path)
    if material is None:
        material = u.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_RC01_Dirt", DEST, u.Material, u.MaterialFactoryNew())
    require(material is not None, "Could not create retainer earth")
    material.set_editor_property("two_sided", True)
    edit = u.MaterialEditingLibrary
    edit.delete_all_material_expressions(material)

    def node(kind, **properties):
        expression = edit.create_material_expression(material, kind)
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        return expression

    def wire(source, output, target, pin):
        require(edit.connect_material_expressions(source, output, target, pin),
                "Could not connect retainer earth " + pin)

    # The same warm field-earth family as FarmCompound, with broader compacted
    # patches. The mesh's vertex tint supplies localized wear and edge darkening.
    noise = node(u.MaterialExpressionNoise, scale=.006, quality=1, levels=3,
                 turbulence=False, output_min=0., output_max=1.)
    low = node(u.MaterialExpressionConstant3Vector,
               constant=u.LinearColor(.085, .064, .040, 1.))
    high = node(u.MaterialExpressionConstant3Vector,
                constant=u.LinearColor(.185, .148, .097, 1.))
    soil = node(u.MaterialExpressionLinearInterpolate)
    wire(low, "", soil, "A")
    wire(high, "", soil, "B")
    wire(noise, "", soil, "Alpha")
    vertex = node(u.MaterialExpressionVertexColor)
    tinted = node(u.MaterialExpressionMultiply)
    wire(soil, "", tinted, "A")
    wire(vertex, "", tinted, "B")
    require(edit.connect_material_property(tinted, "", u.MaterialProperty.MP_BASE_COLOR),
            "Could not connect retainer earth colour")

    # Ground UVs are authored in metres. Reuse the rural stone's subtle granular
    # normal at close spacing; no new texture or shared-material edit is needed.
    uv = node(u.MaterialExpressionTextureCoordinate, u_tiling=6., v_tiling=6.)
    normal = node(u.MaterialExpressionTextureSample,
                  texture=asset("/Game/Art/Buildings/Rural/RuralHouse01/T_RH01_Stone_Normal"),
                  sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    wire(uv, "", normal, "UVs")
    strength = node(u.MaterialExpressionConstant3Vector,
                    constant=u.LinearColor(.22, .22, 1., 1.))
    softened = node(u.MaterialExpressionMultiply)
    wire(normal, "RGB", softened, "A")
    wire(strength, "", softened, "B")
    unit = node(u.MaterialExpressionNormalize)
    wire(softened, "", unit, "")
    require(edit.connect_material_property(unit, "", u.MaterialProperty.MP_NORMAL),
            "Could not connect retainer earth normal")
    for value, prop in ((.96, u.MaterialProperty.MP_ROUGHNESS),
                        (.18, u.MaterialProperty.MP_SPECULAR)):
        constant = node(u.MaterialExpressionConstant, r=value)
        require(edit.connect_material_property(constant, "", prop),
                "Could not connect retainer earth surface response")
    edit.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, True)
    require(not list(edit.recompile_material(material)), "Retainer earth material compile failed")
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False),
            "Could not save retainer earth material")
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
    # The latest Market source was authored but may not yet have been imported.
    # Run its unchanged importer once, serially, before copying that settlement.
    if not Path(map_filename(SOURCE_MAP)).is_file():
        runpy.run_path(str(ROOT / "SourceArt/Buildings/Market01/Scripts/import_unreal.py"))
    require(Path(map_filename(SOURCE_MAP)).is_file(), "Missing existing Market settlement")
    materials = {"SH01_" + family: asset(SH_DEST + "/M_SH01_" + family)
                 for family in ("Thatch", "Timber", "Plaster", "Stone", "Iron")}
    materials["RH01_Rope"] = asset(SH_DEST + "/M_SH01_Rope")
    materials["FC01_Dirt"] = retainer_dirt_material()
    for family in ("Ember", "Charcoal"):
        materials["SM01_" + family] = asset("/Game/Art/Buildings/Craft/Smithy01/M_SM01_" + family)
    for family in ("Cloth", "Ink"):
        materials["MK01_" + family] = asset(MK_DEST + "/M_MK01_" + family)
    for slot, family in (("SH01_Thatch", "Thatch"), ("SH01_Timber", "Timber"), ("MK01_Ink", "Ink")):
        materials[slot] = thin_surface_material(materials[slot], family)
    # Reused display armor and rack weapons retain the existing atlases.
    for family in ("Do01", "Kabuto01", "Sode01", "Kusazuri01"):
        materials["M_" + family] = asset("/Game/Art/Characters/Samurai/" + family + "/M_" + family)
    materials["M_Yumi01"] = asset("/Game/Art/Characters/Samurai/Yumi01/M_Yumi01")
    materials["M_Yumi01_String"] = asset("/Game/Art/Characters/Samurai/Yumi01/M_Yumi01_String")
    materials["M_Tachi01_Fittings"] = asset("/Game/Art/Characters/Samurai/Tachi01/M_Tachi01_Fittings")
    instances = instances_from(ART / "Exports/assembly.json")
    meshes = {name: import_mesh(name, materials) for name in sorted({item["mesh"] for item in instances})}
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
    require(world is not None, "Could not load the existing settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for previous in list(actors.get_all_level_actors()):
        if previous.actor_has_tag("RetainerCompound01"):
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
        actor.set_actor_label("RetainerCompound_01 - " + item["name"])
        actor.set_folder_path("SettlementArt/RetainerCompound01")
        actor.tags = [u.Name("RetainerCompound01"), u.Name("SettlementArt")]
        actor.set_actor_scale3d(u.Vector(*item.get("scale", [1, 1, 1])))
        component = actor.static_mesh_component
        component.set_mobility(u.ComponentMobility.STATIC)
        component.set_static_mesh(meshes[item["mesh"]])
        collision = item["mesh"] in BOX_MODULES or item["mesh"] in POST_BOXES
        component.set_collision_profile_name("BlockAllDynamic")
        component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY if collision else u.CollisionEnabled.NO_COLLISION)
        report.setdefault("placements", []).append({"name": item["name"], "mesh": item["mesh"],
                                                    "position_cm": position, "yaw": yaw})
    # The old review mannequin is not part of this compound's exterior artwork.
    for placed in actors.get_all_level_actors():
        if placed.actor_has_tag("RuralHouse01ScaleFigure"):
            actors.destroy_actor(placed)
    actors.clear_actor_selection_set()
    camera, target = u.Vector(100, 400, 1000), u.Vector(1350, 2600, 210)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(
        camera, u.MathLibrary.find_look_at_rotation(camera, target))
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save retainer settlement")
    report.update(imported=True, map=SETTLEMENT_MAP, source_map=SOURCE_MAP,
                  position_cm=COMPOUND_POSITION, yaw=COMPOUND_YAW)
    write_report("unreal-import.json", report)
    u.log("RETAINER_COMPOUND_01_IMPORTED " + SETTLEMENT_MAP)


def review_scene():
    require("-nullrhi" not in u.SystemLibrary.get_command_line().lower(), "Review needs rendering")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Missing retainer settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for existing in actors.get_all_level_actors():
        if isinstance(existing, (u.DirectionalLight, u.SkyLight)):
            existing.light_component.set_visibility(False)
    # The gameplay scene creates these at BeginPlay; editor review needs temporary
    # equivalents. Nothing below is saved into this map or the existing settlement.
    ground = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -9), u.Rotator())
    ground.set_actor_label("Retainer review - temporary terrain")
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

    views = (("three-quarter", (100, 400, 1000), (1350, 2600, 210), 43.),
             ("settlement", (-3300, -5000, 5500), (-250, 500, 150), 50.))
    cameras = {}
    for name, location, target, fov in views:
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location),
            u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*target)))
        camera.set_actor_label("Retainer review - " + name)
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
    u.log("RETAINER_COMPOUND_01_VIEW_READY " + SETTLEMENT_MAP)


def capture():
    views, cameras = review_scene()
    OUT.mkdir(parents=True, exist_ok=True)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6,
             "start": time.monotonic(), "results": []}

    def tick(_delta):
        try:
            require(time.monotonic() - state["start"] < 120, "Retainer screenshot timed out")
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
    if os.environ.get("SHOEN_RETAINER_CAPTURE") == "1":
        capture()
    else:
        main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report("unreal-import.json", report)
    raise
