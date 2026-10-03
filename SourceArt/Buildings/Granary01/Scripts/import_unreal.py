"""Import Granary01 with shared rural materials and save its settlement comparison map."""
import json
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/Granary01"
OUT = ROOT / "artifacts/granary01"
DEST = "/Game/Art/Buildings/Rural/Granary01"
RH_DEST = "/Game/Art/Buildings/Rural/RuralHouse01"
SH_DEST = "/Game/Art/Buildings/Rural/Storehouse01"
SOURCE_MAP = RH_DEST + "/Review/RuralHouse01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/Granary01_Settlement"
GRANARY_POSITION = (850.0, -1150.0, 0.0)
report = {"asset": "Granary01", "imported": False}


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


def main():
    source = ART / "Exports/Granary_01.fbx"
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
                       "destination_name": "SM_Granary_01", "automated": True,
                       "replace_existing": True, "replace_existing_settings": True,
                       "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    require(task.imported_object_paths, "Granary FBX import failed")
    mesh = asset(DEST + "/SM_Granary_01")
    materials = {"SH01_" + family: asset(SH_DEST + "/M_SH01_" + family)
                 for family in ("Thatch", "Timber", "Plaster", "Stone", "Iron")}
    materials["RH01_Rope"] = asset(SH_DEST + "/M_SH01_Rope")
    slots = [str(item.get_editor_property("material_slot_name"))
             for item in mesh.get_editor_property("static_materials")]
    require(slots and all(slot in materials for slot in slots), "Unexpected slots: " + repr(slots))
    for index, slot in enumerate(slots):
        mesh.set_material(index, materials[slot])
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    require(editor.remove_collisions(mesh), "Could not clear granary collision")
    require(editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX) >= 0,
            "Could not add granary box collision")
    require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), "Could not save granary")

    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
    require(world is not None, "Could not load existing rural-house settlement")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)

    def place(mesh_asset, label, location, tag):
        actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*location), u.Rotator())
        require(actor is not None, "Could not place " + label)
        actor.set_actor_label(label)
        actor.tags = [u.Name(tag), u.Name("SettlementArt")]
        component = actor.static_mesh_component
        component.set_mobility(u.ComponentMobility.STATIC)
        component.set_static_mesh(mesh_asset)
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        return actor

    place(mesh, "Granary_01 - Settlement comparison", GRANARY_POSITION, "Granary01")
    place(asset(SH_DEST + "/SM_Storehouse_01"), "Storehouse_01 - Granary comparison",
          (850.0, -100.0, 0.0), "Granary01Comparison")
    place(asset(SH_DEST + "/SM_SH01_Props"), "Storehouse props - Granary comparison",
          (850.0, -100.0, 0.0), "Granary01Comparison")
    for actor in actors.get_all_level_actors():
        if actor.actor_has_tag("RuralHouse01ScaleFigure"):
            actor.set_actor_location(u.Vector(530.0, -1480.0, 0.0), False, False)
    actors.clear_actor_selection_set()
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save granary review map")
    bounds = mesh.get_bounds()
    report.update(imported=True, mesh=mesh.get_path_name(), map=SETTLEMENT_MAP,
                  material_slots=slots, simple_collision="box", position_cm=GRANARY_POSITION,
                  bounds_origin_cm=[bounds.origin.x, bounds.origin.y, bounds.origin.z],
                  bounds_extent_cm=[bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z])
    write_report("unreal-import.json", report)
    u.log("GRANARY_01_IMPORTED " + mesh.get_path_name())


try:
    main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report("unreal-import.json", report)
    raise
