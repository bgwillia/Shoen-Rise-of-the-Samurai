"""Inspect/export Epic UE5 Manny; run serially in ShoenEditor with real RHI.

Exports original geometry and four existing clips. Package assets are never saved
or retargeted. A_Run is the template's existing forward jog, not a new animation.
"""
import hashlib
import json
from pathlib import Path
import traceback
import unreal as u


ROOT = Path(u.Paths.project_dir()).resolve().parent
BASE = "/Game/Characters/Mannequins"
MESH = BASE + "/Meshes/SKM_Manny_Simple"
SKELETON = BASE + "/Meshes/SK_Mannequin"
OUT = ROOT / "SourceArt/Characters/Mannequins/Manny/Exports"
REPORT = ROOT / "artifacts/do01/manny-unreal-source.json"
CLIPS = {"A_Idle": "/Anims/Unarmed/MM_Idle",
         "A_Walk": "/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd",
         "A_Run": "/Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd",
         "A_Attack": "/Anims/Unarmed/Attack/MM_Attack_01"}
report = {"validated": False, "rendering_validated": False,
          "engine_version": u.SystemLibrary.get_engine_version(), "exports": [],
          "source": "Epic UE 5.8 High/Characters template, unmodified native assets",
          "run_clip_description": "Original forward jog; A_Run is an export filename alias only",
          "matrix_convention": "row arrays, column vectors; centimetres in native mesh space; Manny faces +Y, Z-up",
          "export_options": {"ascii": False, "level_of_detail": False, "collision": False,
                             "force_front_x_axis": False, "export_preview_mesh": False,
                             "export_morph_targets": False}}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def checkpoint(stage):
    report["stage"] = stage
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def matrix(t, q, s):
    x, y, z, w = q
    return [[(1-2*y*y-2*z*z)*s[0], (2*x*y-2*z*w)*s[1], (2*x*z+2*y*w)*s[2], t[0]],
            [(2*x*y+2*z*w)*s[0], (1-2*x*x-2*z*z)*s[1], (2*y*z-2*x*w)*s[2], t[1]],
            [(2*x*z-2*y*w)*s[0], (2*y*z+2*x*w)*s[1], (1-2*x*x-2*y*y)*s[2], t[2]],
            [0, 0, 0, 1]]


def multiply(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def export(obj, name, animation=False):
    options = u.FbxExportOption()
    for key, value in report["export_options"].items():
        options.set_editor_property(key, value)
    # UE 5.8 constructs material-baking data even when disabled: this skeletal
    # exporter needs a real RHI. Disabling bake only avoids material conversion.
    options.set_editor_property("bake_material_inputs", u.FbxMaterialBakeMode.DISABLED)
    task = u.AssetExportTask()
    task.object = obj
    task.filename = str(OUT / (name + ".fbx"))
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    task.options = options
    if animation:
        task.exporter = u.AnimSequenceExporterFBX()
    checkpoint("exporting " + obj.get_path_name())
    require(u.Exporter.run_asset_export_task(task), "Export failed: " + obj.get_path_name())
    path = Path(task.filename)
    require(path.is_file() and path.stat().st_size > 1000, "Missing or empty FBX: " + str(path))
    report["exports"].append({"asset": obj.get_path_name(), "file": str(path.relative_to(ROOT)),
                              "bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "export_errors": [str(e) for e in task.errors]})
    checkpoint("exported " + obj.get_path_name())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous([BASE], force_rescan=True)
    checkpoint("loading native mesh and skeleton")
    mesh, skeleton = u.load_asset(MESH), u.load_asset(SKELETON)
    require(mesh is not None and skeleton is not None, "Copy native Manny template assets before running")
    require(mesh.get_editor_property("skeleton") == skeleton, "Unexpected Manny skeleton identity")
    # This transient preview choice allows exports to use Manny, without copying
    # Quinn or the original editable sequences referenced by preview-only fields.
    u.AnimationLibrary.set_skeleton_preview_mesh(skeleton, mesh, False)
    component = u.SkeletalMeshComponent()
    component.set_skeletal_mesh_asset(mesh)
    bones, world = [], {}
    for index in range(component.get_num_bones()):
        name = str(component.get_bone_name(index))
        parent = str(component.get_parent_bone(name))
        transform = component.get_ref_pose_transform(index)
        t = vec(transform.translation)
        s = vec(transform.scale3d)
        q = transform.rotation
        q = [float(q.x), float(q.y), float(q.z), float(q.w)]
        local = matrix(t, q, s)
        composed = multiply(world[parent], local) if parent in world else local
        world[name] = composed
        bones.append({"index": index, "name": name, "parent": parent,
                      "translation_cm": t, "rotation_xyzw": q, "scale": s,
                      "local_matrix": local, "component_matrix": composed})
    bounds = mesh.get_imported_bounds()
    origin, extent = vec(bounds.origin), vec(bounds.box_extent)
    minimum, maximum = [a-b for a,b in zip(origin, extent)], [a+b for a,b in zip(origin, extent)]
    subsystem = u.get_editor_subsystem(u.SkeletalMeshEditorSubsystem)
    report.update({"mesh": mesh.get_path_name(), "skeleton": skeleton.get_path_name(),
                   "mesh_reference_bone_count": len(bones), "mesh_reference_bones": bones,
                   "bounds_cm": {"min": minimum, "max": maximum, "size": [2*x for x in extent]},
                   "head_bone_reference_height_cm": world.get("head", [[0]*4]*4)[2][3],
                   "mesh_top_height_cm": maximum[2],
                   "materials": [{"slot": str(slot.material_slot_name),
                                  "asset": slot.material_interface.get_path_name() if slot.material_interface else None}
                                 for slot in mesh.get_editor_property("materials")],
                   "lods": [{"lod": lod, "vertices": subsystem.get_num_verts(mesh, lod),
                             "sections": subsystem.get_num_sections(mesh, lod)}
                            for lod in range(subsystem.get_lod_count(mesh))]})
    require("head" in world and len(bones) > 50, "Missing Manny reference hierarchy")
    checkpoint("native mesh measurements complete")
    export(mesh, "SKM_Manny_Simple")
    report["animations"] = []
    for alias, suffix in CLIPS.items():
        checkpoint("loading " + BASE + suffix)
        clip = u.load_asset(BASE + suffix)
        require(clip is not None and clip.get_editor_property("skeleton") == skeleton,
                "Missing or mismatched native animation: " + suffix)
        report["animations"].append({"asset": clip.get_path_name(), "export_alias": alias,
                                     "frames": u.AnimationLibrary.get_num_frames(clip),
                                     "seconds": u.AnimationLibrary.get_sequence_length(clip),
                                     "skeleton": clip.get_editor_property("skeleton").get_path_name()})
        export(clip, alias, True)
    report["validated"] = True


try:
    main()
except Exception:
    report["error"] = traceback.format_exc()
    raise
finally:
    checkpoint("complete" if report["validated"] else report.get("stage", "failed"))
    u.log("Manny source report: " + str(REPORT))
