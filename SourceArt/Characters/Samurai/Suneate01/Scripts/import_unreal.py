"""Import the paired shin guards and save a fitted, neutral-pose outfit map.

Use -ExecutePythonScript for import, then open the saved map normally.
For Metal captures, run with -ExecCmds="py <this script>" and environment
SHOEN_SUNEATE_CAPTURE=1; this mode loads the map, captures both cameras and quits.
Run one Unreal process at a time. Existing outfit packages remain read-only.
"""
import json
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Characters/Samurai/Suneate01"
DEST = "/Game/Art/Characters/Samurai/Suneate01"
MAP = DEST + "/Suneate01_Fitted"
OUT = ROOT / "artifacts/suneate01"
MANNY = "/Game/Characters/Mannequins/Meshes/"
ARMOR = "/Game/Art/Characters/Samurai/"
SOURCE_MATERIAL = ARMOR + "Kusazuri01/M_Kusazuri01"
MATERIAL = DEST + "/M_Suneate01"
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)


def asset(path):
    obj = u.load_asset(path)
    if obj is None:
        raise RuntimeError("Missing existing asset: " + path)
    return obj


def material_variant():
    """Reuse the existing three-image atlas with the lower-leg palette."""
    source = asset(SOURCE_MATERIAL)
    material = u.load_asset(MATERIAL)
    if material is None:
        material = u.EditorAssetLibrary.duplicate_asset(SOURCE_MATERIAL, MATERIAL)
    edit = u.MaterialEditingLibrary
    def palette(mat):
        matches = [expression for expression in edit.get_material_expressions(mat)
                   if isinstance(expression, u.MaterialExpressionCustom)
                   and "floor(UV.x" in expression.get_editor_property("code")
                   and expression.get_editor_property("output_type") == u.CustomMaterialOutputType.CMOT_FLOAT3]
        if len(matches) != 1:
            raise RuntimeError("Expected one existing atlas palette expression")
        return matches[0]
    lines = palette(source).get_editor_property("code").splitlines()
    revised = []
    for line in lines:
        if "tile == 3.0" in line:
            line = "if (tile == 3.0) return float3(0.44, 0.20, 0.17);"
        elif "tile == 2.0 || tile == 11.0" in line:
            line = "if (tile == 2.0 || tile == 11.0) return float3(0.65, 0.52, 0.36);"
        revised.append(line)
        if "float tile =" in line:
            revised.append("if (tile == 4.0) return float3(0.25, 0.19, 0.14);")
            revised.append("if (tile == 7.0) return float3(5.0, 3.2, 1.65);")
    palette(material).set_editor_property("code", "\n".join(revised))
    cloth = [expression for expression in edit.get_material_expressions(material)
             if isinstance(expression, u.MaterialExpressionCustom)
             and expression.get_editor_property("desc") == "KusazuriObi:ClothTileMask"]
    if len(cloth) != 1:
        raise RuntimeError("Expected the existing cloth response mask")
    fabric = [expression for expression in edit.get_material_expressions(material)
              if isinstance(expression, u.MaterialExpressionVertexColor)
              and expression.get_editor_property("desc") == "KusazuriObi:Mask"]
    if len(fabric) != 1:
        raise RuntimeError("Expected the existing cloth vertex-color mask")
    inputs = list(cloth[0].get_editor_property("inputs"))
    if not any(str(item.get_editor_property("input_name")) == "VertexR" for item in inputs):
        vertex_input = u.CustomInput()
        vertex_input.set_editor_property("input_name", "VertexR")
        cloth[0].set_editor_property("inputs", inputs + [vertex_input])
    edit.connect_material_expressions(fabric[0], "R", cloth[0], "VertexR")
    cloth[0].set_editor_property("code",
        "float tile = floor(UV.x * 4.0) + 4.0 * floor((1.0 - UV.y) * 4.0);\n"
        "return max((tile == 12.0 || tile == 7.0) ? 1.0 : 0.0, 1.0 - VertexR);")
    indigo = [expression for expression in edit.get_material_expressions(material)
              if isinstance(expression, u.MaterialExpressionConstant3Vector)
              and expression.get_editor_property("desc") == "KusazuriObi:Indigo"]
    if len(indigo) != 1:
        raise RuntimeError("Expected the existing woven indigo constant")
    indigo[0].set_editor_property("constant", u.LinearColor(.014, .025, .05, 1))
    # Preserve original lacquer normals; soften only woven/vertex-masked cloth.
    def normal_node(label, cls, **properties):
        tag = "Suneate:ClothNormal" + label
        matches = [expression for expression in edit.get_material_expressions(material)
                   if expression.get_editor_property("desc") == tag]
        node = matches[0] if matches else edit.create_material_expression(material, cls)
        node.set_editor_property("desc", tag)
        for key, value in properties.items():
            node.set_editor_property(key, value)
        return node
    previous = edit.get_material_property_input_node(material, u.MaterialProperty.MP_NORMAL)
    strength = normal_node("Strength", u.MaterialExpressionMultiply, const_b=.82)
    flat = normal_node("Flat", u.MaterialExpressionConstant3Vector, constant=u.LinearColor(0, 0, 1, 1))
    blend = normal_node("Blend", u.MaterialExpressionLinearInterpolate)
    unit = normal_node("Unit", u.MaterialExpressionNormalize)
    if previous != unit:
        edit.connect_material_expressions(previous, "", blend, "A")
    for a, b, pin in ((cloth[0], strength, "A"), (strength, blend, "Alpha"),
                       (flat, blend, "B"), (blend, unit, "")):
        edit.connect_material_expressions(a, "", b, pin)
    edit.connect_material_property(unit, "", u.MaterialProperty.MP_NORMAL)
    errors = list(edit.recompile_material(material))
    if errors:
        raise RuntimeError("Suneate material compile failed: " + "; ".join(errors))
    u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def import_guard(side, skeleton, material):
    name = "Suneate_" + side + "_01"
    source = ART / "Exports" / (name + ".fbx")
    if not source.is_file():
        raise RuntimeError("Missing FBX: " + str(source))
    options = u.FbxImportUI()
    options.automated_import_should_detect_type = False
    options.import_as_skeletal = True
    options.mesh_type_to_import = u.FBXImportType.FBXIT_SKELETAL_MESH
    options.import_mesh = True
    options.import_animations = False
    options.import_materials = False
    options.import_textures = False
    options.create_physics_asset = False
    options.skeleton = skeleton
    data = options.skeletal_mesh_import_data
    for key, value in {"convert_scene": False, "convert_scene_unit": True,
                       "force_front_x_axis": False, "update_skeleton_reference_pose": False,
                       "use_t0_as_ref_pose": False, "import_morph_targets": False,
                       "keep_sections_separate": False}.items():
        data.set_editor_property(key, value)
    data.normal_import_method = u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    data.vertex_color_import_option = u.VertexColorImportOption.REPLACE
    task = u.AssetImportTask()
    for key, value in {"filename": str(source), "destination_path": DEST,
                       "destination_name": "SK_" + name, "automated": True,
                       "replace_existing": True, "replace_existing_settings": True,
                       "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError("FBX import failed: " + name)
    mesh = asset(DEST + "/SK_" + name)
    if mesh.get_editor_property("skeleton") != skeleton:
        raise RuntimeError("Guard did not retain the existing Manny skeleton")
    slots = list(mesh.get_editor_property("materials"))
    for slot in slots:
        slot.set_editor_property("material_interface", material)
    mesh.set_editor_property("materials", slots)
    if not u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
        raise RuntimeError("Could not save " + mesh.get_path_name())
    return mesh


def spawn(cls, label, location=(0, 0, 0), rotation=(0, 0, 0)):
    actor = actors.spawn_actor_from_class(cls, u.Vector(*location), u.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]))
    if actor is None:
        raise RuntimeError("Could not create " + label)
    actor.set_actor_label(label)
    return actor


def fit_map(guards):
    world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
    world.get_world_settings().set_editor_property("default_game_mode", u.GameModeBase)
    body = spawn(u.SkeletalMeshActor, "Manny — fitted outfit", rotation=(0, -90, 0))
    body_component = body.skeletal_mesh_component
    body_component.set_skeletal_mesh_asset(asset(MANNY + "SKM_Manny_Simple"))
    body_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    matte_body = asset(ARMOR + "Kabuto01/Review/M_FitMannequin")
    for slot in range(body_component.get_num_materials()):
        body_component.set_material(slot, matte_body)
    pieces = [asset(ARMOR + path) for path in (
        "Do01/SK_Do01", "Sode01/SK_Sode_L_01", "Sode01/SK_Sode_R_01",
        "Kusazuri01/SK_Kusazuri01")] + guards
    for mesh in pieces:
        piece = spawn(u.SkeletalMeshActor, mesh.get_name(), rotation=(0, -90, 0))
        component = piece.skeletal_mesh_component
        component.set_skeletal_mesh_asset(mesh)
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        component.set_leader_pose_component(body_component, True, False)
        piece.attach_to_actor(body, "", u.AttachmentRule.KEEP_WORLD,
                              u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False)
    # Match the measured native-Manny helmet placement used by the Dō review.
    contract = json.loads((ROOT / "SourceArt/Characters/Samurai/Do01/asset-manifest.json").read_text())["review_contract"]
    ox, oy, oz = contract["helmet_offset_from_head_cm"]
    offset = u.Vector(oy, -ox, oz)  # Native +Y-forward mesh rotated -90 degrees.
    helmet = spawn(u.StaticMeshActor, "Kabuto01", rotation=(0, -90, 0))
    helmet.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    helmet.static_mesh_component.set_static_mesh(asset(ARMOR + "Kabuto01/SM_Kabuto01"))
    helmet.set_actor_location(body_component.get_socket_location("head") + offset, False, False)
    helmet.attach_to_component(body_component, "head", u.AttachmentRule.KEEP_WORLD,
                               u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False)
    # A flat review floor removes the noisy engine default texture.
    floor_material = u.load_asset(DEST + "/M_ReviewFloor")
    if floor_material is None:
        floor_material = u.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_ReviewFloor", DEST, u.Material, u.MaterialFactoryNew())
        edit = u.MaterialEditingLibrary
        color = edit.create_material_expression(floor_material, u.MaterialExpressionConstant3Vector)
        color.set_editor_property("constant", u.LinearColor(.035, .040, .045, 1))
        roughness = edit.create_material_expression(floor_material, u.MaterialExpressionConstant)
        roughness.set_editor_property("r", .9)
        edit.connect_material_property(color, "", u.MaterialProperty.MP_BASE_COLOR)
        edit.connect_material_property(roughness, "", u.MaterialProperty.MP_ROUGHNESS)
        edit.recompile_material(floor_material)
        u.EditorAssetLibrary.save_loaded_asset(floor_material)
    ground = spawn(u.StaticMeshActor, "Review floor", location=(0, 0, -6))
    ground.static_mesh_component.set_static_mesh(asset("/Engine/BasicShapes/Cube"))
    ground.static_mesh_component.set_material(0, floor_material)
    ground.set_actor_scale3d(u.Vector(100, 100, .08))
    key = spawn(u.DirectionalLight, "Key light", rotation=(-40, -145, 0))
    key.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    key.light_component.set_intensity(.8)
    key.light_component.set_editor_property("dynamic_shadow_distance_movable_light", 1500.)
    key.light_component.set_editor_property("dynamic_shadow_cascades", 4)
    sky = spawn(u.SkyLight, "Soft environment")
    sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type", u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_cubemap(asset("/Engine/MapTemplates/Sky/DaylightAmbientCubemap"))
    sky.light_component.set_intensity(.45)
    cameras = []
    views = (("Front", (220, 0, 55), (0, 0, 37), 32.),
             ("ThreeQuarter", (194, 112, 57), (0, 0, 37), 32.),
             ("FullFront", (520, 0, 127), (0, 0, 105), 38.),
             ("FullThreeQuarter", (450, 260, 135), (0, 0, 105), 38.))
    for label, location, focus, field_of_view in views:
        rotation = u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*focus))
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location), rotation)
        camera.set_actor_label(label)
        camera.camera_component.set_field_of_view(field_of_view)
        camera.camera_component.set_editor_property("aspect_ratio", 4. / 3.)
        exposure = camera.camera_component.get_editor_property("post_process_settings")
        for prop, value in (("override_auto_exposure_method", True),
                            ("auto_exposure_method", u.AutoExposureMethod.AEM_MANUAL),
                            ("override_auto_exposure_apply_physical_camera_exposure", True),
                            ("auto_exposure_apply_physical_camera_exposure", False),
                            ("override_auto_exposure_bias", True), ("auto_exposure_bias", 3.)):
            exposure.set_editor_property(prop, value)
        camera.camera_component.set_editor_property("post_process_settings", exposure)
        cameras.append(camera)
    cameras[0].set_editor_property("auto_activate_for_player", u.AutoReceiveInput.PLAYER0)
    editor.set_level_viewport_camera_info(cameras[1].get_actor_location(), cameras[1].get_actor_rotation())
    actors.clear_actor_selection_set()
    if not u.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Could not save fitted outfit map")
    return [piece.get_path_name() for piece in pieces]


def capture():
    filename = Path(u.Paths.project_content_dir()) / (MAP.removeprefix("/Game/") + ".umap")
    world = u.EditorLoadingAndSavingUtils.load_map(str(filename))
    cameras = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()
               if isinstance(actor, u.CameraActor)}
    actors.clear_actor_selection_set()
    u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6, "start": time.monotonic()}
    views = ("Front", "ThreeQuarter")

    def tick(_delta):
        try:
            if time.monotonic() - state["start"] > 120:
                raise RuntimeError("Capture did not complete within 120 seconds")
            if state["task"] is not None:
                if not state["task"].is_task_done():
                    return
                state["task"] = None
                state["index"] += 1
                state["next"] = time.monotonic() + 3
            if state["index"] == len(views):
                u.unregister_slate_post_tick_callback(state["handle"])
                u.log("SUNEATE01_CAPTURES_SAVED " + str(OUT))
                u.SystemLibrary.quit_editor()
                return
            if time.monotonic() >= state["next"]:
                name = views[state["index"]]
                state["task"] = u.AutomationLibrary.take_high_res_screenshot(
                    1600, 1200, str(OUT / ("unreal-" + name.lower() + ".png")), camera=cameras[name], delay=1.)
                if state["task"] is None or not state["task"].is_valid_task():
                    raise RuntimeError("Could not request " + name + " screenshot")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            (OUT / "capture-error.txt").write_text(traceback.format_exc())
            u.log_error(traceback.format_exc())
            u.SystemLibrary.quit_editor()
    state["handle"] = u.register_slate_post_tick_callback(tick)


OUT.mkdir(parents=True, exist_ok=True)
if os.environ.get("SHOEN_SUNEATE_CAPTURE") == "1":
    capture()
else:
    skeleton, material = asset(MANNY + "SK_Mannequin"), material_variant()
    guards = [import_guard(side, skeleton, material) for side in ("L", "R")]
    fitted = fit_map(guards)
    (OUT / "unreal-import.json").write_text(json.dumps({"meshes": [mesh.get_path_name() for mesh in guards],
        "skeleton": skeleton.get_path_name(), "material": material.get_path_name(), "map": MAP,
        "fitted_pieces": fitted, "pose": "native Manny reference pose", "kote_present": False}, indent=2) + "\n")
    u.log("SUNEATE01_IMPORTED " + MAP)
