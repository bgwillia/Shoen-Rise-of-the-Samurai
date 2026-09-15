"""Independent saved-source and runtime-copy Sode validation (never saves).

Run with Blender --background --factory-startup --python-exit-code 1 --python.
Actual pose/render/Unreal evidence remains separate from this source check.
"""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import traceback

import bpy
import bmesh
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sode_common import (ART, ROOT, SOURCE, FIT, RUNTIME, STUDIO, SIDES, MATERIAL,
    ROUND_GROUP, source_parts, geometry_hash, rig_hash)

OUTPUT = ROOT / 'artifacts/sode01/source-validation.json'
REPORT = {'asset': 'Sode01', 'validated': False, 'checks': {},
    'scope': 'Reopened editable source and generated runtime copies, neutral geometry/weights and intersections; no rendering/performance claim'}


def check(name, passed, detail=None):
    REPORT['checks'][name] = {'passed': bool(passed), 'detail': detail}


def save_report():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(REPORT, indent=2, allow_nan=False) + '\n')


def topology(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    info = {'nonmanifold_edges': sum(not edge.is_manifold for edge in bm.edges),
        'boundary_edges': sum(edge.is_boundary for edge in bm.edges),
        'inconsistent_winding_edges': sum(edge.is_manifold and not edge.is_contiguous for edge in bm.edges)}
    pending, volumes = set(bm.verts), []
    while pending:
        first = pending.pop()
        group, stack = {first}, [first]
        while stack:
            vertex = stack.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in pending:
                    pending.remove(other)
                    group.add(other)
                    stack.append(other)
        faces = {face for vertex in group for face in vertex.link_faces}
        volume = 0.
        for face in faces:
            points = [vertex.co-first.co for vertex in face.verts]
            for i in range(1, len(points)-1):
                volume += points[0].dot(points[i].cross(points[i+1])) / 6
        volumes.append(volume)
    info.update({'connected_islands': len(volumes),
        'negative_volume_islands': sum(volume < -1e-13 for volume in volumes),
        'flat_volume_islands': sum(abs(volume) <= 1e-13 for volume in volumes)})
    bm.free()
    return info


def evaluated(ob, depsgraph, inspect=True):
    obj = ob.evaluated_get(depsgraph)
    mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        mesh.calc_loop_triangles()
        points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        triangles = [tuple(face.vertices) for face in mesh.loop_triangles]
        if not inspect:
            return {}, points, triangles
        coordinates = [tuple(round(value, 7) for value in point) for point in points]
        faces = [tuple(sorted(coordinates[i] for i in tri)) for tri in triangles]
        zero_area = sum((points[b]-points[a]).cross(points[c]-points[a]).length * .5 <= 1e-12
                        for a, b, c in triangles)
        info = topology(mesh)
        info.update({'vertices': len(points), 'triangles': len(triangles),
            'zero_area_triangles': zero_area, 'duplicate_faces': len(faces)-len(set(faces)),
            'duplicate_position_vertices': len(coordinates)-len(set(coordinates)),
            'finite': all(math.isfinite(value) for point in points for value in point),
            'bounds_metres': [[min(point[axis] for point in points) for axis in range(3)],
                              [max(point[axis] for point in points) for axis in range(3)]] if points else None,
            'uv_layers': [layer.name for layer in mesh.uv_layers],
            'uv0_1_valid': bool(mesh.uv_layers) and all(math.isfinite(value) and -.0001 <= value <= 1.0001
                for layer in mesh.uv_layers for corner in layer.data for value in corner.uv),
            'materials': [mat.name if mat else None for mat in mesh.materials],
            'material_indices': sorted({face.material_index for face in mesh.polygons}),
            'invalid_corner_normals': sum(not all(math.isfinite(value) for value in normal.vector)
                or abs(normal.vector.length-1) > .001 for normal in mesh.corner_normals)})
        return info, points, triangles
    finally:
        obj.to_mesh_clear()


def weights(ob, rig):
    bone_names = {bone.name for bone in rig.data.bones}
    names = {group.index: group.name for group in ob.vertex_groups}
    counts, used, missing, invalid, error = {}, set(), 0, 0, 0.
    for vertex in ob.data.vertices:
        active = [(names[group.group], group.weight) for group in vertex.groups
                  if names[group.group] in bone_names and group.weight > 1e-7]
        invalid += sum(not math.isfinite(group.weight) or group.weight < 0 or
            (group.weight > 1e-7 and names[group.group] not in bone_names and names[group.group] != ROUND_GROUP)
            for group in vertex.groups)
        count = len(active)
        counts[str(count)] = counts.get(str(count), 0)+1
        missing += count == 0
        used.update(name for name, _ in active)
        error = max(error, abs(sum(value for _, value in active)-1))
    modifiers = [mod for mod in ob.modifiers if mod.type == 'ARMATURE']
    return {'vertices': len(ob.data.vertices), 'influence_histogram': counts,
        'max_influences': max((int(count) for count in counts), default=0),
        'missing_weights': missing, 'invalid_groups_or_values': invalid,
        'maximum_weight_sum_error': error, 'bones_used': sorted(used),
        'same_rig_modifier': len(modifiers) == 1 and modifiers[0].object == rig}


def native_reference(body, rig):
    file = ROOT / 'SourceArt/Characters/Mannequins/Manny/Exports/SKM_Manny_Simple.fbx'
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(file), automatic_bone_orientation=False, use_anim=False)
    imported = [ob for ob in bpy.data.objects if ob not in before]
    native_body = next(ob for ob in imported if ob.type == 'MESH')
    native_rig = next(ob for ob in imported if ob.type == 'ARMATURE')
    bpy.context.view_layer.update()
    same_topology = len(body.data.vertices) == len(native_body.data.vertices) and \
        [tuple(face.vertices) for face in body.data.polygons] == [tuple(face.vertices) for face in native_body.data.polygons]
    point_error = max(((body.matrix_world @ a.co)-(native_body.matrix_world @ b.co)).length
        for a, b in zip(body.data.vertices, native_body.data.vertices)) if same_topology else None
    hierarchy = lambda ob: [(bone.name, bone.parent.name if bone.parent else None, bone.use_deform) for bone in ob.data.bones]
    same_hierarchy = hierarchy(rig) == hierarchy(native_rig)
    matrices = [(rig.matrix_world, native_rig.matrix_world)]
    if same_hierarchy:
        matrices += [(rig.matrix_world @ a.matrix_local, native_rig.matrix_world @ b.matrix_local)
            for a, b in zip(rig.data.bones, native_rig.data.bones)]
    matrix_error = max(abs(a-b) for one, two in matrices for row1, row2 in zip(one, two) for a, b in zip(row1, row2))
    fixture = json.loads((ROOT / 'SourceArt/Characters/Mannequins/Manny/fixture-manifest.json').read_text())
    sha = hashlib.sha256(file.read_bytes()).hexdigest()
    provenance = {'reference_fbx': str(file.relative_to(ROOT)), 'reference_fbx_sha256': sha,
        'matches_native_fixture_hash': sha == fixture['source_fbx_sha256'],
        'body_geometry_sha256': geometry_hash(body), 'reference_body_geometry_sha256': geometry_hash(native_body),
        'rig_sha256': rig_hash(rig), 'reference_rig_sha256': rig_hash(native_rig),
        'identical_body_topology': same_topology, 'maximum_body_world_error_metres': point_error,
        'identical_bone_hierarchy': same_hierarchy, 'maximum_rig_world_matrix_error': matrix_error,
        'blender_bones': len(rig.data.bones), 'native_bones_including_object_root': len(rig.data.bones)+1}
    REPORT['preserved_manny'] = provenance
    check('unchanged native Manny body proportions and reference skeleton', same_topology and point_error <= 1e-6 and
        same_hierarchy and matrix_error <= 1e-6 and provenance['matches_native_fixture_hash'] and
        len(rig.data.bones)+1 == fixture['native_reference_bones'], provenance)
    check('native armature object root is retained', rig.name == 'root' and not rig.parent and 'root' not in rig.data.bones)
    for ob in imported:
        bpy.data.objects.remove(ob, do_unlink=True)


def is_attachment(name):
    return 'Suspension' in name


def intersection_report(parts, fixtures, depsgraph):
    observations = {}
    for label, targets in fixtures.items():
        points, faces = [], []
        for ob in targets:
            _, vs, fs = evaluated(ob, depsgraph, inspect=False)
            offset = len(points)
            points.extend(vs)
            faces.extend(tuple(offset+index for index in face) for face in fs)
        tree = BVHTree.FromPolygons(points, faces, all_triangles=True, epsilon=0.)
        details = {}
        for ob in parts:
            _, vs, fs = evaluated(ob, depsgraph, inspect=False)
            armor_tree = BVHTree.FromPolygons(vs, fs, all_triangles=True, epsilon=0.)
            overlaps = tree.overlap(armor_tree)
            distances = [tree.find_nearest(point)[3] for point in vs[::max(1, math.ceil(len(vs)/128))]]
            details[ob.name] = {'triangle_intersections': len(overlaps),
                'attachment_junction': is_attachment(ob.name), 'examples': [list(pair) for pair in overlaps[:5]],
                'sampled_vertices': len(distances),
                'minimum_unsigned_sample_clearance_mm': min(distances)*1000}
        observations[label] = details
    return observations


def main():
    save_report()
    source = ART / 'Sode01.blend'
    check('authoritative Blender source exists', source.is_file(), str(source.relative_to(ROOT)))
    if not source.is_file():
        raise RuntimeError('Missing authoritative Sode01.blend (expected initial RED before asset construction)')
    bpy.ops.wm.open_mainfile(filepath=str(source))
    REPORT['source'] = {'file': str(source.relative_to(ROOT)),
        'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'blender_version': bpy.app.version_string}
    scene = bpy.context.scene
    check('source collections exist', all(name in bpy.data.collections for name in (SOURCE, FIT, RUNTIME, STUDIO)))
    check('source metre units', scene.unit_settings.system == 'METRIC' and abs(scene.unit_settings.scale_length-1) < 1e-6)
    rig, body, helmet = [bpy.data.objects[name] for name in ('root', 'Manny_Review', 'Kabuto_Review')]
    do_parts = [ob for ob in bpy.data.collections[FIT].all_objects if ob.type == 'MESH' and ob.name.startswith('Do_Review')]
    check('preserved Dō review fixture present', bool(do_parts), [ob.name for ob in do_parts])
    components = source_parts()
    runtime_names = [f'SK_Sode_{side}_01_LOD{level}' for side in SIDES for level in range(3)]
    missing_runtime = [name for name in runtime_names if name not in bpy.data.objects]
    check('generated separate skeletal runtime LODs exist', not missing_runtime, missing_runtime)
    if missing_runtime:
        raise RuntimeError('Missing generated runtime exports: ' + ', '.join(missing_runtime))
    runtime = [bpy.data.objects[name] for name in runtime_names]
    check('two modular anatomical source pieces', all(len(source_parts(side)) >= 5 for side in SIDES),
        {side: [ob.name for ob in source_parts(side)] for side in SIDES})
    if rig.animation_data:
        rig.animation_data.action = None
        rig.animation_data.use_nla = False
    rig.matrix_basis = Matrix.Diagonal((.01, .01, .01, 1.))
    rig.data.pose_position = 'REST'
    for ob in components + runtime + [rig, body, helmet] + do_parts:
        ob.hide_set(False)
    bpy.context.view_layer.update()
    native_reference(body, rig)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    REPORT['components'], REPORT['runtime_lods'], REPORT['weights'] = {}, {}, {}
    all_info = {}
    for ob in components + runtime:
        info, _, _ = evaluated(ob, depsgraph)
        all_info[ob.name] = info
        (REPORT['components'] if ob in components else REPORT['runtime_lods'])[ob.name] = info
        REPORT['weights'][ob.name] = weights(ob, rig)
    reject_fields = ('nonmanifold_edges', 'inconsistent_winding_edges', 'negative_volume_islands',
        'flat_volume_islands', 'zero_area_triangles', 'duplicate_faces', 'invalid_corner_normals')
    errors = {name: {field: info[field] for field in reject_fields if info[field]}
        for name, info in all_info.items() if not info['finite'] or info['triangles'] <= 0 or any(info[field] for field in reject_fields)}
    check('closed finite outward geometry and valid normals without duplicate or zero-area faces', not errors, errors)
    check('one shared Dō atlas with valid authored UVs', all(info['materials'] == [MATERIAL] and
        info['material_indices'] == [0] and info['uv0_1_valid'] for info in all_info.values()))
    check('normalized weights with at most four native bone influences', all(info['same_rig_modifier'] and
        not info['missing_weights'] and not info['invalid_groups_or_values'] and info['max_influences'] <= 4 and
        info['maximum_weight_sum_error'] <= 1e-5 for info in REPORT['weights'].values()))
    check('sensible non-mirrored object transforms', all(ob.matrix_world.determinant() > 0 and
        ob.location.length < 1e-6 and max(abs(value) for value in ob.rotation_euler) < 1e-6 and
        max(abs(value-1) for value in ob.scale) < 1e-6 for ob in components + runtime))
    REPORT['sides'] = {}
    for side in SIDES:
        infos = [all_info[ob.name] for ob in source_parts(side)]
        lows, highs = [info['bounds_metres'][0] for info in infos], [info['bounds_metres'][1] for info in infos]
        side_bounds = [[min(point[axis] for point in lows) for axis in range(3)],
                       [max(point[axis] for point in highs) for axis in range(3)]]
        bone_x = (rig.matrix_world @ rig.data.bones['upperarm_' + side.lower()].head_local).x
        handed = side_bounds[0][0] > 0 if bone_x > 0 else side_bounds[1][0] < 0
        weights_correct = all(not any(name.endswith('_'+other.lower()) for name in REPORT['weights'][ob.name]['bones_used'])
            for other in SIDES if other != side for ob in source_parts(side))
        counts = [all_info[f'SK_Sode_{side}_01_LOD{level}']['triangles'] for level in range(3)]
        check(side + ' anatomical handedness and same-side bone weights', handed and weights_correct,
            {'upperarm_bone_x_metres': bone_x, 'armor_bounds_metres': side_bounds})
        check(side + ' decreasing runtime LOD triangle counts', counts[0] > counts[1] > counts[2] > 0, counts)
        REPORT['sides'][side] = {'source_triangles': sum(info['triangles'] for info in infos),
            'runtime_lod_triangles': counts, 'bounds_metres': side_bounds,
            'anatomical_assignment': 'left' if side == 'L' else 'right'}
    REPORT['textures'] = {}
    for suffix in ('BaseColor', 'Normal', 'ORM'):
        image = bpy.data.images['T_Do01_' + suffix]
        file = ART.parent / 'Do01/Textures' / (image.name + '.png')
        payload = file.read_bytes()
        REPORT['textures'][suffix] = {'packed': image.packed_file is not None, 'size': list(image.size),
            'shared_file': str(file.relative_to(ROOT)), 'sha256': hashlib.sha256(payload).hexdigest(),
            'png_size': list(struct.unpack('>II', payload[16:24])) if payload[:8] == b'\x89PNG\r\n\x1a\n' else None,
            'color_space': image.colorspace_settings.name}
    check('reused packed and external 2K textures with correct color spaces', all(info['packed'] and
        info['size'] == [2048, 2048] and info['png_size'] == [2048, 2048] and
        info['color_space'] == ('sRGB' if suffix == 'BaseColor' else 'Non-Color')
        for suffix, info in REPORT['textures'].items()))
    REPORT['neutral_intersections'] = intersection_report(components,
        {'body': [body], 'kabuto': [helmet], 'do': do_parts}, depsgraph)
    for target, details in REPORT['neutral_intersections'].items():
        rejected = {name: info for name, info in details.items()
            if info['triangle_intersections'] and not (target == 'do' and info['attachment_junction'])}
        check('neutral armor clearance against ' + target, not rejected, rejected)
    manifest = json.loads((ART / 'asset-manifest.json').read_text())
    files = manifest['export_files']
    expected = [f'{folder}/{prefix}_Sode_{side}_01{suffix}.fbx'
        for folder, prefix in [('Exports', 'SK'), ('Review/Exports', 'SM')]
        for side in SIDES for suffix in ('', '_LOD1', '_LOD2')]
    file_check = {path: path in files and (ART/path).is_file() and
        hashlib.sha256((ART/path).read_bytes()).hexdigest() == files[path]['sha256'] for path in expected}
    check('twelve separate side and LOD exports match manifest hashes', all(file_check.values()), file_check)
    check('manifest matches authoritative source hash', manifest['source_blend_sha256'] == REPORT['source']['sha256'])
    check('export preserved source geometry fixtures rig and saved pose',
        manifest.get('editable_geometry_preserved_during_export') and manifest.get('rig_pose_and_fixtures_preserved_during_export'))
    REPORT['limitations'] = ['Neutral-pose source check; sampled animation, actual rendering and Unreal import are separate evidence.',
        'Surface-triangle intersections do not detect every enclosed volume or establish continuous collision-free movement.',
        'Dō attachment contact is allowed only on the flexible Suspension objects and is recorded explicitly.',
        'Unsigned clearances are vertex samples, not exhaustive minimum separation.',
        'Intentional intersections within lamellar armor construction are not checked as a boolean union.']
    REPORT['validated'] = all(item['passed'] for item in REPORT['checks'].values())
    save_report()
    if not REPORT['validated']:
        raise RuntimeError('Sode source checks failed: ' + '; '.join(name for name, item in REPORT['checks'].items() if not item['passed']))
    print('SODE01_SOURCE_VALIDATED ' + str(OUTPUT), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        REPORT['validated'] = False
        REPORT['error'] = traceback.format_exc()
        save_report()
        raise
