import unreal as u, math, time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai'); D='/Game/Art/Environment/Ground/RiverGravel01'; O=R/'artifacts/rivergravel01'; L=u.MaterialEditingLibrary; V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem); world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(); actors=es.get_all_level_actors(); land=next(a for a in actors if isinstance(a,u.Landscape))
u.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 0')
t=u.AssetImportTask();t.filename=str(R/'SourceArt/Environment/Ground/RiverGravel01/Textures/T_RiverGravel01_BaseColor.png');t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);tex=u.load_asset(D+'/T_RiverGravel01_BaseColor');tex.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO);tex.set_editor_property('address_x',u.TextureAddress.TA_MIRROR);tex.set_editor_property('address_y',u.TextureAddress.TA_MIRROR)
def node(m,c):return L.create_material_expression(m,c)
def link(a,o,b,i):L.connect_material_expressions(a,o,b,i)
def custom(m,code,inputs,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(m,u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ); entries=[]
 for name in inputs:
  e=u.CustomInput();e.set_editor_property('input_name',name);entries.append(e)
 n.set_editor_property('inputs',entries);return n

def gravel(m):
 p=node(m,u.MaterialExpressionWorldPosition); uv=custom(m,'return float2(W.x*.9563-W.y*.2924,W.x*.2924+W.y*.9563)/78.0;',['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,'',uv,'W')
 tx=node(m,u.MaterialExpressionTextureObject);tx.set_editor_property('texture',tex)
 wet=custom(m,'return (1-smoothstep(635.0,699.0,W.z+3*sin(W.x*.031)*sin(W.y*.022)))*.65;',['W'],u.CustomMaterialOutputType.CMOT_FLOAT1);link(p,'',wet,'W')
 color=custom(m,'''float3 c=Texture2DSample(T,TSampler,UV).rgb;
 float lum=dot(c,float3(.3,.59,.11));
 c=lerp(float3(.245,.203,.164),c,.78);
 float macro=1+.035*sin(W.x*.007+sin(W.y*.005))+.02*sin(W.y*.013);
 return c*macro*(1-Wet*.24);''',['T','UV','W','Wet'])
 for src,out,key in [(tx,'','T'),(uv,'','UV'),(p,'','W'),(wet,'','Wet')]:link(src,out,color,key)
 norm=custom(m,'''float e=.0024;
 float l=dot(Texture2DSampleBias(T,TSampler,UV-float2(e,0),1).rgb,float3(.3,.59,.11));
 float r=dot(Texture2DSampleBias(T,TSampler,UV+float2(e,0),1).rgb,float3(.3,.59,.11));
 float d=dot(Texture2DSampleBias(T,TSampler,UV-float2(0,e),1).rgb,float3(.3,.59,.11));
 float b=dot(Texture2DSampleBias(T,TSampler,UV+float2(0,e),1).rgb,float3(.3,.59,.11));
 return normalize(float3((l-r)*2.0,(b-d)*2.0,1));''',['T','UV'])
 link(tx,'',norm,'T');link(uv,'',norm,'UV')
 rough=custom(m,'return .91-Wet*.22;',['Wet'],u.CustomMaterialOutputType.CMOT_FLOAT1);link(wet,'',rough,'Wet')
 return p,color,norm,rough
mat=u.load_asset(D+'/M_RiverGravel_01') or u.AssetToolsHelpers.get_asset_tools().create_asset('M_RiverGravel_01',D,u.Material,u.MaterialFactoryNew());L.delete_all_material_expressions(mat)
p,c,n,r=gravel(mat)
for a,prop in [(c,u.MaterialProperty.MP_BASE_COLOR),(n,u.MaterialProperty.MP_NORMAL),(r,u.MaterialProperty.MP_ROUGHNESS)]:L.connect_material_property(a,'',prop)
L.recompile_material(mat)
base=land.get_editor_property('landscape_material'); terrain=u.load_asset(D+'/M_RiverGravel01_Bank') or u.EditorAssetLibrary.duplicate_asset(base.get_path_name().split('.')[0],D+'/M_RiverGravel01_Bank')
if not terrain:terrain=u.load_asset(D+'/M_RiverGravel01_Bank')
old=[(prop,L.get_material_property_input_node(terrain,prop),L.get_material_property_input_node_output_name(terrain,prop)) for prop in [u.MaterialProperty.MP_BASE_COLOR,u.MaterialProperty.MP_NORMAL,u.MaterialProperty.MP_ROUGHNESS]]
p,c,n,r=gravel(terrain)
mask=custom(terrain,'float2 q=(W.xy-float2(-23530,-6610))/float2(600,500); float edge=length(q)+.025*sin(W.x*.036)*sin(W.y*.028);return 1-smoothstep(.72,1.0,edge);',['W'],u.CustomMaterialOutputType.CMOT_FLOAT1);link(p,'',mask,'W')
for (prop,src,out),new in zip(old,[c,n,r]):
 if not src:continue
 blend=node(terrain,u.MaterialExpressionLinearInterpolate);link(src,out,blend,'A');link(new,'',blend,'B');link(mask,'',blend,'Alpha');L.connect_material_property(blend,'',prop)
L.recompile_material(terrain);land.set_editor_property('landscape_material',terrain)
# Seat the existing approved rocks on the actual bank surface.
rocks=[a for a in actors if a.get_actor_label() in ['RiverRock_01','RiverRock_02']]
ignore=[a for a in actors if a!=land]
def height(x,y):
 hit=u.SystemLibrary.line_trace_single(world,V(x,y,20000),V(x,y,-5000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True).to_tuple();return hit[5].z
# A single 1m authoring swatch, off to the side of the existing bank.
px,py=-23190,-6490;ph=height(px,py)+4
patch=es.spawn_actor_from_class(u.StaticMeshActor,V(px,py,ph));patch.set_actor_label('RiverGravel_01_1mReviewPatch');patch.set_folder_path('RiverGravel01');patch.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'));patch.static_mesh_component.set_material(0,mat)
patch.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
# A few manually placed, mostly buried fragments using the approved low rock mesh.
mesh=u.load_asset('/Game/Art/Environment/Rocks/RiverRock02/RiverRock_02')
for i,(dx,dy,s,yaw) in enumerate([(-95,-28,.14,22),(-32,57,.11,71),(54,-41,.16,145),(128,72,.12,12),(170,-88,.14,51),(-156,90,.12,121),(12,-108,.11,34),(218,4,.15,84),(-202,-64,.13,177),(93,141,.11,18),(290,-40,.13,99),(-82,178,.12,57)]):
 x,y=-23530+dx,-6610+dy;h=height(x,y);a=es.spawn_actor_from_class(u.StaticMeshActor,V(x,y,h-1.8),u.Rotator(yaw=yaw));a.set_actor_label('RiverGravel01_EmbeddedFragment_%02d'%i);a.set_folder_path('RiverGravel01');a.static_mesh_component.set_static_mesh(mesh);a.set_actor_scale3d(V(s,s*.86,s*.8));a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
u.EditorAssetLibrary.save_directory(D);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
# Fixed art-review views in the actual rendered level.
z=height(-23530,-6610);target=V(-23530,-6610,z+12)
views=[('01-overhead-1m',V(px,py,ph),V(0,0,135)),('02-low-oblique',V(px,py,ph),V(30,-115,55)),('03-close-detail',V(-23520,-6650,height(-23520,-6650)),V(24,-64,52)),('04-rocks-embedded',target,V(85,-255,150)),('05-dry-damp-shoreline',target,V(280,-440,310)),('06-strategy',target,V(1100,-1600,1800)),('07-larger-area',target,V(250,-950,1120))]
cams=[]
for name,targ,off in views:
 cam=es.spawn_actor_from_class(u.CameraActor,targ+off);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),targ),False);cam.set_actor_label('RiverGravel01_'+name);cam.set_folder_path('RiverGravel01/ReviewCameras');cam.camera_component.set_field_of_view(45);cams.append(cam)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level();u.SystemLibrary.execute_console_command(world,'Slate.bAllowThrottling 0');u.SystemLibrary.execute_console_command(world,'t.IdleWhenNotForeground 0');u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(cams[3].get_actor_location(),cams[3].get_actor_rotation())
O.joinpath('built.txt').write_text('RiverGravel01 material and localized riverbank application saved.')
