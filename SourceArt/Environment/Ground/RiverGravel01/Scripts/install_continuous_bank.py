import unreal as u,math,json
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/RiverGravel01';L=u.MaterialEditingLibrary;V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
t=u.AssetImportTask();t.filename=str(R/'SourceArt/Environment/Ground/RiverGravel01/Exports/RiverGravel01_ContinuousBank.fbx');t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True
opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS;opt.static_mesh_import_data.vertex_color_import_option=u.VertexColorImportOption.REPLACE;t.options=opt;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
mesh=u.load_asset(D+'/RiverGravel01_ContinuousBank')
m=u.load_asset(D+'/M_RiverGravel01_Continuous') or u.AssetToolsHelpers.get_asset_tools().create_asset('M_RiverGravel01_Continuous',D,u.Material,u.MaterialFactoryNew());L.delete_all_material_expressions(m);m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('tangent_space_normal',False)
def node(c):return L.create_material_expression(m,c)
def link(a,out,b,i):
 if not L.connect_material_expressions(a,out,b,i):raise RuntimeError('Connection failed '+i)
def custom(code,names,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);inputs=[]
 for name in names:
  e=u.CustomInput();e.set_editor_property('input_name',name);inputs.append(e)
 n.set_editor_property('inputs',inputs);return n
p=node(u.MaterialExpressionWorldPosition);uv=custom('return float2(W.x*.9563-W.y*.2924,W.x*.2924+W.y*.9563)/78.0;',['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,'',uv,'W')
a=node(u.MaterialExpressionTextureSample);a.set_editor_property('texture',u.load_asset(D+'/T_RiverGravel01_BaseColor'));link(uv,'',a,'UVs')
color=custom('float wet=(1-smoothstep(635,699,W.z+3*sin(W.x*.031)*sin(W.y*.022)))*.65;float macro=1+.035*sin(W.x*.007+sin(W.y*.005))+.02*sin(W.y*.013);return lerp(float3(.245,.203,.164),C,.78)*macro*(1-wet*.24);',['C','W']);link(a,'RGB',color,'C');link(p,'',color,'W');L.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
n=node(u.MaterialExpressionTextureSample);n.set_editor_property('texture',u.load_asset(D+'/T_RiverGravel01_Normal'));n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL);link(uv,'',n,'UVs')
geo=node(u.MaterialExpressionVertexNormalWS);normal=custom('float2 q=N.xy;float2 xy=float2(q.x*.9563+q.y*.2924,-q.x*.2924+q.y*.9563)*.65;float3 z=normalize(G);float3 x=normalize(float3(1,0,0)-z*z.x);float3 y=cross(z,x);return normalize(x*xy.x+y*xy.y+z*max(.35,N.z));',['N','G','UV']);link(n,'RGB',normal,'N');link(geo,'',normal,'G');link(uv,'',normal,'UV');L.connect_material_property(normal,'',u.MaterialProperty.MP_NORMAL)
rough=custom('return .91-(1-smoothstep(635,699,W.z))*.143;',['W'],u.CustomMaterialOutputType.CMOT_FLOAT1);link(p,'',rough,'W');L.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
vc=node(u.MaterialExpressionVertexColor);dither=node(u.MaterialExpressionMaterialFunctionCall);dither.set_editor_property('material_function',u.load_asset('/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA'));L.update_material_function(dither.get_editor_property('material_function'))
link(vc,'A',dither,'Alpha Threshold');L.connect_material_property(dither,'',u.MaterialProperty.MP_OPACITY_MASK);L.recompile_material(m)
mesh.set_material(0,m);aa=es.get_all_level_actors();bank=next((a for a in aa if a.get_actor_label()=='RiverGravel01_ContinuousBank'),None) or es.spawn_actor_from_class(u.StaticMeshActor,V(-23600,-6300,650));bank.set_actor_label('RiverGravel01_ContinuousBank');bank.set_folder_path('RiverGravel01');bank.static_mesh_component.set_static_mesh(mesh);bank.static_mesh_component.set_material(0,m);bank.static_mesh_component.set_cast_shadow(False);bank.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
# Retain the original strips for reversible authoring; only the continuous bank renders.
for a in aa:
 if a.get_actor_label().startswith('RP01_SubmergedGravelBed_'):
  a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True);a.get_component_by_class(u.SplineMeshComponent).set_visibility(False);a.set_folder_path('RiverGravel01/OriginalFordStrips')
 if a.get_actor_label().startswith('RiverGravel01_ReviewFragment_') or a.get_actor_label()=='RiverGravel_01_1mReviewPatch':
  a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
u.EditorAssetLibrary.save_directory(D);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
Path('/tmp/gravel-continuous-installed.txt').write_text(str(mesh.get_bounds())+'\n'+str(bank.get_actor_bounds(False)))
# Actual rendered bank views, without recapturing the isolated texture swatch.
O=R/'artifacts/rivergravel01/seam-repair';O.mkdir(exist_ok=True)
views=[('continuous-wide',V(-23530,-6610,700),V(700,-1800,2200)),('continuous-close',V(-23580,-6570,694),V(160,-370,245)),('continuous-low',V(-23710,-6500,680),V(140,-530,90)),('continuous-outer-edge',V(-23900,-7010,765),V(100,-620,490))]
import time
cams=[]
for name,target,off in views:
 cam=es.spawn_actor_from_class(u.CameraActor,target+off);cam.set_actor_label('RiverGravel01_'+name);cam.set_folder_path('RiverGravel01/SeamReview');cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False);cam.camera_component.set_field_of_view(45);cams.append(cam)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level();st={'i':0,'next':time.monotonic()+8,'pending':False}
def seam_tick(dt):
 if st.get('busy'):return
 st['busy']=True
 try:
  i=st['i']
  if st['pending']:
   if not st['path'].exists():return
   st.update(i=i+1,pending=False,next=time.monotonic()+3);i+=1
  if i==len(cams):u.unregister_slate_post_tick_callback(st['handle']);return
  if time.monotonic()>=st['next']:
   path=O/(views[i][0]+'.png');u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera=cams[i],delay=1);st.update(path=path,pending=True)
 finally:st['busy']=False
st['handle']=u.register_slate_post_tick_callback(seam_tick)
