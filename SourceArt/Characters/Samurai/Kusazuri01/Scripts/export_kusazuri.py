"""Export authoritative Kusazuri01.blend in rest pose; regenerate runtime only.

Source construction scripts are never called. Editable components, fit fixtures,
native bones, UVs, skin weights, action, NLA setting and saved pose are preserved.
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
from kusazuri_common import (ART, SOURCE, FIT, RUNTIME, MATERIAL, TINT, REDUCTIONS, PANEL_BONES,
    common, fbx, source_parts, fit_meshes, panel_name, preservation_signature, bounds,
    to_unreal_bounds, normalize_reduced_weights, weight_info, tint_info)


def transform_channels(owner):
    # Matrix decomposition can round an artist's nonzero pose. Preserve the
    # actual transform channels so a saved custom pose survives exact readback.
    return {name: tuple(getattr(owner, name)) for name in
            ('location', 'rotation_euler', 'rotation_quaternion', 'rotation_axis_angle', 'scale')}


def restore_channels(owner, channels):
    for name, values in channels.items():
        setattr(owner, name, values)


def evaluated_copy(ob, collection, depsgraph):
    evaluated = ob.evaluated_get(depsgraph)
    data = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
    data.transform(evaluated.matrix_world)
    copy = bpy.data.objects.new(ob.name + '_runtime', data)
    collection.objects.link(copy)
    for group in ob.vertex_groups:
        copy.vertex_groups.new(name=group.name)
    return copy


def retain_hem(ob):
    """Retain the complete lower reinforcement islands identified by tile 10."""
    bm = bmesh.new()
    try:
        bm.from_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        pending, remove, kept = set(bm.verts), [], 0
        while pending:
            first = pending.pop()
            island, stack = {first}, [first]
            while stack:
                vertex = stack.pop()
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other in pending:
                        pending.remove(other); island.add(other); stack.append(other)
            faces = {face for vertex in island for face in vertex.link_faces}
            tiles = {int(loop[uv].uv.x*4) + 4*int(loop[uv].uv.y*4) for face in faces for loop in face.loops}
            if 10 in tiles:
                kept += 1
            else:
                remove.extend(island)
        if kept == 0:
            raise RuntimeError('LOD2 could not identify the authored lower hem: ' + ob.name)
        bmesh.ops.delete(bm, geom=remove, context='VERTS')
        bm.to_mesh(ob.data)
        return kept
    finally:
        bm.free()


def mesh_edges(ob):
    bm = bmesh.new()
    try:
        bm.from_mesh(ob.data)
        pending, islands = set(bm.verts), 0
        while pending:
            islands += 1
            stack = [pending.pop()]
            while stack:
                vertex = stack.pop()
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other in pending:
                        pending.remove(other); stack.append(other)
        return {'nonmanifold_edges': sum(not edge.is_manifold for edge in bm.edges),
                'boundary_edges': sum(edge.is_boundary for edge in bm.edges),
                'wire_edges': sum(edge.is_wire for edge in bm.edges), 'connected_islands': islands}
    finally:
        bm.free()


def selective_lod2(components, runtime, depsgraph, atlas, rig):
    copies, records = [], {}
    for source in components:
        if source.name.endswith('_Lacing') and source.name != 'Kusazuri_01_Lacing':
            records[source.name] = {'policy': 'omit repeated physical stitches; detailed atlas remains on every shell', 'runtime_triangles': 0}
            continue
        ob = evaluated_copy(source, runtime, depsgraph)
        before = common.triangles(ob)
        record = {'evaluated_source_triangles': before}
        if source.name.endswith('_Trim'):
            record['retained_hem_islands'] = retain_hem(ob)
        record['protected_input_topology'] = mesh_edges(ob)
        common.select([ob])
        mod = ob.modifiers.new('Protected distant armor reduction', 'DECIMATE')
        if source.name == 'Kusazuri_01_Lacing':
            mod.ratio = .20
            mod.use_collapse_triangulate = True
            record['policy'] = 'obi only: collapse ratio .20 with collapse-time triangulation; preserve indigo corner mask'
        else:
            # Dissolving shallow face angles preserves each thin closed plate;
            # global collapse had flattened these shells into deleted islands.
            mod.decimate_type = 'DISSOLVE'
            angle = 25 if source.name in PANEL_BONES and source.name != 'Kusazuri_01_Belt' else 8
            mod.angle_limit = math.radians(angle)
            mod.delimit = {'UV'}
            record['policy'] = f'dissolve face angles below {angle} degrees; preserve closed shell/lining/belt or selected hem'
        bpy.ops.object.modifier_apply(modifier=mod.name)
        record['edges_after_reduction'] = mesh_edges(ob)
        common.clean_flat_islands(ob)
        record['edges_after_flat_island_cleanup'] = mesh_edges(ob)
        common.repair_edge_uvs(ob)
        record['edges_after_uv_triangulation'] = mesh_edges(ob)
        common.surface_normals(ob)
        record['edges_after_triangulation'] = mesh_edges(ob)
        if record['edges_after_triangulation']['nonmanifold_edges']:
            raise RuntimeError('Selective LOD2 introduced nonmanifold geometry: ' + source.name)
        if source.name != 'Kusazuri_01_Lacing' and record['protected_input_topology']['connected_islands'] != record['edges_after_triangulation']['connected_islands']:
            raise RuntimeError('Selective LOD2 lost a protected closed island: ' + source.name)
        record['runtime_triangles'] = common.triangles(ob)
        if record['runtime_triangles'] <= 0:
            raise RuntimeError('Selective LOD2 lost protected component: ' + source.name)
        copies.append(ob)
        records[source.name] = record
    common.select(copies)
    bpy.ops.object.join()
    lod = bpy.context.object
    lod.name = 'SK_Kusazuri01_LOD2'
    lod.data.materials.clear(); lod.data.materials.append(atlas)
    for polygon in lod.data.polygons:
        polygon.material_index = 0
    common.surface_normals(lod)
    return lod, records, normalize_reduced_weights(lod, rig)


def invalid_evaluated_normals(ob):
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = ob.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        return [(index, mesh.loops[index].vertex_index) for index, normal in enumerate(mesh.corner_normals)
                if not all(math.isfinite(value) for value in normal.vector) or abs(normal.vector.length-1) > .001]
    finally:
        evaluated.to_mesh_clear()


def finish_skeletal_normals(ob, level):
    """Refresh normals after cm conversion; flatten only invalid LOD2 corners."""
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
        raise RuntimeError('Invalid generated skeletal normals: ' + ob.name + ' ' + str(remaining[:12]))
    record = {'lod': ob.name, 'invalid_corners_before_final_refresh': len(before),
        'flat_shaded_incident_lod2_face_count': len(flattened), 'face_examples': flattened[:12],
        'invalid_corners_after': 0, 'geometry_and_weights_unchanged': True}
    ob['final_evaluated_normal_repair'] = json.dumps(record)
    return record


def main():
    source = ART / 'Kusazuri01.blend'
    input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    if scene.unit_settings.system != 'METRIC' or abs(scene.unit_settings.scale_length-1) > 1e-6:
        raise RuntimeError('Kusazuri source requires metre units')
    components = source_parts()
    if not set(PANEL_BONES).issubset(ob.name for ob in components):
        raise RuntimeError('Missing required separate Kusazuri leaves or belt')
    if any(ob.get('asset') != 'Kusazuri01' or panel_name(ob.name) is None for ob in components):
        raise RuntimeError('Source collection must contain only tagged Kusazuri components')
    rig = bpy.data.objects['root']
    if rig.type != 'ARMATURE' or rig.parent or 'root' in rig.data.bones or len(rig.data.bones) != 88:
        raise RuntimeError('Preserve native Manny object root and 88 reference bones')
    atlas = bpy.data.materials[MATERIAL]
    if any(list(ob.data.materials) != [atlas] or not ob.data.uv_layers for ob in components):
        raise RuntimeError('All source parts require the shared armor material and authored UVs')
    source_tints = {ob.name: tint_info(ob.data) for ob in components}
    if any(not info['valid'] or info['black_corners' if name == 'Kusazuri_01_Lacing' else 'white_corners'] != info['corners']
           for name, info in source_tints.items()):
        raise RuntimeError('Source ArmorTint must be black on the global obi and white on all other components')
    runtime = bpy.data.collections.get(RUNTIME)
    if runtime is None:
        runtime = bpy.data.collections.new(RUNTIME)
        scene.collection.children.link(runtime)
    preserved = components + fit_meshes()
    if any(ob.name in runtime.all_objects for ob in [*preserved, rig]):
        raise RuntimeError('Editable source or fit fixtures must not belong to runtime collection')
    bpy.context.view_layer.update()
    before = preservation_signature(preserved, rig)
    animation = rig.animation_data
    action, slot = (animation.action, animation.action_slot) if animation else (None, None)
    use_nla = animation.use_nla if animation else False
    root_channels = transform_channels(rig)
    pose_channels = {bone.name: transform_channels(bone) for bone in rig.pose.bones}
    pose_position = rig.data.pose_position
    frame, subframe, start, end = scene.frame_current, scene.frame_subframe, scene.frame_start, scene.frame_end
    old_runtime = set(runtime.all_objects)
    visibility = [(ob, ob.hide_get(), ob.hide_render, ob.select_get())
                  for ob in bpy.context.view_layer.objects if ob not in old_runtime]
    active = bpy.context.view_layer.objects.active
    if active in old_runtime:
        active = None
    files, lods, normalization, influences, normal_repairs, runtime_tints = [], [], [], [], [], []
    try:
        for ob in list(runtime.all_objects):
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
        copies = []
        for ob in components:
            copies.append(evaluated_copy(ob, runtime, depsgraph))
        common.select(copies)
        bpy.ops.object.join()
        base = bpy.context.object
        base.name = 'SK_Kusazuri01_LOD0'
        base.data.materials.clear()
        base.data.materials.append(atlas)
        for polygon in base.data.polygons:
            polygon.material_index = 0
        evaluated_count = common.triangles(base)
        common.repair_edge_uvs(base)
        common.surface_normals(base)
        lods.append(base)
        for level, ratio in enumerate(REDUCTIONS[1:2], 1):
            copy = base.copy()
            copy.data = base.data.copy()
            runtime.objects.link(copy)
            copy.name = f'SK_Kusazuri01_LOD{level}'
            common.select([copy])
            mod = copy.modifiers.new('Distance reduction', 'DECIMATE')
            mod.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=mod.name)
            common.clean_flat_islands(copy)
            common.repair_edge_uvs(copy)
            common.surface_normals(copy)
            normalization.append(normalize_reduced_weights(copy, rig))
            lods.append(copy)
        distant, lod2_policy, distant_weights = selective_lod2(components, runtime, depsgraph, atlas, rig)
        lods.append(distant); normalization.append(distant_weights)
        armor_bounds = bounds(base)
        for level, ob in enumerate(lods):
            tint = tint_info(ob.data)
            if not tint['valid'] or not tint['black_triangles'] or not tint['white_triangles']:
                raise RuntimeError('Generated LOD lost or mixed the ArmorTint mask: ' + ob.name)
            if level == 0 and any(tint[key] != sum(info[key] for info in source_tints.values())
                                  for key in ('black_triangles', 'white_triangles')):
                raise RuntimeError('LOD0 changed the source ArmorTint triangle assignments')
            ob['asset'] = 'Kusazuri01'
            ob['runtime_reduction_ratio'] = REDUCTIONS[level] if REDUCTIONS[level] is not None else common.triangles(ob)/evaluated_count
            influence = weight_info(ob, rig)
            if influence['max'] > 2:
                raise RuntimeError('Kusazuri requires at most two influences per vertex: ' + ob.name)
            influences.append(influence)
            suffix = '' if level == 0 else f'_LOD{level}'
            static = ob.copy()
            static.data = ob.data.copy()
            runtime.objects.link(static)
            static.name = f'SM_Kusazuri01{suffix}'
            static.parent = None
            static.modifiers.clear()
            static.matrix_world = Matrix.Identity(4)
            path = ART / f'Review/Exports/SM_Kusazuri01{suffix}.fbx'
            fbx(path, [static])
            files.append(path)
            # Preserve the native Manny representation: cm mesh beneath .01 root.
            ob.data.transform(rig.matrix_world.inverted())
            ob.parent = rig
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_basis = Matrix.Identity(4)
            mod = ob.modifiers.new('Existing SHŌEN skeleton', 'ARMATURE')
            mod.object = rig
            normal_repairs.append(finish_skeletal_normals(ob, level))
            final_tint = tint_info(ob.data)
            if not final_tint['valid'] or any(final_tint[key] != tint[key] for key in ('black_triangles', 'white_triangles')):
                raise RuntimeError('Native-unit normal refresh changed ArmorTint: ' + ob.name)
            runtime_tints.append(final_tint)
            path = ART / f'Exports/SK_Kusazuri01{suffix}.fbx'
            fbx(path, [rig, ob])
            files.append(path)
    finally:
        if animation:
            animation.action = action
            if action and slot:
                animation.action_slot = slot
            animation.use_nla = use_nla
        rig.data.pose_position = pose_position
        scene.frame_start, scene.frame_end = start, end
        scene.frame_set(frame, subframe=subframe)
        restore_channels(rig, root_channels)
        for name, channels in pose_channels.items():
            restore_channels(rig.pose.bones[name], channels)
        for ob in runtime.all_objects:
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
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'asset': 'Kusazuri01'}
    manifest.update({'asset': 'Kusazuri01', 'blender_version': bpy.app.version_string,
        'source_components': {ob.name: common.triangles(ob) for ob in components},
        'source_component_objects': len(components),
        'source_triangles_before_modifiers': sum(common.triangles(ob) for ob in components),
        'evaluated_source_triangles': evaluated_count, 'exported_triangles': common.triangles(lods[0]),
        'source_materials': len({mat.name for ob in components for mat in ob.data.materials}),
        'major_panel_count': 7, 'separate_attachment_belts': 1, 'panel_bone_mapping': PANEL_BONES,
        'runtime_lod_triangles': [common.triangles(ob) for ob in lods],
        'runtime_materials': len(lods[0].data.materials), 'runtime_material_slots': [MATERIAL],
        'runtime_mesh_sections': 1, 'shared_material': MATERIAL,
        'runtime_attachment_controller': 'Requires KusazuriHinges on an armor-only instance of the native Manny skeleton; seven rigid leaves hinge around authored waist pivots and the independent belt follows pelvis',
        'vertex_color': {'name': TINT, 'domain': 'CORNER', 'data_type': 'FLOAT_COLOR',
            'export_channels': 1, 'fbx_encoding': 'LINEAR', 'prioritize_active_color': True,
            'mask_channel': 'R', 'semantics': '0 = indigo obi cord; 1 = ordinary armor; alpha = 1',
            'source_components': source_tints, 'runtime_lods': runtime_tints},
        'runtime_lod_bone_influences': influences,
        'runtime_lod_max_bone_influences': [info['max'] for info in influences],
        'runtime_lod_normal_repairs': normal_repairs, 'runtime_lod_weight_normalization': normalization,
        'armor_bounds_metres': armor_bounds, 'bounds_cm': to_unreal_bounds(armor_bounds),
        'reduction_ratios': list(REDUCTIONS),
        'lod2_reduction_policy': lod2_policy,
        'runtime_actual_triangle_ratios': [common.triangles(ob)/evaluated_count for ob in lods],
        'source_bone_count': len(rig.data.bones), 'native_reference_bone_count': len(rig.data.bones)+1,
        'native_root_representation': 'Original Manny root is the Blender armature object; local-cm geometry under .01-scale root',
        'export_operation': 'Saved editable source evaluated in rig REST pose; one combined weighted mesh and two distance LODs',
        'export_root_motion_handling': 'Temporarily disable root action/NLA and use canonical .01 rest transform; restore action, slot, frame, root transform and pose matrices',
        'exported_from_source_sha256': input_hash,
        'source_blend_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'editable_geometry_sha256': after, 'editable_geometry_preserved_during_export': True,
        'rig_pose_and_fixtures_preserved_during_export': True,
        'textures': 'Reuse unchanged Do01/Textures/T_Do01_{BaseColor,Normal,ORM}.png through M_Kusazuri01; detailed lamella tiles 8/9/13/14, indigo lining tile 12 and woven obi tile 3 tinted by ArmorTint.R',
        'animation_source': 'Existing native Epic Manny clips drive the body and armor-only stateless panel hinges; no new skeleton or animation asset exported',
        'export_files': {str(path.relative_to(ART)): {'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in files}})
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    (ART / 'FILES.sha').write_text(''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' +
        str(path.relative_to(ART)) + '\n' for path in [source, manifest_path, *sorted(files)]))
    print('KUSAZURI01_SAVED_SOURCE_EXPORTED ' + json.dumps({'source': str(source),
        'runtime_lod_triangles': manifest['runtime_lod_triangles'], 'preserved': True}), flush=True)


if __name__ == '__main__':
    main()
