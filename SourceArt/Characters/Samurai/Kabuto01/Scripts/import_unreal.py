"""Import the isolated Kabuto01 helmet and its existing-body fit review.

Run with the project's Unreal Editor Python commandlet after ShoenEditor builds.
All generated packages remain under /Game/Art/Characters/Samurai/Kabuto01.
Run only when no other Unreal process is using this checkout.
"""
import json
import math
from pathlib import Path
import traceback

import unreal as u


ROOT = Path(u.Paths.project_dir()).resolve().parent
ART = ROOT / "SourceArt/Characters/Samurai/Kabuto01"
DEST = "/Game/Art/Characters/Samurai/Kabuto01"
REVIEW = DEST + "/Review"
MAP = REVIEW + "/Kabuto01_Review"
REPORT_PATH = ROOT / "artifacts/kabuto01/unreal-import.json"
assets = u.AssetToolsHelpers.get_asset_tools()
edit = u.MaterialEditingLibrary
stat = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
skel = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
report = {
    "asset": "Kabuto01",
    "engine_version": u.SystemLibrary.get_engine_version(),
    "validated": False,
    "rendering_validated": False,
    "imports": [],
    "fbx_import": {
        "convert_scene": False,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "coordinate_contract": "Blender metres (x, y, z) -> Unreal cm (100x, -100y, 100z)",
    },
}
dirty_assets = {}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_report():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def remember(obj):
    require(obj is not None, "Unreal returned no asset")
    require(obj.get_path_name().startswith(DEST + "/"), "Asset escaped Kabuto01 destination")
    dirty_assets[obj.get_path_name()] = obj
    return obj


def import_file(path, name, kind="texture", dest=DEST, skeleton=None):
    require(path.is_file(), "Missing source: " + str(path))
    require(dest == DEST or dest == REVIEW, "Unexpected import destination")
    task = u.AssetImportTask()
    task.filename = str(path)
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = True
    task.save = False
    if kind != "texture":
        options = u.FbxImportUI()
        options.automated_import_should_detect_type = False
        options.import_materials = False
        options.import_textures = False
        options.import_mesh = kind != "animation"
        options.import_animations = kind == "animation"
        options.import_as_skeletal = kind in ("skeletal", "animation")
        options.mesh_type_to_import = {
            "static": u.FBXImportType.FBXIT_STATIC_MESH,
            "skeletal": u.FBXImportType.FBXIT_SKELETAL_MESH,
            "animation": u.FBXImportType.FBXIT_ANIMATION,
        }[kind]
        options.create_physics_asset = False
        if skeleton:
            options.skeleton = skeleton
        data = {
            "static": options.static_mesh_import_data,
            "skeletal": options.skeletal_mesh_import_data,
            "animation": options.anim_sequence_import_data,
        }[kind]
        for key in ("convert_scene", "convert_scene_unit", "force_front_x_axis"):
            data.set_editor_property(key, report["fbx_import"][key])
        if kind != "animation":
            data.normal_import_method = u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
            if kind == 'static' and name == 'SM_Kabuto01':
                data.normal_import_method = u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
        if kind == "static":
            data.combine_meshes = True
            data.auto_generate_collision = False
            data.generate_lightmap_u_vs = False
        if kind == "animation":
            data.set_editor_property('animation_length', u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        task.options = options
        task.factory = u.FbxFactory()
    assets.import_asset_tasks([task])
    imported = list(task.imported_object_paths)
    require(imported, "No imported objects: " + str(path))
    report["imports"].append({"source": str(path.relative_to(ROOT)), "assets": imported})
    for asset_path in imported:
        remember(u.load_asset(asset_path))
    return remember(u.load_asset(dest + "/" + name))


def material(name, dest):
    mat = u.load_asset(dest + "/" + name)
    if mat is None:
        mat = assets.create_asset(name, dest, u.Material, u.MaterialFactoryNew())
    remember(mat)
    edit.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", u.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", False)
    mat.set_editor_property("tangent_space_normal", True)
    return mat


def expression(mat, cls, **values):
    node = edit.create_material_expression(mat, cls)
    require(node is not None, "Could not create material expression")
    for key, value in values.items():
        node.set_editor_property(key, value)
    return node


def connect(node, channel, property_):
    require(edit.connect_material_property(node, channel, property_), "Material connection failed")


def finish_material(mat):
    edit.layout_material_expressions(mat)
    edit.recompile_material(mat)


def bounds(mesh):
    box = mesh.get_bounding_box()
    low, high = [box.min.x, box.min.y, box.min.z], [box.max.x, box.max.y, box.max.z]
    size = [b - a for a, b in zip(low, high)]
    require(all(math.isfinite(v) for v in low + high), "Nonfinite mesh bounds")
    require(all(v > 0 for v in size), "Empty mesh bounds")
    return {"min": low, "max": high, "size": size}


def inspect_static(mesh, inspect_uv_values=False):
    lods = []
    for lod in range(stat.get_lod_count(mesh)):
        info = {
            "lod": lod,
            "triangles": mesh.get_num_triangles(lod),
            "render_vertices": mesh.get_num_vertices(lod),
            "sections": mesh.get_num_sections(lod),
            "uv_channels": stat.get_num_uv_channels(mesh, lod),
            "section_material_slots": [
                stat.get_lod_material_slot(mesh, lod, section)
                for section in range(mesh.get_num_sections(lod))
            ],
        }
        require(info["triangles"] > 0 and info["render_vertices"] > 0, "Empty imported mesh")
        require(info["sections"] == 1, "Expected one material section at each LOD")
        require(info["uv_channels"] >= 1, "Imported mesh has no UV channel")
        require(info["section_material_slots"] == [0], "Unexpected section material")
        if inspect_uv_values:
            desc = mesh.get_static_mesh_description(lod)
            require(desc is not None, "Missing imported mesh description")
            count = desc.get_vertex_instance_count()
            uv_min, uv_max = [math.inf, math.inf], [-math.inf, -math.inf]
            # Imported FBX descriptions have compact vertex-instance IDs. Fail
            # explicitly if that changes instead of silently omitting UVs.
            for index in range(count):
                instance = u.VertexInstanceID(id_value=index)
                require(desc.is_vertex_instance_valid(instance), "Noncompact imported UV IDs")
                uv = desc.get_vertex_instance_uv(instance, 0)
                for axis, value in enumerate((uv.x, uv.y)):
                    require(math.isfinite(value), "Nonfinite atlas UV")
                    uv_min[axis] = min(uv_min[axis], value)
                    uv_max[axis] = max(uv_max[axis], value)
            require(count > 0, "No imported UV values")
            require(all(v >= -0.0001 for v in uv_min) and all(v <= 1.0001 for v in uv_max),
                    "Helmet UVs escape the 0-1 atlas")
            info["uv0"] = {"vertex_instances_checked": count, "min": uv_min, "max": uv_max}
        lods.append(info)
    require(lods, "Imported mesh has no LODs")
    material_count = stat.get_number_materials(mesh)
    require(material_count == 1, "Expected one static material slot")
    return {"asset": mesh.get_path_name(), "material_slots": material_count,
            "bounds_cm": bounds(mesh), "lods": lods}


def main():
    # Clear any old success report before mutating/reimporting task-owned assets.
    write_report()
    textures = {}
    texture_report = {}
    for suffix in ("BaseColor", "Normal", "ORM"):
        name = "T_Kabuto01_" + suffix
        tex = import_file(ART / "Textures" / (name + ".png"), name)
        tex.set_editor_property("srgb", suffix == "BaseColor")
        tex.set_editor_property("compression_settings", {
            "BaseColor": u.TextureCompressionSettings.TC_DEFAULT,
            "Normal": u.TextureCompressionSettings.TC_NORMALMAP,
            "ORM": u.TextureCompressionSettings.TC_MASKS,
        }[suffix])
        # The source tangent normal uses OpenGL +Y; Unreal consumes -Y.
        tex.set_editor_property("flip_green_channel", suffix == "Normal")
        textures[suffix] = tex
        info = {"asset": tex.get_path_name(),
                "width": tex.blueprint_get_size_x(), "height": tex.blueprint_get_size_y(),
                "srgb": tex.get_editor_property("srgb"),
                "compression": str(tex.get_editor_property("compression_settings")),
                "flip_green_channel": tex.get_editor_property("flip_green_channel")}
        require(info["width"] == 2048 and info["height"] == 2048, "Expected 2K texture: " + name)
        texture_report[suffix] = info
    report["textures"] = texture_report

    helmet_mat = material("M_Kabuto01", DEST)
    color = expression(helmet_mat, u.MaterialExpressionTextureSampleParameter2D,
                       parameter_name="BaseColor", texture=textures["BaseColor"])
    normal = expression(helmet_mat, u.MaterialExpressionTextureSampleParameter2D,
                        parameter_name="Normal", texture=textures["Normal"],
                        sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    orm = expression(helmet_mat, u.MaterialExpressionTextureSampleParameter2D,
                     parameter_name="ORM", texture=textures["ORM"],
                     sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS)
    connect(color, "RGB", u.MaterialProperty.MP_BASE_COLOR)
    flat_normal = expression(helmet_mat, u.MaterialExpressionConstant3Vector,
                             constant=u.LinearColor(0.0, 0.0, 1.0, 1.0))
    normal_strength = expression(helmet_mat, u.MaterialExpressionLinearInterpolate, const_alpha=0.65)
    normalized = expression(helmet_mat, u.MaterialExpressionNormalize)
    for src, output, dst, input_ in ((flat_normal, "", normal_strength, "A"),
                                    (normal, "RGB", normal_strength, "B"),
                                    (normal_strength, "", normalized, "")):
        require(edit.connect_material_expressions(src, output, dst, input_),
                "Could not set matching 0.65 tangent normal strength")
    connect(normalized, "", u.MaterialProperty.MP_NORMAL)
    connect(orm, "R", u.MaterialProperty.MP_AMBIENT_OCCLUSION)
    connect(orm, "G", u.MaterialProperty.MP_ROUGHNESS)
    connect(orm, "B", u.MaterialProperty.MP_METALLIC)
    edit.set_material_usage(helmet_mat, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    finish_material(helmet_mat)

    mesh = import_file(ART / "Exports/SM_Kabuto01.fbx", "SM_Kabuto01", "static")
    require(stat.get_number_materials(mesh) == 1, "Helmet FBX must export one atlas material")
    mesh.set_material(0, helmet_mat)
    if stat.get_lod_count(mesh) > 1:
        require(stat.remove_lods(mesh), "Could not replace prior Kabuto01 LODs")
    for lod in (1, 2):
        source = ART / "Exports" / ("SM_Kabuto01_LOD%d.fbx" % lod)
        if source.is_file():
            require(stat.get_lod_count(mesh) == lod, "LOD sources must be consecutive")
            require(stat.import_lod(mesh, lod, str(source)) == lod, "LOD import failed")
            report["imports"].append({"source": str(source.relative_to(ROOT)),
                                      "asset": mesh.get_path_name(), "lod": lod})
    # Reimport can append duplicate slots; the source is one atlas per LOD.
    mesh.set_editor_property("static_materials", [u.StaticMaterial(
        material_interface=helmet_mat, material_slot_name="KabutoAtlas")])
    for lod in range(stat.get_lod_count(mesh)):
        require(mesh.get_num_sections(lod) == 1, "Helmet LOD must have a single section")
        stat.set_lod_material_slot(mesh, 0, lod, 0)
        stat.enable_section_collision(mesh, False, lod, 0)
        settings = stat.get_lod_build_settings(mesh, lod)
        settings.use_full_precision_u_vs = True
        settings.generate_lightmap_u_vs = False
        settings.recompute_normals = False
        settings.recompute_tangents = False
        stat.set_lod_build_settings(mesh, lod, settings)
    require(stat.set_lod_screen_sizes(mesh, [1.0, 0.22, 0.08][:stat.get_lod_count(mesh)]),
            "Could not set helmet LOD screen sizes")
    report["helmet"] = inspect_static(mesh, inspect_uv_values=True)
    report["helmet"]["material"] = {"asset": helmet_mat.get_path_name(),
                                    "blend_mode": str(helmet_mat.get_editor_property("blend_mode")),
                                    "two_sided": helmet_mat.get_editor_property("two_sided")}

    gray = material("M_FitMannequin", REVIEW)
    diffuse = expression(gray, u.MaterialExpressionConstant3Vector,
                         constant=u.LinearColor(0.23, 0.25, 0.27, 1.0))
    roughness = expression(gray, u.MaterialExpressionConstant, r=0.75)
    connect(diffuse, "", u.MaterialProperty.MP_BASE_COLOR)
    connect(roughness, "", u.MaterialProperty.MP_ROUGHNESS)
    edit.set_material_usage(gray, u.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    edit.set_material_usage(gray, u.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
    finish_material(gray)
    body = import_file(ART / "Review/Exports/SK_FitMannequin.fbx", "SK_FitMannequin",
                       "skeletal", REVIEW)
    body_materials = body.get_editor_property('materials')
    require(len(body_materials) == 1, 'Expected one existing mannequin material slot')
    body_materials[0].set_editor_property('material_interface', gray)
    body.set_editor_property('materials', body_materials)
    skeleton = remember(body.get_editor_property("skeleton"))
    static_body = import_file(ART / "Review/Exports/SM_FitMannequin.fbx", "SM_FitMannequin",
                              "static", REVIEW)
    static_body.set_material(0, gray)
    report["fit_mannequin_static"] = inspect_static(static_body)

    component = u.SkeletalMeshComponent()
    component.set_skeletal_mesh_asset(body)
    names = [str(component.get_bone_name(index)) for index in range(component.get_num_bones())]
    require("head" in names, "Fit skeleton has no head attachment bone")
    require(not any(name.lower().endswith("_end") for name in names), "Unexpected FBX leaf bones")
    head = component.get_ref_pose_transform(component.get_bone_index("head"))
    report["fit_mannequin_skeletal"] = {
        "asset": body.get_path_name(), "skeleton": skeleton.get_path_name(),
        "bone_count": len(names), "bone_names": names,
        "head_parent": str(component.get_parent_bone("head")),
        "head_local_reference_transform": str(head),
        "lods": [{"lod": lod, "render_vertices": skel.get_num_verts(body, lod),
                  "sections": skel.get_num_sections(body, lod)}
                 for lod in range(skel.get_lod_count(body))],
        "material_slots": len(body.get_editor_property("materials")),
    }
    require(report["fit_mannequin_skeletal"]["material_slots"] == 1, "Fit mesh needs one gray material")
    require(all(info["sections"] == 1 and info["render_vertices"] > 0
                for info in report["fit_mannequin_skeletal"]["lods"]), "Invalid fit skeletal sections")
    report["animations"] = []
    for name in ("A_Idle", "A_Walk"):
        anim = import_file(ART / "Review/Exports" / (name + ".fbx"), name,
                           "animation", REVIEW, skeleton)
        require(anim.get_editor_property("skeleton") == skeleton, "Wrong fit animation skeleton")
        duration = u.AnimationLibrary.get_sequence_length(anim)
        frames = u.AnimationLibrary.get_num_frames(anim)
        require(duration > 0 and frames > 1, "Empty fit animation: " + name)
        report["animations"].append({"asset": anim.get_path_name(), "duration_seconds": duration,
                                     "frames": frames, "skeleton": skeleton.get_path_name()})

    game_mode = u.load_class(None, "/Script/Shoen.KabutoReviewGameMode")
    require(game_mode is not None, "Build ShoenEditor before creating the Kabuto01 review map")
    map_file = Path(u.Paths.project_content_dir()) / "Art/Characters/Samurai/Kabuto01/Review/Kabuto01_Review.umap"
    world = (u.EditorLoadingAndSavingUtils.load_map(str(map_file.resolve())) if map_file.exists()
             else u.EditorLoadingAndSavingUtils.new_blank_map(False))
    require(world is not None, "Could not create or load Kabuto01 review map")
    world.get_world_settings().set_editor_property("default_game_mode", game_mode)
    require(u.EditorLoadingAndSavingUtils.save_map(world, MAP), "Could not save Kabuto01 review map")
    report["review_map"] = {"asset": MAP, "default_game_mode": game_mode.get_path_name()}
    for obj in dirty_assets.values():
        require(u.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False),
                "Could not save " + obj.get_path_name())
    report["saved_assets"] = sorted(dirty_assets)
    report["validated"] = True
    write_report()
    u.log("SHOEN_KABUTO01_IMPORT_VALIDATED " + str(REPORT_PATH))


try:
    main()
except Exception:
    report["validated"] = False
    report["error"] = traceback.format_exc()
    write_report()
    raise
