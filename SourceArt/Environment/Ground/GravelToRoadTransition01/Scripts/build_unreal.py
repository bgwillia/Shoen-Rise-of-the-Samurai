import unreal as u, time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/GravelToRoadTransition01';O=R/'artifacts/graveltoroadtransition01'
L=u.MaterialEditingLibrary;V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
le.new_level(D+'/GravelToRoadTransition01_Review')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
m=u.AssetToolsHelpers.get_asset_tools().create_asset('M_GravelToRoadTransition_01',D,u.Material,u.MaterialFactoryNew())
def node(c):return L.create_material_expression(m,c)
def link(a,o,b,i):L.connect_material_expressions(a,o,b,i)
def custom(code,names,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);items=[]
 for name in names:
  e=u.CustomInput();e.set_editor_property('input_name',name);items.append(e)
 n.set_editor_property('inputs',items);return n
w=node(u.MaterialExpressionWorldPosition);obj=node(u.MaterialExpressionObjectPositionWS)
p=node(u.MaterialExpressionSubtract);link(w,'',p,'A');link(obj,'',p,'B')
guv=custom('return float2(P.x*.9563-P.y*.2924,P.x*.2924+P.y*.9563)/78.0;',['P'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,'',guv,'P')
ruv=custom('return float2(P.x/200+.5,.5-P.y/400);',['P'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,'',ruv,'P')
g=node(u.MaterialExpressionTextureSample);g.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/RiverGravel01/T_RiverGravel01_BaseColor'));link(guv,'',g,'UVs')
r=node(u.MaterialExpressionTextureSample);r.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/T_CompactedEarthRoad01_BaseColor'));link(ruv,'',r,'UVs')
gn=node(u.MaterialExpressionTextureSample);gn.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/RiverGravel01/T_RiverGravel01_Normal'));gn.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL);link(guv,'',gn,'UVs')
mask=custom('''float along=P.y+21*sin(P.x*.034+P.y*.008)+12*sin(P.x*.081-P.y*.016)+7*sin(P.x*.14+P.y*.047);
float t=smoothstep(-160,160,along);
float stone=saturate((dot(G,float3(.3,.59,.11))-.065)*3.3);
float threshold=lerp(-.15,1.15,t);
float coverage=smoothstep(threshold-.045,threshold+.045,stone);
return float3(coverage,t,0);''',['P','G']);link(p,'',mask,'P');link(g,'RGB',mask,'G')
c=custom('return lerp(R,lerp(float3(.245,.203,.164),G,.78),M.x);',['R','G','M']);link(r,'RGB',c,'R');link(g,'RGB',c,'G');link(mask,'',c,'M');L.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
rt=node(u.MaterialExpressionTextureObject);rt.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/T_CompactedEarthRoad01_BaseColor'))
rn=custom('''float2 e=float2(.0009,.00045);
float gx=dot(Texture2DSample(T,TSampler,UV-float2(e.x,0)).rgb-Texture2DSample(T,TSampler,UV+float2(e.x,0)).rgb,float3(.3,.59,.11));
float gy=dot(Texture2DSample(T,TSampler,UV-float2(0,e.y)).rgb-Texture2DSample(T,TSampler,UV+float2(0,e.y)).rgb,float3(.3,.59,.11));return normalize(float3(gx*.6,-gy*.6,1));''',['UV','T']);link(ruv,'',rn,'UV');link(rt,'',rn,'T')
n=custom('''float2 flip=1-2*(floor(UV)-2*floor(floor(UV)/2));float2 q=G.xy*flip;
float2 xy=float2(q.x*.9563+q.y*.2924,-q.x*.2924+q.y*.9563)*.65*(1-.65*M.y);
return normalize(lerp(R,normalize(float3(xy,max(.35,G.z))),M.x));''',['G','R','M','UV']);link(gn,'RGB',n,'G');link(rn,'',n,'R');link(mask,'',n,'M');link(guv,'',n,'UV');L.connect_material_property(n,'',u.MaterialProperty.MP_NORMAL)
rough=custom('return lerp(.92,.91,M.x);',['M'],u.CustomMaterialOutputType.CMOT_FLOAT1);link(mask,'',rough,'M');L.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
spec=node(u.MaterialExpressionConstant);spec.set_editor_property('r',.16);L.connect_material_property(spec,'',u.MaterialProperty.MP_SPECULAR)
L.recompile_material(m)
a=es.spawn_actor_from_class(u.StaticMeshActor,V());a.set_actor_label('GravelToRoadTransition_01_2m_x_4m_BridgeExit');a.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'));a.set_actor_scale3d(V(2,4,1));a.static_mesh_component.set_material(0,m)
sun=es.spawn_actor_from_class(u.DirectionalLight,V(0,0,500),u.Rotator(pitch=-48,yaw=-35));sun.light_component.set_editor_property('intensity',3.0);sun.light_component.set_editor_property('light_source_angle',4)
sky=es.spawn_actor_from_class(u.SkyLight,V(0,0,500));sky.light_component.set_editor_property('intensity',.5);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EngineResources/DefaultTextureCube'));sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
pp=es.spawn_actor_from_class(u.PostProcessVolume,V());pp.set_editor_property('unbound',True);settings=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',0),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_bloom_intensity',True),('bloom_intensity',0)]:settings.set_editor_property(k,v)
pp.set_editor_property('settings',settings)
for name,target,off in [('01-overhead',(0,0,0),(0,0,1050)),('02-low-oblique',(0,0,0),(85,-520,235)),('03-gameplay',(0,0,0),(1100,-1600,1800))]:
 target=V(*target);cam=es.spawn_actor_from_class(u.CameraActor,target+V(*off));cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False);cam.set_actor_label('GravelToRoadTransition01_'+name);cam.camera_component.set_field_of_view(45);cam.camera_component.set_editor_property('post_process_blend_weight',0)
 if name=='01-overhead':cam.set_actor_rotation(u.Rotator(pitch=-90,yaw=-90),False)
u.EditorAssetLibrary.save_directory(D);le.save_current_level();es.clear_actor_selection_set();le.editor_set_viewport_realtime(True)
exec((R/'SourceArt/Environment/Ground/GravelToRoadTransition01/Scripts/capture_unreal.py').read_text(),{'__name__':'__main__'})
