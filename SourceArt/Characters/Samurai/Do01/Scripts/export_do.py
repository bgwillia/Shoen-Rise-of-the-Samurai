"""Export saved Dō source in rest pose; rebuild hidden runtime copies only."""
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
from mathutils import Matrix

ART = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ART.parent / 'Kabuto01/Scripts'))
import kabuto_export_common as common
from export_kabuto import geometry_signature
common.ROUND_GROUP = 'Do_Round_Surfaces'
SOURCE = 'DO01 • editable components'
RUNTIME = 'EXPORT ONLY • runtime LODs'


def signature(objects):
    weights = [(ob.name, [g.name for g in ob.vertex_groups],
                [[(w.group, w.weight) for w in v.groups] for v in ob.data.vertices]) for ob in objects]
    return hashlib.sha256((geometry_signature(objects) + json.dumps(weights)).encode()).hexdigest()


def fbx(path, objects, animation=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    common.select(objects)
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH', 'ARMATURE'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Y', axis_up='Z',
        use_space_transform=False, bake_space_transform=False, mesh_smooth_type='FACE', use_tspace=True,
        use_mesh_modifiers=True, add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
        use_armature_deform_only=False, armature_nodetype='NULL', bake_anim=animation, bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0, path_mode='RELATIVE', embed_textures=False)


def weight_info(ob, rig):
    names = {g.index: g.name for g in ob.vertex_groups}
    counts, totals = [], []
    for vertex in ob.data.vertices:
        weights = [w.weight for w in vertex.groups if names[w.group] in rig.data.bones and w.weight > 1e-7]
        counts.append(len(weights)); totals.append(sum(weights))
    if not counts or min(counts) < 1 or max(counts) > 4 or max(abs(v-1) for v in totals) > .001:
        raise RuntimeError('Unweighted, excessive or non-normalized runtime bone influences: ' + ob.name)
    return {'max': max(counts), 'min': min(counts), 'vertices': len(counts),
            'weight_sum_min': min(totals), 'weight_sum_max': max(totals)}


def normalize_reduced_weights(ob, rig):
    groups = {g.index:g for g in ob.vertex_groups if g.name in rig.data.bones}
    pruned, maximum, discarded = 0, 0, 0.
    for vertex in ob.data.vertices:
        native = [(w.group,w.weight) for w in vertex.groups if w.group in groups]
        if any(not math.isfinite(w) or w < 0 for _,w in native):
            raise RuntimeError('Invalid reduced skin weight: '+ob.name)
        ranked = sorted(((i,w) for i,w in native if w > 1e-7), key=lambda item:(-item[1],item[0]))
        keep = ranked[:4]; total = sum(w for _,w in keep)
        if total <= 0: raise RuntimeError('Unweighted reduced vertex: '+ob.name)
        maximum = max(maximum,len(ranked)); pruned += len(ranked) > 4
        discarded = max(discarded,sum(w for _,w in ranked[4:]))
        for index,_ in native: groups[index].remove([vertex.index])
        for index,weight in keep: groups[index].add([vertex.index],weight/total,'REPLACE')
    return {'lod':ob.name, 'vertices':len(ob.data.vertices), 'max_influences_before':maximum,
            'vertices_with_pruned_influences':pruned, 'max_discarded_weight':discarded}


def main():
    source = ART / 'Do01.blend'
    input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    if scene.unit_settings.system != 'METRIC' or abs(scene.unit_settings.scale_length-1) > 1e-6:
        raise RuntimeError('Dō source must use metre units')
    components = sorted((o for o in bpy.data.collections[SOURCE].objects if o.type == 'MESH'), key=lambda o:o.name)
    if not {'Do_Main','Do_Back','Do_Upper','Do_Straps'}.issubset({o.name for o in components}):
        raise RuntimeError('Missing editable Dō components')
    rig, body = bpy.data.objects['root'], bpy.data.objects['FIT_Manny']
    if 'root' in rig.data.bones: raise RuntimeError('Native Manny root must remain the armature object, not a duplicate bone')
    if rig.parent: raise RuntimeError('Native Manny root must be detached from the FBX import-only empty')
    fixtures = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('FIT_')]
    preserved = components + fixtures
    runtime = bpy.data.collections[RUNTIME]
    if any(o in runtime.objects.values() for o in [*preserved, rig]):
        raise RuntimeError('Source/fit objects must not belong to export-only collection')
    atlas = bpy.data.materials['M_Do01']
    if any(list(o.data.materials) != [atlas] or not o.data.uv_layers for o in components):
        raise RuntimeError('Every editable component needs M_Do01 and UVs')
    bpy.context.view_layer.update()
    before = signature(preserved)
    animation = rig.animation_data
    action, slot = (animation.action, animation.action_slot) if animation else (None,None)
    use_nla = animation.use_nla if animation else False
    root_basis = rig.matrix_basis.copy()
    pose_position = rig.data.pose_position
    frame, subframe, start, end = scene.frame_current, scene.frame_subframe, scene.frame_start, scene.frame_end
    visibility = [(o,o.hide_get(),o.hide_render,o.select_get()) for o in bpy.context.view_layer.objects if o not in runtime.objects.values()]
    active = bpy.context.view_layer.objects.active
    if active and active in runtime.objects.values(): active = None
    lods, influence_info, files, mannequin_lods = [], [], [], []
    weight_normalization = []
    try:
        for ob in list(runtime.objects): bpy.data.objects.remove(ob, do_unlink=True)
        for ob in [rig,*components]: ob.hide_set(False)
        if animation: animation.action = None; animation.use_nla = False
        rig.matrix_basis = Matrix.Diagonal((.01,.01,.01,1.))
        rig.data.pose_position = 'REST'
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        copies = []
        for ob in components:
            evaluated = ob.evaluated_get(depsgraph)
            data = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
            data.transform(ob.matrix_world)
            copy = bpy.data.objects.new(ob.name+'_runtime',data); runtime.objects.link(copy)
            for group in ob.vertex_groups: copy.vertex_groups.new(name=group.name)
            copies.append(copy)
        common.select(copies); bpy.ops.object.join()
        base = bpy.context.object; base.name = 'SK_Do01_LOD0'
        base.data.materials.clear(); base.data.materials.append(atlas)
        for polygon in base.data.polygons: polygon.material_index = 0
        evaluated_count = common.triangles(base)
        common.repair_edge_uvs(base); common.surface_normals(base)
        base['runtime_reduction_ratio'] = 1.; lods.append(base)
        for level,ratio in [(1,.40),(2,.08)]:
            copy = base.copy(); copy.data = base.data.copy(); runtime.objects.link(copy); copy.name = f'SK_Do01_LOD{level}'
            common.select([copy]); mod = copy.modifiers.new('Distance reduction','DECIMATE'); mod.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=mod.name)
            common.clean_flat_islands(copy); common.repair_edge_uvs(copy); common.surface_normals(copy)
            weight_normalization.append(normalize_reduced_weights(copy,rig))
            copy['runtime_reduction_ratio'] = ratio; lods.append(copy)
        for level,ob in enumerate(lods):
            influence_info.append(weight_info(ob,rig))
            suffix = '' if level == 0 else f'_LOD{level}'
            # Static fixture is the exact same feet-relative rest geometry, no axis pretransform.
            static = ob.copy(); static.data = ob.data.copy(); runtime.objects.link(static)
            static.name = 'SM_Do01'+suffix; static.parent = None; static.modifiers.clear(); static.matrix_world = Matrix.Identity(4)
            path = ART/f'Review/Exports/SM_Do01{suffix}.fbx'; fbx(path,[static]); files.append(path)
            # Native Manny uses local-centimetre meshes under the original .01-scale root.
            ob.data.transform(rig.matrix_world.inverted())
            ob.parent = rig; ob.matrix_parent_inverse = Matrix.Identity(4); ob.matrix_basis = Matrix.Identity(4)
            mod = ob.modifiers.new('Existing SHŌEN skeleton','ARMATURE'); mod.object = rig
            path = ART/f'Exports/SK_Do01{suffix}.fbx'; fbx(path,[rig,ob]); files.append(path)
        # Native Manny's static baseline preserves its own UVs/normals and material slots.
        data = bpy.data.meshes.new_from_object(body.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
        data.transform(body.matrix_world)
        static_body = bpy.data.objects.new('SM_Manny',data); runtime.objects.link(static_body)
        common.select([static_body]); mod = static_body.modifiers.new('Export triangles','TRIANGULATE')
        bpy.ops.object.modifier_apply(modifier=mod.name)
        path = ART/'Review/Exports/SM_Manny.fbx'; fbx(path,[static_body]); files.append(path)
        mannequin_lods.append(static_body)
        # These generated static review LODs do not replace Epic's skeletal LODs.
        for level,ratio in [(1,.32),(2,.15)]:
            copy = static_body.copy(); copy.data = static_body.data.copy(); runtime.objects.link(copy)
            copy.name = f'SM_Manny_LOD{level}'; common.select([copy])
            mod = copy.modifiers.new('Static review baseline reduction','DECIMATE'); mod.ratio = ratio
            bpy.ops.object.modifier_apply(modifier=mod.name)
            mod = copy.modifiers.new('Export triangles','TRIANGULATE')
            bpy.ops.object.modifier_apply(modifier=mod.name)
            # Reduced topology needs fresh normals; retain Manny's smooth/sharp flags and UVs.
            copy.data.normals_split_custom_set([(0.,0.,0.)] * len(copy.data.loops)); copy.data.update()
            copy['runtime_reduction_ratio'] = ratio; mannequin_lods.append(copy)
            path = ART/f'Review/Exports/SM_Manny_LOD{level}.fbx'; fbx(path,[copy]); files.append(path)
        world_vertices = [lods[0].matrix_world@v.co for v in lods[0].data.vertices]
        bounds = [[min(v[i] for v in world_vertices) for i in range(3)],
                  [max(v[i] for v in world_vertices) for i in range(3)]]
    finally:
        if animation:
            animation.action = action
            if action and slot: animation.action_slot = slot
            animation.use_nla = use_nla
        rig.data.pose_position = pose_position
        scene.frame_start,scene.frame_end = start,end; scene.frame_set(frame,subframe=subframe)
        rig.matrix_basis = root_basis
        for ob in runtime.objects: ob.hide_render=True; ob.hide_set(True); ob.select_set(False)
        for ob,hidden,render,selected in visibility: ob.hide_set(hidden); ob.hide_render=render; ob.select_set(selected)
        bpy.context.view_layer.objects.active = active
        bpy.context.view_layer.update()
    after = signature(preserved)
    if before != after: raise RuntimeError('Export changed editable/fit geometry, transforms or weights; source not saved')
    for suffix in ['BaseColor','Normal','ORM']:
        image = bpy.data.images['T_Do01_'+suffix]; path = ART/'Textures'/(image.name+'.png')
        image.filepath_raw=str(path); image.file_format='PNG'; image.save(); image.pack(); files.append(path)
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    low,high = bounds
    cm_low,cm_high = [100*low[0],-100*high[1],100*low[2]],[100*high[0],-100*low[1],100*high[2]]
    manifest_path = ART/'asset-manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'asset':'Do01'}
    manifest.update({'blender_version':bpy.app.version_string,
        'source_components':{o.name:common.triangles(o) for o in components}, 'source_component_objects':len(components),
        'source_triangles_before_modifiers':sum(common.triangles(o) for o in components),
        'evaluated_source_triangles':evaluated_count, 'exported_triangles':common.triangles(lods[0]),
        'runtime_lod_triangles':[common.triangles(o) for o in lods], 'runtime_materials':len(lods[0].data.materials),
        'source_materials':len({m.name for o in components for m in o.data.materials}),
        'runtime_lod_bone_influences':influence_info, 'runtime_lod_max_bone_influences':[i['max'] for i in influence_info],
        'runtime_weight_normalization':'Generated armor LOD1/2 only: retain four strongest native bone weights and normalize to sum one; source, LOD0 and non-bone shading tags unchanged',
        'runtime_lod_weight_normalization':weight_normalization,
        'source_bone_count':len(rig.data.bones), 'native_reference_bone_count':len(rig.data.bones)+1,
        'native_root_representation':'Original root is the Blender armature object; localcm geometry under .01-scale root', 'armor_bounds_metres':bounds,
        'bounds_cm':{'min':cm_low,'max':cm_high,'size':[b-a for a,b in zip(cm_low,cm_high)]},
        'export_operation':'Saved editable source evaluated in rig REST pose; combined hidden weighted runtime copies',
        'export_root_motion_handling':'Temporarily disable root action/NLA and use canonical .01 rest transform; restore source action/frame/transform',
        'exported_from_source_sha256':input_hash,'source_blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'editable_geometry_sha256':after,'editable_geometry_preserved_during_export':True,
        'fit_body_geometry_unchanged':True,'reduction_ratios':[1.,.40,.08],
        'static_mannequin':{'source_asset':'/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',
            'generation':'Native LOD0 rest mesh; generated static review LOD1/2 using Blender DECIMATE, not Epic skeletal LODs',
            'reduction_ratios':[1.,.32,.15], 'lod_triangles':[common.triangles(o) for o in mannequin_lods],
            'lod_material_slots':[len(o.data.materials) for o in mannequin_lods],
            'native_skeletal_manny_unchanged':True},
        'exported_animations':{}, 'animation_source':'Unmodified native Epic Manny clips used directly in Unreal',
        'export_files':{str(p.relative_to(ART)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}})
    manifest_path.write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
    (ART/'FILES.sha').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ART))+'\n' for p in [source,manifest_path,*sorted(files)]))
    print('DO01_SAVED_SOURCE_EXPORTED '+json.dumps({'source':str(source),'triangles':manifest['runtime_lod_triangles'],'preserved':True}))


if __name__ == '__main__': main()
