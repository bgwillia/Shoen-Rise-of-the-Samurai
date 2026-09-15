"""Import Dō01 and its static review copy, using Epic's native UE5 Manny.

Execute in the built ShoenEditor Python commandlet, with no other Unreal
process using this checkout. Native Manny assets are read-only dependencies.
"""
import hashlib
import json
import math
from pathlib import Path
import traceback

import unreal as u


ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Characters/Samurai/Do01"
DEST = "/Game/Art/Characters/Samurai/Do01"
REVIEW = DEST + "/Review"
MAP = REVIEW + "/Do01_Review"
MANNY = "/Game/Characters/Mannequins"
FIT = MANNY + "/Meshes/SKM_Manny_Simple"
SKELETON = MANNY + "/Meshes/SK_Mannequin"
NATIVE_CLIPS = {"idle": MANNY + "/Anims/Unarmed/MM_Idle",
                "walk": MANNY + "/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd",
                "run": MANNY + "/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd",
                "attack": MANNY + "/Anims/Unarmed/Attack/MM_Attack_01"}
REPORT_PATH = ROOT / "artifacts/do01/unreal-import.json"
NORMAL_STRENGTH = .65
REVIEW_SCREEN_SIZES = [1.0, .22, .08]
# FBX float rotations can move a distal bone by ~20 microns in a native-Manny
# roundtrip. These bounds allow that precision loss, never hierarchy changes.
REFERENCE_TOLERANCES = {"translation_cm": .01, "scale": 1e-4, "quaternion_dot_error": 1e-6}
assets = u.AssetToolsHelpers.get_asset_tools()
edit = u.MaterialEditingLibrary
stat = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
skel = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
dirty = {}
report = {"asset": "Do01", "engine_version": u.SystemLibrary.get_engine_version(),
          "validated": False, "rendering_validated": False, "imports": [],
          "fbx_import": {"convert_scene": False, "convert_scene_unit": True,
                         "force_front_x_axis": False, "normal_import": "Import normals and tangents",
                         "coordinate_contract": "Blender world metres, -Y forward, preserved native .01-scale root; raw FBX maps (100x,-100y,100z) into native Manny +Y-forward mesh space."}}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_report():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def remember(obj):
    require(obj is not None and obj.get_path_name().startswith(DEST + "/"),
            "Missing asset or attempted write outside Do01")
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
    return remember(u.load_asset(dest + "/" + name))


def create_material(textures):
    mat = u.load_asset(DEST + "/M_Do01")
    if mat is None:
        mat = assets.create_asset("M_Do01", DEST, u.Material, u.MaterialFactoryNew())
    remember(mat)
    edit.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", u.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", False)
    mat.set_editor_property("tangent_space_normal", True)

    def node(cls, **values):
        obj = edit.create_material_expression(mat, cls)
        for key, value in values.items():
            obj.set_editor_property(key, value)
        return obj

    def output(src, channel, property_):
        require(edit.connect_material_property(src, channel, property_), "Material output connection failed")

    color = node(u.MaterialExpressionTextureSampleParameter2D, parameter_name="BaseColor", texture=textures["BaseColor"])
    normal = node(u.MaterialExpressionTextureSampleParameter2D, parameter_name="Normal", texture=textures["Normal"],
                  sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    orm = node(u.MaterialExpressionTextureSampleParameter2D, parameter_name="ORM", texture=textures["ORM"],
               sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS)
    flat = node(u.MaterialExpressionConstant3Vector, constant=u.LinearColor(0, 0, 1, 1))
    blend = node(u.MaterialExpressionLinearInterpolate, const_alpha=NORMAL_STRENGTH)
    normalized = node(u.MaterialExpressionNormalize)
    for src, channel, dst, input_ in ((flat, "", blend, "A"), (normal, "RGB", blend, "B"), (blend, "", normalized, "")):
        require(edit.connect_material_expressions(src, channel, dst, input_), "Normal-strength connection failed")
    for src, channel, property_ in ((color, "RGB", u.MaterialProperty.MP_BASE_COLOR),
                                   (normalized, "", u.MaterialProperty.MP_NORMAL),
                                   (orm, "R", u.MaterialProperty.MP_AMBIENT_OCCLUSION),
                                   (orm, "G", u.MaterialProperty.MP_ROUGHNESS),
                                   (orm, "B", u.MaterialProperty.MP_METALLIC)):
        output(src, channel, property_)
    edit.set_material_usage(mat, u.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    edit.set_material_usage(mat, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    edit.layout_material_expressions(mat)
    compile_errors = list(edit.recompile_material(mat))
    require(not compile_errors, "Dō material compile errors: " + "; ".join(compile_errors))
    report["material"] = {"asset": mat.get_path_name(), "blend_mode": str(mat.get_editor_property("blend_mode")),
                           "two_sided": mat.get_editor_property("two_sided"), "normal_strength": NORMAL_STRENGTH,
                           "compile_errors": compile_errors,
                           "active_render_device_verified": False,
                           "render_preflight": "Run compile_do_materials.py with real RHI before rendered review; NullRHI import cannot validate active-device shader permutations."}
    return mat


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
    require(armor.get_editor_property("skeleton") == skeleton, "Dō must reuse the exact existing mannequin skeleton")
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
    report["skeleton"] = result
    require(not errors, "Dō reference skeleton mismatch: " + "; ".join(errors))
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


def import_static_manny(mannequin):
    mesh = import_file(ART / "Review/Exports/SM_Manny.fbx", "SM_Manny", "static", REVIEW)
    if stat.get_lod_count(mesh) > 1:
        require(stat.remove_lods(mesh), "Could not replace prior static Manny LODs")
    for lod in (1, 2):
        source = ART / "Review/Exports" / ("SM_Manny_LOD%d.fbx" % lod)
        require(source.is_file(), "Missing generated static Manny review LOD: " + str(source))
        require(stat.get_lod_count(mesh) == lod and stat.import_lod(mesh, lod, str(source)) == lod,
                "Static Manny manual LOD import failed")
        report["imports"].append({"source": str(source.relative_to(ROOT)), "asset": mesh.get_path_name(),
            "lod": lod, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    native_slots = list(mannequin.get_editor_property("materials"))
    slots = list(mesh.get_editor_property("static_materials"))
    require(len(slots) == len(native_slots), "Static Manny must preserve its native material slots")
    by_name = {}
    for slot in native_slots:
        material = slot.material_interface
        require(material is not None, "Native Manny material is missing")
        by_name[str(slot.material_slot_name)] = material
        by_name[material.get_name()] = material
    mapping = []
    for index, slot in enumerate(slots):
        name = str(slot.material_slot_name)
        material = by_name.get(name)
        method = "native material or slot name"
        if material is None:
            # The copied native FBX retains its material order; the exact slot
            # count was checked above. UE 5.8 exposes only material_slot_name.
            material = native_slots[index].material_interface
            method = "validated native slot order"
        mesh.set_material(index, material)
        mapping.append({"slot": index, "source_name": name, "mapping_method": method,
                        "material": material.get_path_name()})
    lods = []
    for lod in range(stat.get_lod_count(mesh)):
        # The supplied FBXs already contain the intended geometry. UE must not
        # generate another reduction from LOD0 over these manual review LODs.
        reduction = stat.get_lod_reduction_settings(mesh, lod)
        reduction.percent_triangles = reduction.percent_vertices = 1.0
        reduction.max_deviation = 0.0
        reduction.base_lod_model = lod
        stat.set_lod_reduction_settings(mesh, lod, reduction)
        settings = build_settings(stat, mesh, lod, static=True)
        sections = [{"section": section, "material_slot": stat.get_lod_material_slot(mesh, lod, section)}
                    for section in range(mesh.get_num_sections(lod))]
        for section in sections:
            require(0 <= section["material_slot"] < len(native_slots), "Static Manny LOD has an invalid material index")
            section["material"] = mesh.get_material(section["material_slot"]).get_path_name()
            stat.enable_section_collision(mesh, False, lod, section["section"])
        info = {"lod": lod, "triangles": mesh.get_num_triangles(lod), "vertices": mesh.get_num_vertices(lod),
                "sections": sections, "uv_channels": stat.get_num_uv_channels(mesh, lod),
                "build_settings": settings, "ue_reduction_percent_triangles": reduction.percent_triangles,
                "ue_reduction_percent_vertices": reduction.percent_vertices}
        require(info["triangles"] > 0 and info["uv_channels"] > 0 and
                {section["material_slot"] for section in sections} == set(range(len(native_slots))),
                "Static Manny LOD lacks geometry, UVs or either native material")
        lods.append(info)
    require(lods[0]["triangles"] > lods[1]["triangles"] > lods[2]["triangles"],
            "Static Manny review LODs must decrease in triangle count")
    require(stat.set_lod_screen_sizes(mesh, REVIEW_SCREEN_SIZES), "Could not set manual static Manny LOD screensizes")
    bounds = mesh.get_bounding_box()
    report["static_mannequin"] = {"asset": mesh.get_path_name(), "native_reference": FIT,
        "lods": lods, "material_mapping": mapping,
        "screen_sizes": list(stat.get_lod_screen_sizes(mesh)), "automatic_screen_sizes": False,
        "source_reduction_ratios": [1.0, .32, .15],
        "generation": "Native Manny LOD0 rest geometry; Blender DECIMATE creates approximate static review LOD1/2. These are not Epic skeletal LODs.",
        "bounds_cm": box(vector(bounds.min), vector(bounds.max))}


def main():
    write_report()
    skeleton, mannequin = u.load_asset(SKELETON), u.load_asset(FIT)
    require(skeleton is not None and mannequin is not None, "Native Epic Manny mesh and skeleton are required")
    require(mannequin.get_editor_property("skeleton") == skeleton, "Existing mannequin skeleton identity mismatch")
    reference = bones(mannequin)
    skeleton_file = Path(u.Paths.project_content_dir()) / (SKELETON.removeprefix("/Game/") + ".uasset")
    before_hash = hashlib.sha256(skeleton_file.read_bytes()).hexdigest()
    native_mesh_file = Path(u.Paths.project_content_dir()) / (FIT.removeprefix("/Game/") + ".uasset")
    native_mesh_hash = hashlib.sha256(native_mesh_file.read_bytes()).hexdigest()
    textures = {}
    report["textures"] = {}
    for suffix in ("BaseColor", "Normal", "ORM"):
        name = "T_Do01_" + suffix
        texture = import_file(ART / "Textures" / (name + ".png"), name, "texture")
        texture.set_editor_property("srgb", suffix == "BaseColor")
        texture.set_editor_property("compression_settings", {"BaseColor": u.TextureCompressionSettings.TC_DEFAULT,
            "Normal": u.TextureCompressionSettings.TC_NORMALMAP, "ORM": u.TextureCompressionSettings.TC_MASKS}[suffix])
        texture.set_editor_property("flip_green_channel", suffix == "Normal")
        width, height = texture.blueprint_get_size_x(), texture.blueprint_get_size_y()
        require(width == 2048 and height == 2048, "Dō textures must be 2048x2048")
        report["textures"][suffix] = {"asset": texture.get_path_name(), "size": [width, height],
            "srgb": texture.get_editor_property("srgb"), "flip_green_channel": texture.get_editor_property("flip_green_channel"),
            "compression": str(texture.get_editor_property("compression_settings"))}
        textures[suffix] = texture
    material = create_material(textures)
    armor = import_file(ART / "Exports/SK_Do01.fbx", "SK_Do01", "skeletal", skeleton=skeleton)
    report["skeleton"] = verify_skeleton(armor, skeleton, reference)
    if skel.get_lod_count(armor) > 1:
        require(skel.remove_lods(armor, list(range(1, skel.get_lod_count(armor)))), "Could not replace prior Dō skeletal LODs")
    for lod in (1, 2):
        source = ART / "Exports" / ("SK_Do01_LOD%d.fbx" % lod)
        if source.exists():
            require(skel.get_lod_count(armor) == lod, "Dō skeletal LOD exports must be consecutive")
            require(skel.import_lod(armor, lod, str(source)) == lod, "Dō skeletal LOD import failed")
            report["imports"].append({"source": str(source.relative_to(ROOT)), "asset": armor.get_path_name(), "lod": lod})
    materials = armor.get_editor_property("materials")
    require(len(materials) == 1, "Dō skeletal mesh must have one material slot")
    materials[0].set_editor_property("material_interface", material)
    armor.set_editor_property("materials", materials)
    lods = []
    for lod in range(skel.get_lod_count(armor)):
        info = {"lod": lod, "render_vertices": skel.get_num_verts(armor, lod),
                "sections": skel.get_num_sections(armor, lod), "section_material_slot": skel.get_lod_material_slot(armor, lod, 0),
                "build_settings": build_settings(skel, armor, lod)}
        require(info["render_vertices"] > 0 and info["sections"] == 1 and info["section_material_slot"] == 0,
                "Dō skeletal LOD is empty or has unexpected material sections")
        lods.append(info)
    bounds = armor.get_imported_bounds()
    report["skeletal_mesh"] = {"asset": armor.get_path_name(), "material_slots": len(materials), "lods": lods,
        "bounds_cm": box(vector(bounds.origin - bounds.box_extent), vector(bounds.origin + bounds.box_extent)),
        "weights": {"per_vertex_inspection_available": False,
                    "note": "Imported geometry and skinning weights; Python API has no reflected render-buffer weight query. DoReviewGameMode records actual section MaxBoneInfluences, triangles and UV channels separately."}}

    static = import_file(ART / "Review/Exports/SM_Do01.fbx", "SM_Do01", "static", REVIEW)
    if stat.get_lod_count(static) > 1:
        require(stat.remove_lods(static), "Could not replace prior Dō static LODs")
    for lod in (1, 2):
        source = ART / "Review/Exports" / ("SM_Do01_LOD%d.fbx" % lod)
        if source.exists():
            require(stat.get_lod_count(static) == lod and stat.import_lod(static, lod, str(source)) == lod,
                    "Dō static LOD import failed or sources are nonconsecutive")
            report["imports"].append({"source": str(source.relative_to(ROOT)), "asset": static.get_path_name(), "lod": lod})
    require(stat.get_number_materials(static) == 1, "Dō static review mesh must have one material slot")
    static.set_material(0, material)
    static_lods = []
    for lod in range(stat.get_lod_count(static)):
        settings = build_settings(stat, static, lod, static=True)
        info = {"lod": lod, "triangles": static.get_num_triangles(lod), "render_vertices": static.get_num_vertices(lod),
                "sections": static.get_num_sections(lod), "uv_channels": stat.get_num_uv_channels(static, lod),
                "material_slot": stat.get_lod_material_slot(static, lod, 0), "build_settings": settings}
        require(info["triangles"] > 0 and info["sections"] == 1 and info["uv_channels"] >= 1 and info["material_slot"] == 0,
                "Invalid Dō static review LOD")
        stat.enable_section_collision(static, False, lod, 0)
        static_lods.append(info)
    require(stat.set_lod_screen_sizes(static, REVIEW_SCREEN_SIZES[:len(static_lods)]), "Could not set static Dō LOD screen sizes")
    bounds = static.get_bounding_box()
    report["static_review_mesh"] = {"asset": static.get_path_name(), "material_slots": 1, "lods": static_lods,
                                    "bounds_cm": box(vector(bounds.min), vector(bounds.max))}
    import_static_manny(mannequin)
    report["animations"] = []
    for role, path in NATIVE_CLIPS.items():
        clip = u.load_asset(path)
        require(clip is not None and clip.get_editor_property("skeleton") == skeleton,
                "Native Manny review animation is missing or uses a different skeleton: " + path)
        duration, frames = u.AnimationLibrary.get_sequence_length(clip), u.AnimationLibrary.get_num_frames(clip)
        require(duration > 0 and frames > 1, "Empty native Manny animation: " + path)
        report["animations"].append({"role": role, "asset": clip.get_path_name(), "seconds": duration,
            "frames": frames, "skeleton": skeleton.get_path_name(), "reused_native_asset": True,
            "description": "Original native forward jog" if role == "run" else "Original native template clip"})

    verify_skeleton(armor, skeleton, reference)
    mode = u.load_class(None, "/Script/Shoen.DoReviewGameMode")
    require(mode is not None, "Build ShoenEditor with DoReviewGameMode before importing the review map")
    map_file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix("/Game/") + ".umap")
    world = (u.EditorLoadingAndSavingUtils.load_map(str(map_file)) if map_file.exists()
             else u.EditorLoadingAndSavingUtils.new_blank_map(False))
    require(world is not None, "Could not load or create Dō review map")
    world.get_world_settings().set_editor_property("default_game_mode", mode)
    require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Could not save Dō review map")
    for obj in dirty.values():
        require(u.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False), "Could not save " + obj.get_path_name())
    after_hash = hashlib.sha256(skeleton_file.read_bytes()).hexdigest()
    require(after_hash == before_hash, "Existing shared skeleton package was changed")
    report["skeleton"]["package_sha256_before"] = before_hash
    report["skeleton"]["package_sha256_after"] = after_hash
    native_mesh_after = hashlib.sha256(native_mesh_file.read_bytes()).hexdigest()
    require(native_mesh_hash == native_mesh_after, "Native skeletal Manny package was changed")
    report["static_mannequin"].update({"native_skeletal_mesh_unchanged": True,
        "native_skeletal_package_sha256_before": native_mesh_hash, "native_skeletal_package_sha256_after": native_mesh_after})
    report["review_map"] = {"asset": MAP, "default_game_mode": mode.get_path_name()}
    report["saved_assets"] = sorted(dirty)
    report["validated"] = True
    write_report()
    u.log("SHOEN_DO01_IMPORT_VALIDATED " + str(REPORT_PATH))


try:
    main()
except Exception:
    report["validated"] = False
    report["error"] = traceback.format_exc()
    write_report()
    raise
