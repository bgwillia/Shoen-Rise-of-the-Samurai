"""Preserve Epic's native body/rest skeleton and import its existing clip exports."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Matrix
ART=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.render.fps=30
bpy.ops.import_scene.fbx(filepath=str(ART/'Exports/SKM_Manny_Simple.fbx'),automatic_bone_orientation=False,use_anim=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH');body.name='FIT_Manny'
assert rig.name=='root' and 'root' not in rig.data.bones
rest_rig_world=rig.matrix_world.copy();rest_body_world=body.matrix_world.copy()
# These simple preview shaders do not alter Epic geometry or its native UE materials.
for i,mat in enumerate(body.data.materials):
    mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF')
    if bs:
        for inp in ['Base Color','Metallic','Roughness','Normal']:
            for link in list(bs.inputs[inp].links):mat.node_tree.links.remove(link)
        bs.inputs['Base Color'].default_value=(.26,.285,.30,1) if i==0 else (.19,.215,.23,1)
        bs.inputs['Metallic'].default_value=.42;bs.inputs['Roughness'].default_value=.39
    mat['fixture_preview']='Neutral metal; original Epic materials are used in Unreal'
actions=[]
for alias in ['A_Idle','A_Walk','A_Run','A_Attack']:
    before=set(bpy.data.objects);before_actions=set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=str(ART/'Exports'/(alias+'.fbx')),automatic_bone_orientation=False,use_anim=True)
    imported=[o for o in bpy.data.objects if o not in before]
    temp=next(o for o in imported if o.type=='ARMATURE')
    action=temp.animation_data.action
    if action is None:action=next(a for a in bpy.data.actions if a not in before_actions)
    action.name=alias;action.use_fake_user=True
    actions.append({'name':alias,'frames':list(action.frame_range),'slots':[s.identifier for s in action.slots]})
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)
rig.animation_data_clear();rig.data.pose_position='REST';scene.frame_set(1)
rig.matrix_world=rest_rig_world;body.matrix_world=rest_body_world
# Persist actual transform channels, not only the FBX importer's evaluated
# matrix cache. The native mesh and all bone data remain in centimetres.
wrapper=rig.parent
rig.parent=None;rig.matrix_parent_inverse=Matrix.Identity(4)
rig.location=(0,0,0);rig.rotation_mode='XYZ';rig.rotation_euler=(0,0,0);rig.scale=(.01,.01,.01)
body.parent=rig;body.matrix_parent_inverse=Matrix.Identity(4)
body.location=(0,0,0);body.rotation_mode='XYZ';body.rotation_euler=(0,0,0);body.scale=(1,1,1)
bpy.context.view_layer.update()
if wrapper and wrapper.type=='EMPTY':bpy.data.objects.remove(wrapper,do_unlink=True)
assert abs((body.matrix_world@max(body.data.vertices,key=lambda v:v.co.z).co).z-1.8052362)<.00001
scene.render.fps=30
for p in rig.pose.bones:p.matrix_basis.identity()
rig['source_asset']='/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple';rig['source_skeleton']='/Game/Characters/Mannequins/Meshes/SK_Mannequin'
body['geometry_provenance']='Unmodified official Epic UE 5.8 Manny Simple exported geometry'
for o in bpy.context.selected_objects:o.select_set(False)
body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Manny.blend'))
report={'source':'Official Epic UE5 template SKM_Manny_Simple; unmodified mesh, reference skeleton and imported native clips','body':'FIT_Manny','rig':'root','rig_object_is_unreal_root_bone':True,'blender_deform_bones':len(rig.data.bones),'native_reference_bones':len(rig.data.bones)+1,'rig_object_scale':list(rig.scale),'axes':'Blender metres, -Y forward. Data coordinates centimetres under .01 root object scale. Native Unreal +Y forward.','body_vertices':len(body.data.vertices),'body_triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'actions':actions,'preview_materials':'Neutral metal simplification for Blender only. Native Epic materials retained in Unreal.','source_fbx_sha256':hashlib.sha256((ART/'Exports/SKM_Manny_Simple.fbx').read_bytes()).hexdigest(),'blend_sha256':hashlib.sha256((ART/'Manny.blend').read_bytes()).hexdigest()}
(ART/'fixture-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('MANNY_FIXTURE '+json.dumps(report))
