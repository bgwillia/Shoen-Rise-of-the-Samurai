"""Reopen Kabuto01.blend in Blender and measure the saved source independently.

Run: Blender --background --factory-startup --python Scripts/validate_kabuto.py
Writes artifacts/kabuto01/source-validation.json; never modifies the blend file.
"""
import hashlib
import json
import math
from pathlib import Path
import struct
import traceback

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
OUTPUT = ROOT / "artifacts/kabuto01/source-validation.json"
REPORT = {"asset": "Kabuto01", "validated": False, "checks": [],
          "scope": "Saved Blender source, static neutral fit and export files; no rendering or Unreal claim"}
AREA_EPSILON_M2 = 1e-12
POSITION_DIGITS = 7


def check(name, passed, detail=None):
    REPORT["checks"].append({"name": name, "passed": bool(passed), "detail": detail})


def save_report():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(REPORT, indent=2, allow_nan=False) + "\n")


def geometry_hash(ob, subset=None):
    """Exact float32 coordinates and ordered topology, excluding names/materials."""
    selected = set(range(len(ob.data.vertices))) if subset is None else set(subset)
    digest = hashlib.sha256()
    for vertex in ob.data.vertices:
        if vertex.index in selected:
            digest.update(struct.pack("<I3f", vertex.index, *vertex.co))
    for face in ob.data.polygons:
        if all(index in selected for index in face.vertices):
            digest.update(struct.pack("<I", len(face.vertices)))
            digest.update(struct.pack("<" + "I" * len(face.vertices), *face.vertices))
    return digest.hexdigest()


def head_indices(body):
    group = body.vertex_groups.get("head")
    if group is None:
        raise RuntimeError("Fit body is missing its original head vertex group")
    return {v.index for v in body.data.vertices
            if any(g.group == group.index and g.weight > 0.5 for g in v.groups)}


def evaluate(ob, depsgraph):
    evaluated = ob.evaluated_get(depsgraph)
    data = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        data.calc_loop_triangles()
        vertices = [evaluated.matrix_world @ vertex.co for vertex in data.vertices]
        triangles = [tuple(face.vertices) for face in data.loop_triangles]
        bm = bmesh.new()
        bm.from_mesh(data)
        nonmanifold = sum(not edge.is_manifold for edge in bm.edges)
        boundary = sum(edge.is_boundary for edge in bm.edges)
        wire = sum(edge.is_wire for edge in bm.edges)
        volume = bm.calc_volume(signed=True)
        bm.free()
        quantized = [tuple(round(value, POSITION_DIGITS) for value in co) for co in vertices]
        faces = [tuple(sorted(quantized[index] for index in triangle)) for triangle in triangles]
        degenerate = sum((vertices[b] - vertices[a]).cross(vertices[c] - vertices[a]).length * 0.5
                         <= AREA_EPSILON_M2 for a, b, c in triangles)
        uv_layers = []
        for layer in data.uv_layers:
            values = [tuple(uv.uv) for uv in layer.data]
            uv_layers.append({"name": layer.name, "loops": len(values),
                              "finite": all(math.isfinite(v) for pair in values for v in pair),
                              "min": [min(pair[axis] for pair in values) for axis in range(2)] if values else [],
                              "max": [max(pair[axis] for pair in values) for axis in range(2)] if values else []})
        info = {"vertices": len(vertices), "triangles": len(triangles),
                "nonmanifold_edges": nonmanifold, "boundary_edges": boundary, "wire_edges": wire,
                "degenerate_triangles": degenerate,
                "duplicate_position_vertices": len(quantized) - len(set(quantized)),
                "duplicate_geometric_triangles": len(faces) - len(set(faces)),
                "signed_volume_m3": volume,
                "bounds_world_metres": [[min(co[axis] for co in vertices) for axis in range(3)],
                                         [max(co[axis] for co in vertices) for axis in range(3)]],
                "materials": [mat.name if mat else None for mat in data.materials],
                "polygon_material_indices": sorted({p.material_index for p in data.polygons}),
                "uv_layers": uv_layers,
                "location": list(ob.location), "rotation_euler": list(ob.rotation_euler),
                "scale": list(ob.scale),
                "modifiers": [{"name": mod.name, "type": mod.type} for mod in ob.modifiers]}
        return info, vertices, triangles
    finally:
        evaluated.to_mesh_clear()


def bvh(vertices, triangles):
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=0.0)


def validate_mesh(name, info, closed=True):
    check(name + ": finite nonempty geometry", info["triangles"] > 0 and
          all(math.isfinite(v) for bound in info["bounds_world_metres"] for v in bound))
    check(name + ": no zero-area triangles", info["degenerate_triangles"] == 0,
          {"count": info["degenerate_triangles"], "area_tolerance_m2": AREA_EPSILON_M2})
    check(name + ": no duplicate faces", info["duplicate_geometric_triangles"] == 0,
          info["duplicate_geometric_triangles"])
    if closed:
        check(name + ": closed manifold parts", info["nonmanifold_edges"] == 0,
              {key: info[key] for key in ("nonmanifold_edges", "boundary_edges", "wire_edges")})
    check(name + ": one atlas material", info["materials"] == ["M_Kabuto01"] and
          info["polygon_material_indices"] == [0], info["materials"])
    check(name + ": finite 0-1 UV atlas", bool(info["uv_layers"]) and all(
        layer["finite"] and layer["loops"] > 0 and min(layer["min"]) >= -0.0001
        and max(layer["max"]) <= 1.0001 for layer in info["uv_layers"]), info["uv_layers"])
    check(name + ": unit scale and zero rotation",
          all(abs(value - 1) < 1e-6 for value in info["scale"]) and
          all(abs(value) < 1e-6 for value in info["rotation_euler"]))


def main():
    save_report()
    source = ART / "Kabuto01.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    REPORT["blender_version"] = bpy.app.version_string
    REPORT["source"] = {"file": str(source.relative_to(ROOT)),
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    scene = bpy.context.scene
    check('fit actions survive reopening the source', all(
        name in bpy.data.actions for name in ('A_Neutral', 'A_Idle', 'A_Walk')))
    body = bpy.data.objects["FIT_MaleBody"]
    rig = bpy.data.objects["FIT_Rig"]
    rig.animation_data.action = bpy.data.actions["A_Neutral"]
    scene.frame_set(1)
    for ob in (body, rig):
        ob.hide_set(False)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    check("metre source units", scene.unit_settings.system == "METRIC" and
          abs(scene.unit_settings.scale_length - 1) < 1e-6)
    names = {bone.name for bone in rig.data.bones}
    check("head attachment exists without exported leaf bones", "head" in names and
          not any(name.lower().endswith("_end") for name in names))
    head_set = head_indices(body)
    REPORT["fit_body"] = {"vertices": len(body.data.vertices), "head_vertices": len(head_set),
                          "geometry_sha256": geometry_hash(body),
                          "head_geometry_sha256": geometry_hash(body, head_set),
                          "bone_count": len(names), "head_pivot_metres": list(rig.data.bones["head"].head_local)}
    legacy = ART.parent / "Prototype01/Samurai01.blend"
    if legacy.exists():
        with bpy.data.libraries.load(str(legacy), link=False) as (available, appended):
            if "SK_Body" not in available.objects:
                raise RuntimeError("Legacy source exists but has no SK_Body for provenance comparison")
            appended.objects = ["SK_Body"]
        original = appended.objects[0]
        original_head = head_indices(original)
        REPORT["fit_body"]["original_geometry_sha256"] = geometry_hash(original)
        REPORT["fit_body"]["original_head_geometry_sha256"] = geometry_hash(original, original_head)
        check("fit body preserves original geometry", geometry_hash(body) == geometry_hash(original))
        check("fit head preserves original geometry", geometry_hash(body, head_set) == geometry_hash(original, original_head))
    else:
        REPORT["fit_body"]["original_comparison"] = "Unavailable: legacy untracked source is absent; embedded snapshot measured only"

    source_collection = bpy.data.collections["KABUTO01 • editable components"]
    components = sorted((ob for ob in source_collection.objects if ob.type == "MESH"), key=lambda ob: ob.name)
    required = {"Hachi", "Mabisashi", "Shikoro", "Fukigaeshi_L", "Fukigaeshi_R", "Maedate", "Uchiwa", "ShinHimo"}
    check("editable helmet components present", required.issubset({ob.name for ob in components}))
    REPORT["source_component_count"] = len(components)
    REPORT["components"] = {}
    evaluated_parts = {}
    for ob in components:
        info, vertices, triangles = evaluate(ob, depsgraph)
        REPORT["components"][ob.name] = info
        evaluated_parts[ob.name] = (vertices, triangles)
        validate_mesh(ob.name, info)
        check(ob.name + ": consistent head attachment pivot",
              (ob.location - rig.data.bones["head"].head_local).length < 1e-6)
    REPORT["evaluated_source_triangles"] = sum(info["triangles"] for info in REPORT["components"].values())
    REPORT["runtime_lods"] = []
    for level in range(3):
        name = "SM_Kabuto01_LOD%d" % level
        ob = bpy.data.objects[name]
        ob.hide_set(False)
        info, _, _ = evaluate(ob, depsgraph)
        validate_mesh(name, info)
        check(name + ": head-local origin", ob.location.length < 1e-6)
        REPORT["runtime_lods"].append(info)
    counts = [info["triangles"] for info in REPORT["runtime_lods"]]
    check("runtime LOD triangle counts decrease", counts[0] > counts[1] > counts[2] > 0, counts)
    manifest_file = ART / "asset-manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())
        check("manifest matches reopened runtime counts", manifest.get("runtime_lod_triangles") == counts,
              {"measured": counts, "manifest": manifest.get("runtime_lod_triangles")})

    REPORT["textures"] = {}
    for suffix in ("BaseColor", "Normal", "ORM"):
        name = "T_Kabuto01_" + suffix
        image = bpy.data.images[name]
        path = ART / "Textures" / (name + ".png")
        payload = path.read_bytes()
        png_size = list(struct.unpack(">II", payload[16:24])) if payload[:8] == b"\x89PNG\r\n\x1a\n" else None
        pixels = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(pixels)
        pixels = pixels.reshape(-1, image.channels)
        info = {"packed": image.packed_file is not None, "blend_size": list(image.size),
                "external_png_size": png_size, "color_space": image.colorspace_settings.name,
                "external_sha256": hashlib.sha256(payload).hexdigest(),
                "channel_min": pixels.min(axis=0).tolist(), "channel_max": pixels.max(axis=0).tolist()}
        REPORT["textures"][suffix] = info
        check(name + ": packed and external 2K texture", info["packed"] and
              info["blend_size"] == [2048, 2048] and png_size == [2048, 2048])
        check(name + ": opaque alpha", image.channels == 4 and float(pixels[:, 3].min()) >= 0.9999)
        if suffix != "BaseColor":
            check(name + ": linear data", info["color_space"] == "Non-Color")
    material = bpy.data.materials["M_Kabuto01"]
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    normal_nodes = [node for node in material.node_tree.nodes if node.type == "NORMAL_MAP"]
    check("opaque shader alpha", not shader.inputs["Alpha"].is_linked and shader.inputs["Alpha"].default_value >= .9999)
    REPORT["material"] = {"name": material.name,
                          "normal_strengths": [node.inputs["Strength"].default_value for node in normal_nodes],
                          "uses_transparency": shader.inputs["Alpha"].is_linked or shader.inputs["Alpha"].default_value < .9999}

    # True triangle intersections against the unchanged head mesh, not bounding boxes.
    _, body_vertices, body_triangles = evaluate(body, depsgraph)
    if len(body_vertices) != len(body.data.vertices):
        raise RuntimeError("Fit body modifiers changed topology; head vertex mapping cannot be assumed")
    head_triangles = [triangle for triangle in body_triangles if all(index in head_set for index in triangle)]
    head_tree = bvh(body_vertices, head_triangles)
    intersections = {}
    trees = {}
    for name, (vertices, triangles) in evaluated_parts.items():
        tree = bvh(vertices, triangles)
        trees[name] = tree
        pairs = head_tree.overlap(tree)
        intersections[name] = {"triangle_pairs": len(pairs), "examples": [list(pair) for pair in pairs[:8]]}
        check(name + ": no head surface intersections", len(pairs) == 0, len(pairs))
    REPORT["head_to_helmet_bvh"] = intersections

    # Independent radial clearance from actual upper-skull vertices. The head
    # center is measured from the preserved body, not the helmet construction.
    head_vertices = [body_vertices[index] for index in sorted(head_set)]
    low = Vector(tuple(min(vertex[axis] for vertex in head_vertices) for axis in range(3)))
    high = Vector(tuple(max(vertex[axis] for vertex in head_vertices) for axis in range(3)))
    center = Vector(((low.x + high.x) * .5, (low.y + high.y) * .5, high.z - .083))
    scalp = [vertex for vertex in head_vertices if vertex.z > center.z + .012]
    radial = {}
    for name in ("Hachi",):
        distances, missed, aperture = [], 0, 0
        for vertex in scalp:
            delta = vertex - center
            direction = delta.normalized()
            location, _, _, distance = trees[name].ray_cast(center, direction, .5)
            if location is not None:
                distances.append(distance - delta.length)
            elif name == "Hachi" and direction.z > .95:
                aperture += 1
            else:
                missed += 1
        radial[name] = {"sampled_skull_vertices": len(scalp), "surface_hits": len(distances),
                        "open_region_rays": missed, "axial_crown_aperture_rays": aperture,
                        "min_clearance_mm": min(distances) * 1000 if distances else None,
                        "median_clearance_mm": float(np.median(distances)) * 1000 if distances else None}
        check(name + ": upper-skull radial clearance", bool(distances) and min(distances) > 0,
              radial[name])
        if name == "Hachi":
            check("bowl covers sampled upper skull outside crown aperture", missed == 0, radial[name])
    REPORT["upper_skull_clearance"] = {"center_metres": list(center), "results": radial}

    # The lining is an open collar, not a second bowl. Upward skull rays can
    # correctly leave through its open top, so measure its inside surface at
    # the same height as actual skull vertices within the collar's body.
    padding_vertices = [vertex for vertex in head_vertices if 1.695 <= vertex.z <= 1.735]
    padding_distances, padding_missed = [], 0
    for vertex in padding_vertices:
        origin = Vector((0.0, .006, vertex.z))
        delta = vertex - origin
        if delta.length <= 1e-9:
            padding_missed += 1
            continue
        location, _, _, distance = trees["Uchiwa"].ray_cast(origin, delta.normalized(), .5)
        if location is None:
            padding_missed += 1
        else:
            padding_distances.append(distance - delta.length)
    padding = {
        "method": "Horizontal outward rays from the collar center to its inside surface at each actual skull vertex height",
        "height_interval_metres": [1.695, 1.735], "ray_origin_xy_metres": [0.0, .006],
        "sampled_skull_vertices": len(padding_vertices), "surface_hits": len(padding_distances),
        "missed_rays": padding_missed, "required_clearance_mm": 3.0,
        "min_clearance_mm": min(padding_distances) * 1000 if padding_distances else None,
        "median_clearance_mm": float(np.median(padding_distances)) * 1000 if padding_distances else None,
    }
    REPORT["padding_clearance"] = padding
    check("Uchiwa: horizontal skull clearance at least 3mm",
          bool(padding_distances) and padding_missed == 0 and min(padding_distances) >= .003,
          padding)

    # Actual eye-region points looking straight forward (-Y); forehead, ears,
    # chin cords and the deliberate crown opening have separate roles.
    head_z = rig.data.bones["head"].head_local.z
    eye_points = [vertex for vertex in head_vertices if head_z + .085 <= vertex.z <= head_z + .110
                  and abs(vertex.x) <= .06 and vertex.y <= -.06]
    eye_obstructions = {name: sum(tree.ray_cast(point + Vector((0, -.00001, 0)),
                                                   Vector((0, -1, 0)), .3)[0] is not None
                                   for point in eye_points) for name, tree in trees.items()}
    REPORT["eye_region_forward_visibility"] = {"sampled_points": len(eye_points), "obstructions": eye_obstructions}
    check("eyes have unobstructed forward clearance", len(eye_points) > 0 and not any(eye_obstructions.values()),
          REPORT["eye_region_forward_visibility"])

    required_exports = ["Exports/SM_Kabuto01.fbx", "Exports/SM_Kabuto01_LOD1.fbx", "Exports/SM_Kabuto01_LOD2.fbx",
                        "Review/Exports/SK_FitMannequin.fbx", "Review/Exports/SM_FitMannequin.fbx",
                        "Review/Exports/A_Idle.fbx", "Review/Exports/A_Walk.fbx"]
    REPORT["exports"] = {}
    for name in required_exports:
        path = ART / name
        payload = path.read_bytes()
        check(name + ": binary FBX exists", payload.startswith(b"Kaydara FBX Binary") and len(payload) > 1000)
        REPORT["exports"][name] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    REPORT["limitations"] = [
        "Texture detail is procedural tangent-space relief, not a sculpt-to-low-poly bake.",
        "ORM red contains procedural pore and cord-contact occlusion, not mesh-baked ambient occlusion.",
        "Disconnected closed plates, trim, rivets and cords intentionally overlap each other; no boolean union or inter-part self-intersection acceptance is claimed.",
        "Duplicate vertex positions are reported separately from duplicate faces because UV seams and intersecting independent parts can share coordinates.",
        "Bowl clearance samples the preserved mannequin's upper head; padding clearance uses horizontal rays within the collar height. Both use the neutral pose. Eye rays check forward visibility, not peripheral vision or animated neck clearance.",
        "The fit mannequin is existing original prototype anatomy, not a certified production retarget standard.",
    ]
    REPORT["validated"] = all(item["passed"] for item in REPORT["checks"])
    save_report()
    if not REPORT["validated"]:
        raise RuntimeError("Kabuto01 source validation failed: " + "; ".join(
            item["name"] for item in REPORT["checks"] if not item["passed"]))
    print("KABUTO01_SOURCE_VALIDATED " + str(OUTPUT))


try:
    main()
except Exception:
    REPORT["validated"] = False
    REPORT["error"] = traceback.format_exc()
    save_report()
    raise
