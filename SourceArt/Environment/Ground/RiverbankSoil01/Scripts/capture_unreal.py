import unreal as u,time
from pathlib import Path
SO=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/riverbanksoil01')
ses=u.get_editor_subsystem(u.EditorActorSubsystem);scams=sorted([a for a in ses.get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('RiverbankSoil01_')],key=lambda a:a.get_actor_label())
sstate={'i':0,'next':time.monotonic()+8,'pending':False}
def soil_tick(dt):
 if sstate.get('busy'):return
 sstate['busy']=True
 try:
  i=sstate['i']
  if sstate['pending']:
   if not sstate['path'].exists():return
   sstate.update(i=i+1,pending=False,next=time.monotonic()+2);i+=1
  if i>=len(scams):
   u.unregister_slate_post_tick_callback(sstate['handle']);SO.joinpath('captures-complete.txt').write_text('Five rendered Unreal views.');return
  if time.monotonic()>=sstate['next']:
   c=scams[i];path=SO/(c.get_actor_label().replace('RiverbankSoil01_','')+'.png');path.unlink(missing_ok=True)
   u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera=c,delay=1);sstate.update(pending=True,path=path)
 finally:sstate['busy']=False
sstate['handle']=u.register_slate_post_tick_callback(soil_tick)
