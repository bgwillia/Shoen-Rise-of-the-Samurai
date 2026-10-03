"""Import RuralHouse01 and place seven copies in a settlement review map.

Run this script through ShoenEditor with -ExecutePythonScript. It writes only
the RuralHouse01 content folder and a copy of the existing Foundation map; the
shared Foundation map and its runtime settlement implementation stay unchanged.
"""

import hashlib
import json
from pathlib import Path
import traceback

import unreal as u


ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/RuralHouse01"
DEST = "/Game/Art/Buildings/Rural/RuralHouse01"
REVIEW = DEST + "/Review"
SOURCE_MAP = "/Game/Domain/Maps/Foundation"
SETTLEMENT_MAP = REVIEW + "/RuralHouse01_Settlement"
OUT = ROOT / "artifacts/ruralhouse01"
REPORT_PATH = OUT / "unreal-import.json"

MESH_NAME = "SM_RuralHouse_01"
SLOTS = ("RH01_Thatch", "RH01_Timber", "RH01_Plaster", "RH01_Stone", "RH01_Rope")
MANNY = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
MANNY_LABEL = "RuralHouse01 - 180 cm scale figure"
FILL_LABEL = "RuralHouse01 - Review fill light"

# All sites lie on the flat part of the authored settlement height field. The
# loose orientations read as a village while leaving space for the existing
# runtime building-placement presentation.
PLACEMENTS = (
    (-2150.0, -1200.0, 0.0, 15.0),
    (-1050.0, -1200.0, 0.0, 352.0),
    (50.0, -1200.0, 0.0, 8.0),
    (-2150.0, -100.0, 0.0, 340.0),
    (-1050.0, -100.0, 0.0, 12.0),
    (50.0, -100.0, 0.0, 348.0),
    (-1050.0, 1000.0, 0.0, 5.0),
)

ASSET_TOOLS = u.AssetToolsHelpers.get_asset_tools()
ACTORS = u.get_editor_subsystem(u.EditorActorSubsystem)
STATIC_MESH_EDITOR = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
MATERIAL_EDIT = u.MaterialEditingLibrary

report = {
    "asset": "RuralHouse01",
    "engine_version": u.SystemLibrary.get_engine_version(),
    "validated": False,
    "destination": DEST,
    "settlement_map": SETTLEMENT_MAP,
    "imports": [],
    "placements": [],
    "fbx_import": {
        "convert_scene": False,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "combine_meshes": True,
        "normal_import": "Import normals and tangents",
        "coordinate_contract": "Blender metres, -Y front, origin at ground-footprint center",
    },
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_report():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def asset(path):
    result = u.load_asset(path)
    require(result is not None, "Missing Unreal asset: " + path)
    return result


def source_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_texture(path, name):
    require(path.is_file(), "Missing texture: " + str(path))
    task = u.AssetImportTask()
    for key, value in {
        "filename": str(path),
        "destination_path": DEST,
        "destination_name": name,
        "automated": True,
        "replace_existing": True,
        "replace_existing_settings": True,
        "save": False,
    }.items():
        task.set_editor_property(key, value)
    ASSET_TOOLS.import_asset_tasks([task])
    require(task.imported_object_paths, "Texture import failed: " + str(path))
    texture = asset(DEST + "/" + name)
    report["imports"].append({
        "source": str(path.relative_to(ROOT)),
        "sha256": source_digest(path),
        "assets": list(task.imported_object_paths),
    })
    return texture


def import_mesh():
    source = ART / "Exports/RuralHouse_01.fbx"
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
        "filename": str(source),
        "destination_path": DEST,
        "destination_name": MESH_NAME,
        "automated": True,
        "replace_existing": True,
        "replace_existing_settings": True,
        "save": False,
        "options": options,
        "factory": u.FbxFactory(),
    }.items():
        task.set_editor_property(key, value)
    ASSET_TOOLS.import_asset_tasks([task])
    require(task.imported_object_paths, "FBX import failed: " + str(source))
    report["imports"].append({
        "source": str(source.relative_to(ROOT)),
        "sha256": source_digest(source),
        "assets": list(task.imported_object_paths),
    })
    return asset(DEST + "/" + MESH_NAME)


def texture_sample(material, texture, sampler_type=None):
    node = MATERIAL_EDIT.create_material_expression(material, u.MaterialExpressionTextureSample)
    node.set_editor_property("texture", texture)
    if sampler_type is not None:
        node.set_editor_property("sampler_type", sampler_type)
    return node


def build_material(slot):
    texture_dir = ART / "Textures"
    source_base_name = slot + "_BaseColor"
    source_normal_name = slot + "_Normal"
    source_orm_name = slot + "_ORM"
    source_roughness_name = slot + "_Roughness"
    base_name = "T_" + source_base_name
    normal_name = "T_" + source_normal_name
    orm_name = "T_" + source_orm_name
    roughness_name = "T_" + source_roughness_name

    base = import_texture(texture_dir / (source_base_name + ".png"), base_name)
    normal = import_texture(texture_dir / (source_normal_name + ".png"), normal_name)
    orm_path = texture_dir / (source_orm_name + ".png")
    roughness_path = texture_dir / (source_roughness_name + ".png")
    require(orm_path.is_file() or roughness_path.is_file(),
            "Expected either %s or %s" % (orm_path, roughness_path))
    packed = orm_path.is_file()
    surface = import_texture(orm_path if packed else roughness_path,
                             orm_name if packed else roughness_name)

    base.set_editor_property("srgb", True)
    normal.set_editor_property("srgb", False)
    normal.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP)
    normal.set_editor_property("flip_green_channel", True)
    surface.set_editor_property("srgb", False)
    surface.set_editor_property(
        "compression_settings",
        u.TextureCompressionSettings.TC_MASKS if packed else u.TextureCompressionSettings.TC_GRAYSCALE,
    )
    for texture in (base, normal, surface):
        require(u.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False),
                "Could not save " + texture.get_path_name())

    material_name = "M_" + slot
    material_path = DEST + "/" + material_name
    material = u.load_asset(material_path)
    if material is None:
        material = ASSET_TOOLS.create_asset(material_name, DEST, u.Material, u.MaterialFactoryNew())
    require(material is not None, "Could not create material: " + material_path)
    MATERIAL_EDIT.delete_all_material_expressions(material)
    material.set_editor_property("blend_mode", u.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("two_sided", False)
    material.set_editor_property("tangent_space_normal", True)

    base_sample = texture_sample(material, base)
    normal_sample = texture_sample(material, normal, u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    surface_sample = texture_sample(
        material,
        surface,
        u.MaterialSamplerType.SAMPLERTYPE_MASKS if packed else u.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE,
    )
    require(MATERIAL_EDIT.connect_material_property(
        base_sample, "RGB", u.MaterialProperty.MP_BASE_COLOR), "Could not connect BaseColor for " + slot)
    require(MATERIAL_EDIT.connect_material_property(
        normal_sample, "RGB", u.MaterialProperty.MP_NORMAL), "Could not connect Normal for " + slot)
    if packed:
        outputs = (
            ("R", u.MaterialProperty.MP_AMBIENT_OCCLUSION),
            ("G", u.MaterialProperty.MP_ROUGHNESS),
            ("B", u.MaterialProperty.MP_METALLIC),
        )
        for channel, property_ in outputs:
            require(MATERIAL_EDIT.connect_material_property(surface_sample, channel, property_),
                    "Could not connect ORM for " + slot)
    else:
        require(MATERIAL_EDIT.connect_material_property(
            surface_sample, "R", u.MaterialProperty.MP_ROUGHNESS),
            "Could not connect Roughness for " + slot)
        ao = MATERIAL_EDIT.create_material_expression(material, u.MaterialExpressionConstant)
        ao.set_editor_property("r", 1.0)
        metallic = MATERIAL_EDIT.create_material_expression(material, u.MaterialExpressionConstant)
        metallic.set_editor_property("r", 0.0)
        require(MATERIAL_EDIT.connect_material_property(
            ao, "", u.MaterialProperty.MP_AMBIENT_OCCLUSION), "Could not connect AO for " + slot)
        require(MATERIAL_EDIT.connect_material_property(
            metallic, "", u.MaterialProperty.MP_METALLIC), "Could not connect Metallic for " + slot)
    MATERIAL_EDIT.layout_material_expressions(material)
    errors = list(MATERIAL_EDIT.recompile_material(material))
    require(not errors, "Material compile errors for %s: %s" % (slot, "; ".join(errors)))
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False),
            "Could not save " + material_path)
    return material, packed


def assign_materials(mesh, materials):
    static_materials = list(mesh.get_editor_property("static_materials"))
    slot_names = [str(item.get_editor_property("material_slot_name")) for item in static_materials]
    require(len(slot_names) == len(SLOTS),
            "RuralHouse_01 must import exactly five material slots; got " + repr(slot_names))
    require(set(slot_names) == set(SLOTS),
            "RuralHouse_01 material slots must be %s; got %s" % (SLOTS, slot_names))
    for index, slot in enumerate(slot_names):
        mesh.set_material(index, materials[slot])
    require(STATIC_MESH_EDITOR.get_number_materials(mesh) == len(SLOTS),
            "Unexpected material count after RuralHouse01 assignment")
    require(STATIC_MESH_EDITOR.remove_collisions(mesh),
            "Could not clear prior RuralHouse01 simple collision")
    collision_index = STATIC_MESH_EDITOR.add_simple_collisions(
        mesh, u.ScriptCollisionShapeType.BOX)
    require(collision_index >= 0, "Could not add RuralHouse01 box collision")
    require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False),
            "Could not save " + mesh.get_path_name())
    report["mesh"] = {
        "asset": mesh.get_path_name(),
        "material_slots": slot_names,
        "bounds_cm": {
            "origin": [mesh.get_bounds().origin.x, mesh.get_bounds().origin.y, mesh.get_bounds().origin.z],
            "extent": [mesh.get_bounds().box_extent.x, mesh.get_bounds().box_extent.y,
                       mesh.get_bounds().box_extent.z],
        },
        "simple_collision": "box",
    }


def map_filename(asset_path):
    return str(Path(u.Paths.project_content_dir()) /
               (asset_path.removeprefix("/Game/") + ".umap"))


def settlement_map(mesh):
    target_file = Path(map_filename(SETTLEMENT_MAP))
    if target_file.is_file():
        world = u.EditorLoadingAndSavingUtils.load_map(str(target_file))
    else:
        world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
        require(world is not None, "Could not load source map: " + SOURCE_MAP)
        require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP),
                "Could not copy Foundation map to " + SETTLEMENT_MAP)
        world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Could not load settlement review map")

    label_prefix = "RuralHouse_01 - Settlement "
    for actor in list(ACTORS.get_all_level_actors()):
        if (actor.get_actor_label().startswith(label_prefix)
                or actor.get_actor_label() in (MANNY_LABEL, FILL_LABEL)):
            ACTORS.destroy_actor(actor)

    for index, (x, y, z, yaw) in enumerate(PLACEMENTS, start=1):
        actor = ACTORS.spawn_actor_from_class(
            u.StaticMeshActor, u.Vector(x, y, z), u.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
        require(actor is not None, "Could not place RuralHouse01 copy %d" % index)
        actor.set_actor_label(label_prefix + "%02d" % index)
        actor.tags = [u.Name("RuralHouse01"), u.Name("SettlementArt")]
        component = actor.static_mesh_component
        component.set_mobility(u.ComponentMobility.STATIC)
        component.set_static_mesh(mesh)
        component.set_collision_profile_name("BlockAllDynamic")
        component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)
        report["placements"].append({
            "label": actor.get_actor_label(),
            "location_cm": [x, y, z],
            "yaw_degrees": yaw,
        })

    manny = ACTORS.spawn_actor_from_class(
        u.SkeletalMeshActor, u.Vector(-470.0, -520.0, 0.0),
        u.Rotator(pitch=0.0, yaw=-95.0, roll=0.0))
    require(manny is not None, "Could not place the Manny scale figure")
    manny.set_actor_label(MANNY_LABEL)
    manny.tags = [u.Name("RuralHouse01ScaleFigure")]
    manny_component = manny.skeletal_mesh_component
    manny_component.set_mobility(u.ComponentMobility.MOVABLE)
    manny_component.set_skeletal_mesh_asset(asset(MANNY))
    manny_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)

    # The settlement runtime has a key light but no ambient sky source. A low,
    # shadowless opposite-direction fill keeps the exterior materials readable
    # in this copied art-review map without changing the shared game scene.
    fill = ACTORS.spawn_actor_from_class(
        u.DirectionalLight, u.Vector(0.0, 0.0, 1200.0),
        u.Rotator(pitch=-28.0, yaw=145.0, roll=0.0))
    require(fill is not None, "Could not place the RuralHouse01 review fill light")
    fill.set_actor_label(FILL_LABEL)
    fill.tags = [u.Name("RuralHouse01ReviewLighting")]
    fill_component = fill.get_component_by_class(u.DirectionalLightComponent)
    require(fill_component is not None, "Could not access the review fill light component")
    fill_component.set_editor_property("intensity", 1.2)
    fill_component.set_editor_property("cast_shadows", False)

    ACTORS.clear_actor_selection_set()
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP),
            "Could not save " + SETTLEMENT_MAP)


def main():
    mesh = import_mesh()
    materials = {}
    packed = {}
    for slot in SLOTS:
        materials[slot], packed[slot] = build_material(slot)
    assign_materials(mesh, materials)
    settlement_map(mesh)
    report["materials"] = {
        slot: {"asset": materials[slot].get_path_name(), "uses_orm": packed[slot]}
        for slot in SLOTS
    }
    report["validated"] = True
    write_report()
    u.log("RURAL_HOUSE_01_IMPORTED " + mesh.get_path_name())
    u.log("RURAL_HOUSE_01_SETTLEMENT_MAP " + SETTLEMENT_MAP)



try:
    main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report()
    raise
