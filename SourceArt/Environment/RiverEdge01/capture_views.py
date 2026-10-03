import unreal as u,time
from pathlib import Path
re_out=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/riveredge01');re_out.mkdir(exist_ok=True)
re_cams=sorted([a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('RiverEdge_01_')],key=lambda a:a.get_actor_label())
re_state={'i':0,'next':time.monotonic()+5,'pending':False}
def riveredge_tick(dt):
 if re_state.get('busy'):return
 re_state['busy']=True
 try:
  i=re_state['i']
  if re_state['pending']:
   if not re_state['path'].exists():return
   re_state.update(i=i+1,pending=False,next=time.monotonic()+2);i+=1
  if i>=len(re_cams):
   u.unregister_slate_post_tick_callback(re_state['handle']);c=re_cams[-1];u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(c.get_actor_location(),c.get_actor_rotation());return
  if time.monotonic()>=re_state['next']:
   c=re_cams[i];p=re_out/(c.get_actor_label().replace('RiverEdge_01_','')+'.png');p.unlink(missing_ok=True);u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(p),camera=c,delay=1);re_state.update(pending=True,path=p)
 finally:re_state['busy']=False
re_state['handle']=u.register_slate_post_tick_callback(riveredge_tick)
