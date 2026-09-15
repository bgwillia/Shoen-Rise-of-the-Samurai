"""Evaluate saved Sode01.blend into separate native-Manny skeletal exports.

Only hidden runtime copies and Sode export files are regenerated. The editable
components, fit fixtures, source weights, reference bones, animation and saved
pose remain authoritative; this never runs the construction script.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sode_common import (ART, ROOT, SOURCE, FIT, RUNTIME, SIDES, MATERIAL, REDUCTIONS,
    common, fbx, source_parts, fit_meshes, preservation_signature, bounds,
    to_unreal_bounds, normalize_reduced_weights, weight_info)


def invalid_evaluated_normals(ob):
    """Inspect the actual modifier result, not only cached source mesh normals."""
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = ob.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        return [(index, mesh.loops[index].vertex_index) for index, normal in enumerate(mesh.corner_normals)
                if not all(math.isfinite(value) for value in normal.vector) or abs(normal.vector.length-1) > .001]
    finally:
        evaluated.to_mesh_clear()


def orient_reduced_islands(ob):
    """Keep each closed reduced island outward, including tiny ornaments.

    Collapse can invert a small closed island without making it non-manifold.
    The shared flat-island cleanup removes zero volume but deliberately keeps
    either volume sign. Reverse only complete inward islands on this generated
    mesh, preserving positions, UV corner data, weights and closed topology.
    """
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    pending = set(bm.verts)
    ordered = iter(bm.verts)
    flipped, islands = [], 0
    try:
        while pending:
            first = next(vertex for vertex in ordered if vertex in pending)
            pending.remove(first)
            group, stack = {first}, [first]
            while stack:
                vertex = stack.pop()
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other in pending:
                        pending.remove(other)
                        group.add(other)
                        stack.append(other)
            faces = sorted({face for vertex in group for face in vertex.link_faces}, key=lambda face: face.index)
            edges = {edge for vertex in group for edge in vertex.link_edges}
            if not faces or any(not edge.is_manifold or not edge.is_contiguous for edge in edges):
                raise RuntimeError('Generated reduced island is not closed with consistent winding: ' + ob.name)
            islands += 1
            # Python float arithmetic and local centering avoid float32 cross
            # products and reduce cancellation in small ornament tetrahedra.
            origin = tuple(float(value) for value in first.co)
            contributions = []
            for face in faces:
                points = [tuple(float(vertex.co[axis])-origin[axis] for axis in range(3)) for vertex in face.verts]
                a = points[0]
                for index in range(1, len(points)-1):
                    b, c = points[index], points[index+1]
                    contributions.append((a[0]*(b[1]*c[2]-b[2]*c[1]) +
                        a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0]))/6)
            volume = math.fsum(contributions)
            if not math.isfinite(volume) or volume == 0:
                raise RuntimeError('Generated island has invalid or flat signed volume: ' + ob.name)
            if volume < 0:
                flipped.append({'vertices': len(group), 'faces': len(faces), 'signed_volume_before_metres3': volume})
                bmesh.ops.reverse_faces(bm, faces=faces)
        bm.normal_update()
        bm.to_mesh(ob.data)
        ob.data.update()
    finally:
        bm.free()
    return {'lod': ob.name, 'closed_islands': islands, 'reoriented_islands': flipped,
        'vertices_or_triangles_removed': 0}


def finish_skeletal_normals(ob, level):
    """Rebuild generated normals after native-unit transform and skin binding.

    Very thin reduced islands can have a zero averaged normal only after the
    Armature modifier evaluates. Keep geometry/weights intact and give only the
    incident LOD2 faces flat geometric normals if a refresh cannot resolve it.
    """
    before = invalid_evaluated_normals(ob)
    common.surface_normals(ob)
    remaining = invalid_evaluated_normals(ob)
    flattened = []
    if remaining and level == 2:
        vertices = {vertex for _, vertex in remaining}
        for polygon in ob.data.polygons:
            if any(index in vertices for index in polygon.vertices):
                polygon.use_smooth = False
                flattened.append(polygon.index)
        ob.data.update()
        common.surface_normals(ob)
        remaining = invalid_evaluated_normals(ob)
    if remaining:
        raise RuntimeError('Invalid evaluated skeletal normals after generated-copy repair: ' + ob.name + ' ' + str(remaining))
    record = {'lod': ob.name, 'invalid_corners_before_final_refresh': len(before),
        'flat_shaded_incident_lod2_faces': flattened, 'invalid_corners_after': 0,
        'geometry_and_weights_unchanged': True}
    ob['final_evaluated_normal_repair'] = json.dumps(record)
    return record


def main():
    source = ART / 'Sode01.blend'
    input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    if scene.unit_settings.system != 'METRIC' or abs(scene.unit_settings.scale_length-1) > 1e-6:
        raise RuntimeError('Sode source requires metre units')
    components = source_parts()
    for side in SIDES:
        if len(source_parts(side)) < 5:
            raise RuntimeError('Missing modular source for side ' + side)
    rig = bpy.data.objects['root']
    if rig.type != 'ARMATURE' or rig.parent or 'root' in rig.data.bones:
        raise RuntimeError('Preserve native Manny object root and reference skeleton')
    atlas = bpy.data.materials[MATERIAL]
    if any(list(ob.data.materials) != [atlas] or not ob.data.uv_layers for ob in components):
        raise RuntimeError('All source parts require the shared Dō atlas and authored UVs')
    runtime = bpy.data.collections.get(RUNTIME)
    if runtime is None:
        runtime = bpy.data.collections.new(RUNTIME)
        scene.collection.children.link(runtime)
    preserved = components + fit_meshes()
    if any(ob.name in runtime.objects for ob in [*preserved, rig]):
        raise RuntimeError('Editable source or fit fixtures must not belong to runtime collection')
    bpy.context.view_layer.update()
    before = preservation_signature(preserved, rig)
    animation = rig.animation_data
    action, slot = (animation.action, animation.action_slot) if animation else (None, None)
    use_nla = animation.use_nla if animation else False
    root_basis = rig.matrix_basis.copy()
    pose_bases = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
    pose_position = rig.data.pose_position
    frame, subframe, start, end = scene.frame_current, scene.frame_subframe, scene.frame_start, scene.frame_end
    old_runtime = set(runtime.objects)
    visibility = [(ob, ob.hide_get(), ob.hide_render, ob.select_get())
                  for ob in bpy.context.view_layer.objects if ob not in old_runtime]
    active = bpy.context.view_layer.objects.active
    if active in old_runtime:
        active = None
    results, files = {}, []
    try:
        for ob in list(runtime.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for ob in [rig, *components]:
            ob.hide_set(False)
        if animation:
            animation.action = None
            animation.use_nla = False
        rig.matrix_basis = Matrix.Diagonal((.01, .01, .01, 1.))
        rig.data.pose_position = 'REST'
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for side in SIDES:
            parts = source_parts(side)
            copies = []
            for ob in parts:
                evaluated = ob.evaluated_get(depsgraph)
                data = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
                data.transform(ob.matrix_world)
                copy = bpy.data.objects.new(ob.name + '_runtime', data)
                runtime.objects.link(copy)
                for group in ob.vertex_groups:
                    copy.vertex_groups.new(name=group.name)
                copies.append(copy)
            common.select(copies)
            bpy.ops.object.join()
            base = bpy.context.object
            base.name = f'SK_Sode_{side}_01_LOD0'
            base.data.materials.clear()
            base.data.materials.append(atlas)
            for polygon in base.data.polygons:
                polygon.material_index = 0
            evaluated_count = common.triangles(base)
            evaluated_bounds = bounds(base)
            common.repair_edge_uvs(base)
            lods, normalization, orientation = [base], [], []
            # Copy all levels before reducing any of them. Even LOD0 is a
            # generated mesh; no runtime reduction touches editable components.
            for level in range(1, len(REDUCTIONS)):
                copy = base.copy()
                copy.data = base.data.copy()
                runtime.objects.link(copy)
                copy.name = f'SK_Sode_{side}_01_LOD{level}'
                lods.append(copy)
            for level, (ob, ratio) in enumerate(zip(lods, REDUCTIONS)):
                common.select([ob])
                mod = ob.modifiers.new('Runtime detail reduction from full source', 'DECIMATE')
                mod.ratio = ratio
                bpy.ops.object.modifier_apply(modifier=mod.name)
                common.clean_flat_islands(ob)
                orientation.append(orient_reduced_islands(ob))
                common.repair_edge_uvs(ob)
                common.surface_normals(ob)
                normalization.append(normalize_reduced_weights(ob, rig))
            side_bounds = bounds(base)
            lod_bounds = [bounds(ob) for ob in lods]
            influences, normal_repairs = [], []
            for level, ob in enumerate(lods):
                ob['runtime_reduction_ratio'] = REDUCTIONS[level]
                influences.append(weight_info(ob, rig))
                suffix = '' if level == 0 else f'_LOD{level}'
                static = ob.copy()
                static.data = ob.data.copy()
                runtime.objects.link(static)
                static.name = f'SM_Sode_{side}_01{suffix}'
                static.parent = None
                static.modifiers.clear()
                static.matrix_world = Matrix.Identity(4)
                path = ART / f'Review/Exports/SM_Sode_{side}_01{suffix}.fbx'
                fbx(path, [static])
                files.append(path)
                # Exactly the same rest geometry in native Manny local centimetres.
                ob.data.transform(rig.matrix_world.inverted())
                ob.parent = rig
                ob.matrix_parent_inverse = Matrix.Identity(4)
                ob.matrix_basis = Matrix.Identity(4)
                mod = ob.modifiers.new('Existing SHŌEN skeleton', 'ARMATURE')
                mod.object = rig
                normal_repairs.append(finish_skeletal_normals(ob, level))
                path = ART / f'Exports/SK_Sode_{side}_01{suffix}.fbx'
                fbx(path, [rig, ob])
                files.append(path)
            results[side] = {'asset': f'Sode_{side}_01', 'anatomical_side': 'left' if side == 'L' else 'right',
                'source_components': {ob.name: common.triangles(ob) for ob in parts},
                'source_component_objects': len(parts),
                'source_triangles_before_modifiers': sum(common.triangles(ob) for ob in parts),
                'evaluated_source_triangles': evaluated_count,
                'evaluated_source_bounds_metres': evaluated_bounds,
                'runtime_lod_triangles': [common.triangles(ob) for ob in lods],
                'runtime_lod_source_relative_ratios': [common.triangles(ob)/evaluated_count for ob in lods],
                'runtime_lod_bounds_metres': lod_bounds,
                'runtime_lod_maximum_axis_bound_change_metres': [max(abs(actual[edge][axis]-evaluated_bounds[edge][axis])
                    for edge in range(2) for axis in range(3)) for actual in lod_bounds],
                'runtime_materials': len(lods[0].data.materials),
                'runtime_lod_bone_influences': influences,
                'runtime_lod_normal_repairs': normal_repairs,
                'runtime_lod_weight_normalization': normalization,
                'runtime_lod_orientation_repairs': orientation,
                'armor_bounds_metres': side_bounds, 'bounds_cm': to_unreal_bounds(side_bounds)}
    finally:
        if animation:
            animation.action = action
            if action and slot:
                animation.action_slot = slot
            animation.use_nla = use_nla
        rig.data.pose_position = pose_position
        scene.frame_start, scene.frame_end = start, end
        scene.frame_set(frame, subframe=subframe)
        rig.matrix_basis = root_basis
        for name, basis in pose_bases.items():
            rig.pose.bones[name].matrix_basis = basis
        for ob in runtime.objects:
            ob.hide_render = True
            ob.hide_set(True)
            ob.select_set(False)
        for ob, hidden, render, selected in visibility:
            ob.hide_set(hidden)
            ob.hide_render = render
            ob.select_set(selected)
        bpy.context.view_layer.objects.active = active
        bpy.context.view_layer.update()
    after = preservation_signature(preserved, rig)
    if before != after:
        raise RuntimeError('Export altered source/fit geometry, UVs, weights, rig or pose; source was not saved')
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    manifest_path = ART / 'asset-manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'asset': 'Sode01'}
    manifest.update({'blender_version': bpy.app.version_string, 'sides': results,
        'source_component_objects': len(components),
        'source_triangles_before_modifiers': sum(common.triangles(ob) for ob in components),
        'source_materials': len({mat.name for ob in components for mat in ob.data.materials}),
        'runtime_attachment_controller': 'SodeSuspension pose controller required: same skeleton, rigid panel swing with axial twist filtered and overhead roll/opening; only Suspension braids blend',
        'motion_script_sha256': hashlib.sha256((ART/'Scripts/sode_motion.py').read_bytes()).hexdigest(),
        'runtime_materials_per_piece': 1, 'pair_shared_material': MATERIAL,
        'runtime_lod_triangles_pair': [sum(results[side]['runtime_lod_triangles'][level] for side in SIDES) for level in range(3)],
        'reduction_ratios': list(REDUCTIONS),
        'reduction_basis': 'Each LOD independently reduced from complete evaluated source; LOD0 is also a generated reduced copy',
        'runtime_budget_target_triangles_pair': [73000, 27000, 9000],
        'runtime_budget_note': 'Approximate targets for current 120196-triangle pair; actual reduced topology and silhouette require validation and rendered review',
        'source_bone_count': len(rig.data.bones), 'native_reference_bone_count': len(rig.data.bones)+1,
        'native_root_representation': 'Original Manny root is the Blender armature object; local-cm geometry under .01-scale root',
        'export_operation': 'Saved editable source evaluated in rig REST pose; one combined weighted mesh per side plus two distance LODs',
        'export_root_motion_handling': 'Temporarily disable root action/NLA and use canonical .01 rest transform; restore action, slot, frame, root transform and pose matrices',
        'exported_from_source_sha256': input_hash,
        'source_blend_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'editable_geometry_sha256': after, 'editable_geometry_preserved_during_export': True,
        'rig_pose_and_fixtures_preserved_during_export': True,
        'textures': 'Reuse unchanged Do01/Textures/T_Do01_{BaseColor,Normal,ORM}.png with M_Sode01 finish variant',
        'animation_source': 'Existing native Epic Manny animations; no new skeleton or animation asset exported',
        'export_files': {str(path.relative_to(ART)): {'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in files}})
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    (ART / 'FILES.sha').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' +
        str(path.relative_to(ART)) + '\n' for path in [source, manifest_path, *sorted(files)]))
    print('SODE01_SAVED_SOURCE_EXPORTED ' + json.dumps({'source': str(source),
        'pair_lod_triangles': manifest['runtime_lod_triangles_pair'], 'preserved': True}), flush=True)


if __name__ == '__main__':
    main()
