"""Import modular Kusazuri01 and static review copies on the unchanged native Manny skeleton.

Execute in the built ShoenEditor Python commandlet, with no other Unreal
process using this checkout. Native Manny assets are read-only dependencies.
"""
import hashlib
import json
import math
import re
from pathlib import Path
import traceback

import unreal as u


ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Characters/Samurai/Kusazuri01"
DEST = "/Game/Art/Characters/Samurai/Kusazuri01"
REVIEW = DEST + "/Review"
MAP = REVIEW + "/Kusazuri01_Review"
MANNY = "/Game/Characters/Mannequins"
FIT = MANNY + "/Meshes/SKM_Manny_Simple"
SKELETON = MANNY + "/Meshes/SK_Mannequin"
NATIVE_CLIPS = {"idle": MANNY + "/Anims/Unarmed/MM_Idle",
                "walk": MANNY + "/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd",
                "run": MANNY + "/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd",
                "attack": MANNY + "/Anims/Unarmed/Attack/MM_Attack_01"}
REPORT_PATH = ROOT / "artifacts/kusazuri01/unreal-import.json"
REVIEW_SCREEN_SIZES = [1.0, .22, .08]
# FBX float rotations can move a distal bone by ~20 microns in a native-Manny
# roundtrip. These bounds allow that precision loss, never hierarchy changes.
REFERENCE_TOLERANCES = {"translation_cm": .01, "scale": 1e-4, "quaternion_dot_error": 1e-6}
assets = u.AssetToolsHelpers.get_asset_tools()
edit = u.MaterialEditingLibrary
stat = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
skel = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
dirty = {}
report = {"asset": "Kusazuri01", "engine_version": u.SystemLibrary.get_engine_version(),
          "validated": False, "rendering_validated": False, "imports": [],
          "fbx_import": {"convert_scene": False, "convert_scene_unit": True,
                         "force_front_x_axis": False, "normal_import": "Import normals and tangents", "vertex_colors": "Replace with FBX colors (ArmorTint: R=0 indigo obi, R=1 original palette)",
                         "coordinate_contract": "Blender world metres, -Y forward, preserved native .01-scale root; raw FBX maps (100x,-100y,100z) into native Manny +Y-forward mesh space."}}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_report():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def remember(obj):
    require(obj is not None and obj.get_path_name().startswith(DEST + "/"),
            "Missing asset or attempted write outside Kusazuri01")
    dirty[obj.get_path_name()] = obj
    return obj


def vector(value):
    return [value.x, value.y, value.z]


def box(low, high):
    size = [b - a for a, b in zip(low, high)]
    require(all(math.isfinite(v) for v in low + high) and all(v > 0 for v in size),
            "Invalid imported mesh bounds")
    return {"min": low, "max": high, "size": size}


def import_file(source, name, kind, dest=DEST, skeleton=None):
    require(source.is_file(), "Missing export: " + str(source))
    task = u.AssetImportTask()
    for key, value in {"filename": str(source), "destination_path": dest,
                       "destination_name": name, "automated": True, "replace_existing": True,
                       "replace_existing_settings": True, "save": False}.items():
        task.set_editor_property(key, value)
    if kind != "texture":
        options = u.FbxImportUI()
        options.automated_import_should_detect_type = False
        options.import_materials = False
        options.import_textures = False
        options.import_mesh = kind != "animation"
        options.import_animations = kind == "animation"
        options.import_as_skeletal = kind != "static"
        options.mesh_type_to_import = {"static": u.FBXImportType.FBXIT_STATIC_MESH,
                                      "skeletal": u.FBXImportType.FBXIT_SKELETAL_MESH,
                                      "animation": u.FBXImportType.FBXIT_ANIMATION}[kind]
        options.create_physics_asset = False
        if skeleton is not None:
            options.skeleton = skeleton
        data = {"static": options.static_mesh_import_data,
                "skeletal": options.skeletal_mesh_import_data,
                "animation": options.anim_sequence_import_data}[kind]
        for key in ("convert_scene", "convert_scene_unit", "force_front_x_axis"):
            data.set_editor_property(key, report["fbx_import"][key])
        if kind != "animation":
            data.normal_import_method = u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
            data.set_editor_property("vertex_color_import_option", u.VertexColorImportOption.REPLACE)
        if kind == "skeletal":
            data.set_editor_property("update_skeleton_reference_pose", False)
            data.set_editor_property("use_t0_as_ref_pose", False)
            data.set_editor_property("import_content_type", u.FBXImportContentType.FBXICT_ALL)
            data.set_editor_property("import_morph_targets", False)
            data.set_editor_property("keep_sections_separate", False)
        elif kind == "static":
            data.combine_meshes = True
            data.auto_generate_collision = False
            data.generate_lightmap_u_vs = False
        else:
            data.set_editor_property("animation_length", u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        task.options = options
        task.factory = u.FbxFactory()
    assets.import_asset_tasks([task])
    paths = list(task.imported_object_paths)
    require(paths, "FBX/texture import produced no asset: " + str(source))
    report["imports"].append({"source": str(source.relative_to(ROOT)),
                              "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "assets": paths})
    for path in paths:
        obj = u.load_asset(path)
        # UE may include the explicitly supplied skeleton among its results.
        # It remains a reference, never a package this task saves.
        if obj != skeleton:
            remember(obj)
    imported = remember(u.load_asset(dest + "/" + name))
    if kind in ("static", "skeletal"):
        imported_data = imported.get_editor_property("asset_import_data")
        color_option = imported_data.get_editor_property("vertex_color_import_option")
        require(color_option == u.VertexColorImportOption.REPLACE,
                "Imported mesh did not preserve the requested FBX vertex-color replacement setting")
        report["imports"][-1]["vertex_color_import_option_readback"] = str(color_option)
    return imported


def bones(mesh):
    component = u.SkeletalMeshComponent()
    component.set_skeletal_mesh_asset(mesh)
    result = []
    for index in range(component.get_num_bones()):
        name = str(component.get_bone_name(index))
        transform = component.get_ref_pose_transform(index)
        rotation = transform.get_editor_property("rotation")
        result.append({"name": name, "parent": str(component.get_parent_bone(name)),
                       "translation": vector(transform.get_editor_property("translation")),
                       "scale": vector(transform.get_editor_property("scale3d")),
                       "rotation_xyzw": [rotation.x, rotation.y, rotation.z, rotation.w]})
    return result


def verify_skeleton(armor, skeleton, reference):
    require(armor.get_editor_property("skeleton") == skeleton, "Kusazuri must reuse the exact existing mannequin skeleton")
    actual = bones(armor)
    errors = []
    maximum = dict.fromkeys(REFERENCE_TOLERANCES, 0.0)
    deltas = []
    if len(actual) != len(reference):
        errors.append("Different bone count")
    for have, want in zip(actual, reference):
        if have["name"] != want["name"] or have["parent"] != want["parent"]:
            errors.append("Hierarchy differs at " + have["name"])
        delta = {"name": have["name"]}
        for field in ("translation", "scale"):
            key = "translation_cm" if field == "translation" else field
            value = max(abs(a-b) for a,b in zip(have[field], want[field]))
            delta[key] = value
            maximum[key] = max(maximum[key], value)
        dot = sum(a * b for a, b in zip(have["rotation_xyzw"], want["rotation_xyzw"]))
        delta["quaternion_dot_error"] = abs(abs(dot)-1)
        maximum["quaternion_dot_error"] = max(maximum["quaternion_dot_error"], delta["quaternion_dot_error"])
        for key, tolerance in REFERENCE_TOLERANCES.items():
            if not math.isfinite(delta[key]) or delta[key] > tolerance:
                errors.append(key + " differs at " + have["name"])
        deltas.append(delta)
    result = {"asset": skeleton.get_path_name(), "exact_existing_asset": True,
              "reference_mesh": FIT, "matching_reference_transforms": not errors,
              "reference_tolerances": REFERENCE_TOLERANCES, "maximum_reference_delta": maximum,
              "reference_deltas": deltas, "reference_errors": errors,
              "bone_count": len(actual), "bones": actual}
    require(not errors, "Kusazuri reference skeleton mismatch: " + "; ".join(errors))
    return result


def build_settings(subsystem, mesh, lod, static=False):
    settings = subsystem.get_lod_build_settings(mesh, lod)
    settings.recompute_normals = False
    settings.recompute_tangents = False
    settings.use_full_precision_u_vs = True
    if static:
        settings.generate_lightmap_u_vs = False
    subsystem.set_lod_build_settings(mesh, lod, settings)
    return {"recompute_normals": settings.recompute_normals,
            "recompute_tangents": settings.recompute_tangents, "full_precision_uvs": settings.use_full_precision_u_vs}


DO = "/Game/Art/Characters/Samurai/Do01"
SOURCE_MATERIAL = "/Game/Art/Characters/Samurai/Sode01/M_Sode01"
MATERIAL = DEST + "/M_Kusazuri01"
READ_ONLY_DEPENDENCIES = [FIT, SKELETON, SOURCE_MATERIAL, DO + "/M_Do01", DO + "/SK_Do01", DO + "/Review/SM_Do01",
    "/Game/Art/Characters/Samurai/Kabuto01/SM_Kabuto01"] + list(NATIVE_CLIPS.values()) + [
    DO + "/T_Do01_" + suffix for suffix in ("BaseColor", "Normal", "ORM")] + [
    "/Game/Art/Characters/Samurai/Sode01/" + name for name in ("SK_Sode_L_01", "SK_Sode_R_01",
        "Review/SM_Sode_L_01", "Review/SM_Sode_R_01")] + [DO + "/Review/SM_Manny"]



def create_material_variant():
    """Clone final Sode finish; retain atlas fibers with a vertex-masked indigo obi."""
    source = u.load_asset(SOURCE_MATERIAL)
    require(source is not None, "Missing calibrated final Sode material")
    material = u.load_asset(MATERIAL)
    if material is None:
        material = u.EditorAssetLibrary.duplicate_asset(SOURCE_MATERIAL, MATERIAL)
    remember(material)
    source_custom = [expr for expr in edit.get_material_expressions(source)
                     if isinstance(expr, u.MaterialExpressionCustom) and "floor(UV.x" in expr.get_editor_property("code")
                     and expr.get_editor_property("output_type") == u.CustomMaterialOutputType.CMOT_FLOAT3]
    target_custom = [expr for expr in edit.get_material_expressions(material)
                     if isinstance(expr, u.MaterialExpressionCustom) and "floor(UV.x" in expr.get_editor_property("code")
                     and expr.get_editor_property("output_type") == u.CustomMaterialOutputType.CMOT_FLOAT3]
    require(len(source_custom) == len(target_custom) == 1, "Expected exactly one atlas tint expression in source and duplicate")
    original_code = source_custom[0].get_editor_property("code")
    branch = "if (tile == 12.0) return float3(0.10, 0.18, 0.48);"
    pattern = r"if\s*\(\s*tile\s*==\s*12(?:\.0)?\s*\)\s*return\s*float3\([^;]+;"
    code, changed = re.subn(pattern, branch, original_code)
    require(changed <= 1, "Ambiguous tile-12 tint in existing material")
    if changed == 0:
        lines = original_code.splitlines()
        declarations = [index for index, line in enumerate(lines)
                        if re.match(r"\s*float\s+tile\s*=", line)]
        require(len(declarations) == 1, "Expected exactly one atlas tile declaration")
        lines.insert(declarations[0] + 1, branch)
        code = "\n".join(lines)
    target_custom[0].set_editor_property("code", code)
    # Reuse the original texture node and palette result. Locate by graph
    # connections so repeated imports cannot accidentally stack tint branches.
    expressions = list(edit.get_material_expressions(material))
    raw_color = [expr for expr in expressions if isinstance(expr, u.MaterialExpressionTextureSampleParameter2D)
                 and str(expr.get_editor_property("parameter_name")) == "BaseColor"]
    palette_color = [expr for expr in expressions if isinstance(expr, u.MaterialExpressionMultiply)
                     and target_custom[0] in edit.get_inputs_for_material_expression(material, expr)]
    require(len(raw_color) == len(palette_color) == 1, "Expected one shared BaseColor sample and original palette multiply")

    def node(tag, cls, **properties):
        marker = "KusazuriObi:" + tag
        matches = [expr for expr in expressions if expr.get_editor_property("desc") == marker]
        require(len(matches) <= 1, "Duplicated obi material expression: " + tag)
        expression = matches[0] if matches else edit.create_material_expression(material, cls)
        require(isinstance(expression, cls), "Wrong expression type for obi material node: " + tag)
        expression.set_editor_property("desc", marker)
        for key, value in properties.items():
            expression.set_editor_property(key, value)
        return expression

    def connect(source_node, channel, destination_node, pin):
        require(edit.connect_material_expressions(source_node, channel, destination_node, pin),
                "Could not connect indigo obi material pin: " + pin)

    vertex_color = node("Mask", u.MaterialExpressionVertexColor)
    desaturation = node("WovenLuminance", u.MaterialExpressionDesaturation)
    fraction = node("FullDesaturation", u.MaterialExpressionConstant, r=1.)
    indigo = node("Indigo", u.MaterialExpressionConstant3Vector, constant=u.LinearColor(.08,.18,.50,1))
    indigo_color = node("WovenIndigo", u.MaterialExpressionMultiply)
    selected_color = node("Select", u.MaterialExpressionLinearInterpolate)
    # MaterialGraphNode shortens the pin named Input to NAME_None.
    connect(raw_color[0], "RGB", desaturation, "")
    connect(fraction, "", desaturation, "Fraction")
    connect(desaturation, "", indigo_color, "A")
    connect(indigo, "", indigo_color, "B")
    connect(indigo_color, "", selected_color, "A")
    connect(palette_color[0], "", selected_color, "B")
    connect(vertex_color, "R", selected_color, "Alpha")
    require(edit.connect_material_property(selected_color, "", u.MaterialProperty.MP_BASE_COLOR),
            "Could not connect vertex-masked indigo BaseColor")
    require(edit.get_material_property_input_node(material, u.MaterialProperty.MP_BASE_COLOR) == selected_color,
            "Material BaseColor did not retain the obi selection node")
    # Classify cloth with the same native V-flip correction as the palette.
    # Only tile 12 becomes matte nonmetal cloth; all other atlas samples retain
    # the duplicated Sode material's scalar inputs and normal response.
    declarations = [line for line in original_code.splitlines() if re.match(r"\s*float\s+tile\s*=", line)]
    require(len(declarations) == 1, "Expected exactly one source atlas tile declaration")
    cloth_code = declarations[0] + "\nreturn tile == 12.0 ? 1.0 : 0.0;"
    cloth_uv = [expr for expr in edit.get_inputs_for_material_expression(material, target_custom[0])
                if isinstance(expr, u.MaterialExpressionTextureCoordinate)]
    require(len(cloth_uv) == 1 and cloth_uv[0].get_editor_property("coordinate_index") == 0,
            "Expected palette coordinates from UV channel 0")
    cloth_input = u.CustomInput()
    cloth_input.set_editor_property("input_name", "UV")
    cloth_mask = node("ClothTileMask", u.MaterialExpressionCustom, code=cloth_code,
                      output_type=u.CustomMaterialOutputType.CMOT_FLOAT1, inputs=[cloth_input])
    connect(cloth_uv[0], "", cloth_mask, "UV")
    for label, property_, value in (("Metallic", u.MaterialProperty.MP_METALLIC, 0.),
                                    ("Roughness", u.MaterialProperty.MP_ROUGHNESS, .90),
                                    ("Specular", u.MaterialProperty.MP_SPECULAR, 0.)):
        selected = node("Cloth" + label, u.MaterialExpressionLinearInterpolate, const_b=value)
        prior = edit.get_material_property_input_node(material, property_)
        require(prior is not None, "Missing existing Sode scalar input: " + label)
        if prior != selected:
            channel = edit.get_material_property_input_node_output_name(material, property_)
            connect(prior, channel, selected, "A")
        # On reimport retain the existing A input rather than stacking overrides.
        connect(cloth_mask, "", selected, "Alpha")
        require(edit.connect_material_property(selected, "", property_), "Could not connect cloth " + label)
        require(edit.get_material_property_input_node(material, property_) == selected,
                "Material did not retain cloth selection: " + label)
        inputs = edit.get_inputs_for_material_expression(material, selected)
        require(cloth_mask in inputs and len([expr for expr in inputs if expr and expr != cloth_mask]) == 1,
                "Cloth selection must preserve one original scalar input: " + label)
    errors = list(edit.recompile_material(material))
    require(not errors, "Kusazuri variant failed shader compilation: " + "; ".join(errors))
    def texture_references(mat):
        return sorted({expr.get_editor_property("texture").get_path_name()
                       for expr in edit.get_material_expressions(mat)
                       if isinstance(expr, u.MaterialExpressionTextureSampleParameter2D)
                       and expr.get_editor_property("texture") is not None})

    # GetMaterialUsedTextures reads active shader resources, which NullRHI does
    # not supply. Compare serialized graph references here, then render Metal.
    source_textures, target_textures = texture_references(source), texture_references(material)
    report["material_texture_readback"] = {
        "source_graph": source_textures, "target_graph": target_textures,
        "source_active_resource": sorted(texture.get_path_name() for texture in edit.get_material_used_textures(source)),
        "target_active_resource": sorted(texture.get_path_name() for texture in edit.get_material_used_textures(material))}
    require(source_textures == target_textures and len(target_textures) == 3,
            "Kusazuri must preserve all three shared atlas texture references")
    report["material"] = {"asset": material.get_path_name(), "cloned_from": SOURCE_MATERIAL,
        "rationale": "Match final Sode lacquer/brass/red panel cords; tile 12 tints quilted lining indigo, and ArmorTint.R selects desaturated woven tile-3 texture for the indigo obi and bow",
        "obi_vertex_mask": {"attribute": "ArmorTint", "channel": "R", "indigo_value": 0, "original_palette_value": 1,
                            "color": [.08,.18,.50], "desaturation": 1., "formula": "lerp(desaturate(raw BaseColor,1)*indigo, original palette BaseColor, VertexColor.R)",
                            "normal_and_orm": "Unchanged shared atlas maps; tile 3 retains woven cord surface detail"},
        "tile_12_multiplier": [.10,.18,.48], "source_custom_code": original_code, "custom_code": code,
        "tile_12_surface": {"metallic": 0., "roughness": .90, "specular": 0., "mask_code": cloth_code,
                            "reason": "Suppress chalky grazing specular on indigo cloth; preserve all other atlas regions",
                            "normal_strength": .65, "other_atlas_scalar_inputs_unchanged": True},
        "textures": target_textures, "new_texture_allocations": 0, "runtime_material_slots": 1,
        "existing_material_changed": False, "compile_errors": errors,
        "rendering_limit": "NullRHI import checks compilation responses; actual Metal review still required"}
    return material


def package_hashes():
    result = {}
    for path in READ_ONLY_DEPENDENCIES:
        file = Path(u.Paths.project_content_dir()) / (path.removeprefix("/Game/") + ".uasset")
        require(file.is_file(), "Missing existing armor-set dependency: " + path)
        result[path] = hashlib.sha256(file.read_bytes()).hexdigest()
    optional = "/Game/Art/Characters/Samurai/Sode01/M_Sode01"
    optional_file = Path(u.Paths.project_content_dir()) / (optional.removeprefix("/Game/") + ".uasset")
    if optional_file.exists():
        result[optional] = hashlib.sha256(optional_file.read_bytes()).hexdigest()
    return result


def add_lods(mesh, name, skeletal):
    subsystem = skel if skeletal else stat
    folder = ART / ("Exports" if skeletal else "Review/Exports")
    import_data = mesh.get_editor_property("asset_import_data")
    import_data.set_editor_property("vertex_color_import_option", u.VertexColorImportOption.REPLACE)
    if subsystem.get_lod_count(mesh) > 1:
        removed = (skel.remove_lods(mesh, list(range(1, skel.get_lod_count(mesh)))) if skeletal
                   else stat.remove_lods(mesh))
        require(removed, "Could not replace prior Kusazuri LODs")
    for lod in (1, 2):
        source = folder / (name + "_LOD%d.fbx" % lod)
        require(source.is_file(), "Missing required Kusazuri LOD: " + str(source))
        require(subsystem.get_lod_count(mesh) == lod and subsystem.import_lod(mesh, lod, str(source)) == lod,
                "Kusazuri LOD import failed or sources were nonconsecutive")
        report["imports"].append({"source": str(source.relative_to(ROOT)), "asset": mesh.get_path_name(),
                                 "lod": lod, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    require(subsystem.get_lod_count(mesh) == 3, "Kusazuri requires three LODs")


def import_armor(material, skeleton, reference):
    name = "SK_Kusazuri01"
    armor = import_file(ART / "Exports" / (name + ".fbx"), name, "skeletal", skeleton=skeleton)
    add_lods(armor, name, skeletal=True)
    materials = list(armor.get_editor_property("materials"))
    require(len(materials) == 1, "Kusazuri skeletal mesh must have one material slot")
    materials[0].set_editor_property("material_interface", material)
    armor.set_editor_property("materials", materials)
    lods = []
    for lod in range(skel.get_lod_count(armor)):
        info = {"lod": lod, "render_vertices": skel.get_num_verts(armor, lod),
                "sections": skel.get_num_sections(armor, lod), "section_material_slot": skel.get_lod_material_slot(armor, lod, 0),
                "build_settings": build_settings(skel, armor, lod)}
        require(info["render_vertices"] > 0 and info["sections"] == 1 and info["section_material_slot"] == 0,
                "Kusazuri skeletal LOD is empty or has unexpected sections")
        lods.append(info)
    require(lods[0]["render_vertices"] > lods[1]["render_vertices"] > lods[2]["render_vertices"],
            "Kusazuri skeletal LODs must decrease")
    bounds = armor.get_imported_bounds()
    skeletal_bounds = box(vector(bounds.origin - bounds.box_extent), vector(bounds.origin + bounds.box_extent))
    require(10 < max(skeletal_bounds["size"]) < 100 and 40 < bounds.origin.z < 130,
            "Kusazuri scale/height is implausible in native centimetres")
    result = {"asset": armor.get_path_name(), "material_slots": 1,
        "material": material.get_path_name(), "lods": lods, "bounds_cm": skeletal_bounds,
        "skeleton": verify_skeleton(armor, skeleton, reference),
        "weight_readback": "Source validator inspects vertex weights; rendered KusazuriReviewGameMode reports section influences and verifies follower bone alignment"}

    name = "SM_Kusazuri01"
    static = import_file(ART / "Review/Exports" / (name + ".fbx"), name, "static", REVIEW)
    add_lods(static, name, skeletal=False)
    require(stat.get_number_materials(static) == 1, "Kusazuri static review mesh must have one material slot")
    static.set_material(0, material)
    static_lods = []
    for lod in range(stat.get_lod_count(static)):
        # The exported LOD already has the intended reduction; avoid a second
        # engine reduction that would erase the authored lamellar silhouette.
        reduction = stat.get_lod_reduction_settings(static, lod)
        reduction.percent_triangles = reduction.percent_vertices = 1.0
        reduction.max_deviation = 0.0
        reduction.base_lod_model = lod
        stat.set_lod_reduction_settings(static, lod, reduction)
        info = {"lod": lod, "triangles": static.get_num_triangles(lod), "render_vertices": static.get_num_vertices(lod),
                "sections": static.get_num_sections(lod), "uv_channels": stat.get_num_uv_channels(static, lod),
                "material_slot": stat.get_lod_material_slot(static, lod, 0),
                "build_settings": build_settings(stat, static, lod, static=True)}
        require(info["triangles"] > 0 and info["sections"] == 1 and info["uv_channels"] >= 1 and info["material_slot"] == 0,
                "Invalid Kusazuri static review LOD")
        stat.enable_section_collision(static, False, lod, 0)
        static_lods.append(info)
    require(static_lods[0]["triangles"] > static_lods[1]["triangles"] > static_lods[2]["triangles"],
            "Kusazuri static LODs must decrease")
    require(stat.set_lod_screen_sizes(static, REVIEW_SCREEN_SIZES), "Could not set Kusazuri static LOD screen sizes")
    bounds = static.get_bounding_box()
    static_bounds = box(vector(bounds.min), vector(bounds.max))
    maximum_bounds_delta = max(abs(a-b) for edge in ("min", "max")
                               for a,b in zip(skeletal_bounds[edge], static_bounds[edge]))
    require(maximum_bounds_delta < .01, "Skeletal/static Kusazuri exports differ in orientation, scale or placement")
    result["static_review_mesh"] = {"asset": static.get_path_name(), "material_slots": 1, "lods": static_lods,
                                    "bounds_cm": static_bounds, "maximum_skeletal_bounds_delta_cm": maximum_bounds_delta}
    report["skeletal_mesh"] = result
    return armor


def main():
    write_report()
    before = package_hashes()
    skeleton, mannequin = u.load_asset(SKELETON), u.load_asset(FIT)
    require(skeleton is not None and mannequin is not None,
            "Existing Manny mesh and skeleton are required")
    require(mannequin.get_editor_property("skeleton") == skeleton, "Native mannequin skeleton identity mismatch")
    reference = bones(mannequin)
    material = create_material_variant()
    armor = import_armor(material, skeleton, reference)
    report["animations"] = []
    for role, path in NATIVE_CLIPS.items():
        clip = u.load_asset(path)
        require(clip is not None and clip.get_editor_property("skeleton") == skeleton,
                "Missing native Manny animation or incompatible skeleton: " + path)
        duration, frames = u.AnimationLibrary.get_sequence_length(clip), u.AnimationLibrary.get_num_frames(clip)
        require(duration > 0 and frames > 1, "Empty native Manny animation: " + path)
        report["animations"].append({"role": role, "asset": clip.get_path_name(), "seconds": duration,
                                    "frames": frames, "reused_native_asset": True})
    verify_skeleton(armor, skeleton, reference)
    mode = u.load_class(None, "/Script/Shoen.KusazuriReviewGameMode")
    require(mode is not None, "Build ShoenEditor with KusazuriReviewGameMode before importing the review map")
    map_file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix("/Game/") + ".umap")
    world = (u.EditorLoadingAndSavingUtils.load_map(str(map_file)) if map_file.exists()
             else u.EditorLoadingAndSavingUtils.new_blank_map(False))
    require(world is not None, "Could not load or create Kusazuri review map")
    world.get_world_settings().set_editor_property("default_game_mode", mode)
    require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Could not save Kusazuri review map")
    for obj in dirty.values():
        require(u.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False), "Could not save " + obj.get_path_name())
    after = package_hashes()
    require(before == after, "A read-only Manny/Kabuto/Dō/animation dependency package changed")
    report["read_only_dependencies"] = {"unchanged": True, "sha256_before": before, "sha256_after": after}
    report["review_map"] = {"asset": MAP, "default_game_mode": mode.get_path_name()}
    report["saved_assets"] = sorted(dirty)
    report["validated"] = True
    write_report()
    u.log("SHOEN_KUSAZURI01_IMPORT_VALIDATED " + str(REPORT_PATH))


try:
    main()
except Exception:
    report["validated"] = False
    report["error"] = traceback.format_exc()
    write_report()
    raise
