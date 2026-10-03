"""Import Storehouse01 with shared RuralHouse materials and its own review map.

Import FBX assets and copy the existing seven-house review settlement.
SHOEN_STOREHOUSE_REVIEW_FILL optionally adjusts the copied map fill light.
"""
import hashlib
import json
import os
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Buildings/Storehouse01"
DEST = "/Game/Art/Buildings/Rural/Storehouse01"
RH_DEST = "/Game/Art/Buildings/Rural/RuralHouse01"
SOURCE_MAP = RH_DEST + "/Review/RuralHouse01_Settlement"
SETTLEMENT_MAP = DEST + "/Review/Storehouse01_Settlement"
OUT = ROOT / "artifacts/storehouse01"
SHARED_SLOTS = ("RH01_Thatch", "RH01_Timber", "RH01_Plaster", "RH01_Stone", "RH01_Rope")
ASSET_TOOLS = u.AssetToolsHelpers.get_asset_tools()
MESH_EDITOR = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
report = {"asset": "Storehouse01", "engine_version": u.SystemLibrary.get_engine_version(),
          "imports": [], "meshes": [], "shared_materials_unchanged": True}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def asset(path):
    value = u.load_asset(path)
    require(value is not None, "Missing asset: " + path)
    return value


def map_filename(path):
    return str(Path(u.Paths.project_content_dir()) / (path.removeprefix("/Game/") + ".umap"))


def write_report():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "unreal-import.json").write_text(json.dumps(report, indent=2) + "\n")


def weathered_material(family):
    """Keep the RuralHouse maps; add only Storehouse vertex color and response."""
    source_path = RH_DEST + "/M_RH01_" + family
    target_path = DEST + "/M_SH01_" + family
    material = u.load_asset(target_path)
    if material is None:
        material = u.EditorAssetLibrary.duplicate_asset(source_path, target_path)
    require(material is not None, "Could not duplicate " + source_path)
    edit = u.MaterialEditingLibrary

    def node(label, cls, **properties):
        tag = "SH01:" + label
        matches = [expression for expression in edit.get_material_expressions(material)
                   if expression.get_editor_property("desc") == tag]
        require(len(matches) <= 1, "Duplicate material node: " + tag)
        expression = matches[0] if matches else edit.create_material_expression(material, cls)
        require(expression is not None, "Could not create " + tag)
        expression.set_editor_property("desc", tag)
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        return expression

    previous = edit.get_material_property_input_node(material, u.MaterialProperty.MP_BASE_COLOR)
    output = edit.get_material_property_input_node_output_name(material, u.MaterialProperty.MP_BASE_COLOR)
    require(previous is not None, "Missing copied BaseColor input for " + family)
    vertex = node("WeatherColor", u.MaterialExpressionVertexColor)
    multiply = node("WeatherMultiply", u.MaterialExpressionMultiply)
    if previous != multiply:
        require(edit.connect_material_expressions(previous, output, multiply, "A"),
                "Could not retain BaseColor input for " + family)
    require(edit.connect_material_expressions(vertex, "", multiply, "B"),
            "Could not connect vertex color for " + family)
    require(edit.connect_material_property(multiply, "", u.MaterialProperty.MP_BASE_COLOR),
            "Could not connect weathered BaseColor for " + family)

    normal_strength = 0.65 if family in ("Thatch", "Timber") else 1.0
    if normal_strength < 1.0:
        previous = edit.get_material_property_input_node(material, u.MaterialProperty.MP_NORMAL)
        output = edit.get_material_property_input_node_output_name(material, u.MaterialProperty.MP_NORMAL)
        require(previous is not None, "Missing copied Normal input for " + family)
        scale = node("NormalScale", u.MaterialExpressionConstant3Vector,
                     constant=u.LinearColor(normal_strength, normal_strength, 1.0, 1.0))
        multiply_normal = node("NormalMultiply", u.MaterialExpressionMultiply)
        normalize = node("NormalUnit", u.MaterialExpressionNormalize)
        if previous != normalize:
            require(edit.connect_material_expressions(previous, output, multiply_normal, "A"),
                    "Could not retain Normal input for " + family)
        require(edit.connect_material_expressions(scale, "", multiply_normal, "B"),
                "Could not connect normal strength for " + family)
        require(edit.connect_material_expressions(multiply_normal, "", normalize, ""),
                "Could not normalize softened normal for " + family)
        require(edit.connect_material_property(normalize, "", u.MaterialProperty.MP_NORMAL),
                "Could not connect softened Normal for " + family)

    edit.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, True)
    errors = list(edit.recompile_material(material))
    require(not errors, "Material compile failed for %s: %s" % (family, "; ".join(errors)))
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False),
            "Could not save " + target_path)
    report.setdefault("material_variants", []).append({
        "asset": target_path, "copied_from": source_path,
        "base_color": "existing BaseColor multiplied by mesh vertex RGB",
        "normal_xy_strength": normal_strength, "textures_added": 0})
    return material


def iron_material():
    path = DEST + "/M_SH01_Iron"
    material = u.load_asset(path)
    if material is not None:
        return material
    material = ASSET_TOOLS.create_asset("M_SH01_Iron", DEST, u.Material, u.MaterialFactoryNew())
    require(material is not None, "Could not create iron material")
    edit = u.MaterialEditingLibrary
    base = edit.create_material_expression(material, u.MaterialExpressionConstant3Vector)
    base.set_editor_property("constant", u.LinearColor(0.055, 0.05, 0.042, 1.0))
    edit.connect_material_property(base, "", u.MaterialProperty.MP_BASE_COLOR)
    for value, prop in ((0.76, u.MaterialProperty.MP_ROUGHNESS), (0.7, u.MaterialProperty.MP_METALLIC)):
        node = edit.create_material_expression(material, u.MaterialExpressionConstant)
        node.set_editor_property("r", value)
        edit.connect_material_property(node, "", prop)
    edit.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, True)
    require(not list(edit.recompile_material(material)), "Iron material compile failed")
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False), "Could not save iron")
    return material


def rope_material():
    source_path = RH_DEST + "/M_RH01_Rope"
    target_path = DEST + "/M_SH01_Rope"
    material = u.load_asset(target_path)
    if material is None:
        material = u.EditorAssetLibrary.duplicate_asset(source_path, target_path)
    require(material is not None, "Could not duplicate rope material")
    edit = u.MaterialEditingLibrary
    edit.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, True)
    errors = list(edit.recompile_material(material))
    require(not errors, "Rope material compile failed: " + "; ".join(errors))
    require(u.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False),
            "Could not save " + target_path)
    report.setdefault("material_variants", []).append({
        "asset": target_path, "copied_from": source_path,
        "change": "instanced static mesh usage enabled", "textures_added": 0})
    return material


def review_lighting():
    """Give the copied review fill a unique forward priority; optional intensity."""
    value = os.environ.get("SHOEN_STOREHOUSE_REVIEW_FILL")
    intensity = float(value) if value is not None else None
    if intensity is not None:
        require(0 <= intensity <= 3, "SHOEN_STOREHOUSE_REVIEW_FILL must be between 0 and 3")
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SETTLEMENT_MAP))
    require(world is not None, "Could not load copied Storehouse review map")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    fills = [actor for actor in actors.get_all_level_actors()
             if actor.actor_has_tag("RuralHouse01ReviewLighting")
             or actor.actor_has_tag("Storehouse01ReviewLighting")]
    if not fills and intensity is not None:
        fill = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 1200),
                                             u.Rotator(pitch=-28, yaw=145, roll=0))
        require(fill is not None, "Could not create review fill")
        fills = [fill]
    if not fills:
        return
    for fill in fills:
        component = fill.get_component_by_class(u.DirectionalLightComponent)
        require(component is not None, "Review fill has no directional light component")
        fill.set_actor_label("Storehouse01 - Review fill")
        fill.tags = [u.Name("Storehouse01ReviewLighting")]
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_editor_property("forward_shading_priority", 1)
        require(component.get_editor_property("forward_shading_priority") == 1,
                "Could not set copied review fill priority")
        if intensity is not None:
            component.set_editor_property("intensity", intensity)
        component.set_editor_property("cast_shadows", False)
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save review lighting")
    report["review_fill_forward_shading_priority"] = 1
    if intensity is not None:
        report["review_fill_intensity"] = intensity


def import_mesh(filename, name, materials, collision):
    source = ART / "Exports" / filename
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
    for key, value in {"filename": str(source), "destination_path": DEST, "destination_name": name,
                       "automated": True, "replace_existing": True, "replace_existing_settings": True,
                       "save": False, "options": options, "factory": u.FbxFactory()}.items():
        task.set_editor_property(key, value)
    ASSET_TOOLS.import_asset_tasks([task])
    require(task.imported_object_paths, "FBX import failed: " + filename)
    mesh = asset(DEST + "/" + name)
    slots = [str(item.get_editor_property("material_slot_name"))
             for item in mesh.get_editor_property("static_materials")]
    require(slots and all(slot in materials for slot in slots), "Unexpected slots: " + repr(slots))
    for index, slot in enumerate(slots):
        mesh.set_material(index, materials[slot])
    require(MESH_EDITOR.remove_collisions(mesh), "Could not clear collision: " + name)
    if collision:
        require(MESH_EDITOR.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX) >= 0,
                "Could not create storehouse collision")
    require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), "Could not save " + name)
    bounds = mesh.get_bounds()
    report["imports"].append({"source": str(source.relative_to(ROOT)),
                              "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                              "assets": list(task.imported_object_paths)})
    report["meshes"].append({"asset": mesh.get_path_name(), "material_slots": slots,
                             "bounds_origin_cm": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
                             "bounds_extent_cm": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
                             "simple_collision": "box" if collision else "none"})
    return mesh


def main():
    materials = {slot: asset(RH_DEST + "/M_" + slot) for slot in SHARED_SLOTS}
    for family in ("Thatch", "Timber", "Plaster", "Stone"):
        materials["SH01_" + family] = weathered_material(family)
    materials["SH01_Iron"] = iron_material()
    materials["SH01_Rope"] = rope_material()
    materials["RH01_Rope"] = materials["SH01_Rope"]
    import_mesh("Storehouse_01.fbx", "SM_Storehouse_01", materials, True)
    import_mesh("SH01_Props.fbx", "SM_SH01_Props", materials, False)
    world = u.EditorLoadingAndSavingUtils.load_map(map_filename(SOURCE_MAP))
    require(world is not None, "Could not load the seven-house settlement")
    require(u.EditorLoadingAndSavingUtils.save_map(world, SETTLEMENT_MAP), "Could not save review map")
    review_lighting()
    report["review_map"] = SETTLEMENT_MAP
    report["decorative_house_count"] = 7
    report["storehouse_placement"] = "Runtime Small Storehouse placed with existing B / click or Enter controls"
    report["materials"] = {slot: value.get_path_name() for slot, value in materials.items()}
    report["imported"] = True
    write_report()
    u.log("STOREHOUSE_01_IMPORTED " + DEST)


try:
    main()
except Exception:
    report["error"] = traceback.format_exc()
    write_report()
    raise
