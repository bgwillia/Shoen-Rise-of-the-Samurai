import unreal as u,time
from pathlib import Path
GTRO=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/graveltoroadtransition01')
gtr_es=u.get_editor_subsystem(u.EditorActorSubsystem);gtr_cams=sorted([a for a in gtr_es.get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('GravelToRoadTransition01_')],key=lambda a:a.get_actor_label())
gtr_state={'i':0,'next':time.monotonic()+4,'pending':False}
def gtr_tick(dt):
 if gtr_state.get('busy'):return
 gtr_state['busy']=True
 try:
  i=gtr_state['i']
  if gtr_state['pending']:
   if not gtr_state['path'].exists():return
   gtr_state.update(i=i+1,pending=False,next=time.monotonic()+2);i+=1
  if i>=len(gtr_cams):
   u.unregister_slate_post_tick_callback(gtr_state['handle']);GTRO.joinpath('captures-complete.txt').write_text('Three rendered transition views.');return
  if time.monotonic()>=gtr_state['next']:
   c=gtr_cams[i];path=GTRO/(c.get_actor_label().replace('GravelToRoadTransition01_','')+'.png');path.unlink(missing_ok=True)
   u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera=c,delay=1);gtr_state.update(pending=True,path=path)
 finally:gtr_state['busy']=False
gtr_state['handle']=u.register_slate_post_tick_callback(gtr_tick)
