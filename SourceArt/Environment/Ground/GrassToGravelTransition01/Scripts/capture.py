import unreal as u,time
from pathlib import Path
out=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/grasstograveltransition01')
cams=sorted([a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.CameraActor)],key=lambda a:a.get_actor_label())
state={'i':0,'next':time.monotonic()+6}
def patch_tick(dt):
 if state.get('busy'):return
 state['busy']=True
 try:
  if time.monotonic()<state['next']:return
  if state['i']>=len(cams):
   u.unregister_slate_post_tick_callback(state['handle']);out.joinpath('complete.txt').write_text('Two Unreal Metal views captured.');return
  c=cams[state['i']];u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(out/(c.get_actor_label()+'.png')),camera=c,delay=1)
  state['i']+=1;state['next']=time.monotonic()+8
 finally:state['busy']=False
state['handle']=u.register_slate_post_tick_callback(patch_tick)
