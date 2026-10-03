"""Road-specific visual revision: landscape-integrated surfaces and finished crossings."""
import unreal as u,math,time,json,traceback,random
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');S=R/'SourceArt/Environment/RoadsPaths01';O=R/'artifacts/roadspaths01/revision';D='/Game/Art/Environment/RoadsPaths01';L=u.MaterialEditingLibrary;V=u.Vector

def run():
 global w,a,actors,land,ignore
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 w=u.EditorLoadingAndSavingUtils.load_map(str(R/'game/Content/Art/Environment/TerrainBase01/TerrainBase_01.umap'));a=u.get_editor_subsystem(u.EditorActorSubsystem);actors=a.get_all_level_actors();land=next(x for x in actors if isinstance(x,u.Landscape));ignore=[x for x in actors if x!=land]
 tasks=[]
 for f in [S/'RoadsPaths_01_surface-mask.png']+list((S/'Exports').glob('*.fbx')):
  t=u.AssetImportTask();t.filename=str(f);t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True
  if f.suffix=='.fbx':
   opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.combine_meshes=True;t.options=opt
  tasks.append(t)
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
 tex=u.load_asset(D+'/RoadsPaths_01_surface_mask') or u.load_asset(D+'/RoadsPaths_01_surface-mask')
 if not tex:
  tex=u.load_asset(tasks[0].imported_object_paths[0])
 tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS);tex.set_editor_property('max_texture_size',8192);tex.set_editor_property('address_x',u.TextureAddress.TA_CLAMP);tex.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
 terrain=u.EditorAssetLibrary.duplicate_asset('/Game/Art/Environment/TerrainBase01/M_TerrainBase_01',D+'/M_RP01_LandscapeSurface')
 if terrain is None:terrain=u.load_asset(D+'/M_RP01_LandscapeSurface')
 base=L.get_material_property_input_node(terrain,u.MaterialProperty.MP_BASE_COLOR);baseout=L.get_material_property_input_node_output_name(terrain,u.MaterialProperty.MP_BASE_COLOR)
 oldnormal=L.get_material_property_input_node(terrain,u.MaterialProperty.MP_NORMAL)
 pos=node(terrain,u.MaterialExpressionWorldPosition);xy=node(terrain,u.MaterialExpressionComponentMask);xy.set_editor_property('r',True);xy.set_editor_property('g',True);connect(pos,'',xy,'')
 uv=custom(terrain,'return W/150000.0+0.5;',['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);connect(xy,'',uv,'W')
 weights=sample(terrain,tex,uv)
 dirtuv=custom(terrain,'return W/320.0;',['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);connect(xy,'',dirtuv,'W')
 dirt=sample(terrain,watertex('dirt_aerial_03_diff_2k'),dirtuv);gravel=sample(terrain,watertex('gravel_ground_01_diff_2k'),dirtuv);mud=sample(terrain,watertex('brown_mud_02_diff_2k'),dirtuv)
 finish=custom(terrain,'''float3 packed=lerp(Dirt*float3(.58,.57,.55),Gravel*.52,.16);
 packed*=1.0-Ruts*.13;
 float3 worn=lerp(Dirt*float3(.50,.48,.43),packed,.32);
 float3 soft=lerp(Dirt*.38,Mud*.95,.58);
 float3 c=lerp(Base,soft,Weights.b*.82);
 c=lerp(c,worn,Weights.g*.9);
 return lerp(c,packed,Weights.r*.94);''',['Base','Dirt','Gravel','Mud','Weights','Ruts'])
 for n,out,key in [(base,baseout,'Base'),(dirt,'RGB','Dirt'),(gravel,'RGB','Gravel'),(mud,'RGB','Mud'),(weights,'RGB','Weights'),(weights,'A','Ruts')]:connect(n,out,finish,key)
 L.connect_material_property(finish,'',u.MaterialProperty.MP_BASE_COLOR)
 dn=sample(terrain,watertex('dirt_aerial_03_nor_dx_2k'),dirtuv,True)
 norm=custom(terrain,'return normalize(lerp(Base,Detail,saturate(max(Weights.r,max(Weights.g,Weights.b)))*.55));',['Base','Detail','Weights'])
 connect(oldnormal,'',norm,'Base');connect(dn,'RGB',norm,'Detail');connect(weights,'RGB',norm,'Weights');L.connect_material_property(norm,'',u.MaterialProperty.MP_NORMAL);L.recompile_material(terrain);land.set_editor_property('landscape_material',terrain)
 wood=u.load_asset('/Game/Art/Buildings/Rural/RuralHouse01/M_RH01_Timber');stone=u.load_asset('/Game/Art/Buildings/Rural/RuralHouse01/M_RH01_Stone')
 approachmat=surface_material('M_RP01_EarthApproach','dirt_aerial_03',(.58,.57,.55));gravelmat=surface_material('M_RP01_FordBed','gravel_ground_01',(.62,.65,.64))
 rng=random.Random(1180);ramps=[]
 for actor in actors:
  label=actor.get_actor_label();folder=str(actor.get_folder_path())
  if not folder.startswith('RoadsPaths_01'):continue
  c=actor.get_component_by_class(u.SplineMeshComponent)
  if c and label.startswith('RP01_MainRoad'):
   loc=actor.get_actor_location();end=c.get_end_position();mid=loc+end*.5
   along=(mid.x+8728.7)*.97664+(mid.y+25000)*.21486
   if 1750<abs(along)<3750:ramps.append((loc,end))
  if c:
   # Keep original native splines editable but remove their floating strips from rendering.
   c.set_visibility(False);actor.set_actor_hidden_in_game(True);actor.set_editor_property('is_editor_only_actor',True);actor.set_folder_path('RoadsPaths_01/AuthoringSplines')
  if label.startswith('TimberBridge_01_'):
   kind='Plank' if '_Deck_' in label else 'Rail' if '_Rail' in label and '_RailPost' not in label else 'Post' if '_Pier_' in label or '_RailPost' in label else 'Beam'
   actor.static_mesh_component.set_static_mesh(u.load_asset(D+'/RP01_'+kind));actor.static_mesh_component.set_material(0,wood)
   if kind=='Plank':
    sc=actor.get_actor_scale3d();sc.x*=rng.uniform(.96,1.01);actor.set_actor_scale3d(sc);rot=actor.get_actor_rotation();rot.roll+=rng.uniform(-.18,.18);actor.set_actor_rotation(rot,False)
  if label.startswith('RP01_FordGravel_'):
   actor.static_mesh_component.set_material(0,stone);sc=actor.get_actor_scale3d();actor.set_actor_scale3d(V(sc.x*rng.uniform(.7,1.3),sc.y*rng.uniform(.7,1.3),sc.z*rng.uniform(.8,1.5)))
 for i,(loc,end) in enumerate(ramps):
  # A broad sloped shoulder intersects the ground instead of exposing a vertical block wall.
  start=V(loc.x,loc.y,loc.z-10);finish=start+end;h0=max(4,start.z-height(start.x,start.y)+22);h1=max(4,finish.z-height(finish.x,finish.y)+22)
  act=a.spawn_actor_from_class(u.SplineMeshActor,start);act.set_actor_label('RP01_GradedEarthApproach_'+str(i));act.set_folder_path('RoadsPaths_01/TimberBridge_01');c=act.get_component_by_class(u.SplineMeshComponent);c.set_static_mesh(u.load_asset(D+'/RP01_Approach'));c.set_material(0,approachmat);c.set_start_and_end(V(0,0,0),end,end,end,False);c.set_start_scale(u.Vector2D(1.1,h0/300),False);c.set_end_scale(u.Vector2D(1.1,h1/300),True);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
 # Timber cross-braces below the deck, a readable load path between paired piers.
 cube=u.load_asset(D+'/RP01_Beam');bx=-8728.7;by=-25000;dx=.97664;dy=.21486
 for i,t in enumerate(range(-1400,1401,400)):
  center=V(bx+dx*t,by+dy*t,500);act=a.spawn_actor_from_class(u.StaticMeshActor,center,u.Rotator(yaw=102.407));act.set_actor_label('TimberBridge_01_CrossBeam_'+str(i));act.set_folder_path('RoadsPaths_01/TimberBridge_01');act.static_mesh_component.set_static_mesh(cube);act.static_mesh_component.set_material(0,wood);act.set_actor_scale3d(V(3.9,.24,.28))
 u.EditorAssetLibrary.save_directory(D);u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Art/Environment/TerrainBase01/TerrainBase_01')
 capture()

def node(m,cls):return L.create_material_expression(m,cls)
def connect(a,o,b,i):
 if not L.connect_material_expressions(a,o,b,i):raise RuntimeError('Material connection '+i)
def custom(m,code,names,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(m,u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);inputs=[]
 for x in names:
  entry=u.CustomInput();entry.set_editor_property('input_name',x);inputs.append(entry)
 n.set_editor_property('inputs',inputs);return n
def watertex(n):return u.load_asset('/Game/Art/Environment/WaterBase01/Textures/'+n)
def sample(m,t,uv,normal=False):
 n=node(m,u.MaterialExpressionTextureSample);n.set_editor_property('texture',t)
 if normal:n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
 elif not t.get_editor_property('srgb'):n.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_MASKS)
 connect(uv,'',n,'UVs');return n
def height(x,y):
 h=u.SystemLibrary.line_trace_single(w,V(x,y,20000),V(x,y,-5000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True).to_tuple();return h[5].z

def surface_material(name,tex,tint):
 m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,D,u.Material,u.MaterialFactoryNew())
 if m is None:m=u.load_asset(D+'/'+name);L.delete_all_material_expressions(m)
 p=node(m,u.MaterialExpressionWorldPosition);uv=custom(m,'return W.xy/320.0;',['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);connect(p,'',uv,'W');t=sample(m,watertex(tex+'_diff_2k'),uv);c=custom(m,'return T*float3'+str(tint)+';',['T']);connect(t,'RGB',c,'T');L.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 n=sample(m,watertex(tex+'_nor_dx_2k'),uv,True);L.connect_material_property(n,'RGB',u.MaterialProperty.MP_NORMAL);rough=node(m,u.MaterialExpressionConstant);rough.set_editor_property('r',.92);L.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS);L.recompile_material(m);return m

def capture():
 u.SystemLibrary.execute_console_command(w,'Slate.bAllowThrottling 0');u.SystemLibrary.execute_console_command(w,'t.IdleWhenNotForeground 0')
 views=[('overview',(46000,22000,67000),(0,-9000,1000)),('strategy',(25000,-8000,16000),(13000,-22000,1900)),('bridge',(-4600,-20800,2550),(-8728,-25000,560)),('ford',(-21400,-3900,2150),(-23600,-6300,650)),('road-detail',(19300,-18700,2350),(17500,-20500,1950))]
 cams=[];names=[]
 for name,loc,target in views:
  c=a.spawn_actor_from_class(u.CameraActor,V(*loc),u.MathLibrary.find_look_at_rotation(V(*loc),V(*target)));c.set_actor_label('RoadsPaths_01_Refined_'+name);c.set_folder_path('RoadsPaths_01/Cameras');cams.append(c);names.append(name)
 for name in ['top-down','low-oblique']:
  cams.append(next(x for x in actors if x.get_actor_label()=='TerrainBase_01_'+name));names.append(name)
 u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(cams[1].get_actor_location(),cams[1].get_actor_rotation());u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Art/Environment/TerrainBase01/TerrainBase_01')
 u.AutomationLibrary.finish_loading_before_screenshot();state={'i':0,'task':None,'next':time.monotonic()+7}
 def tick(dt):
  if state.get('busy'):return
  state['busy']=True
  try:
   if state['task'] is not None:
    if not (O/(names[state['i']]+'.png')).exists():return
    state.update(i=state['i']+1,task=None,next=time.monotonic()+2)
   if state['i']==len(names):u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_editor();return
   if time.monotonic()>=state['next']:
    i=state['i'];state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1200,str(O/(names[i]+'.png')),camera=cams[i],delay=1)
  finally:state['busy']=False
 state['handle']=u.register_slate_post_tick_callback(tick)
try:run()
except:u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
