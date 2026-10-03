import unreal as u,time
from pathlib import Path
fw_out=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/landcrossingwater01')/globals().get('fw_pass','final');fw_out.mkdir(exist_ok=True,parents=True)
fw_cams=sorted([a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('RiverEdge_01_')],key=lambda a:a.get_actor_label())
fw_state={'i':0,'next':time.monotonic()+3,'pending':False}
def ford_capture_tick(dt):
 if fw_state.get('busy'):return
 fw_state['busy']=True
 try:
  i=fw_state['i']
  if fw_state['pending']:
   if not fw_state['path'].exists():return
   fw_state.update(i=i+1,pending=False,next=time.monotonic()+1);i+=1
  if i>=len(fw_cams):
   u.unregister_slate_post_tick_callback(fw_state['handle']);return
  if time.monotonic()>=fw_state['next']:
   c=fw_cams[i];p=fw_out/(c.get_actor_label().replace('RiverEdge_01_','')+'.png');p.unlink(missing_ok=True);u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(p),camera=c,delay=1);fw_state.update(pending=True,path=p)
 finally:fw_state['busy']=False
fw_state['handle']=u.register_slate_post_tick_callback(ford_capture_tick)
