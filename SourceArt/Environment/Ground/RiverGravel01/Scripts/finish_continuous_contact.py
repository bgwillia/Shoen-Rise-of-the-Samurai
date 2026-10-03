import unreal as u,time,math,json
from pathlib import Path
es=u.get_editor_subsystem(u.EditorActorSubsystem);aa=es.get_all_level_actors();world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();V=u.Vector
bank=next(a for a in aa if a.get_actor_label()=='RiverGravel01_ContinuousBank');bank.set_actor_location(V(-23600,-6300,653),False,False)
land=next(a for a in aa if isinstance(a,u.Landscape));ignore=[a for a in aa if a not in [bank,land]];bc=bank.static_mesh_component;bc.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY);bc.set_collision_profile_name('BlockAll')
changes=[]
for a in aa:
 label=a.get_actor_label()
 if not (label.startswith('RP01_FordCobble_') or label.startswith('RiverGravel01_EmbeddedFragment_') or label in ['RiverRock_01','RiverRock_02','RiverRock_03']):continue
 p=a.get_actor_location();side=-(p.x+23600)*.907524+(p.y+6300)*.42;along=(p.x+23600)*.42+(p.y+6300)*.907524
 if abs(side)>440 or abs(along)>1080:continue
 hit=u.SystemLibrary.line_trace_single(world,V(p.x,p.y,20000),V(p.x,p.y,-5000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True).to_tuple();h=hit[5].z;center,ext=a.get_actor_bounds(False);bottom=center.z-ext.z;gap=bottom-h
 if label.startswith('RiverRock'):
  if gap>1:delta=-gap-3
  else:continue
 else:delta=h-bottom-min(1.8,ext.z*.4)
 a.set_actor_location(p+V(0,0,delta),False,False);changes.append([label,round(delta,2)])
bc.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
Path('/tmp/gravel-contact-adjustments.json').write_text(json.dumps(changes))
# Four final render checks, no extra review scene.
O=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/rivergravel01/seam-repair');cs=sorted([a for a in aa if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('RiverGravel01_continuous-')],key=lambda a:a.get_actor_label());ss={'i':0,'next':time.monotonic()+4,'pending':False}
def final_seam_tick(dt):
 if ss.get('busy'):return
 ss['busy']=True
 try:
  i=ss['i']
  if ss['pending']:
   if not ss['path'].exists():return
   ss.update(i=i+1,pending=False,next=time.monotonic()+2);i+=1
  if i==len(cs):
   u.unregister_slate_post_tick_callback(ss['handle']);c=next(a for a in cs if a.get_actor_label().endswith('wide'));u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(c.get_actor_location(),c.get_actor_rotation());return
  if time.monotonic()>=ss['next']:
   c=cs[i];path=O/(c.get_actor_label().replace('RiverGravel01_','')+'.png');path.unlink(missing_ok=True);u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera=c,delay=1);ss.update(path=path,pending=True)
 finally:ss['busy']=False
ss['handle']=u.register_slate_post_tick_callback(final_seam_tick)
