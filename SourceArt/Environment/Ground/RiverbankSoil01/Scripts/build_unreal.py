import unreal as u, time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai'); D='/Game/Art/Environment/Ground/RiverbankSoil01'; O=R/'artifacts/riverbanksoil01'; L=u.MaterialEditingLibrary; V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem); le=u.get_editor_subsystem(u.LevelEditorSubsystem)
# Preserve the open scene before switching to the separate material review map.
le.save_current_level()
le.new_level('/Game/Art/Environment/Ground/RiverbankSoil01/RiverbankSoil01_Review')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
t=u.AssetImportTask(); t.filename=str(R/'SourceArt/Environment/Ground/RiverbankSoil01/Textures/T_RiverbankSoil01_BaseColor.png'); t.destination_path=D; t.automated=True;t.save=True
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);tex=u.load_asset(D+'/T_RiverbankSoil01_BaseColor');tex.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO);tex.set_editor_property('address_x',u.TextureAddress.TA_MIRROR);tex.set_editor_property('address_y',u.TextureAddress.TA_MIRROR)
def node(m,c):return L.create_material_expression(m,c)
def link(a,o,b,i):L.connect_material_expressions(a,o,b,i)
def custom(m,code,inputs,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(m,u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);entries=[]
 for name in inputs:
  e=u.CustomInput();e.set_editor_property('input_name',name);entries.append(e)
 n.set_editor_property('inputs',entries);return n
def make(name,transition=False):
 m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,D,u.Material,u.MaterialFactoryNew());p=node(m,u.MaterialExpressionWorldPosition)
 uv=custom(m,'return (W.xy+float2(1.8*sin(W.y*.019),1.8*sin(W.x*.023)))/100.0+float2(0,.5);',['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,'',uv,'W')
 tx=node(m,u.MaterialExpressionTextureObject);tx.set_editor_property('texture',tex)
 c=custom(m,'float3 c=Texture2DSample(T,TSampler,UV).rgb; return lerp(float3(.188,.150,.109),c,.70)*(1+.025*sin(W.x*.009+sin(W.y*.006)));',['T','UV','W'])
 for a,k in [(tx,'T'),(uv,'UV'),(p,'W')]:link(a,'',c,k)
 n=custom(m,'float e=.0016; float2 g=float2(dot(Texture2DSampleBias(T,TSampler,UV-float2(e,0),.5).rgb-Texture2DSampleBias(T,TSampler,UV+float2(e,0),.5).rgb,float3(.3,.59,.11)),dot(Texture2DSampleBias(T,TSampler,UV-float2(0,e),.5).rgb-Texture2DSampleBias(T,TSampler,UV+float2(0,e),.5).rgb,float3(.3,.59,.11)));return normalize(float3(g*.7,1));',['T','UV']);link(tx,'',n,'T');link(uv,'',n,'UV')
 rough=node(m,u.MaterialExpressionConstant);rough.set_editor_property('r',.93)
 if transition:
  gt=node(m,u.MaterialExpressionTextureObject);gt.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/RiverGravel01/T_RiverGravel01_BaseColor'))
  blend=custom(m,'float3 g=Texture2DSample(G,GSampler,float2(W.x*.9563-W.y*.2924,W.x*.2924+W.y*.9563)/78).rgb;g=lerp(float3(.245,.203,.164),g,.78);float edge=W.x+9*sin(W.y*.037)+4*sin(W.y*.087);return lerp(C,g,smoothstep(35,165,edge));',['G','W','C']);link(gt,'',blend,'G');link(p,'',blend,'W');link(c,'',blend,'C');c=blend
 for a,prop in [(c,u.MaterialProperty.MP_BASE_COLOR),(n,u.MaterialProperty.MP_NORMAL),(rough,u.MaterialProperty.MP_ROUGHNESS)]:L.connect_material_property(a,'',prop)
 spec=node(m,u.MaterialExpressionConstant);spec.set_editor_property('r',.18);L.connect_material_property(spec,'',u.MaterialProperty.MP_SPECULAR);L.recompile_material(m);return m
soil=make('M_RiverbankSoil_01');transition=make('M_RiverbankSoil01_ReviewTransition',True)
def mesh(label,path,loc,scale,mat=None,yaw=0):
 a=es.spawn_actor_from_class(u.StaticMeshActor,V(*loc),u.Rotator(yaw=yaw));a.set_actor_label(label);a.static_mesh_component.set_static_mesh(u.load_asset(path));a.set_actor_scale3d(V(*scale));
 if mat:a.static_mesh_component.set_material(0,mat)
 return a
plane='/Engine/BasicShapes/Plane'
mesh('RiverbankSoil_01_OneMetre',plane,(-650,0,0),(1,1,1),soil)
mesh('RiverbankSoil_01_Context',plane,(0,0,0),(6,6,1),transition)
gp='/Game/Art/Environment/Vegetation/Grass/RiverbankGrass01/RiverbankGrass_01'
for i,(x,y,s,ang) in enumerate([(-168,-75,1,18),(-65,46,.9,147),(-187,132,1.1,61),(-30,167,.85,204),(-225,-188,.95,90),(-72,-190,.8,12)]):mesh('ApprovedGrass_%02d'%i,gp,(x,y,-.5),(s,s,s),yaw=ang)
mesh('ApprovedRiverRock_01','/Game/Art/Environment/Rocks/RiverRock01/RiverRock_01',(42,90,-9),(.65,.65,.65),yaw=24)
sun=es.spawn_actor_from_class(u.DirectionalLight,V(0,0,500),u.Rotator(pitch=-48,yaw=-35));sun.light_component.set_editor_property('intensity',3.0);sun.light_component.set_editor_property('light_source_angle',4)
sky=es.spawn_actor_from_class(u.SkyLight,V(0,0,500));sky.light_component.set_editor_property('intensity',.5);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EngineResources/DefaultTextureCube'));sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
pp=es.spawn_actor_from_class(u.PostProcessVolume,V());pp.set_editor_property('unbound',True);settings=pp.get_editor_property('settings');settings.set_editor_property('override_auto_exposure_method',True);settings.set_editor_property('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL);settings.set_editor_property('override_auto_exposure_bias',True);settings.set_editor_property('auto_exposure_bias',0);settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True);settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',False);settings.set_editor_property('override_bloom_intensity',True);settings.set_editor_property('bloom_intensity',0);pp.set_editor_property('settings',settings)
views=[('01-overhead-1m',(-650,0,0),(0,0,235)),('02-close-oblique',(-650,0,0),(30,-125,90)),('03-grass-integration',(-125,-50,6),(80,-220,155)),('04-gravel-transition',(40,25,5),(260,-340,300)),('05-strategy', (0,0,0),(1100,-1600,1800))]
for name,target,off in views:
 target=V(*target);cam=es.spawn_actor_from_class(u.CameraActor,target+V(*off));cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False);cam.set_actor_label('RiverbankSoil01_'+name);cam.camera_component.set_field_of_view(45);cam.camera_component.set_editor_property('post_process_blend_weight',0)
u.EditorAssetLibrary.save_directory(D);le.save_current_level()
es.clear_actor_selection_set()
for cmd in ['Slate.bAllowThrottling 0','t.IdleWhenNotForeground 0','r.Streaming.FullyLoadUsedTextures 1']:u.SystemLibrary.execute_console_command(world,cmd)
O.joinpath('built.txt').write_text('Material, imported albedo and review map saved in Unreal.')
exec((R/'SourceArt/Environment/Ground/RiverbankSoil01/Scripts/capture_unreal.py').read_text())
