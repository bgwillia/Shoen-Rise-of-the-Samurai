"""One authored environment pass using native Unreal spline-mesh actors. Run in editor."""
import unreal as u, math, json, traceback, time
from pathlib import Path
ROOT=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai')
OUT=ROOT/'artifacts/roadspaths01'; DEST='/Game/Art/Environment/RoadsPaths01'
V=u.Vector; SPACE=u.SplineCoordinateSpace.WORLD

def run():
 global world, actors, land, ignore, subsystem
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 world=u.EditorLoadingAndSavingUtils.load_map(str(ROOT/'game/Content/Art/Environment/TerrainBase01/TerrainBase_01.umap'))
 subsystem=u.get_editor_subsystem(u.EditorActorSubsystem)
 actors=subsystem.get_all_level_actors();land=next(x for x in actors if isinstance(x,u.Landscape));ignore=[x for x in actors if x!=land]
 for a in actors:
  if str(a.get_folder_path()).startswith('RoadsPaths_01'):subsystem.destroy_actor(a)
 actors=subsystem.get_all_level_actors();ignore=[x for x in actors if x!=land]
 u.EditorAssetLibrary.make_directory(DEST)
 mat={k:material(k,tex,col) for k,tex,col in [('main','dirt_aerial_03',(.84,.70,.51)),('village','dirt_aerial_03',(.66,.55,.40)),('farm','brown_mud_02',(.53,.45,.34)),('gravel','gravel_ground_01',(.85,.79,.66))]}
 wood=solid('WeatheredTimber',(.18,.105,.055));fillmat=solid('PackedApproachFill',(.32,.25,.16))
 plane=u.load_asset('/Engine/BasicShapes/Plane');cube=u.load_asset('/Engine/BasicShapes/Cube')
 layout=json.loads((ROOT/'SourceArt/Environment/RoadsPaths01/layout.json').read_text())
 bridge=layout['bridge']; bx,by=bridge['center'];dx,dy=bridge['direction'];mag=math.hypot(dx,dy);dx/=mag;dy/=mag
 half=bridge['length']/2
 deck=max(height((bx-dx*half)*100,(by-dy*half)*100),height((bx+dx*half)*100,(by+dy*half)*100),560)+55
 stats=[]
 for route in layout['routes']:
  pts=catmull(route['points']); distances=[]; max_grade=0
  for i,(p,q) in enumerate(zip(pts,pts[1:])):
   x,y=p;xx,yy=q;cx=(x+xx)/2;cy=(y+yy)/2
   along=(cx-bx)*dx+(cy-by)*dy;side=abs((cx-bx)*dy-(cy-by)*dx)
   if route['kind']=='main' and abs(along)<half and side<3:continue
   width=route['width']*(1+.045*math.sin(i*.73))
   if route['name']=='Village_FordLumberBranch':width+=3.1*math.exp(-((cx+236)**2+(cy+63)**2)/160)
   z1=roadheight(x,y,route,bridge,deck,dx,dy);z2=roadheight(xx,yy,route,bridge,deck,dx,dy)
   delta=V((xx-x)*100,(yy-y)*100,z2-z1);length=math.hypot(delta.x,delta.y)
   grade=math.degrees(math.atan2(abs(z2-z1),length));max_grade=max(max_grade,grade)
   a=subsystem.spawn_actor_from_class(u.SplineMeshActor,V(x*100,y*100,z1))
   a.set_actor_label(f"RP01_{route['name']}_{i:03d}");a.set_folder_path('RoadsPaths_01/'+route['kind'])
   c=a.get_component_by_class(u.SplineMeshComponent);c.set_static_mesh(plane);c.set_material(0,mat['gravel'] if route['name']=='Village_FordLumberBranch' and math.hypot(cx+236,cy+63)<14 else mat[route['kind']]);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
   c.set_start_and_end(V(0,0,0),delta,delta,delta,False)
   c.set_start_scale(u.Vector2D(width,1),False);c.set_end_scale(u.Vector2D(width,1),False)
   # Cross slope aligns the full road width to the existing landscape.
   nx=-delta.y/length;ny=delta.x/length
   for ex,ey,setter in [(x,y,c.set_start_roll),(xx,yy,c.set_end_roll)]:
    cross=(height(ex*100+nx*width*50,ey*100+ny*width*50)-height(ex*100-nx*width*50,ey*100-ny*width*50))/(width*100)
    setter(math.atan(cross),False)
   c.set_cast_shadow(False);c.update_mesh();distances.append(length/100)
   if route['kind']=='main' and abs(along)<half+18 and side<7:
    ground=height(cx*100,cy*100);top=(z1+z2)/2
    if top-ground>12:
     fill=subsystem.spawn_actor_from_class(u.SplineMeshActor,V(x*100,y*100,z1-(top-ground)/2-3));fill.set_actor_label('RP01_BridgeApproachFill_'+str(i));fill.set_folder_path('RoadsPaths_01/TimberBridge_01');fc=fill.get_component_by_class(u.SplineMeshComponent);fc.set_static_mesh(cube);fc.set_material(0,fillmat);fc.set_start_and_end(V(0,0,0),delta,delta,delta,False);fc.set_start_scale(u.Vector2D(width,(top-ground)/100),False);fc.set_end_scale(u.Vector2D(width,(top-ground)/100),True);fc.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
  stats.append({'route':route['name'],'width_m':route['width'],'length_m':round(sum(distances),1),'max_grade_degrees':round(max_grade,1)})
 def timber(label,x,y,z,sx,sy,sz,yaw):
  a=subsystem.spawn_actor_from_class(u.StaticMeshActor,V(x,y,z),u.Rotator(pitch=0,yaw=yaw,roll=0));a.set_actor_label('TimberBridge_01_'+label);a.set_folder_path('RoadsPaths_01/TimberBridge_01')
  c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,wood);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_scale3d(V(sx/100,sy/100,sz/100))
 def bpos(t,side,z):return (bx*100+dx*t-dy*side,by*100+dy*t+dx*side,z)
 yaw=math.degrees(math.atan2(dy,dx))
 for i in range(math.ceil(bridge['length']*100/28)):
  t=-half*100+(i+.5)*28
  timber('Deck_%03d'%i,*bpos(t,0,deck-10),26,bridge['width']*100,20,yaw)
 for side in [-135,135]:timber('LongBeam'+str(side),*bpos(0,side,deck-40),bridge['length']*100,24,45,yaw)
 for i,t in enumerate(range(-1600,1601,400)):
  for side in [-155,155]:
   x,y,_=bpos(t,side,0);base=height(x,y)-80
   timber(f'Pier_{i}_{side}',x,y,(base+deck-20)/2,28,28,deck-20-base,yaw)
   timber(f'RailPost_{i}_{side}',*bpos(t,side,deck+48),14,14,110,yaw)
 for side in [-155,155]:
  for z in [deck+50,deck+100]:timber('Rail'+str(side)+str(z),*bpos(0,side,z),bridge['length']*100,12,13,yaw)
 # One shallow gravel crossing at the actual lower tributary, no bridge.
 # Reusable stones sit in and beside the water, avoiding a dry slab over it.
 stone=u.load_asset('/Engine/BasicShapes/Sphere')
 for i in range(42):
  t=(i%14-6.5)*95;side=(i//14-1)*135+35*math.sin(i*2.1)
  x=-23600+.42*t+.91*side;y=-6300+.91*t-.42*side
  stream=next(a for a in actors if a.get_actor_label()=='WaterBase_01_Tributary').get_water_spline()
  z=max(height(x,y)+12,stream.find_location_closest_to_world_location(V(x,y,600),SPACE).z-10)
  a=subsystem.spawn_actor_from_class(u.StaticMeshActor,V(x,y,z));a.set_actor_label(f'RP01_FordGravel_{i:02d}');a.set_folder_path('RoadsPaths_01/ShallowFord_01')
  a.static_mesh_component.set_static_mesh(stone);a.static_mesh_component.set_material(0,mat['gravel']);a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_scale3d(V(.65+.2*math.sin(i),.5,.16))
 (OUT/'layout-check.json').write_text(json.dumps({'routes':stats,'bridge_deck_cm':deck,'buildings_present':any('Building' in x.get_class().get_name() for x in actors),'note':layout['note']},indent=2))
 u.EditorAssetLibrary.save_directory(DEST)
 assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Art/Environment/TerrainBase01/TerrainBase_01')
 capture(bx,by,deck)

def height(x,y):
 x=max(-74900,min(74900,x));y=max(-74900,min(74900,y))
 hit=u.SystemLibrary.line_trace_single(world,V(x,y,20000),V(x,y,-5000),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,u.DrawDebugTrace.NONE,True).to_tuple()
 if not hit[0]:raise RuntimeError('No terrain '+str((x,y)))
 return hit[5].z

def roadheight(x,y,route,b,deck,dx,dy):
 h=height(x*100,y*100)+14
 if route['kind']=='main':
  along=(x-b['center'][0])*dx+(y-b['center'][1])*dy;side=abs((x-b['center'][0])*dy-(y-b['center'][1])*dx)
  if side<7:
   t=max(0,min(1,(abs(along)-b['length']/2)/18));t=t*t*(3-2*t)
   h=deck*(1-t)+h*t
 if route['name']=='Village_FordLumberBranch' and math.hypot(x+236,y+63)<12:
  stream=next(a for a in actors if a.get_actor_label()=='WaterBase_01_Tributary').get_water_spline()
  water=stream.find_location_closest_to_world_location(V(x*100,y*100,h),SPACE).z
  h=max(h,water-12)
 return h

def catmull(points):
 out=[]
 for i in range(len(points)-1):
  p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(len(points)-1,i+2)]
  steps=max(2,math.ceil(math.dist(p1,p2)/3))
  for k in range(steps):
   t=k/steps
   out.append([.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t*t+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t*t*t) for j in range(2)])
 return out+[points[-1]]

def solid(name,color):
 m=u.load_asset(DEST+'/M_RP01_'+name)
 if m:return m
 m=u.AssetToolsHelpers.get_asset_tools().create_asset('M_RP01_'+name,DEST,u.Material,u.MaterialFactoryNew())
 e=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant3Vector);e.set_editor_property('constant',u.LinearColor(*color,1));u.MaterialEditingLibrary.connect_material_property(e,'',u.MaterialProperty.MP_BASE_COLOR)
 r=u.MaterialEditingLibrary.create_material_expression(m,u.MaterialExpressionConstant);r.set_editor_property('r',.9);u.MaterialEditingLibrary.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS);u.MaterialEditingLibrary.recompile_material(m);return m

def material(kind,texture,tint):
 m=u.load_asset(DEST+'/M_RP01_'+kind)
 if m:
  u.MaterialEditingLibrary.delete_all_material_expressions(m)
 else:m=u.AssetToolsHelpers.get_asset_tools().create_asset('M_RP01_'+kind,DEST,u.Material,u.MaterialFactoryNew())
 lib=u.MaterialEditingLibrary
 def node(cls):return lib.create_material_expression(m,cls)
 def link(a,o,b,i):lib.connect_material_expressions(a,o,b,i)
 pos=node(u.MaterialExpressionWorldPosition);mask=node(u.MaterialExpressionComponentMask);mask.set_editor_property('r',True);mask.set_editor_property('g',True);link(pos,'',mask,'')
 scale=node(u.MaterialExpressionMultiply);scale.set_editor_property('const_b',.0025);link(mask,'',scale,'A')
 tex=node(u.MaterialExpressionTextureSample);tex.set_editor_property('texture',u.load_asset('/Game/Art/Environment/WaterBase01/Textures/'+texture+'_diff_2k'));link(scale,'',tex,'UVs')
 col=node(u.MaterialExpressionConstant3Vector);col.set_editor_property('constant',u.LinearColor(*tint,1));mul=node(u.MaterialExpressionMultiply);link(tex,'RGB',mul,'A');link(col,'',mul,'B');lib.connect_material_property(mul,'',u.MaterialProperty.MP_BASE_COLOR)
 rough=node(u.MaterialExpressionConstant);rough.set_editor_property('r',.95);lib.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
 # Feathered irregular mask retains a solid centre and breaks up the outer 15%.
 uv=node(u.MaterialExpressionTextureCoordinate);ym=node(u.MaterialExpressionComponentMask);ym.set_editor_property('r',False);ym.set_editor_property('g',True);link(uv,'',ym,'')
 sub=node(u.MaterialExpressionSubtract);sub.set_editor_property('const_b',.5);link(ym,'',sub,'A');ab=node(u.MaterialExpressionAbs);link(sub,'',ab,'')
 noise=node(u.MaterialExpressionMultiply);noise.set_editor_property('const_b',.16);link(tex,'R',noise,'A');add=node(u.MaterialExpressionAdd);add.set_editor_property('const_b',.37);link(noise,'',add,'A');edge=node(u.MaterialExpressionSubtract);link(add,'',edge,'A');link(ab,'',edge,'B');lib.connect_material_property(edge,'',u.MaterialProperty.MP_OPACITY_MASK)
 m.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);m.set_editor_property('opacity_mask_clip_value',.001);m.set_editor_property('two_sided',True);lib.recompile_material(m);return m

def capture(bx,by,deck):
 u.SystemLibrary.execute_console_command(world,'Slate.bAllowThrottling 0');u.SystemLibrary.execute_console_command(world,'t.IdleWhenNotForeground 0')
 names=['overview','top-down','strategy','low-oblique','bridge','ford'];cams=[]
 for name in names[:4]:
  old=next(x for x in actors if x.get_actor_label()=='TerrainBase_01_'+name)
  loc,target=({'overview':((100000,100000,155000),(0,0,0)),'strategy':((31000,6000,23000),(12000,-18000,1300))}.get(name,(None,None)))
  if loc:
   cam=subsystem.spawn_actor_from_class(u.CameraActor,V(*loc),u.MathLibrary.find_look_at_rotation(V(*loc),V(*target)));cam.set_actor_label('RoadsPaths_01_'+name);cam.set_folder_path('RoadsPaths_01/Cameras');cams.append(cam)
  else:cams.append(old)
 for name,loc,target in [('bridge',(bx*100+3400,by*100+3900,deck+2600),(bx*100,by*100,deck)),('ford',(-20500,-2700,2600),(-23600,-6300,650))]:
  c=subsystem.spawn_actor_from_class(u.CameraActor,V(*loc),u.MathLibrary.find_look_at_rotation(V(*loc),V(*target)));c.set_actor_label('RoadsPaths_01_'+name);c.set_folder_path('RoadsPaths_01/Cameras');cams.append(c)
 u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Art/Environment/TerrainBase01/TerrainBase_01')
 u.AutomationLibrary.finish_loading_before_screenshot();state={'i':0,'task':None,'next':time.monotonic()+5}
 def tick(dt):
  if state.get('busy'):return
  state['busy']=True
  try:
   if state['task'] is not None:
    if not (OUT/(names[state['i']]+'.png')).exists():return
    state.update(i=state['i']+1,task=None,next=time.monotonic()+2)
   if state['i']==len(names):u.unregister_slate_post_tick_callback(state['handle']);u.SystemLibrary.quit_editor();return
   if time.monotonic()>=state['next']:
    i=state['i'];state['task']=u.AutomationLibrary.take_high_res_screenshot(1920,1200,str(OUT/(names[i]+'.png')),camera=cams[i],delay=1)
  finally:state['busy']=False
 state['handle']=u.register_slate_post_tick_callback(tick)
try:run()
except Exception:u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
