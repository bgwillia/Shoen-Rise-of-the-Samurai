"""Import the paired Kote and save a fitted, neutral-pose outfit map.

Use -ExecutePythonScript for import, then open the saved map normally.
For Metal captures, run with -ExecCmds="py <this script>" and environment
SHOEN_KOTE_CAPTURE=1; this mode loads the map, captures front, three-quarter and bent elbows, then quits.
Set SHOEN_KOTE_KEEP_OPEN=1 to return to the neutral fitted map after capture.
Run one Unreal process at a time. Existing outfit packages remain read-only.
"""
import json
import os
from pathlib import Path
import re
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Characters/Samurai/Kote01"
DEST = "/Game/Art/Characters/Samurai/Kote01"
MAP = DEST + "/Kote01_Fitted"
OUT = ROOT / "artifacts/kote01"
MANNY = "/Game/Characters/Mannequins/Meshes/"
ARMOR = "/Game/Art/Characters/Samurai/"
SOURCE_MATERIAL = ARMOR + "Kusazuri01/M_Kusazuri01"
MATERIAL = DEST + "/M_Kote01"
BODY_LABEL = "Manny — fitted outfit"
VIEWS = (("Front", (320, 0, 137), (0, 0, 132), 38.),
         ("ThreeQuarter", (270, 190, 145), (0, 0, 132), 38.),
         ("BentElbows", (270, 190, 145), (0, 0, 132), 38.))
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)


def asset(path):
    obj = u.load_asset(path)
    if obj is None:
        raise RuntimeError("Missing existing asset: " + path)
    return obj


def kote_material():
    """Clone the existing atlas material; darken only the leather tile."""
    source = asset(SOURCE_MATERIAL)
    material = u.load_asset(MATERIAL)
    if material is None:
        material = u.EditorAssetLibrary.duplicate_asset(SOURCE_MATERIAL, MATERIAL)
    if material is None:
        raise RuntimeError("Could not duplicate the shared Kote material")
    edit = u.MaterialEditingLibrary

    def palette(mat):
        matches = [expression for expression in edit.get_material_expressions(mat)
                   if isinstance(expression, u.MaterialExpressionCustom)
                   and expression.get_editor_property("description") == "Sode restrained atlas palette"
                   and expression.get_editor_property("output_type") == u.CustomMaterialOutputType.CMOT_FLOAT3]
        if len(matches) != 1:
            raise RuntimeError("Expected exactly one inherited atlas palette in " + mat.get_path_name())
        return matches[0]

    code = palette(source).get_editor_property("code")
    branch = "if (tile == 4.0) return float3(0.17, 0.15, 0.13);"
    pattern = r"if\s*\(\s*tile\s*==\s*4(?:\.0)?\s*\)\s*return\s*float3\([^;]+;"
    code, changed = re.subn(pattern, branch, code)
    if changed > 1:
        raise RuntimeError("Ambiguous leather tile in shared atlas palette")
    if changed == 0:
        declarations = list(re.finditer(r"(?m)^\s*float\s+tile\s*=.*;", code))
        if len(declarations) != 1:
            raise RuntimeError("Expected one atlas tile declaration")
        at = declarations[0].end()
        code = code[:at] + "\n" + branch + code[at:]
    palette(material).set_editor_property("code", code)
    errors = list(edit.recompile_material(material))
    if errors:
        raise RuntimeError("Kote material compilation: " + "; ".join(errors))
    if not u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError("Could not save " + MATERIAL)
    return material


def import_guard(side, skeleton, material):
    name = "Kote_" + side + "_01"
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
    body = spawn(u.SkeletalMeshActor, BODY_LABEL, rotation=(0, -90, 0))
    body_component = body.skeletal_mesh_component
    body_component.set_skeletal_mesh_asset(asset(MANNY + "SKM_Manny_Simple"))
    body_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    matte_body = asset(ARMOR + "Kabuto01/Review/M_FitMannequin")
    for slot in range(body_component.get_num_materials()):
        body_component.set_material(slot, matte_body)
    pieces = [asset(ARMOR + path) for path in (
        "Do01/SK_Do01", "Sode01/SK_Sode_L_01", "Sode01/SK_Sode_R_01",
        "Kusazuri01/SK_Kusazuri01", "Suneate01/SK_Suneate_L_01",
        "Suneate01/SK_Suneate_R_01")] + guards
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
    floor_material = matte_body
    ground = spawn(u.StaticMeshActor, "Review floor", location=(0, 0, -5))
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
    for label, location, focus, field_of_view in VIEWS:
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
        camera.camera_component.set_editor_property("post_process_blend_weight", 1.)
        cameras.append(camera)
    cameras[0].set_editor_property("auto_activate_for_player", u.AutoReceiveInput.PLAYER0)
    editor.set_level_viewport_camera_info(cameras[1].get_actor_location(), cameras[1].get_actor_rotation())
    actors.clear_actor_selection_set()
    if not u.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Could not save fitted outfit map")
    return [piece.get_path_name() for piece in pieces]


def bent_elbows():
    """Flex the native elbows 75 degrees with the rest of the outfit at rest.

    Only two lower-arm rotations change. Their hand/finger descendants follow
    normally; existing Sode/Kusazuri helper bones retain the fitted pose. The
    poseable component is capture-only and no animation asset is created.
    """
    body = next(actor for actor in actors.get_all_level_actors()
                if actor.get_actor_label() == BODY_LABEL)
    source = body.skeletal_mesh_component
    # The instance subobject facility registers a component without a new BP.
    subsystem = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_instance(body)
    handle, reason = subsystem.add_new_subobject(u.AddNewSubobjectParams(
        parent_handle=handles[0], new_class=u.PoseableMeshComponent))
    library = u.SubobjectDataBlueprintFunctionLibrary
    if not library.is_handle_valid(handle):
        raise RuntimeError("Could not create temporary elbow pose: " + str(reason))
    pose = library.get_associated_object(library.get_data(handle))
    pose.set_skinned_asset_and_update(asset(MANNY + "SKM_Manny_Simple"))
    pose.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    for slot in range(source.get_num_materials()):
        pose.set_material(slot, source.get_material(slot))
    pose.copy_pose_from_skeletal_component(source)

    def length(v):
        return (v.x * v.x + v.y * v.y + v.z * v.z) ** .5

    def normal(v):
        magnitude = length(v)
        if magnitude < 1.e-7:
            raise RuntimeError("Degenerate elbow hinge")
        return u.Vector(v.x / magnitude, v.y / magnitude, v.z / magnitude)

    def cross(a, b):
        return u.Vector(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z,
                        a.x * b.y - a.y * b.x)

    wrists = {}
    for side in ("l", "r"):
        shoulder = source.get_socket_location("upperarm_" + side)
        transform = source.get_socket_transform("lowerarm_" + side, u.RelativeTransformSpace.RTS_WORLD)
        elbow = source.get_socket_location("lowerarm_" + side)
        wrists[side] = source.get_socket_location("hand_" + side)
        upper, lower = normal(elbow - shoulder), normal(wrists[side] - elbow)
        axis = cross(upper, lower)
        # The authored reference arms are almost straight. Fall back to the
        # native character's forward direction if its hinge plane is unstable.
        if length(axis) < .02:
            axis = cross(lower, u.Vector(1, 0, 0))
        axis = normal(axis)
        if cross(axis, lower).x < 0:
            axis = u.Vector(-axis.x, -axis.y, -axis.z)
        delta = u.MathLibrary.rotator_from_axis_and_angle(axis, 75.).quaternion()
        transform.set_editor_property("rotation", delta * transform.rotation)
        pose.set_bone_transform_by_name("lowerarm_" + side, transform, u.BoneSpaces.WORLD_SPACE)

    # Poseable meshes do not tick in editor worlds. The forced leader update
    # calls AllocateTransformData -> FillComponentSpaceTransforms -> Finalize;
    # it preserves these local transforms and publishes the bent socket pose.
    pose.set_leader_pose_component(None, True, False)
    pose.set_visibility(False, False)
    pose.set_visibility(True, False)
    for side in ("l", "r"):
        displacement = length(pose.get_socket_location("hand_" + side) - wrists[side])
        if displacement < 5.:
            raise RuntimeError("Elbow pose did not reach renderer: " + side)
        u.log("KOTE01_ELBOW_" + side.upper() + " wrist displacement cm=" + str(round(displacement, 2)))
    source.set_visibility(False, False)
    for actor in actors.get_all_level_actors():
        if isinstance(actor, u.SkeletalMeshActor) and actor != body:
            actor.skeletal_mesh_component.set_leader_pose_component(pose, True, False)
    u.log("KOTE01_BENT_ELBOWS 75-degree flexion; lower-arm rotations only")


def capture():
    filename = Path(u.Paths.project_content_dir()) / (MAP.removeprefix("/Game/") + ".umap")
    world = u.EditorLoadingAndSavingUtils.load_map(str(filename))
    cameras = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()
               if isinstance(actor, u.CameraActor)}
    # Correct the existing saved cameras without reimporting either mesh.
    for label, location, focus, field_of_view in VIEWS:
        camera = cameras[label]
        camera.set_actor_location(u.Vector(*location), False, False)
        camera.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*focus)), False)
        camera.camera_component.set_field_of_view(field_of_view)
        exposure = camera.camera_component.get_editor_property("post_process_settings")
        exposure.set_editor_property("override_auto_exposure_bias", True)
        exposure.set_editor_property("auto_exposure_bias", 3.)
        camera.camera_component.set_editor_property("post_process_settings", exposure)
        camera.camera_component.set_editor_property("post_process_blend_weight", 1.)
    if not u.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Could not save the corrected review cameras")
    actors.clear_actor_selection_set()
    u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6, "start": time.monotonic()}
    views = ("Front", "ThreeQuarter", "BentElbows")

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
                u.log("KOTE01_CAPTURES_SAVED " + str(OUT))
                if os.environ.get("SHOEN_KOTE_KEEP_OPEN") == "1":
                    u.EditorLoadingAndSavingUtils.load_map(str(filename))
                    camera = next(actor for actor in actors.get_all_level_actors()
                                  if isinstance(actor, u.CameraActor) and actor.get_actor_label() == "BentElbows")
                    editor.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
                    level_editor = u.get_editor_subsystem(u.LevelEditorSubsystem)
                    if level_editor is not None:
                        level_editor.pilot_level_actor(camera)
                    actors.clear_actor_selection_set()
                else:
                    u.SystemLibrary.quit_editor()
                return
            if time.monotonic() >= state["next"]:
                name = views[state["index"]]
                if name == "BentElbows":
                    bent_elbows()
                state["task"] = u.AutomationLibrary.take_high_res_screenshot(
                    1600, 1200, str(OUT / ("unreal-" + name.lower() + ".png")), camera=cameras[name], delay=1.)
                if state["task"] is None or not state["task"].is_valid_task():
                    raise RuntimeError("Could not request " + name + " screenshot")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            (OUT / "capture-error.txt").write_text(traceback.format_exc())
            u.log_error(traceback.format_exc())
            if os.environ.get("SHOEN_KOTE_KEEP_OPEN") != "1":
                u.SystemLibrary.quit_editor()
    state["handle"] = u.register_slate_post_tick_callback(tick)


OUT.mkdir(parents=True, exist_ok=True)
if os.environ.get("SHOEN_KOTE_CAPTURE") == "1":
    capture()
else:
    skeleton, material = asset(MANNY + "SK_Mannequin"), kote_material()
    guards = [import_guard(side, skeleton, material) for side in ("L", "R")]
    fitted = fit_map(guards)
    (OUT / "unreal-import.json").write_text(json.dumps({"meshes": [mesh.get_path_name() for mesh in guards],
        "skeleton": skeleton.get_path_name(), "material": material.get_path_name(), "map": MAP,
        "fitted_pieces": fitted, "pose": "native Manny reference pose", "kote_present": True}, indent=2) + "\n")
    u.log("KOTE01_IMPORTED " + MAP)
