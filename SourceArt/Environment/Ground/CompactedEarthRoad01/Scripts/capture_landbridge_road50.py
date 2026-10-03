import unreal as u,time
from pathlib import Path
LB50O=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/landbridge-road50')
lb50_es=u.get_editor_subsystem(u.EditorActorSubsystem);lb50_cams=sorted([a for a in lb50_es.get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('LandBridgeRoad50_')],key=lambda a:a.get_actor_label())
lb50_state={'i':0,'next':time.monotonic()+4,'pending':False}
def lb50_tick(dt):
 if lb50_state.get('busy'):return
 lb50_state['busy']=True
 try:
  i=lb50_state['i']
  if lb50_state['pending']:
   if not lb50_state['path'].exists():return
   lb50_state.update(i=i+1,pending=False,next=time.monotonic()+2);i+=1
  if i>=len(lb50_cams):
   u.unregister_slate_post_tick_callback(lb50_state['handle']);LB50O.joinpath('captures-complete.txt').write_text('Two actual rendered Unreal road connection views.');return
  if time.monotonic()>=lb50_state['next']:
   c=lb50_cams[i];path=LB50O/(c.get_actor_label().replace('LandBridgeRoad50_','')+'.png');path.unlink(missing_ok=True)
   u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera=c,delay=1);lb50_state.update(pending=True,path=path)
 finally:lb50_state['busy']=False
lb50_state['handle']=u.register_slate_post_tick_callback(lb50_tick)
