"""Import the quiver and arrows into a copy of the complete Kote outfit review.

Use -ExecutePythonScript for import. For rendered views, set
SHOEN_QUIVER_CAPTURE=1 and use -ExecCmds="py <this script>" without NullRHI.
Run one Unreal process at a time. Existing outfit assets and maps are read-only.
"""
import json
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Characters/Samurai/Quiver01"
DEST = "/Game/Art/Characters/Samurai/Quiver01"
MAP = DEST + "/Quiver01_Fitted"
SOURCE_MAP = "/Game/Art/Characters/Samurai/Kote01/Kote01_Fitted"
QUIVER_MATERIAL = "/Game/Art/Characters/Samurai/Kote01/M_Kote01"
ARROW_MATERIAL = DEST + "/M_Arrow01"
OUT = ROOT / "artifacts/quiver01"
BODY_LABEL = "Manny — fitted outfit"
VIEWS = (
    ("Back", (-390, 0, 125), (0, 0, 100), 38.),
    ("ThreeQuarter", (-350, 230, 137), (0, 0, 103), 38.),
    ("Close", (-165, 115, 177), (-15, 0, 151), 31.),
    ("Front", (390, 0, 125), (0, 0, 100), 38.),
    ("Side", (0, 390, 125), (0, 0, 100), 38.),
    ("Tactical", (-560, 420, 440), (0, 0, 100), 38.),
)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)


def asset(path):
    obj = u.load_asset(path)
    if obj is None:
        raise RuntimeError("Missing existing asset: " + path)
    return obj


def arrow_material():
    """Match the authored ArrowSurface RGB color and alpha metallic channel."""
    material = u.load_asset(ARROW_MATERIAL)
    if material is None:
        material = u.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_Arrow01", DEST, u.Material, u.MaterialFactoryNew())
    if material is None:
        raise RuntimeError("Could not create " + ARROW_MATERIAL)
    edit = u.MaterialEditingLibrary
    edit.delete_all_material_expressions(material)
    material.set_editor_property("blend_mode", u.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("two_sided", False)
    color = edit.create_material_expression(material, u.MaterialExpressionVertexColor)
    color.set_editor_property("desc", "ArrowSurface: RGB color, alpha metallic")
    roughness = edit.create_material_expression(material, u.MaterialExpressionConstant)
    roughness.set_editor_property("r", .55)
    for node, channel, prop in (
        (color, "", u.MaterialProperty.MP_BASE_COLOR),
        (color, "A", u.MaterialProperty.MP_METALLIC),
        (roughness, "", u.MaterialProperty.MP_ROUGHNESS),
    ):
        if not edit.connect_material_property(node, channel, prop):
            raise RuntimeError("Could not connect arrow material " + str(prop))
    errors = list(edit.recompile_material(material))
    if errors:
        raise RuntimeError("Arrow material compilation: " + "; ".join(errors))
    if not u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError("Could not save " + ARROW_MATERIAL)
    return material


def import_mesh(name, material):
    source = ART / "Exports" / (name + ".fbx")
    if not source.is_file():
        raise RuntimeError("Missing FBX: " + str(source))
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
    for key, value in {
        "convert_scene": False,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "combine_meshes": True,
        "auto_generate_collision": False,
        "generate_lightmap_u_vs": False,
    }.items():
        data.set_editor_property(key, value)
    data.normal_import_method = u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    data.vertex_color_import_option = u.VertexColorImportOption.REPLACE
    task = u.AssetImportTask()
    for key, value in {
        "filename": str(source), "destination_path": DEST,
        "destination_name": "SM_" + name, "automated": True,
        "replace_existing": True, "replace_existing_settings": True,
        "save": False, "options": options, "factory": u.FbxFactory(),
    }.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError("FBX import failed: " + name)
    mesh = asset(DEST + "/SM_" + name)
    for slot in range(u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_number_materials(mesh)):
        mesh.set_material(slot, material)
    if not u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
        raise RuntimeError("Could not save " + mesh.get_path_name())
    return mesh


def map_filename(path):
    return str(Path(u.Paths.project_content_dir()) / (path.removeprefix("/Game/") + ".umap"))


def fit_map(quiver, bundle):
    if not Path(map_filename(MAP)).exists():
        world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
        if not u.EditorLoadingAndSavingUtils.save_map(world, MAP):
            raise RuntimeError("Could not copy fitted outfit map to " + MAP)
    # Save As writes a copy; explicitly load it before modifying any actors.
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(MAP))
    if world is None:
        raise RuntimeError("Could not load copied outfit map")
    for actor in list(actors.get_all_level_actors()):
        if actor.get_actor_label() in ("Quiver_01", "ArrowBundle_01", "Quiver soft rear key", "Outfit viewing exposure"):
            actors.destroy_actor(actor)
    body = next((actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label() == BODY_LABEL
                 and isinstance(actor, u.SkeletalMeshActor)), None)
    if body is None:
        raise RuntimeError("Existing fitted Manny was not found")
    body_component = body.skeletal_mesh_component
    if not body_component.does_socket_exist("spine_03"):
        raise RuntimeError("Existing native Manny spine_03 is missing")
    for mesh, label in ((quiver, "Quiver_01"), (bundle, "ArrowBundle_01")):
        actor = actors.spawn_actor_from_class(
            u.StaticMeshActor, u.Vector(0, 0, 0), u.Rotator(pitch=0, yaw=-90, roll=0))
        if actor is None:
            raise RuntimeError("Could not create " + label)
        actor.set_actor_label(label)
        component = actor.static_mesh_component
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_static_mesh(mesh)
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        # Full-body FBX coordinates match the already-fitted native outfit.
        actor.attach_to_component(body_component, "spine_03", u.AttachmentRule.KEEP_WORLD,
                                  u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False)
    for actor in list(actors.get_all_level_actors()):
        if isinstance(actor, u.CameraActor):
            actors.destroy_actor(actor)
    rear = actors.spawn_actor_from_class(
        u.DirectionalLight, u.Vector(0, 0, 0), u.Rotator(pitch=-35, yaw=15, roll=0))
    rear.set_actor_label("Quiver soft rear key")
    rear.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    rear.light_component.set_intensity(.35)
    rear.light_component.set_editor_property("light_source_angle", 6.)
    rear.light_component.set_editor_property("dynamic_shadow_distance_movable_light", 1500.)
    cameras = []
    for label, location, focus, field_of_view in VIEWS:
        rotation = u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*focus))
        camera = actors.spawn_actor_from_class(u.CameraActor, u.Vector(*location), rotation)
        camera.set_actor_label(label)
        camera.camera_component.set_field_of_view(field_of_view)
        camera.camera_component.set_editor_property("aspect_ratio", 1600. / 1400.)
        exposure = camera.camera_component.get_editor_property("post_process_settings")
        for prop, value in (
            ("override_auto_exposure_method", True),
            ("auto_exposure_method", u.AutoExposureMethod.AEM_MANUAL),
            ("override_auto_exposure_apply_physical_camera_exposure", True),
            ("auto_exposure_apply_physical_camera_exposure", False),
            ("override_auto_exposure_bias", True), ("auto_exposure_bias", 3.),
        ):
            exposure.set_editor_property(prop, value)
        camera.camera_component.set_editor_property("post_process_settings", exposure)
        camera.camera_component.set_editor_property("post_process_blend_weight", 1.)
        cameras.append(camera)
    cameras[0].set_editor_property("auto_activate_for_player", u.AutoReceiveInput.PLAYER0)
    volume = actors.spawn_actor_from_class(u.PostProcessVolume, u.Vector(0, 0, 0))
    volume.set_actor_label("Outfit viewing exposure")
    volume.set_editor_property("unbound", True)
    volume.set_editor_property("settings", cameras[0].camera_component.get_editor_property("post_process_settings"))
    editor.set_level_viewport_camera_info(cameras[1].get_actor_location(), cameras[1].get_actor_rotation())
    actors.clear_actor_selection_set()
    if not u.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Could not save " + MAP)


def capture():
    if u.EditorLoadingAndSavingUtils.load_map(map_filename(MAP)) is None:
        raise RuntimeError("Could not load " + MAP)
    cameras = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()
               if isinstance(actor, u.CameraActor)}
    for actor in actors.get_all_level_actors():
        if isinstance(actor, u.DirectionalLight):
            actor.light_component.set_forward_shading_priority(
                0 if actor.get_actor_label() == "Quiver soft rear key" else 1)
    u.EditorLoadingAndSavingUtils.save_current_level()
    views = [view[0] for view in VIEWS]
    if any(name not in cameras for name in views):
        raise RuntimeError("The fitted map is missing a requested review camera")
    actors.clear_actor_selection_set()
    u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"index": 0, "task": None, "next": time.monotonic() + 6, "start": time.monotonic()}

    def tick(_delta):
        try:
            if time.monotonic() - state["start"] > 180:
                raise RuntimeError("Capture did not complete within 180 seconds")
            if state["task"] is not None:
                if not state["task"].is_task_done():
                    return
                state["task"] = None
                state["index"] += 1
                state["next"] = time.monotonic() + 3
            if state["index"] == len(views):
                u.unregister_slate_post_tick_callback(state["handle"])
                u.log("QUIVER01_CAPTURES_SAVED " + str(OUT))
                if os.environ.get("SHOEN_QUIVER_KEEP_OPEN") != "1":
                    u.SystemLibrary.quit_editor()
                return
            if time.monotonic() >= state["next"]:
                name = views[state["index"]]
                state["task"] = u.AutomationLibrary.take_high_res_screenshot(
                    1600, 1400, str(OUT / ("unreal-" + name.lower() + ".png")),
                    camera=cameras[name], delay=1.)
                if state["task"] is None or not state["task"].is_valid_task():
                    raise RuntimeError("Could not request " + name + " screenshot")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            (OUT / "capture-error.txt").write_text(traceback.format_exc())
            u.log_error(traceback.format_exc())
            if os.environ.get("SHOEN_QUIVER_KEEP_OPEN") != "1":
                u.SystemLibrary.quit_editor()
    state["handle"] = u.register_slate_post_tick_callback(tick)


OUT.mkdir(parents=True, exist_ok=True)
if os.environ.get("SHOEN_QUIVER_CAPTURE") == "1":
    capture()
else:
    quiver_material = asset(QUIVER_MATERIAL)
    arrows_material = arrow_material()
    quiver = import_mesh("Quiver_01", quiver_material)
    bundle = import_mesh("ArrowBundle_01", arrows_material)
    arrow = import_mesh("Arrow_01", arrows_material)
    fit_map(quiver, bundle)
    (OUT / "unreal-import.json").write_text(json.dumps({
        "meshes": [mesh.get_path_name() for mesh in (quiver, bundle, arrow)],
        "quiver_material": quiver_material.get_path_name(),
        "arrow_material": arrows_material.get_path_name(),
        "source_map": SOURCE_MAP, "map": MAP,
        "attachment_bone": "spine_03", "pose": "native Manny reference pose",
        "standalone_arrow_in_review_scene": False,
    }, indent=2) + "\n")
    u.log("QUIVER01_IMPORTED " + MAP)
