import unreal as u,time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/MixedGround01';L=u.MaterialEditingLibrary;V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
le.save_current_level();le.new_level(D+'/MixedGround01_Review');world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
# Duplicate the approved grass graph; every original asset stays unchanged.
m=u.EditorAssetLibrary.duplicate_asset('/Game/Art/Environment/Ground/GrasslandGround01/M_GrasslandGround_01',D+'/M_MixedGround_01')
grass=[L.get_material_property_input_node(m,prop) for prop in [u.MaterialProperty.MP_BASE_COLOR,u.MaterialProperty.MP_NORMAL,u.MaterialProperty.MP_ROUGHNESS]]
def node(cls):return L.create_material_expression(m,cls)
def custom(code,names,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);entries=[]
 for name in names:
  e=u.CustomInput();e.set_editor_property('input_name',name);entries.append(e)
 n.set_editor_property('inputs',entries);return n
def link(a,b,k):L.connect_material_expressions(a,'',b,k)
# Reuse the current approved soil's actual expressions and texture references.
source=u.load_asset('/Game/Art/Environment/Ground/RiverbankSoil01/M_RiverbankSoil_01')
p=node(u.MaterialExpressionWorldPosition)
src_uv=next(n for n in L.get_material_expressions(source) if isinstance(n,u.MaterialExpressionCustom) and 'W.xy' in n.get_editor_property('code'))
uv=custom(src_uv.get_editor_property('code'),['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,uv,'W')
src_tx=next(n for n in L.get_material_expressions(source) if isinstance(n,u.MaterialExpressionTextureObject));tx=node(u.MaterialExpressionTextureObject);tx.set_editor_property('texture',src_tx.get_editor_property('texture'))
sc=custom(L.get_material_property_input_node(source,u.MaterialProperty.MP_BASE_COLOR).get_editor_property('code'),['T','UV','W']);link(tx,sc,'T');link(uv,sc,'UV');link(p,sc,'W')
sn=custom(L.get_material_property_input_node(source,u.MaterialProperty.MP_NORMAL).get_editor_property('code'),['T','UV']);link(tx,sn,'T');link(uv,sn,'UV')
sr=node(u.MaterialExpressionConstant);sr.set_editor_property('r',L.get_material_property_input_node(source,u.MaterialProperty.MP_ROUGHNESS).get_editor_property('r'))
mask=custom('''struct Field {
 float hash(float2 p) {return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 float noise(float2 p) {float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);}
};Field f;float2 q=W.xy/16.0+float2(3.7,8.81);
q+=float2(f.noise(q*.7+19),f.noise(q*.7-31))*.7;
float v=f.noise(q)*.65+f.noise(q*2.7+7.3)*.25+f.noise(q*7.1-13)*.10;
return smoothstep(.38,.62,v);''',['W'],u.CustomMaterialOutputType.CMOT_FLOAT1);mask.set_editor_property('desc','MixedGround_01 soft connected coverage');link(p,mask,'W')
for a,b,prop in zip([sc,sn,sr],grass,[u.MaterialProperty.MP_BASE_COLOR,u.MaterialProperty.MP_NORMAL,u.MaterialProperty.MP_ROUGHNESS]):
 mix=node(u.MaterialExpressionLinearInterpolate);link(a,mix,'A');link(b,mix,'B');link(mask,mix,'Alpha');L.connect_material_property(mix,'',prop)
L.recompile_material(m)
patch=es.spawn_actor_from_class(u.StaticMeshActor,V());patch.set_actor_label('MixedGround_01_SmallSample');patch.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'));patch.static_mesh_component.set_material(0,m);patch.set_actor_scale3d(V(4,4,1))
clump=es.spawn_actor_from_class(u.StaticMeshActor,V(0,5,-.4),u.Rotator(yaw=24));clump.set_actor_label('Approved_RiverbankGrass_01_Unchanged');clump.static_mesh_component.set_static_mesh(u.load_asset('/Game/Art/Environment/Vegetation/Grass/RiverbankGrass01/RiverbankGrass_01'))
sun=es.spawn_actor_from_class(u.DirectionalLight,V(0,0,500),u.Rotator(pitch=-48,yaw=130));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_editor_property('intensity',3);sun.light_component.set_editor_property('light_source_angle',4)
sky=es.spawn_actor_from_class(u.SkyLight,V(0,0,500));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('intensity',.8);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EngineResources/DefaultTextureCube'));sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
pp=es.spawn_actor_from_class(u.PostProcessVolume,V());pp.set_editor_property('unbound',True);q=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_auto_exposure_bias',True),('auto_exposure_bias',0),('override_bloom_intensity',True),('bloom_intensity',0)]:q.set_editor_property(k,v)
pp.set_editor_property('settings',q)
views=[('01-overhead-1m-detail',(-80,70,0),(0,0,215)),('02-close-oblique',(-80,70,1),(30,-85,55)),('03-with-clump',(0,5,4),(32,-80,45)),('04-sample-patch',(0,0,0),(300,-450,490)),('05-strategy',(0,0,0),(1100,-1600,1800))]
for name,target,offset in views:
 target=V(*target);cam=es.spawn_actor_from_class(u.CameraActor,target+V(*offset));cam.set_actor_label('MixedGround01_'+name);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False);cam.camera_component.set_field_of_view(45);cam.camera_component.set_editor_property('post_process_blend_weight',0)
 if name=='01-overhead-1m-detail':cam.camera_component.set_editor_property('constrain_aspect_ratio',True);cam.camera_component.set_editor_property('aspect_ratio',1.0);cam.camera_component.set_field_of_view(26.18)
u.EditorAssetLibrary.save_directory(D);le.save_current_level();es.clear_actor_selection_set();le.editor_set_viewport_realtime(True)
for cmd in ['Slate.bAllowThrottling 0','t.IdleWhenNotForeground 0','r.Streaming.FullyLoadUsedTextures 1']:u.SystemLibrary.execute_console_command(world,cmd)
exec((R/'SourceArt/Environment/Ground/MixedGround01/Scripts/capture_unreal.py').read_text())
