"""Import the Sode01 pair and static review copies on the unchanged native Manny skeleton.

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
ART = ROOT / "SourceArt/Characters/Samurai/Sode01"
DEST = "/Game/Art/Characters/Samurai/Sode01"
REVIEW = DEST + "/Review"
MAP = REVIEW + "/Sode01_Review"
MANNY = "/Game/Characters/Mannequins"
FIT = MANNY + "/Meshes/SKM_Manny_Simple"
SKELETON = MANNY + "/Meshes/SK_Mannequin"
NATIVE_CLIPS = {"idle": MANNY + "/Anims/Unarmed/MM_Idle",
                "walk": MANNY + "/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd",
                "run": MANNY + "/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd",
                "attack": MANNY + "/Anims/Unarmed/Attack/MM_Attack_01"}
REPORT_PATH = ROOT / "artifacts/sode01/unreal-import.json"
REVIEW_SCREEN_SIZES = [1.0, .22, .08]
# FBX float rotations can move a distal bone by ~20 microns in a native-Manny
# roundtrip. These bounds allow that precision loss, never hierarchy changes.
REFERENCE_TOLERANCES = {"translation_cm": .01, "scale": 1e-4, "quaternion_dot_error": 1e-6}
assets = u.AssetToolsHelpers.get_asset_tools()
edit = u.MaterialEditingLibrary
stat = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
skel = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
dirty = {}
report = {"asset": "Sode01", "engine_version": u.SystemLibrary.get_engine_version(),
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
            "Missing asset or attempted write outside Sode01")
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
    require(armor.get_editor_property("skeleton") == skeleton, "Sode must reuse the exact existing mannequin skeleton")
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
    require(not errors, "Sode reference skeleton mismatch: " + "; ".join(errors))
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
MATERIAL = DEST + "/M_Sode01"
NORMAL_STRENGTH = .65
ROUGHNESS_BIAS = .08
SPECULAR = .30
ATLAS_TINT_CODE = """
// FBX import flips V for Unreal texture sampling. Recover Blender's atlas row
// only for palette classification; texture samples retain their native UVs.
float tile = floor(UV.x * 4.0) + 4.0 * floor((1.0 - UV.y) * 4.0);
if (tile == 0.0 || tile == 10.0) return float3(0.28, 0.29, 0.30);
if (tile == 3.0) return float3(0.38, 0.30, 0.28);
if (tile == 2.0 || tile == 11.0) return float3(0.85, 0.78, 0.67);
return float3(0.85, 0.85, 0.85);
""".strip()
READ_ONLY_DEPENDENCIES = [FIT, SKELETON, DO + "/M_Do01", DO + "/SK_Do01", DO + "/Review/SM_Do01",
    "/Game/Art/Characters/Samurai/Kabuto01/SM_Kabuto01"] + list(NATIVE_CLIPS.values()) + [
    DO + "/T_Do01_" + suffix for suffix in ("BaseColor", "Normal", "ORM")]



def create_material():
    """One Sode material reuses three existing Dō texture assets without edits."""
    textures = {suffix: u.load_asset(DO + "/T_Do01_" + suffix) for suffix in ("BaseColor", "Normal", "ORM")}
    require(all(texture is not None for texture in textures.values()), "Missing existing Dō atlas texture")
    mat = u.load_asset(MATERIAL)
    if mat is None:
        mat = assets.create_asset("M_Sode01", DEST, u.Material, u.MaterialFactoryNew())
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

    def connect(src, channel, dst, pin):
        require(edit.connect_material_expressions(src, channel, dst, pin), "Sode material expression connection failed: " + pin)

    def output(src, channel, property_):
        require(edit.connect_material_property(src, channel, property_), "Sode material output connection failed")

    color = node(u.MaterialExpressionTextureSampleParameter2D, parameter_name="BaseColor", texture=textures["BaseColor"])
    normal = node(u.MaterialExpressionTextureSampleParameter2D, parameter_name="Normal", texture=textures["Normal"],
                  sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    orm = node(u.MaterialExpressionTextureSampleParameter2D, parameter_name="ORM", texture=textures["ORM"],
               sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS)
    uv = node(u.MaterialExpressionTextureCoordinate, coordinate_index=0)
    uv_input = u.CustomInput()
    uv_input.set_editor_property("input_name", "UV")
    tint = node(u.MaterialExpressionCustom, code=ATLAS_TINT_CODE, output_type=u.CustomMaterialOutputType.CMOT_FLOAT3,
                description="Sode restrained atlas palette", inputs=[uv_input])
    connect(uv, "", tint, "UV")
    colored = node(u.MaterialExpressionMultiply)
    connect(color, "RGB", colored, "A")
    connect(tint, "", colored, "B")
    roughness = node(u.MaterialExpressionAdd, const_b=ROUGHNESS_BIAS)
    connect(orm, "G", roughness, "A")
    clamped = node(u.MaterialExpressionClamp, min_default=0.0, max_default=1.0)
    connect(roughness, "", clamped, "")
    flat = node(u.MaterialExpressionConstant3Vector, constant=u.LinearColor(0,0,1,1))
    blend = node(u.MaterialExpressionLinearInterpolate, const_alpha=NORMAL_STRENGTH)
    normalized = node(u.MaterialExpressionNormalize)
    connect(flat, "", blend, "A")
    connect(normal, "RGB", blend, "B")
    connect(blend, "", normalized, "")
    specular = node(u.MaterialExpressionConstant, r=SPECULAR)
    for src, channel, property_ in ((colored,"",u.MaterialProperty.MP_BASE_COLOR),
                                   (normalized,"",u.MaterialProperty.MP_NORMAL),
                                   (orm,"R",u.MaterialProperty.MP_AMBIENT_OCCLUSION),
                                   (clamped,"",u.MaterialProperty.MP_ROUGHNESS),
                                   (orm,"B",u.MaterialProperty.MP_METALLIC),
                                   (specular,"",u.MaterialProperty.MP_SPECULAR)):
        output(src,channel,property_)
    edit.set_material_usage(mat,u.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    edit.set_material_usage(mat,u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    edit.layout_material_expressions(mat)
    compile_errors = list(edit.recompile_material(mat))
    require(not compile_errors, "Sode material compile errors: " + "; ".join(compile_errors))
    report["material"] = {"asset":mat.get_path_name(), "shared_by_both_sides":True,
        "reused_existing_do_material":False, "reused_existing_do_textures":True,
        "saved_or_changed":True, "new_texture_allocations":0,
        "textures":{key:texture.get_path_name() for key,texture in textures.items()},
        "texture_atlas":"Existing Dō 2048px BaseColor/Normal/ORM, unchanged",
        "tile_index":"floor(U*4)+4*floor((1-V)*4); recover Blender atlas row after FBX V flip", "tile_color_multipliers":{
            "0,10":[.28,.29,.30], "3":[.38,.30,.28], "2,11":[.85,.78,.67], "others":[.85,.85,.85]},
        "normal_strength":NORMAL_STRENGTH, "normal_method":"normalize(lerp(flat normal, existing normal, strength))",
        "roughness_bias":ROUGHNESS_BIAS, "roughness_clamp":[0,1], "specular":SPECULAR,
        "metallic":"unchanged existing ORM.B", "ambient_occlusion":"unchanged existing ORM.R",
        "blend_mode":str(mat.get_editor_property("blend_mode")), "two_sided":False,
        "runtime_slots_per_side":1, "runtime_slots_pair":2, "unique_runtime_materials_pair":1,
        "custom_hlsl":ATLAS_TINT_CODE, "compile_errors":compile_errors,
        "active_render_device_verified":False,
        "render_preflight":"NullRHI import cannot certify active-device shader permutations; rendered review remains required"}
    return mat


def package_hashes():
    result = {}
    for path in READ_ONLY_DEPENDENCIES:
        file = Path(u.Paths.project_content_dir()) / (path.removeprefix("/Game/") + ".uasset")
        require(file.is_file(), "Missing existing armor-set dependency: " + path)
        result[path] = hashlib.sha256(file.read_bytes()).hexdigest()
    return result


def add_lods(mesh, name, skeletal):
    subsystem = skel if skeletal else stat
    folder = ART / ("Exports" if skeletal else "Review/Exports")
    if subsystem.get_lod_count(mesh) > 1:
        removed = (skel.remove_lods(mesh, list(range(1, skel.get_lod_count(mesh)))) if skeletal
                   else stat.remove_lods(mesh))
        require(removed, "Could not replace prior Sode LODs")
    for lod in (1, 2):
        source = folder / (name + "_LOD%d.fbx" % lod)
        require(source.is_file(), "Missing required Sode LOD: " + str(source))
        require(subsystem.get_lod_count(mesh) == lod and subsystem.import_lod(mesh, lod, str(source)) == lod,
                "Sode LOD import failed or sources were nonconsecutive")
        report["imports"].append({"source": str(source.relative_to(ROOT)), "asset": mesh.get_path_name(),
                                 "lod": lod, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    require(subsystem.get_lod_count(mesh) == 3, "Sode requires three LODs")


def import_side(side, material, skeleton, reference):
    name = "SK_Sode_" + side + "_01"
    armor = import_file(ART / "Exports" / (name + ".fbx"), name, "skeletal", skeleton=skeleton)
    add_lods(armor, name, skeletal=True)
    materials = list(armor.get_editor_property("materials"))
    require(len(materials) == 1, "Each Sode skeletal mesh must have one material slot")
    materials[0].set_editor_property("material_interface", material)
    armor.set_editor_property("materials", materials)
    lods = []
    for lod in range(skel.get_lod_count(armor)):
        info = {"lod": lod, "render_vertices": skel.get_num_verts(armor, lod),
                "sections": skel.get_num_sections(armor, lod), "section_material_slot": skel.get_lod_material_slot(armor, lod, 0),
                "build_settings": build_settings(skel, armor, lod)}
        require(info["render_vertices"] > 0 and info["sections"] == 1 and info["section_material_slot"] == 0,
                "Sode skeletal LOD is empty or has unexpected sections")
        lods.append(info)
    require(lods[0]["render_vertices"] > lods[1]["render_vertices"] > lods[2]["render_vertices"],
            "Sode skeletal LODs must decrease")
    bounds = armor.get_imported_bounds()
    skeletal_bounds = box(vector(bounds.origin - bounds.box_extent), vector(bounds.origin + bounds.box_extent))
    require(bounds.origin.x * (1 if side == "L" else -1) > 0, "Sode handedness mismatch in native Manny coordinates")
    require(5 < max(skeletal_bounds["size"]) < 100 and 70 < bounds.origin.z < 190,
            "Sode scale/height is implausible in native centimetres")
    result = {"asset": armor.get_path_name(), "side": "anatomical left" if side == "L" else "anatomical right",
        "native_x_sign": "positive" if side == "L" else "negative", "material_slots": 1,
        "material": material.get_path_name(), "lods": lods, "bounds_cm": skeletal_bounds,
        "skeleton": verify_skeleton(armor, skeleton, reference),
        "weight_readback": "Source validator inspects vertex weights; rendered SodeReviewGameMode reports section influences and verifies follower bone alignment"}

    name = "SM_Sode_" + side + "_01"
    static = import_file(ART / "Review/Exports" / (name + ".fbx"), name, "static", REVIEW)
    add_lods(static, name, skeletal=False)
    require(stat.get_number_materials(static) == 1, "Each Sode static review mesh must have one material slot")
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
                "Invalid Sode static review LOD")
        stat.enable_section_collision(static, False, lod, 0)
        static_lods.append(info)
    require(static_lods[0]["triangles"] > static_lods[1]["triangles"] > static_lods[2]["triangles"],
            "Sode static LODs must decrease")
    require(stat.set_lod_screen_sizes(static, REVIEW_SCREEN_SIZES), "Could not set Sode static LOD screen sizes")
    bounds = static.get_bounding_box()
    static_bounds = box(vector(bounds.min), vector(bounds.max))
    maximum_bounds_delta = max(abs(a-b) for edge in ("min", "max")
                               for a,b in zip(skeletal_bounds[edge], static_bounds[edge]))
    require(maximum_bounds_delta < .01, "Skeletal/static Sode exports differ in orientation, scale or placement")
    result["static_review_mesh"] = {"asset": static.get_path_name(), "material_slots": 1, "lods": static_lods,
                                    "bounds_cm": static_bounds, "maximum_skeletal_bounds_delta_cm": maximum_bounds_delta}
    report["sides"][side] = result
    return armor


def main():
    write_report()
    before = package_hashes()
    skeleton, mannequin = u.load_asset(SKELETON), u.load_asset(FIT)
    require(skeleton is not None and mannequin is not None,
            "Existing Manny mesh and skeleton are required")
    require(mannequin.get_editor_property("skeleton") == skeleton, "Native mannequin skeleton identity mismatch")
    reference = bones(mannequin)
    material = create_material()
    report["sides"] = {}
    shoulders = [import_side(side, material, skeleton, reference) for side in ("L", "R")]
    report["animations"] = []
    for role, path in NATIVE_CLIPS.items():
        clip = u.load_asset(path)
        require(clip is not None and clip.get_editor_property("skeleton") == skeleton,
                "Missing native Manny animation or incompatible skeleton: " + path)
        duration, frames = u.AnimationLibrary.get_sequence_length(clip), u.AnimationLibrary.get_num_frames(clip)
        require(duration > 0 and frames > 1, "Empty native Manny animation: " + path)
        report["animations"].append({"role": role, "asset": clip.get_path_name(), "seconds": duration,
                                    "frames": frames, "reused_native_asset": True})
    for armor in shoulders:
        verify_skeleton(armor, skeleton, reference)
    mode = u.load_class(None, "/Script/Shoen.SodeReviewGameMode")
    require(mode is not None, "Build ShoenEditor with SodeReviewGameMode before importing the review map")
    map_file = Path(u.Paths.project_content_dir()) / (MAP.removeprefix("/Game/") + ".umap")
    world = (u.EditorLoadingAndSavingUtils.load_map(str(map_file)) if map_file.exists()
             else u.EditorLoadingAndSavingUtils.new_blank_map(False))
    require(world is not None, "Could not load or create Sode review map")
    world.get_world_settings().set_editor_property("default_game_mode", mode)
    require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Could not save Sode review map")
    for obj in dirty.values():
        require(u.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False), "Could not save " + obj.get_path_name())
    after = package_hashes()
    require(before == after, "A read-only Manny/Kabuto/Dō/animation dependency package changed")
    report["read_only_dependencies"] = {"unchanged": True, "sha256_before": before, "sha256_after": after}
    report["review_map"] = {"asset": MAP, "default_game_mode": mode.get_path_name()}
    report["saved_assets"] = sorted(dirty)
    report["validated"] = True
    write_report()
    u.log("SHOEN_SODE01_IMPORT_VALIDATED " + str(REPORT_PATH))


try:
    main()
except Exception:
    report["validated"] = False
    report["error"] = traceback.format_exc()
    write_report()
    raise
