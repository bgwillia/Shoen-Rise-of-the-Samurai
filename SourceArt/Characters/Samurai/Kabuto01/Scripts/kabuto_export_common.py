"""Shared runtime-copy operations; never reduce or join editable helmet objects."""
import bmesh
import bpy
import math
from mathutils import Matrix


SOURCE_COLLECTION = 'KABUTO01 • editable components'
RUNTIME_COLLECTION = 'EXPORT ONLY • evaluated helmet LODs'
REQUIRED_COMPONENTS = {'Hachi', 'Mabisashi', 'Shikoro', 'Fukigaeshi_L',
                       'Fukigaeshi_R', 'Maedate', 'Uchiwa', 'ShinHimo'}
COMPONENT_ORDER = ('Hachi', 'Hachi_Fittings', 'Mabisashi', 'Mabisashi_Edge',
                   'Shikoro', 'Fukigaeshi_L', 'Fukigaeshi_R', 'Maedate',
                   'Uchiwa', 'Padding rolled rim', 'ShinHimo')
ROUND_COMPONENTS = {'Hachi_Fittings', 'Mabisashi_Edge', 'Padding rolled rim', 'ShinHimo'}
ROUND_GROUP = 'Kabuto_Runtime_Round_Surfaces'


def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.hide_set(False)
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def fbx(path, objects, animation=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    select(objects)
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={'MESH', 'ARMATURE'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Y', axis_up='Z', use_space_transform=False,
        bake_space_transform=False, mesh_smooth_type='FACE', use_mesh_modifiers=True,
        add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
        use_armature_deform_only=False, bake_anim=animation,
        bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0, path_mode='RELATIVE', embed_textures=False,
        use_tspace=all(ob.type=='MESH' and all(len(p.vertices)==3 for p in ob.data.polygons) for ob in objects))


def triangles(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def clean_flat_islands(ob):
    # Reduction can flatten tiny disconnected trim into coincident faces.
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    pending, remove = set(bm.verts), []
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
        origin, volume = first.co, 0
        for face in faces:
            points = [vertex.co - origin for vertex in face.verts]
            for i in range(1, len(points) - 1):
                volume += points[0].dot(points[i].cross(points[i + 1])) / 6
        if abs(volume) < 1e-13:
            remove.extend(group)
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()


def surface_normals(ob):
    # Keep ordinary smooth normals on curved surfaces and authored flat faces
    # on the crest. Mark plate/thickness corners sharp without splitting mesh
    # vertices, so these remain closed manifold parts.
    mesh = ob.data
    group = ob.vertex_groups.get(ROUND_GROUP)
    rounded = ({vertex.index for vertex in mesh.vertices
                if any(weight.group == group.index and weight.weight > .5 for weight in vertex.groups)}
               if group else set())
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    angle = math.radians(40)
    for edge in bm.edges:
        if all(vertex.index in rounded for vertex in edge.verts):
            continue
        if len(edge.link_faces) == 2 and edge.calc_face_angle() > angle:
            edge.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    # LOD copies can inherit normals calculated before reduction. Zero custom
    # vectors request automatic normals using the current sharp/smooth flags.
    mesh.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(mesh.loops))
    mesh.update()
    normals = [normal.vector.copy() for normal in mesh.corner_normals]
    repaired = 0
    for polygon in mesh.polygons:
        a, b, c = [mesh.vertices[index].co for index in polygon.vertices[:3]]
        geometric = (b - a).cross(c - a).normalized()
        for loop_index in polygon.loop_indices:
            normal = normals[loop_index]
            if normal.length_squared < .5 or not all(math.isfinite(value) for value in normal):
                if geometric.length_squared < .5:
                    raise RuntimeError('Cannot export a degenerate triangle normal: ' + ob.name)
                normals[loop_index] = geometric
                repaired += 1
    mesh.normals_split_custom_set(normals)
    ob['geometric_normal_fallback_corners'] = repaired


def repair_edge_uvs(ob):
    # Keep authored surface UVs; repair collapsed thickness/cap UV triangles.
    select([ob])
    mod = ob.modifiers.new('Export triangles', 'TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=mod.name)
    uv = ob.data.uv_layers.active.data
    # Collapse can extrapolate a seam coordinate slightly beyond the atlas.
    # Constrain only the export copy; the editable UVs remain untouched.
    for corner in uv:
        corner.uv.x = min(.999, max(.001, corner.uv.x))
        corner.uv.y = min(.999, max(.001, corner.uv.y))
    repaired = 0
    for polygon in ob.data.polygons:
        ids = list(polygon.loop_indices)
        a, b, c = [uv[i].uv.copy() for i in ids]
        area = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
        if abs(area) < 1e-9:
            center, du = (a + b + c) / 3, .0003
            center.x = min(.999, max(.001, center.x))
            center.y = min(.999, max(.001, center.y))
            for i, delta in zip(ids, [(-du, -du), (du, -du), (0, du)]):
                uv[i].uv = (center.x + delta[0], center.y + delta[1])
            repaired += 1
    ob['repaired_edge_uv_triangles'] = repaired


def export_runtime(components, runtime, art, pivot, body, rig):
    """Rebuild export-owned copies from evaluated editable meshes at neutral pose.

    Returns the new helmet LODs and the evaluated source triangle count. Caller
    controls saving the .blend. Temporary fit-pose and visibility changes are
    restored even if an FBX operation fails.
    """
    if not REQUIRED_COMPONENTS.issubset({ob.name for ob in components}):
        raise RuntimeError('Editable helmet collection is missing required components')
    atlas = bpy.data.materials['M_Kabuto01']
    for ob in components:
        if ob in runtime.objects.values():
            raise RuntimeError('Editable object is also in the export-only collection: ' + ob.name)
        if list(ob.data.materials) != [atlas] or not ob.data.uv_layers:
            raise RuntimeError('Each helmet component needs the M_Kabuto01 atlas and UVs: ' + ob.name)
    for name in ('A_Neutral', 'A_Idle', 'A_Walk'):
        if name not in bpy.data.actions:
            raise RuntimeError('Missing embedded fit action: ' + name)
    scene = bpy.context.scene
    frame, start, end = scene.frame_current, scene.frame_start, scene.frame_end
    rig.animation_data_create()
    action = rig.animation_data.action
    visibility = [(ob, ob.hide_get(), ob.hide_render, ob.select_get())
                  for ob in bpy.context.view_layer.objects if ob not in runtime.objects.values()]
    active = bpy.context.view_layer.objects.active
    if active and active in runtime.objects.values():
        active = None
    try:
        for ob in list(runtime.objects):
            if ob in (body, rig):
                raise RuntimeError('Fit source must not be in the export-only collection')
            bpy.data.objects.remove(ob, do_unlink=True)
        for ob in (body, rig, *components):
            ob.hide_set(False)
        rig.animation_data.action = bpy.data.actions['A_Neutral']
        scene.frame_set(1)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        copies = []
        for ob in components:
            data = bpy.data.meshes.new_from_object(ob.evaluated_get(depsgraph))
            # Include artist object-level edits while retaining the head-local pivot.
            data.transform(Matrix.Translation(-pivot) @ ob.matrix_world)
            copy = bpy.data.objects.new(ob.name + '_runtime', data)
            runtime.objects.link(copy)
            for group in ob.vertex_groups:
                copy.vertex_groups.new(name=group.name)
            if ob.name in ROUND_COMPONENTS:
                group = copy.vertex_groups.get(ROUND_GROUP) or copy.vertex_groups.new(name=ROUND_GROUP)
                group.add(list(range(len(data.vertices))), 1.0, 'REPLACE')
            copies.append(copy)
        select(copies)
        bpy.ops.object.join()
        helmet = bpy.context.object
        helmet.name = 'SM_Kabuto01_LOD0'
        helmet.data.materials.clear()
        helmet.data.materials.append(atlas)
        for polygon in helmet.data.polygons:
            polygon.material_index = 0
        evaluated_count = triangles(helmet)
        # The close-view mesh preserves all evaluated source geometry. Distance
        # LODs carry the reduction cost instead of damaging the hero silhouette.
        repair_edge_uvs(helmet)
        surface_normals(helmet)
        helmet['runtime_reduction_ratio'] = 1.0
        fbx(art / 'Exports/SM_Kabuto01.fbx', [helmet])
        lods = [helmet]
        for level, ratio in [(1, .33), (2, .075)]:
            copy = helmet.copy()
            copy.data = helmet.data.copy()
            runtime.objects.link(copy)
            copy.name = f'SM_Kabuto01_LOD{level}'
            select([copy])
            mod = copy.modifiers.new('Prototype silhouette reduction', 'DECIMATE')
            mod.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=mod.name)
            clean_flat_islands(copy)
            repair_edge_uvs(copy)
            surface_normals(copy)
            copy['runtime_reduction_ratio'] = ratio
            fbx(art / f'Exports/SM_Kabuto01_LOD{level}.fbx', [copy])
            lods.append(copy)
        fbx(art / 'Review/Exports/SK_FitMannequin.fbx', [rig, body])
        static_body = body.copy()
        static_body.data = body.data.copy()
        runtime.objects.link(static_body)
        static_body.parent = None
        static_body.matrix_world = body.matrix_world.copy()
        static_body.modifiers.clear()
        static_body.name = 'SM_FitMannequin'
        fbx(art / 'Review/Exports/SM_FitMannequin.fbx', [static_body])
        for name, last_frame in [('A_Idle', 61), ('A_Walk', 31)]:
            rig.animation_data.action = bpy.data.actions[name]
            scene.frame_start, scene.frame_end = 1, last_frame
            fbx(art / f'Review/Exports/{name}.fbx', [rig], True)
        return lods, evaluated_count
    finally:
        rig.animation_data.action = action
        scene.frame_start, scene.frame_end = start, end
        scene.frame_set(frame)
        for ob in runtime.objects:
            ob.hide_render = True
            ob.hide_set(True)
            ob.select_set(False)
        for ob, hidden, hide_render, selected in visibility:
            ob.hide_set(hidden)
            ob.hide_render = hide_render
            ob.select_set(selected)
        if active and active.name in bpy.context.view_layer.objects:
            bpy.context.view_layer.objects.active = active
