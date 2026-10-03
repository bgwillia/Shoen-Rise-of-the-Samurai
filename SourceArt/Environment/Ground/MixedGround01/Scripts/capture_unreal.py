import unreal as u,time
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_viewport_realtime(True)
from pathlib import Path
SO=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/mixedground01')
mges=u.get_editor_subsystem(u.EditorActorSubsystem);mgcams=sorted([a for a in mges.get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('MixedGround01_')],key=lambda a:a.get_actor_label())
mgstate={'i':0,'next':time.monotonic()+8,'pending':False}
def mg_tick(dt):
 if mgstate.get('busy'):return
 mgstate['busy']=True
 try:
  i=mgstate['i']
  if mgstate['pending']:
   if not mgstate['path'].exists():return
   mgstate.update(i=i+1,pending=False,next=time.monotonic()+2);i+=1
  if i>=len(mgcams):
   u.unregister_slate_post_tick_callback(mgstate['handle']);SO.joinpath('captures-complete.txt').write_text('Five rendered Unreal views.');return
  if time.monotonic()>=mgstate['next']:
   c=mgcams[i];path=SO/(c.get_actor_label().replace('MixedGround01_','')+'.png');path.unlink(missing_ok=True)
   u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera=c,delay=1);mgstate.update(pending=True,path=path)
 finally:mgstate['busy']=False
mgstate['handle']=u.register_slate_post_tick_callback(mg_tick)
