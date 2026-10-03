import unreal as u,time
from pathlib import Path
def capture_sample_views():
 out=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/soiltograsslandtransition01')
 cams=sorted([a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.CameraActor)],key=lambda a:a.get_actor_label())
 st={'i':0,'next':time.monotonic()+5,'busy':False}
 def tick(dt):
  if st['busy'] or time.monotonic()<st['next']:return
  st['busy']=True
  try:
   if st['i']>=len(cams):u.unregister_slate_post_tick_callback(st['handle']);return
   c=cams[st['i']];u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(out/(c.get_actor_label()+'.png')),camera=c,delay=1)
   st['i']+=1;st['next']=time.monotonic()+7
  finally:st['busy']=False
 st['handle']=u.register_slate_post_tick_callback(tick)
capture_sample_views()
