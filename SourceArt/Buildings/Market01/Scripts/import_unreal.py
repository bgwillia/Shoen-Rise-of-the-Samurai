"""Import Market01 into a copy of the existing authored settlement.

SHOEN_MARKET_CAPTURE=1 captures two rendered Unreal editor views of the settlement. Launch with
-ShoenScenario=settlement so its actual terrain and roads surround the art.
Missing farm/shrine assets are imported serially using their existing scripts.
"""
import json
import os
from pathlib import Path
import runpy
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/Market01"
OUT = ROOT / "artifacts/market01"
DEST = "/Game/Art/Buildings/Commerce/Market01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
RH_DEST = "/Game/Art/Buildings/Rural/RuralHouse01"
SR_DEST = "/Game/Art/Buildings/Religion/SmallShrine01"
SOURCE_MAP = "/Game/Art/Buildings/Religion/SmallShrine01/Review/SmallShrine01_Settlement"
SHRINE_MAP = SR_DEST + "/Review/SmallShrine01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/Market01_Settlement"
MARKET_POSITION = (-2250.0, 1200.0, 0.0)
SHRINE_POSITION = (50.0, 1000.0, 0.0)
BOX_MODULES = {"MK01_Table_A", "MK01_Table_B", "MK01_Fence"}
# Local metres: boxes hug individual supports, never spanning the trading aisle.
POST_BOXES = {
    "Market_01": [(x, y, 1.265, .18, .18, 2.25)
                  for x in (-2.35, 0., 2.35) for y in (-1.65, 1.65) if not (x == 0 and y < 0)],
    "MarketStall_Open_01": [(x, y, 1.18 if y > 0 else 1.07, .096, .096,
                              2.32 if y > 0 else 2.10)
                             for x in (-1.05, 1.05) for y in (-.70, .70)],
    "MK01_AwningPosts": [(x, -.77, 1.065, .092, .092, 2.13) for x in (-1.32, 1.32)],
}
report = {"asset": "Market01", "imported": False}


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


def market_material(name, color, roughness, cloth=False):
    material = u.load_asset(DEST + "/M_" + name)
    if material is None:
        material = u.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_" + name, DEST, u.Material, u.MaterialFactoryNew())
    require(material is not None, "Could not create " + name)
    edit = u.MaterialEditingLibrary
    edit.delete_all_material_expressions(material)
    material.set_editor_property("two_sided", cloth)
    material.set_editor_property("blend_mode", u.BlendMode.BLEND_OPAQUE)

    def node(kind, **properties):
        expression = edit.create_material_expression(material, kind)
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        return expression

    def wire(source, output, target, pin):
        require(edit.connect_material_expressions(source, output, target, pin),
                "Could not connect " + name + " " + pin)

    base = node(u.MaterialExpressionConstant3Vector, constant=u.LinearColor(*color, 1.0))
    pottery = name == "MK01_Pottery"
    rough = node(u.MaterialExpressionConstant, r=roughness)
    if cloth or pottery:
        # Natural-fibre and stone grain reuse the rural kit's existing texture
        # sets. The pottery remains dry unglazed clay; its authored vertex tint
        # carries the broad firing variation, while this detail supplies pores.
        family = "Rope" if cloth else "Stone"
        tiling = 1.5 if cloth else 2.8
        uv = node(u.MaterialExpressionTextureCoordinate, u_tiling=tiling, v_tiling=tiling)
        grain = node(u.MaterialExpressionTextureSample,
                     texture=asset(RH_DEST + "/T_RH01_" + family + "_BaseColor"))
        wire(uv, "", grain, "UVs")
        grain_mix = node(u.MaterialExpressionLinearInterpolate, const_a=1.0,
                         const_alpha=.22 if cloth else .12)
        wire(grain, "RGB", grain_mix, "B")
        tinted = node(u.MaterialExpressionMultiply)
        wire(base, "", tinted, "A")
        wire(grain_mix, "", tinted, "B")
        base = tinted
        normal = node(u.MaterialExpressionTextureSample,
                      texture=asset(RH_DEST + "/T_RH01_" + family + "_Normal"),
                      sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        wire(uv, "", normal, "UVs")
        normal_strength = .24 if cloth else .10
        strength = node(u.MaterialExpressionConstant3Vector,
                        constant=u.LinearColor(normal_strength, normal_strength, 1.0, 1.0))
        softened = node(u.MaterialExpressionMultiply)
        wire(normal, "RGB", softened, "A")
        wire(strength, "", softened, "B")
        unit = node(u.MaterialExpressionNormalize)
        wire(softened, "", unit, "")
        require(edit.connect_material_property(unit, "", u.MaterialProperty.MP_NORMAL),
                "Could not connect " + name + " surface normal")
        surface = node(u.MaterialExpressionTextureSample,
                       texture=asset(RH_DEST + "/T_RH01_" + family + "_ORM"),
                       sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS)
        wire(uv, "", surface, "UVs")
        matte = node(u.MaterialExpressionLinearInterpolate, const_alpha=.65)
        wire(rough, "", matte, "A")
        wire(surface, "G", matte, "B")
        rough = matte
        ao = node(u.MaterialExpressionLinearInterpolate, const_a=1.0, const_alpha=.4)
        wire(surface, "R", ao, "B")
        require(edit.connect_material_property(ao, "", u.MaterialProperty.MP_AMBIENT_OCCLUSION),
                "Could not connect " + name + " surface occlusion")
        specular = node(u.MaterialExpressionConstant, r=.12 if cloth else .20)
        require(edit.connect_material_property(specular, "", u.MaterialProperty.MP_SPECULAR),
                "Could not connect " + name + " matte reflectance")
    vertex = node(u.MaterialExpressionVertexColor)
    weathered = node(u.MaterialExpressionMultiply)
    wire(base, "", weathered, "A")
    wire(vertex, "", weathered, "B")
    require(edit.connect_material_property(weathered, "", u.MaterialProperty.MP_BASE_COLOR),
            "Could not connect " + name + " colour")
    require(edit.connect_material_property(rough, "", u.MaterialProperty.MP_ROUGHNESS),
            "Could not connect " + name + " roughness")
    edit.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, True)
    require(not list(edit.recompile_material(material)), "Material compile failed: " + name)
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False),
            "Could not save " + name)
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
    require(slots and all(slot in materials for slot in slots), "Unexpected slots: " + repr(slots))
    for index, slot in enumerate(slots):
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
        collision = str(len(boxes)) + " separate post boxes; open aisle"
    require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), "Could not save " + name)
    bounds = mesh.get_bounds()
    report.setdefault("meshes", []).append({
        "asset": mesh.get_path_name(), "source": str(source), "material_slots": slots,
        "simple_collision": collision, "bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
        "bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]})
    return mesh


def ensure_existing_context():
    require(Path(map_filename(SOURCE_MAP)).is_file(),
            "Finish the existing SmallShrine settlement import before importing Market01")


def place(actors, item, mesh, position, tag, collision):
    x, y, z = item["location"]
    location = (position[0] + x * 100, position[1] - y * 100, position[2] + z * 100)
    yaw = -item.get("rotation_degrees", 0)
    actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*location),
                                         u.Rotator(pitch=0, yaw=yaw, roll=0))
    require(actor is not None, "Could not place " + item["name"])
    actor.set_actor_label(("Market_01" if tag == "Market01" else "SmallShrine_01") + " - " + item["name"])
    actor.set_folder_path("SettlementArt/" + tag)
    actor.tags = [u.Name(tag), u.Name("SettlementArt")]
    actor.set_actor_scale3d(u.Vector(*item.get("scale", [1, 1, 1])))
    component = actor.static_mesh_component
    component.set_mobility(u.ComponentMobility.STATIC)
    component.set_static_mesh(mesh)
    component.set_collision_profile_name("BlockAllDynamic")
    component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY if collision else u.CollisionEnabled.NO_COLLISION)
    if tag == "Market01":
        report.setdefault("placements", []).append({"name": item["name"], "mesh": item["mesh"],
                                                   "position_cm": location, "yaw": yaw, "collision": collision})
    return actor


def main():
    ensure_existing_context()
    materials = {"SH01_" + family: asset(SH_DEST + "/M_SH01_" + family)
                 for family in ("Thatch", "Timber", "Plaster", "Stone", "Iron")}
    materials["RH01_Rope"] = asset(SH_DEST + "/M_SH01_Rope")
    materials["FC01_Dirt"] = asset("/Game/Art/Buildings/Agriculture/FarmCompound01/M_FC01_Dirt")
    for name, colour, roughness in (
        ("MK01_Cloth", (.58, .50, .37), .95),
        ("MK01_Pottery", (.19, .105, .058), .93),
        ("MK01_Leaf", (.14, .22, .055), .88),
        ("MK01_Root", (.68, .60, .40), .91),
        ("MK01_Fish", (.32, .30, .22), .7),
        ("MK01_Ink", (.025, .020, .014), .96),
    ):
        materials[name] = market_material(name, colour, roughness, cloth=name == "MK01_Cloth")
    instances = instances_from(ART / "Exports/assembly.json")
    meshes = {name: import_mesh(name, materials) for name in sorted({item["mesh"] for item in instances})}
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
    require(world is not None, "Could not load existing farm settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for previous in list(actors.get_all_level_actors()):
        if previous.actor_has_tag("Market01"):
            actors.destroy_actor(previous)
    # Farm and shrine were authored as independent copies of Smithy. Restore the
    # unchanged shrine assembly in this new map so all earlier buildings coexist.
    if not any(actor.actor_has_tag("SmallShrine01") for actor in actors.get_all_level_actors()):
        for item in instances_from(ROOT / "SourceArt/Buildings/SmallShrine01/Exports/assembly.json"):
            place(actors, item, asset(SR_DEST + "/SM_" + item["mesh"]), SHRINE_POSITION,
                  "SmallShrine01", item["mesh"] != "Torii_01")
    for item in instances:
        place(actors, item, meshes[item["mesh"]], MARKET_POSITION, "Market01",
              item["mesh"] in BOX_MODULES or item["mesh"] in POST_BOXES)
    for placed in actors.get_all_level_actors():
        if placed.actor_has_tag("RuralHouse01ScaleFigure"):
            placed.set_actor_location(u.Vector(MARKET_POSITION[0] + 280,
                                              MARKET_POSITION[1] + 520, 0), False, False)
    actors.clear_actor_selection_set()
    camera = u.Vector(MARKET_POSITION[0] + 1200, MARKET_POSITION[1] + 1800, 560)
    target = u.Vector(MARKET_POSITION[0], MARKET_POSITION[1], 165)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(
        camera, u.MathLibrary.find_look_at_rotation(camera, target))
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save Market settlement")
    report.update(imported=True, map=SETTLEMENT_MAP, position_cm=MARKET_POSITION,
                  source_map=SOURCE_MAP, shrine_position_cm=SHRINE_POSITION,
                  grouping="SettlementArt/Market01", collision_policy="Structure only; open aisle and non-colliding goods")
    write_report("unreal-import.json", report)
    u.log("MARKET_01_IMPORTED " + SETTLEMENT_MAP)


def review_scene():
    require("-nullrhi" not in u.SystemLibrary.get_command_line().lower(), "Review needs rendering")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Missing market settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    for existing in actors.get_all_level_actors():
        if isinstance(existing, (u.DirectionalLight, u.SkyLight)):
            existing.light_component.set_visibility(False)
    # The gameplay scene creates these at BeginPlay; editor review needs temporary
    # equivalents. Nothing below is saved into this map or the existing settlement.
    ground = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -9), u.Rotator())
    ground.set_actor_label("Market review - temporary terrain")
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

    views = (("three-quarter", (-1050, 3000, 560), (-2250, 1190, 165), 40.),
             ("settlement", (-1200, 6100, 4900), (-350, 100, 130), 49.))
    cameras = {}
    for name, location, target, fov in views:
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location),
            u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*target)))
        camera.set_actor_label("Market review - " + name)
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
    u.log("MARKET_01_VIEW_READY " + SETTLEMENT_MAP)


def capture():
    views, cameras = review_scene()
    OUT.mkdir(parents=True, exist_ok=True)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6,
             "start": time.monotonic(), "results": []}

    def tick(_delta):
        try:
            require(time.monotonic() - state["start"] < 120, "Market screenshot timed out")
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
    if os.environ.get("SHOEN_MARKET_VIEW") == "1":
        def open_when_ready(_delta):
            level = u.get_editor_subsystem(u.LevelEditorSubsystem)
            if level is None:
                return
            u.unregister_slate_post_tick_callback(VIEW_HANDLE)
            show()
            level.editor_set_viewport_realtime(True)
        VIEW_HANDLE = u.register_slate_post_tick_callback(open_when_ready)
    elif os.environ.get("SHOEN_MARKET_CAPTURE") == "1":
        capture()
    else:
        main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report("unreal-import.json", report)
    raise
