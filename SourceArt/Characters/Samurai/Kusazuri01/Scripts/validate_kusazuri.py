"""Reopen and inspect Kusazuri source/runtime copies without saving the blend.

Blender --background --factory-startup --python-exit-code 1 --python <this file>.
Animation, Unreal import and rendered performance require separate evidence.
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
from kusazuri_common import (ART, ROOT, SOURCE, FIT, RUNTIME, STUDIO, MATERIAL, TINT,
    ROUND_GROUP, PANEL_BONES, REDUCTIONS, source_parts, fit_meshes, panel_name,
    geometry_hash, rig_hash, preservation_signature, expected_exports, to_unreal_bounds, tint_info)

OUTPUT = ROOT / 'artifacts/kusazuri01/source-validation.json'
REPORT = {'asset': 'Kusazuri01', 'validated': False, 'checks': {},
    'scope': 'Reopened editable source and generated runtime copies; rest geometry, native skeleton, weights and intersections; no rendering claim'}


def check(name, passed, detail=None):
    REPORT['checks'][name] = {'passed': bool(passed), 'detail': detail}


def save_report():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(REPORT, indent=2, allow_nan=False) + '\n')


def topology(mesh, scale):
    bm = bmesh.new()
    try:
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
            volumes.append(volume * scale)
        info.update({'connected_islands': len(volumes),
            'negative_volume_islands': sum(volume < -1e-15 for volume in volumes),
            'flat_volume_islands': sum(abs(volume) <= 1e-15 for volume in volumes)})
        return info
    finally:
        bm.free()


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
        info = topology(mesh, obj.matrix_world.to_3x3().determinant())
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
            'vertex_color': tint_info(mesh),
            'invalid_corner_normals': sum(not all(math.isfinite(value) for value in normal.vector)
                or abs(normal.vector.length-1) > .001 for normal in mesh.corner_normals)})
        return info, points, triangles
    finally:
        obj.to_mesh_clear()


def weights(ob, rig):
    bone_names = {bone.name for bone in rig.data.bones}
    names = {group.index: group.name for group in ob.vertex_groups}
    counts, used, missing, invalid, error = {}, set(), 0, 0, 0.
    wrong_primary = 0
    for vertex in ob.data.vertices:
        active = [(names[group.group], group.weight) for group in vertex.groups
                  if names.get(group.group) in bone_names and group.weight > 1e-7]
        invalid += sum(not math.isfinite(group.weight) or group.weight < 0 or
            (group.weight > 1e-7 and names.get(group.group) not in bone_names and names.get(group.group) != ROUND_GROUP)
            for group in vertex.groups)
        count = len(active)
        counts[str(count)] = counts.get(str(count), 0)+1
        missing += count == 0
        used.update(name for name, _ in active)
        error = max(error, abs(sum(value for _, value in active)-1))
        if ob.name in PANEL_BONES:
            wrong_primary += count != 1 or active[0][0] != PANEL_BONES[ob.name] or abs(active[0][1]-1) > 1e-6
    modifiers = [mod for mod in ob.modifiers if mod.type == 'ARMATURE']
    return {'vertices': len(ob.data.vertices), 'influence_histogram': counts,
        'max_influences': max((int(count) for count in counts), default=0),
        'missing_weights': missing, 'invalid_groups_or_values': invalid,
        'maximum_weight_sum_error': error, 'bones_used': sorted(used),
        'vertices_not_rigid_on_primary_panel_bone': wrong_primary,
        'same_rig_modifier': len(modifiers) == 1 and modifiers[0].object == rig}


def lamellar_counts(ob):
    counts = {bone: 0 for panel, bone in PANEL_BONES.items() if panel != 'Kusazuri_01_Belt'}
    names = {group.index: group.name for group in ob.vertex_groups}
    uv = ob.data.uv_layers.active.data
    for face in ob.data.polygons:
        loops = list(face.loop_indices)
        tile = int(4*sum(uv[index].uv.x for index in loops)/len(loops)) + 4*int(4*sum(uv[index].uv.y for index in loops)/len(loops))
        if tile not in (8, 9, 13, 14):
            continue
        bones = {names[weight.group] for index in face.vertices for weight in ob.data.vertices[index].groups
                 if weight.weight > 1e-7 and names[weight.group] in counts}
        if len(bones) == 1:
            counts[next(iter(bones))] += len(face.vertices)-2
    return counts


def native_reference(body, rig):
    file = ROOT / 'SourceArt/Characters/Mannequins/Manny/Exports/SKM_Manny_Simple.fbx'
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(file), automatic_bone_orientation=False, use_anim=False)
    imported = [ob for ob in bpy.data.objects if ob not in before]
    try:
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
            len(rig.data.bones) == 88 and len(rig.data.bones)+1 == fixture['native_reference_bones'], provenance)
        check('native armature object root is retained', rig.name == 'root' and not rig.parent and 'root' not in rig.data.bones)
    finally:
        for ob in imported:
            bpy.data.objects.remove(ob, do_unlink=True)


def material_references(material):
    """Inspect actual connected surface inputs, including the color-mask source."""
    if not material.use_nodes or not material.node_tree:
        return {'surface_output': False, 'textures': [], 'tint_attributes': []}
    output = next((node for node in material.node_tree.nodes
                   if node.type == 'OUTPUT_MATERIAL' and node.is_active_output), None)
    pending = [link.from_node for link in output.inputs['Surface'].links] if output else []
    visited = set()
    while pending:
        node = pending.pop()
        if node in visited:
            continue
        visited.add(node)
        pending.extend(link.from_node for socket in node.inputs for link in socket.links)
    image_nodes = [node for node in visited if node.type == 'TEX_IMAGE']
    return {'surface_output': bool(output and output.inputs['Surface'].is_linked),
        'textures': sorted(({'node': node.name, 'image': node.image.name if node.image else None,
                            'is_shared_image': bool(node.image and bpy.data.images.get(node.image.name) == node.image)}
                            for node in image_nodes), key=lambda item: item['node']),
        'tint_attributes': sorted({node.layer_name for node in visited if node.type == 'VERTEX_COLOR'} |
                                  {node.attribute_name for node in visited if node.type == 'ATTRIBUTE'})}


def intersection_report(parts, fixtures, depsgraph):
    """Bound report size; all triangle tests still run, only examples are sampled."""
    armor = {ob.name: evaluated(ob, depsgraph, inspect=False)[1:] for ob in parts}
    observations = {}
    for label, targets in fixtures.items():
        points, faces = [], []
        for ob in targets:
            _, vs, fs = evaluated(ob, depsgraph, inspect=False)
            offset = len(points)
            points.extend(vs)
            faces.extend(tuple(offset+index for index in face) for face in fs)
        if not points or not faces:
            raise RuntimeError('Empty clearance fixture: ' + label)
        tree = BVHTree.FromPolygons(points, faces, all_triangles=True, epsilon=0.)
        details = {}
        for ob in parts:
            vs, fs = armor[ob.name]
            armor_tree = BVHTree.FromPolygons(vs, fs, all_triangles=True, epsilon=0.)
            overlaps = tree.overlap(armor_tree)
            # Triangle AABB overlap bounds conservatively enclose the actual
            # intersection. Only contact confined to the authored attachment
            # band is eligible; lower-shell penetrations always remain errors.
            contact_z = [(max(min(points[i].z for i in faces[a]), min(vs[i].z for i in fs[b])),
                          min(max(points[i].z for i in faces[a]), max(vs[i].z for i in fs[b])))
                         for a, b in overlaps]
            outside_band = sum(low < .9895 or high > 1.030 for low, high in contact_z)
            attachment = (ob.name in ('Kusazuri_01_Belt', 'Kusazuri_01_Lacing') or
                          ob.name.endswith('_Trim') or ob.name.startswith('SK_Kusazuri01_LOD'))
            contact_vertices = {index for _, triangle in overlaps for index in fs[triangle]}
            depths = []
            if label == 'do':
                for index in contact_vertices:
                    point = vs[index]
                    nearest, normal, _, _ = tree.find_nearest(point)
                    depths.append(max(0., -(point-nearest).dot(normal)*1000))
            depth = max(depths, default=0.)
            distances = [tree.find_nearest(point)[3] for point in vs[::max(1, math.ceil(len(vs)/128))]]
            details[ob.name] = {'triangle_intersections': len(overlaps),
                'attachment_band_metres': [.9895, 1.030],
                'triangle_intersections_outside_attachment_band': outside_band,
                'intersection_z_bounds_metres': [min(low for low, _ in contact_z), max(high for _, high in contact_z)] if contact_z else None,
                'maximum_projected_contact_depth_mm': depth if label == 'do' else None,
                'contact_depth_method': 'nearest-triangle normal projection at every intersecting armor triangle vertex; approximate local depth',
                'allowed_do_attachment_contact': label == 'do' and attachment and bool(overlaps) and outside_band == 0 and depth <= 3.,
                'examples': [list(pair) for pair in overlaps[:5]], 'sampled_vertices': len(distances),
                'minimum_unsigned_sample_clearance_mm': min(distances)*1000 if distances else None}
        observations[label] = details
    return observations


def main():
    save_report()
    source = ART / 'Kusazuri01.blend'
    check('authoritative Blender source exists', source.is_file(), str(source.relative_to(ROOT)))
    if not source.is_file():
        raise RuntimeError('Missing authoritative Kusazuri01.blend')
    bpy.ops.wm.open_mainfile(filepath=str(source))
    REPORT['source'] = {'file': str(source.relative_to(ROOT)),
        'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'blender_version': bpy.app.version_string}
    scene = bpy.context.scene
    check('source collections exist', all(name in bpy.data.collections for name in (SOURCE, FIT, RUNTIME, STUDIO)))
    check('source metre units', scene.unit_settings.system == 'METRIC' and abs(scene.unit_settings.scale_length-1) < 1e-6)
    rig, body, helmet = [bpy.data.objects[name] for name in ('root', 'Manny_Review', 'Kabuto_Review')]
    fixtures = fit_meshes()
    do_parts = [ob for ob in fixtures if ob.name.startswith('Do_Review')]
    sode_parts = [ob for ob in fixtures if ob.name.startswith('Sode_Review')]
    check('preserved body and current upper armor fixtures present', body in fixtures and helmet in fixtures and
        bool(do_parts) and bool(sode_parts), [ob.name for ob in fixtures])
    components = source_parts()
    check('seven separate primary leaves and belt', set(PANEL_BONES).issubset(ob.name for ob in components), list(PANEL_BONES))
    check('source contains only tagged Kusazuri construction', bool(components) and
        all(ob.get('asset') == 'Kusazuri01' and panel_name(ob.name) for ob in components), [ob.name for ob in components])
    runtime_names = [f'SK_Kusazuri01_LOD{level}' for level in range(3)]
    static_names = ['SM_Kusazuri01' + (f'_LOD{level}' if level else '') for level in range(3)]
    missing = [name for name in runtime_names + static_names if name not in bpy.data.objects]
    check('three skeletal and three static runtime copies exist', not missing, missing)
    if missing:
        raise RuntimeError('Missing generated runtime objects: ' + ', '.join(missing))
    runtime = [bpy.data.objects[name] for name in runtime_names]
    statics = [bpy.data.objects[name] for name in static_names]
    check('runtime collection contains generated copies only',
        set(bpy.data.collections[RUNTIME].all_objects) == set(runtime + statics))
    manifest = json.loads((ART / 'asset-manifest.json').read_text())
    check('saved editable geometry and pose match preservation signature',
        manifest.get('editable_geometry_sha256') == preservation_signature(components + fixtures, rig))
    if rig.animation_data:
        rig.animation_data.action = None
        rig.animation_data.use_nla = False
    rig.matrix_basis = Matrix.Diagonal((.01, .01, .01, 1.))
    rig.data.pose_position = 'REST'
    for ob in components + runtime + statics + [rig] + fixtures:
        ob.hide_set(False)
    bpy.context.view_layer.update()
    native_reference(body, rig)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    REPORT['components'], REPORT['runtime_lods'], REPORT['static_lods'], REPORT['weights'] = {}, {}, {}, {}
    all_info = {}
    all_geometry = {}
    for ob in components + runtime + statics:
        info, points, triangles = evaluated(ob, depsgraph)
        all_info[ob.name] = info
        all_geometry[ob.name] = (points, triangles)
        destination = 'components' if ob in components else 'runtime_lods' if ob in runtime else 'static_lods'
        REPORT[destination][ob.name] = info
        if ob not in statics:
            REPORT['weights'][ob.name] = weights(ob, rig)
    reject_fields = ('nonmanifold_edges', 'inconsistent_winding_edges', 'negative_volume_islands',
        'flat_volume_islands', 'zero_area_triangles', 'duplicate_faces', 'invalid_corner_normals')
    errors = {name: {field: info[field] for field in reject_fields if info[field]}
        for name, info in all_info.items() if not info['finite'] or info['triangles'] <= 0 or any(info[field] for field in reject_fields)}
    check('closed finite outward geometry and valid normals without duplicate or zero-area faces', not errors, errors)
    check('one Kusazuri material using shared Dō atlas with valid authored UVs', all(info['materials'] == [MATERIAL] and
        info['material_indices'] == [0] and info['uv0_1_valid'] for info in all_info.values()))
    source_tints = {ob.name: tint_info(ob.data) for ob in components}
    check('source ArmorTint is black only on the obi and white on other components', all(info['valid'] and
        info['black_corners' if name == 'Kusazuri_01_Lacing' else 'white_corners'] == info['corners']
        for name, info in source_tints.items()), source_tints)
    check('all evaluated meshes preserve the single binary opaque ArmorTint channel', all(
        info['vertex_color']['valid'] for info in all_info.values()))
    check('all runtime LODs retain both obi and ordinary armor tint regions', all(
        all_info[ob.name]['vertex_color']['black_triangles'] > 0 and
        all_info[ob.name]['vertex_color']['white_triangles'] > 0 for ob in runtime + statics))
    check('LOD0 preserves source tint triangle assignments', all(
        all_info[runtime[0].name]['vertex_color'][key] == sum(info[key] for info in source_tints.values())
        for key in ('black_triangles', 'white_triangles')))
    color_manifest = manifest.get('vertex_color', {})
    check('manifest records ArmorTint encoding and current mask counts',
        color_manifest.get('name') == TINT and color_manifest.get('domain') == 'CORNER' and
        color_manifest.get('data_type') == 'FLOAT_COLOR' and color_manifest.get('fbx_encoding') == 'LINEAR' and
        color_manifest.get('export_channels') == 1 and color_manifest.get('mask_channel') == 'R' and
        color_manifest.get('source_components') == source_tints and
        color_manifest.get('runtime_lods') == [tint_info(ob.data) for ob in runtime])
    check('normalized weights with at most two native bone influences', all(info['same_rig_modifier'] and
        not info['missing_weights'] and not info['invalid_groups_or_values'] and info['max_influences'] <= 2 and
        info['maximum_weight_sum_error'] <= 1e-5 and set(info['bones_used']).issubset(PANEL_BONES.values())
        for info in REPORT['weights'].values()))
    check('primary leaves and belt remain rigid on assigned existing bone', all(
        not REPORT['weights'][name]['vertices_not_rigid_on_primary_panel_bone'] for name in PANEL_BONES))
    check('all runtime LODs retain all seven panel regions and the belt', all(
        set(REPORT['weights'][ob.name]['bones_used']) == set(PANEL_BONES.values()) for ob in runtime),
        {ob.name: REPORT['weights'][ob.name]['bones_used'] for ob in runtime})
    lamellae = {ob.name: lamellar_counts(ob) for ob in runtime}
    REPORT['runtime_lamellar_triangles_by_bone'] = lamellae
    check('all runtime LODs retain actual lacquer shell faces for every panel', all(
        counts[bone] >= 2*all_info[panel]['connected_islands']
        for counts in lamellae.values() for panel, bone in PANEL_BONES.items() if panel != 'Kusazuri_01_Belt'), lamellae)
    check('static copies are unparented and unskinned', all(ob.parent is None and not ob.modifiers for ob in statics))
    check('sensible non-mirrored object transforms', all(ob.matrix_world.determinant() > 0 and
        ob.location.length < 1e-6 and max(abs(value) for value in ob.rotation_euler) < 1e-6 and
        max(abs(value-1) for value in ob.scale) < 1e-6 for ob in components + runtime + statics))
    counts = [all_info[ob.name]['triangles'] for ob in runtime]
    check('decreasing runtime LOD triangle counts', counts[0] > counts[1] > counts[2] > 0, counts)
    check('runtime counts and reduction ratios match manifest', counts == manifest.get('runtime_lod_triangles') and
        list(REDUCTIONS) == manifest.get('reduction_ratios'))
    correspondence = {}
    for skeletal, static in zip(runtime, statics):
        sv, sf = all_geometry[skeletal.name]
        tv, tf = all_geometry[static.name]
        same = len(sv) == len(tv) and sf == tf
        error = max(((a-b).length for a, b in zip(sv, tv)), default=0.) if same else None
        correspondence[skeletal.name] = {'same_topology': same, 'maximum_world_vertex_error_metres': error,
            'same_corner_tint_colors': all_info[skeletal.name]['vertex_color'] == all_info[static.name]['vertex_color']}
    check('skeletal and static LOD geometry agree in native rest pose', all(info['same_topology'] and
        info['maximum_world_vertex_error_metres'] <= 1e-6 for info in correspondence.values()), correspondence)
    check('skeletal and static copies use identical corner tint masks', all(
        info['same_corner_tint_colors'] for info in correspondence.values()))
    measured_bounds = to_unreal_bounds(all_info[runtime[0].name]['bounds_metres'])
    check('manifest bounds describe rest LOD0', all(key in manifest.get('bounds_cm', {}) and
        len(manifest['bounds_cm'][key]) == 3 and max(abs(a-b) for a, b in zip(manifest['bounds_cm'][key], values)) <= 1e-4
        for key, values in measured_bounds.items()))
    check('LOD0 preserves evaluated source triangle count', counts[0] == sum(all_info[ob.name]['triangles'] for ob in components)
        == manifest.get('evaluated_source_triangles'))
    REPORT['textures'] = {}
    for suffix in ('BaseColor', 'Normal', 'ORM'):
        image = bpy.data.images['T_Do01_' + suffix]
        file = ART.parent / 'Do01/Textures' / (image.name + '.png')
        payload = file.read_bytes()
        REPORT['textures'][suffix] = {'packed': image.packed_file is not None, 'size': list(image.size),
            'shared_file': str(file.relative_to(ROOT)), 'sha256': hashlib.sha256(payload).hexdigest(),
            'packed_matches_external': image.packed_file is not None and bytes(image.packed_file.data) == payload,
            'png_size': list(struct.unpack('>II', payload[16:24])) if payload[:8] == b'\x89PNG\r\n\x1a\n' else None,
            'color_space': image.colorspace_settings.name}
    check('reused packed and external 2K textures with correct color spaces', all(info['packed'] and
        info['packed_matches_external'] and info['size'] == [2048, 2048] and info['png_size'] == [2048, 2048] and
        info['color_space'] == ('sRGB' if suffix == 'BaseColor' else 'Non-Color')
        for suffix, info in REPORT['textures'].items()))
    references = material_references(bpy.data.materials[MATERIAL])
    REPORT['material_references'] = references
    expected_images = {'T_Do01_' + suffix for suffix in ('BaseColor', 'Normal', 'ORM')}
    check('material surface actually uses unchanged shared texture images', references['surface_output'] and
        {info['image'] for info in references['textures']} == expected_images and
        all(info['is_shared_image'] for info in references['textures']), references)
    check('material surface actually reads ArmorTint', TINT in references['tint_attributes'])
    targets = {'body': [body], 'kabuto': [helmet], 'do': do_parts, 'sode': sode_parts}
    REPORT['neutral_intersections'] = intersection_report(components, targets, depsgraph)
    REPORT['runtime_neutral_intersections'] = intersection_report(runtime, targets, depsgraph)
    for category in ('neutral_intersections', 'runtime_neutral_intersections'):
        for target, details in REPORT[category].items():
            rejected = {name: info for name, info in details.items()
                        if info['triangle_intersections'] and not info['allowed_do_attachment_contact']}
            check(category + ' clearance against ' + target, not rejected, rejected)
    files = manifest.get('export_files', {})
    file_check = {path: path in files and (ART/path).is_file() and
        (ART/path).stat().st_size == files[path]['bytes'] and
        hashlib.sha256((ART/path).read_bytes()).hexdigest() == files[path]['sha256'] for path in expected_exports()}
    check('six separate skeletal static and LOD exports match manifest hashes', all(file_check.values()), file_check)
    check('manifest matches authoritative source hash', manifest.get('source_blend_sha256') == REPORT['source']['sha256'])
    check('export preserved source geometry fixtures rig and saved pose',
        manifest.get('editable_geometry_preserved_during_export') and manifest.get('rig_pose_and_fixtures_preserved_during_export'))
    REPORT['limitations'] = ['Rest-pose source check; sampled animation, actual rendering and Unreal import are separate evidence.',
        'Surface-triangle intersections do not detect every enclosed volume or establish continuous collision-free movement.',
        'Only Dō contacts on belt, waist lacing or upper trim confined to z .9895–1.030m with projected local depth ≤3mm are allowed as intended attachment overlap; source shell contacts remain errors. Runtime contacts use the same spatial band and depth bound.',
        'Unsigned clearances sample at most 128 vertices per object and are not exhaustive minimum separation.',
        'Intentional internal contacts among armor construction parts are not tested as a boolean union.']
    REPORT['validated'] = all(item['passed'] for item in REPORT['checks'].values())
    save_report()
    if not REPORT['validated']:
        raise RuntimeError('Kusazuri source checks failed: ' + '; '.join(name for name, item in REPORT['checks'].items() if not item['passed']))
    print('KUSAZURI01_SOURCE_VALIDATED ' + str(OUTPUT), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        REPORT['validated'] = False
        REPORT['error'] = traceback.format_exc()
        save_report()
        raise
