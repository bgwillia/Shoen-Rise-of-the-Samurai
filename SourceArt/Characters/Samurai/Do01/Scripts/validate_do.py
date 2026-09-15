"""Reopen authoritative Do01.blend and verify the saved neutral-pose asset.

Run in Blender --background --factory-startup --python validate_do.py.
Metres, -Y forward, Epic Manny's original root object and reference skeleton.
Imports the original Manny FBX independently; never saves either source file.
This bounded source check does not claim animation, rendering or Unreal fit.
"""
import hashlib
import json
import math
from pathlib import Path
import struct
import traceback

import bpy
import bmesh
from mathutils.bvhtree import BVHTree


ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
OUTPUT = ROOT / "artifacts/do01/source-validation.json"
PARTS = {"Do_Main", "Do_Back", "Do_Side_L", "Do_Side_R", "Do_Upper", "Do_Straps",
         "Do_Edge", "Do_Lacing", "Do_Fittings", "Do_Lining"}
REPORT = {"asset": "Do01", "validated": False, "checks": {},
          "scope": "Reopened source, neutral-pose geometry/skin weights and static intersections"}


def check(name, passed, detail=None):
    REPORT["checks"][name] = {"passed": bool(passed), "detail": detail}


def save_report():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(REPORT, indent=2, allow_nan=False) + "\n")


def geometry_hash(ob):
    digest = hashlib.sha256()
    for vertex in ob.data.vertices:
        digest.update(struct.pack("<I3f", vertex.index, *vertex.co))
    for face in ob.data.polygons:
        digest.update(struct.pack("<I", len(face.vertices)))
        digest.update(struct.pack("<" + "I" * len(face.vertices), *face.vertices))
    return digest.hexdigest()


def rig_hash(ob):
    digest = hashlib.sha256()
    for bone in ob.data.bones:
        digest.update((bone.name + "\0" + (bone.parent.name if bone.parent else "") + "\0").encode())
        digest.update(struct.pack("<16f", *(value for row in bone.matrix_local for value in row)))
        digest.update(struct.pack("<6f?", *bone.head_local, *bone.tail_local, bone.use_deform))
    return digest.hexdigest()


def native_reference(body, rig):
    # Loaded object matrices can be stale until Blender evaluates the scene.
    bpy.context.view_layer.update()
    file = ROOT / "SourceArt/Characters/Mannequins/Manny/Exports/SKM_Manny_Simple.fbx"
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(file), automatic_bone_orientation=False, use_anim=False)
    imported = [ob for ob in bpy.data.objects if ob not in before]
    original_body = next(ob for ob in imported if ob.type == "MESH")
    original_rig = next(ob for ob in imported if ob.type == "ARMATURE")
    bpy.context.view_layer.update()
    same_topology = len(body.data.vertices) == len(original_body.data.vertices) and [tuple(p.vertices) for p in body.data.polygons] == [tuple(p.vertices) for p in original_body.data.polygons]
    point_error = max(((body.matrix_world @ a.co) - (original_body.matrix_world @ b.co)).length
                      for a, b in zip(body.data.vertices, original_body.data.vertices)) if same_topology else None
    matrices = [(rig.matrix_world, original_rig.matrix_world)]
    same_hierarchy = [(b.name, b.parent.name if b.parent else None, b.use_deform) for b in rig.data.bones] == [(b.name, b.parent.name if b.parent else None, b.use_deform) for b in original_rig.data.bones]
    if same_hierarchy:
        matrices += [(rig.matrix_world @ a.matrix_local, original_rig.matrix_world @ b.matrix_local)
                     for a, b in zip(rig.data.bones, original_rig.data.bones)]
    matrix_error = max(abs(x-y) for a,b in matrices for row_a,row_b in zip(a,b) for x,y in zip(row_a,row_b))
    sha = hashlib.sha256(file.read_bytes()).hexdigest()
    native_report = json.loads((ROOT / "artifacts/do01/manny-unreal-source.json").read_text())
    export = next(item for item in native_report["exports"] if item["asset"].endswith(".SKM_Manny_Simple"))
    provenance = {"reference_fbx": str(file.relative_to(ROOT)), "reference_fbx_sha256": sha,
        "matches_validated_native_unreal_export": native_report["validated"] and sha == export["sha256"],
        "body_geometry_sha256": geometry_hash(body), "reference_body_geometry_sha256": geometry_hash(original_body),
        "rig_sha256": rig_hash(rig), "reference_rig_sha256": rig_hash(original_rig),
        "identical_body_topology": same_topology, "maximum_body_world_error_metres": point_error,
        "identical_bone_hierarchy": same_hierarchy, "maximum_rig_world_matrix_error": matrix_error,
        "blender_bones": len(rig.data.bones), "native_bones_including_object_root": len(rig.data.bones)+1,
        "native_unreal_bones": native_report["mesh_reference_bone_count"]}
    REPORT["preserved_manny"] = provenance
    check("unchanged native Manny geometry and world reference bones", same_topology and point_error <= 1e-6 and
          same_hierarchy and matrix_error <= 1e-6 and provenance["matches_validated_native_unreal_export"] and
          provenance["native_bones_including_object_root"] == provenance["native_unreal_bones"], provenance)
    check("native Manny source identity", rig.name == "root" and "root" not in rig.data.bones and
          rig.get("source_skeleton") == "/Game/Characters/Mannequins/Meshes/SK_Mannequin" and
          body.get("geometry_provenance") == "Unmodified official Epic UE 5.8 Manny Simple exported geometry")
    for ob in imported:
        bpy.data.objects.remove(ob, do_unlink=True)


def evaluated(ob, depsgraph):
    obj = ob.evaluated_get(depsgraph)
    mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        mesh.calc_loop_triangles()
        vertices = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        triangles = [tuple(face.vertices) for face in mesh.loop_triangles]
        bm = bmesh.new(); bm.from_mesh(mesh)
        edges = sum(not edge.is_manifold for edge in bm.edges)
        boundary = sum(edge.is_boundary for edge in bm.edges)
        bm.free()
        coordinates = [tuple(round(v, 7) for v in point) for point in vertices]
        faces = [tuple(sorted(coordinates[i] for i in tri)) for tri in triangles]
        area_zero = sum((vertices[b] - vertices[a]).cross(vertices[c] - vertices[a]).length * .5 <= 1e-12
                        for a, b, c in triangles)
        uv_valid = bool(mesh.uv_layers) and all(math.isfinite(v) and -.0001 <= v <= 1.0001
                      for layer in mesh.uv_layers for loop in layer.data for v in loop.uv)
        info = {"vertices": len(vertices), "triangles": len(triangles), "nonmanifold_edges": edges,
                "boundary_edges": boundary, "zero_area_triangles": area_zero,
                "duplicate_faces": len(faces) - len(set(faces)),
                "duplicate_position_vertices": len(coordinates) - len(set(coordinates)),
                "finite": all(math.isfinite(v) for co in vertices for v in co),
                "bounds_metres": [[min(co[axis] for co in vertices) for axis in range(3)],
                                   [max(co[axis] for co in vertices) for axis in range(3)]] if vertices else None,
                "uv_layers": [layer.name for layer in mesh.uv_layers], "uv0_1_valid": uv_valid,
                "materials": [mat.name if mat else None for mat in mesh.materials],
                "material_indices": sorted({face.material_index for face in mesh.polygons})}
        return info, vertices, triangles
    finally:
        obj.to_mesh_clear()


def weights(ob, rig):
    bone_names = {bone.name for bone in rig.data.bones}
    group_names = {group.index: group.name for group in ob.vertex_groups}
    counts, used, missing, invalid, error = {}, set(), 0, 0, 0.0
    for vertex in ob.data.vertices:
        active = [(group_names[group.group], group.weight) for group in vertex.groups
                  if group_names[group.group] in bone_names and group.weight > 1e-7]
        invalid += sum(group.weight > 1e-7 and group_names[group.group] not in bone_names
                       and group_names[group.group] != "Do_Round_Surfaces" for group in vertex.groups)
        count = len(active); counts[str(count)] = counts.get(str(count), 0) + 1
        missing += count == 0; used.update(name for name, _ in active)
        error = max(error, abs(sum(value for _, value in active) - 1))
    modifiers = [mod for mod in ob.modifiers if mod.type == "ARMATURE"]
    return {"vertices": len(ob.data.vertices), "influence_histogram": counts,
            "max_influences": max((int(n) for n in counts), default=0), "missing_weights": missing,
            "invalid_groups": invalid, "maximum_weight_sum_error": error, "bones_used": sorted(used),
            "same_rig_modifier": len(modifiers) == 1 and modifiers[0].object == rig}


def main():
    save_report()
    source = ART / "Do01.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    REPORT["source"] = {"file": str(source.relative_to(ROOT)), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "blender_version": bpy.app.version_string}
    scene = bpy.context.scene
    body, rig, helmet = [bpy.data.objects[name] for name in ("FIT_Manny", "root", "FIT_Kabuto01")]
    source_parts = sorted(bpy.data.collections["DO01 • editable components"].objects, key=lambda ob: ob.name)
    source_parts = [ob for ob in source_parts if ob.type == "MESH"]
    runtime = [bpy.data.objects["SK_Do01_LOD%d" % level] for level in range(3)]
    check("named components and collections", PARTS.issubset({ob.name for ob in source_parts}) and
          "FIT ONLY • preserved mannequin and Kabuto" in bpy.data.collections and
          "EXPORT ONLY • runtime LODs" in bpy.data.collections)
    check("source metre units", scene.unit_settings.system == "METRIC" and abs(scene.unit_settings.scale_length - 1) < 1e-6)
    native_reference(body, rig)
    rig.data.pose_position = 'REST'
    scene.frame_set(1)
    for ob in source_parts + runtime + [body, rig, helmet]:
        ob.hide_set(False)
    bpy.context.view_layer.update(); depsgraph = bpy.context.evaluated_depsgraph_get()
    REPORT["components"], REPORT["runtime_lods"], REPORT["weights"] = {}, [], {}
    source_geometry, all_info = {}, []
    for ob in source_parts + runtime:
        info, vertices, triangles = evaluated(ob, depsgraph)
        REPORT["weights"][ob.name] = weights(ob, rig)
        all_info.append((ob.name, info))
        if ob in source_parts:
            REPORT["components"][ob.name] = info
            source_geometry[ob.name] = (vertices, triangles)
        else:
            REPORT["runtime_lods"].append(info)
    mesh_errors = {name: {key: info[key] for key in ("nonmanifold_edges", "zero_area_triangles", "duplicate_faces", "finite")}
                   for name, info in all_info if not info["finite"] or info["triangles"] <= 0 or
                   info["nonmanifold_edges"] or info["zero_area_triangles"] or info["duplicate_faces"]}
    check("closed finite geometry without duplicate or zero-area faces", not mesh_errors, mesh_errors)
    check("one material and consistent atlas UVs", all(info["materials"] == ["M_Do01"] and
          info["material_indices"] == [0] and info["uv_layers"] == ["UV0_DoAtlas"] and info["uv0_1_valid"] for _, info in all_info))
    counts = [info["triangles"] for info in REPORT["runtime_lods"]]
    REPORT["source_triangles"] = sum(info["triangles"] for info in REPORT["components"].values())
    check("decreasing runtime LOD triangles", counts[0] > counts[1] > counts[2] > 0, counts)
    check("normalized weights with at most four native bone influences", all(info["same_rig_modifier"] and
          not info["missing_weights"] and not info["invalid_groups"] and info["max_influences"] <= 4 and
          info["maximum_weight_sum_error"] <= 1e-5 for info in REPORT["weights"].values()))
    check("unit scale and stable origins", all(ob.location.length < 1e-6 and max(abs(v) for v in ob.rotation_euler) < 1e-6
          and max(abs(v - 1) for v in ob.scale) < 1e-6 for ob in source_parts + runtime))
    REPORT["textures"] = {}
    for suffix in ("BaseColor", "Normal", "ORM"):
        image = bpy.data.images["T_Do01_" + suffix]; file = ART / "Textures" / (image.name + ".png")
        payload = file.read_bytes()
        REPORT["textures"][suffix] = {"packed": image.packed_file is not None, "size": list(image.size),
            "png_size": list(struct.unpack(">II", payload[16:24])) if payload[:8] == b"\x89PNG\r\n\x1a\n" else None,
            "color_space": image.colorspace_settings.name, "sha256": hashlib.sha256(payload).hexdigest()}
    check("packed and external 2K textures with correct color spaces", all(info["packed"] and info["size"] == [2048, 2048]
          and info["png_size"] == [2048, 2048] and info["color_space"] == ("sRGB" if suffix == "BaseColor" else "Non-Color")
          for suffix, info in REPORT["textures"].items()))
    REPORT["neutral_intersections"] = {}
    for target_name, target in (("body", body), ("kabuto", helmet)):
        _, points, faces = evaluated(target, depsgraph)
        tree = BVHTree.FromPolygons(points, faces, all_triangles=True, epsilon=0.0)
        observations = {}
        for name, (vertices, triangles) in source_geometry.items():
            armor_tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=0.0)
            overlaps = tree.overlap(armor_tree)
            distances = [tree.find_nearest(point)[3] for point in vertices[::max(1, math.ceil(len(vertices) / 128))]]
            observations[name] = {"triangle_intersections": len(overlaps), "examples": [list(pair) for pair in overlaps[:5]],
                                  "sampled_vertices": len(distances), "minimum_unsigned_sample_clearance_mm": min(distances) * 1000}
        REPORT["neutral_intersections"][target_name] = observations
        check("no neutral armor intersections with " + target_name,
              not any(info["triangle_intersections"] for info in observations.values()), observations)
    REPORT["limitations"] = ["Neutral pose only: motion clearance requires the separate pose renders and Unreal review.",
        "Nearest clearances are unsigned samples of armor vertices, not continuous minimum thickness or all-pose clearance.",
        "Plate/trim/lacing overlaps within the armor are intentional construction and are not tested as a boolean union.",
        "Duplicate positions are reported; only duplicate faces are rejected. Procedural/generated texture detail is not a sculpt bake."]
    REPORT["validated"] = all(check_["passed"] for check_ in REPORT["checks"].values())
    save_report()
    if not REPORT["validated"]:
        raise RuntimeError("Dō source checks failed: " + "; ".join(name for name, item in REPORT["checks"].items() if not item["passed"]))
    print("DO01_SOURCE_VALIDATED " + str(OUTPUT))


try:
    main()
except Exception:
    REPORT["validated"] = False; REPORT["error"] = traceback.format_exc()
    save_report()
    raise
