import unreal as u,time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/GrasslandGround01';O=R/'artifacts/grasslandground01';L=u.MaterialEditingLibrary;V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
le.save_current_level();le.new_level(D+'/GrasslandGround01_Review');world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
t=u.AssetImportTask();t.filename=str(R/'SourceArt/Environment/Ground/GrasslandGround01/Textures/T_GrasslandGround01_BaseColor.png');t.destination_path=D;t.automated=True;t.save=True;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);tex=u.load_asset(D+'/T_GrasslandGround01_BaseColor');tex.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO);tex.set_editor_property('address_x',u.TextureAddress.TA_MIRROR);tex.set_editor_property('address_y',u.TextureAddress.TA_MIRROR)
m=u.AssetToolsHelpers.get_asset_tools().create_asset('M_GrasslandGround_01',D,u.Material,u.MaterialFactoryNew())
def node(cls):return L.create_material_expression(m,cls)
def custom(code,names,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);entries=[]
 for name in names:
  e=u.CustomInput();e.set_editor_property('input_name',name);entries.append(e)
 n.set_editor_property('inputs',entries);return n
def link(a,b,k):L.connect_material_expressions(a,'',b,k)
p=node(u.MaterialExpressionWorldPosition);uv=custom('return (W.xy+float2(3*sin(W.y*.016),3*sin(W.x*.019)))/80.0+float2(.31,.57);',['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,uv,'W')
tx=node(u.MaterialExpressionTextureObject);tx.set_editor_property('texture',tex)
c=custom('float3 c=Texture2DSample(T,TSampler,UV).rgb; float g=dot(c,float3(.3,.59,.11)); c=lerp(g.xxx,c,.78); c*=float3(.84,1.0,.94); float macro=1+.04*sin(W.x*.008+sin(W.y*.009)); return lerp(float3(.075,.12,.05),c,.68)*macro;',['T','UV','W']);link(tx,c,'T');link(uv,c,'UV');link(p,c,'W')
n=custom('float e=.0016;float2 d=float2(dot(Texture2DSampleBias(T,TSampler,UV-float2(e,0),.5).rgb-Texture2DSampleBias(T,TSampler,UV+float2(e,0),.5).rgb,float3(.3,.59,.11)),dot(Texture2DSampleBias(T,TSampler,UV-float2(0,e),.5).rgb-Texture2DSampleBias(T,TSampler,UV+float2(0,e),.5).rgb,float3(.3,.59,.11))); return normalize(float3(d*.65,1));',['T','UV']);link(tx,n,'T');link(uv,n,'UV')
r=node(u.MaterialExpressionConstant);r.set_editor_property('r',.91);spec=node(u.MaterialExpressionConstant);spec.set_editor_property('r',.18)
for a,prop in [(c,u.MaterialProperty.MP_BASE_COLOR),(n,u.MaterialProperty.MP_NORMAL),(r,u.MaterialProperty.MP_ROUGHNESS),(spec,u.MaterialProperty.MP_SPECULAR)]:L.connect_material_property(a,'',prop)
L.recompile_material(m)
patch=es.spawn_actor_from_class(u.StaticMeshActor,V());patch.set_actor_label('GrasslandGround_01_4mSample');patch.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'));patch.static_mesh_component.set_material(0,m);patch.set_actor_scale3d(V(4,4,1))
clump=es.spawn_actor_from_class(u.StaticMeshActor,V(0,-15,-.3),u.Rotator(yaw=24));clump.set_actor_label('Approved_RiverbankGrass_01_Unchanged');clump.static_mesh_component.set_static_mesh(u.load_asset('/Game/Art/Environment/Vegetation/Grass/RiverbankGrass01/RiverbankGrass_01'))
sun=es.spawn_actor_from_class(u.DirectionalLight,V(0,0,500),u.Rotator(pitch=-48,yaw=130));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_editor_property('intensity',3);sun.light_component.set_editor_property('light_source_angle',4)
sky=es.spawn_actor_from_class(u.SkyLight,V(0,0,500));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('intensity',.8);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EngineResources/DefaultTextureCube'));sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
pp=es.spawn_actor_from_class(u.PostProcessVolume,V());pp.set_editor_property('unbound',True);q=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_auto_exposure_bias',True),('auto_exposure_bias',0),('override_bloom_intensity',True),('bloom_intensity',0)]:q.set_editor_property(k,v)
pp.set_editor_property('settings',q)
views=[('01-overhead-1m-detail',(-90,80,0),(0,0,215)),('02-close-with-clump',(0,-15,4),(32,-80,45)),('03-sample-patch',(0,0,0),(300,-450,490)),('04-strategy',(0,0,0),(1100,-1600,1800))]
for name,target,offset in views:
 target=V(*target);cam=es.spawn_actor_from_class(u.CameraActor,target+V(*offset));cam.set_actor_label('GrasslandGround01_'+name);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False);cam.camera_component.set_field_of_view(45);cam.camera_component.set_editor_property('post_process_blend_weight',0)
 if name=='01-overhead-1m-detail':cam.camera_component.set_editor_property('constrain_aspect_ratio',True);cam.camera_component.set_editor_property('aspect_ratio',1.0);cam.camera_component.set_field_of_view(26.18)
u.EditorAssetLibrary.save_directory(D);le.save_current_level();es.clear_actor_selection_set()
for cmd in ['Slate.bAllowThrottling 0','t.IdleWhenNotForeground 0','r.Streaming.FullyLoadUsedTextures 1']:u.SystemLibrary.execute_console_command(world,cmd)
exec((R/'SourceArt/Environment/Ground/GrasslandGround01/Scripts/capture_unreal.py').read_text())
