"""Import Smithy01 using the existing rural FBX/material workflow.

Default: import meshes and save a copy of the Granary settlement review map.
SHOEN_SMITHY_CAPTURE=1: capture the exterior and settlement context in rendered
PIE with -ShoenScenario=settlement. No gameplay or shared-material edits.
"""
import json
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/Smithy01"
OUT = ROOT / "artifacts/smithy01"
DEST = "/Game/Art/Buildings/Craft/Smithy01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
SOURCE_MAP = "/Game/Art/Buildings/Rural/Granary01/Review/Granary01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/Smithy01_Settlement"
SMITHY_POSITION = (1900.0, -1150.0, 0.0)
report = {"asset": "Smithy01", "imported": False}


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
    materials["SM01_Charcoal"] = simple_material("SM01_Charcoal", (0.009, 0.008, 0.007), 0.95)
    materials["SM01_Ember"] = simple_material("SM01_Ember", (0.3, 0.035, 0.004), 0.85,
                                            emission=(0.7, 0.077, 0.0028))
    materials["SM01_Water"] = simple_material("SM01_Water", (0.024, 0.057, 0.065), 0.22, 0.15)
    mesh = import_mesh("Smithy_01.fbx", "SM_Smithy_01", materials)
    import_mesh("Anvil_01.fbx", "SM_Anvil_01", materials)

    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
    require(world is not None, "Could not load existing Granary settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*SMITHY_POSITION), u.Rotator())
    require(actor is not None, "Could not place Smithy01")
    actor.set_actor_label("Smithy_01 - Settlement comparison")
    actor.tags = [u.Name("Smithy01"), u.Name("SettlementArt")]
    component = actor.static_mesh_component
    component.set_mobility(u.ComponentMobility.STATIC)
    component.set_static_mesh(mesh)
    component.set_collision_profile_name("BlockAllDynamic")
    component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)

    light_position = (SMITHY_POSITION[0] + 135.0, SMITHY_POSITION[1] + 5.0, 100.0)
    light = actors.spawn_actor_from_class(u.PointLight, u.Vector(*light_position), u.Rotator())
    require(light is not None, "Could not place forge light")
    light.set_actor_label("Smithy_01 - Warm forge light")
    light.tags = [u.Name("Smithy01")]
    light_component = light.get_component_by_class(u.PointLightComponent)
    require(light_component is not None, "Could not access forge light")
    light_component.set_mobility(u.ComponentMobility.MOVABLE)
    light_component.set_editor_property("intensity", 9.0)
    light_component.set_editor_property("attenuation_radius", 220.0)
    light_component.set_editor_property("light_color", u.Color(r=255, g=99, b=18, a=255))
    light_component.set_editor_property("cast_shadows", False)
    for placed in actors.get_all_level_actors():
        if placed.actor_has_tag("RuralHouse01ScaleFigure"):
            placed.set_actor_location(u.Vector(1540.0, -1460.0, 0.0), False, False)
    actors.clear_actor_selection_set()
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save Smithy review map")
    report.update(imported=True, mesh=mesh.get_path_name(), map=SETTLEMENT_MAP,
                  position_cm=SMITHY_POSITION, forge_light_position_cm=light_position)
    write_report("unreal-import.json", report)
    u.log("SMITHY_01_IMPORTED " + mesh.get_path_name())


def capture():
    require("-nullrhi" not in u.SystemLibrary.get_command_line().lower(), "Capture needs rendering")
    world=u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None,"Missing Smithy settlement")
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    # Temporary editor lighting and earth support the existing settlement layout.
    # They are review-only and are not saved into the gameplay map.
    ground=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-9),u.Rotator())
    ground.static_mesh_component.set_static_mesh(asset("/Engine/BasicShapes/Cube"))
    ground.static_mesh_component.set_material(0,simple_material("SM01_ReviewEarth",(.085,.095,.068),1.0))
    ground.set_actor_scale3d(u.Vector(1500,1500,.15))
    key=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,1500),u.Rotator(pitch=-42,yaw=-35,roll=0))
    key.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    key.light_component.set_intensity(2.4)
    key.light_component.set_editor_property("dynamic_shadow_distance_movable_light",10000.)
    key.light_component.set_editor_property("dynamic_shadow_cascades",4)
    sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(),u.Rotator())
    sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type",u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_cubemap(asset("/Engine/MapTemplates/Sky/DaylightAmbientCubemap"))
    sky.light_component.set_intensity(.7)
    views=(("three-quarter",(1160,-20,540),(1890,-1100,205),43.),
           ("settlement",(-700,2700,2250),(800,-650,140),43.))
    cameras={}
    for name,location,target,fov in views:
        camera=actors.spawn_actor_from_class(u.CameraActor,u.Vector(*location),
            u.MathLibrary.find_look_at_rotation(u.Vector(*location),u.Vector(*target)))
        camera.set_actor_label("Smithy review "+name)
        camera.camera_component.set_field_of_view(fov)
        camera.camera_component.set_editor_property("aspect_ratio",4./3.)
        exposure=camera.camera_component.get_editor_property("post_process_settings")
        for prop,value in (("override_auto_exposure_method",True),("auto_exposure_method",u.AutoExposureMethod.AEM_MANUAL),
                           ("override_auto_exposure_apply_physical_camera_exposure",True),("auto_exposure_apply_physical_camera_exposure",False),
                           ("override_auto_exposure_bias",True),("auto_exposure_bias",1.2)):
            exposure.set_editor_property(prop,value)
        camera.camera_component.set_editor_property("post_process_settings",exposure)
        camera.camera_component.set_editor_property("post_process_blend_weight",1.)
        cameras[name]=camera
    actors.clear_actor_selection_set()
    u.AutomationLibrary.set_editor_viewport_view_mode(u.ViewModeIndex.VMI_LIT)
    u.AutomationLibrary.finish_loading_before_screenshot()
    state={"index":0,"task":None,"next":time.monotonic()+6,"start":time.monotonic(),"results":[]}
    def tick(_delta):
        try:
            require(time.monotonic()-state["start"]<120,"Smithy screenshot timed out")
            if state["task"] is not None:
                if not state["task"].is_task_done():return
                name=views[state["index"]][0]
                path=OUT/("unreal-"+name+".png")
                require(path.is_file(),"Missing screenshot "+str(path))
                state["results"].append(str(path));state["task"]=None;state["index"]+=1;state["next"]=time.monotonic()+3
            if state["index"]==len(views):
                u.unregister_slate_post_tick_callback(state["handle"])
                write_report("capture.json",{"rendered":True,"map":SETTLEMENT_MAP,"mode":"Metal editor; existing settlement layout; temporary review lighting","captures":state["results"]})
                u.SystemLibrary.quit_editor();return
            if time.monotonic()>=state["next"]:
                name=views[state["index"]][0]
                state["task"]=u.AutomationLibrary.take_high_res_screenshot(1600,1200,str(OUT/("unreal-"+name+".png")),camera=cameras[name],delay=1.)
                require(state["task"] is not None and state["task"].is_valid_task(),"Screenshot request failed")
        except Exception:
            u.unregister_slate_post_tick_callback(state["handle"])
            write_report("capture.json",{"rendered":False,"error":traceback.format_exc()})
            u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
    state["handle"]=u.register_slate_post_tick_callback(tick)


try:
    if os.environ.get("SHOEN_SMITHY_CAPTURE") == "1":
        main()
        capture()
    else:
        main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report("unreal-import.json", report)
    raise
