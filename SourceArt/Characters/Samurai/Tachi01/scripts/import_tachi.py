"""Import Tachi01, fit it in a copy of the existing outfit map, capture once.

Run in the normal Metal editor with -ExecCmds="py <absolute script path>".
Leaves the fitted map open; SHOEN_TACHI_KEEP_OPEN=0 closes a batch editor.
"""
import json
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Characters/Samurai/Tachi01"
DEST = "/Game/Art/Characters/Samurai/Tachi01"
MAP = DEST + "/Tachi01_Fitted"
OUT = ROOT / "artifacts/tachi01"
BASE_MAP = "/Game/Art/Characters/Samurai/Kote01/Kote01_Fitted"
TOOLS = u.AssetToolsHelpers.get_asset_tools()
ACTORS = u.get_editor_subsystem(u.EditorActorSubsystem)
EDITOR = u.get_editor_subsystem(u.UnrealEditorSubsystem)


def asset(path):
    result = u.load_asset(path)
    if result is None:
        raise RuntimeError("Missing asset: " + path)
    return result


def import_file(path, name, mesh=False):
    if not path.is_file():
        raise RuntimeError("Missing export: " + str(path))
    task = u.AssetImportTask()
    for key, value in dict(filename=str(path), destination_path=DEST,
                           destination_name=name, automated=True, replace_existing=True,
                           replace_existing_settings=True, save=False).items():
        task.set_editor_property(key, value)
    if mesh:
        options = u.FbxImportUI()
        options.automated_import_should_detect_type = False
        options.import_as_skeletal = False
        options.mesh_type_to_import = u.FBXImportType.FBXIT_STATIC_MESH
        options.import_mesh = True
        options.import_animations = False
        options.import_materials = False
        options.import_textures = False
        data = options.static_mesh_import_data
        for key, value in dict(convert_scene=False, convert_scene_unit=True,
                               force_front_x_axis=False, combine_meshes=True,
                               auto_generate_collision=False, generate_lightmap_u_vs=False).items():
            data.set_editor_property(key, value)
        data.normal_import_method = u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        data.vertex_color_import_option = u.VertexColorImportOption.REPLACE
        task.options = options
        task.factory = u.FbxFactory()
    TOOLS.import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError("Import failed: " + str(path))
    return asset(DEST + "/" + name)


def pbr_material(prefix, material_name, normal=False):
    textures = {}
    suffixes = ("BaseColor", "Normal", "ORM") if normal else ("BaseColor", "ORM")
    for suffix in suffixes:
        name = prefix + suffix
        texture = import_file(ART / "Textures" / (name + ".png"), name)
        texture.set_editor_property("srgb", suffix == "BaseColor")
        if suffix == "ORM":
            texture.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_MASKS)
        elif suffix == "Normal":
            texture.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property("flip_green_channel", True)
        u.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
        textures[suffix] = texture
    material = u.load_asset(DEST + "/" + material_name)
    if material is None:
        material = TOOLS.create_asset(material_name, DEST, u.Material, u.MaterialFactoryNew())
    edit = u.MaterialEditingLibrary
    edit.delete_all_material_expressions(material)
    if normal:
        response = edit.create_material_expression(material, u.MaterialExpressionVertexColor)
        edit.connect_material_property(response, "R", u.MaterialProperty.MP_SPECULAR)
    for suffix in suffixes:
        sample = edit.create_material_expression(material, u.MaterialExpressionTextureSample)
        sample.set_editor_property("texture", textures[suffix])
        if suffix == "ORM":
            sample.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_MASKS)
            outputs = (("R", u.MaterialProperty.MP_AMBIENT_OCCLUSION),
                       ("G", u.MaterialProperty.MP_ROUGHNESS),
                       ("B", u.MaterialProperty.MP_METALLIC))
        elif suffix == "Normal":
            sample.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
            outputs = (("RGB", u.MaterialProperty.MP_NORMAL),)
        else:
            outputs = (("RGB", u.MaterialProperty.MP_BASE_COLOR),)
        for channel, property_ in outputs:
            edit.connect_material_property(sample, channel, property_)
    edit.recompile_material(material)
    u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def sword_actor(label, mesh, location, rotation, component, bone, hidden=False):
    actor = ACTORS.spawn_actor_from_class(u.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
    actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.attach_to_component(component, bone, u.AttachmentRule.KEEP_WORLD,
                              u.AttachmentRule.KEEP_WORLD, u.AttachmentRule.KEEP_WORLD, False)
    actor.static_mesh_component.set_visibility(not hidden)
    actor.set_actor_hidden_in_game(hidden)
    return actor


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    shared = pbr_material("T_Tachi01_", "M_Tachi01_Fittings", normal=True)
    steel = pbr_material("T_Tachi01_Steel_", "M_Tachi01_Steel")
    meshes = {}
    for state in ("Sheathed", "Drawn", "Saya"):
        name = "SM_Tachi01_" + state
        mesh = import_file(ART / "exports" / (name + ".fbx"), name, mesh=True)
        slots = list(mesh.get_editor_property("static_materials"))
        for index, slot in enumerate(slots):
            name = str(slot.get_editor_property("material_slot_name"))
            mesh.set_material(index, steel if "Steel" in name else shared)
        u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        meshes[state] = mesh

    filename = Path(u.Paths.project_content_dir()) / (BASE_MAP.removeprefix("/Game/") + ".umap")
    world = u.EditorLoadingAndSavingUtils.load_map(str(filename))
    body = next(actor for actor in ACTORS.get_all_level_actors()
                if actor.get_actor_label() == "Manny — fitted outfit")
    component = body.skeletal_mesh_component
    bone = "sword_socket" if component.does_socket_exist("sword_socket") else "pelvis"
    # Blender: (0.255, -0.12, 0.97) m. FBX reflects Y; outfit actor rotates -90°.
    location = u.Vector(12, -25.5, 97)
    rotation = u.Rotator(pitch=-17.5, yaw=180, roll=0)
    sword_actor("Tachi01 — sheathed at left hip", meshes["Sheathed"], location, rotation, component, bone)
    sword_actor("Tachi01 — separate saya (hidden)", meshes["Saya"], location, rotation, component, bone, True)
    drawn_rotation = u.Rotator(pitch=-82, yaw=180, roll=0)
    hand = component.get_socket_location("hand_r")
    grip_to_guard = u.MathLibrary.get_forward_vector(drawn_rotation) * 12.0
    sword_actor("Tachi01 — drawn at hand_r (hidden)", meshes["Drawn"], hand + grip_to_guard,
                drawn_rotation, component, "hand_r", True)

    old_camera = next(actor for actor in ACTORS.get_all_level_actors() if isinstance(actor, u.CameraActor))
    camera_location = u.Vector(195, -370, 150)
    camera_rotation = u.MathLibrary.find_look_at_rotation(camera_location, u.Vector(-8, -10, 107))
    camera = ACTORS.spawn_actor_from_class(u.CameraActor, camera_location, camera_rotation)
    camera.set_actor_label("Tachi01 — on-character")
    camera.camera_component.set_field_of_view(33)
    camera.camera_component.set_editor_property("aspect_ratio", 1.125)
    camera.camera_component.set_editor_property("post_process_settings",
        old_camera.camera_component.get_editor_property("post_process_settings"))
    camera.camera_component.set_editor_property("post_process_blend_weight", 1.)
    for existing in ACTORS.get_all_level_actors():
        if isinstance(existing, u.CameraActor):
            existing.set_editor_property("auto_activate_for_player", u.AutoReceiveInput.DISABLED)
    camera.set_editor_property("auto_activate_for_player", u.AutoReceiveInput.PLAYER0)
    EDITOR.set_level_viewport_camera_info(camera_location, camera_rotation)
    ACTORS.clear_actor_selection_set()
    if not u.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Could not save " + MAP)
    (OUT / "unreal-import.json").write_text(json.dumps({
        "meshes": [mesh.get_path_name() for mesh in meshes.values()], "map": MAP,
        "hip_attachment": bone, "drawn_attachment": "hand_r",
        "materials": [shared.get_path_name(), steel.get_path_name()],
        "preview": "Sheathed visible; hide it and show separate saya + drawn actors to preview drawn state."
    }, indent=2) + "\n")
    u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state = {"task": None, "ready": time.monotonic() + 8, "start": time.monotonic()}

    def tick(_delta):
        try:
            if time.monotonic() - state["start"] > 120:
                raise RuntimeError("Tachi screenshot timed out")
            if state["task"] is not None:
                if not state["task"].is_task_done():
                    return
                u.unregister_slate_post_tick_callback(state["handle"])
                u.log("TACHI01_IMPORTED_AND_CAPTURED " + MAP)
                if os.environ.get("SHOEN_TACHI_KEEP_OPEN", "1") != "1":
                    u.SystemLibrary.quit_editor()
                return
            if time.monotonic() >= state["ready"]:
                state["task"] = u.AutomationLibrary.take_high_res_screenshot(
                    1800, 1600, str(OUT / "unreal-on-character.png"), camera=camera, delay=1.)
                if state["task"] is None or not state["task"].is_valid_task():
                    raise RuntimeError("Could not request on-character screenshot")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            (OUT / "capture-error.txt").write_text(traceback.format_exc())
            u.log_error(traceback.format_exc())
            if os.environ.get("SHOEN_TACHI_KEEP_OPEN", "1") != "1":
                u.SystemLibrary.quit_editor()
    state["handle"] = u.register_slate_post_tick_callback(tick)


main()
