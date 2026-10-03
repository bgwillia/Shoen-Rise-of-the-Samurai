import unreal as u,time
from pathlib import Path
root=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/landbridge-comedy/frames')
u.EditorPythonScripting.set_keep_python_script_alive(True)
st={'frame':0,'stage':0,'time':time.monotonic(),'ticks':0};cine['setframe'](0)
def render_tick(dt):
 st['ticks']+=1
 path=root/('%04d.png'%st['frame'])
 if st['stage']==0:
  if st['ticks']<8 or time.monotonic()-st['time']<.22:return
  u.SystemLibrary.execute_console_command(None,'HighResShot 1920x1080 filename='+str(path));st['stage']=1
 elif path.exists() and path.stat().st_size>10000:
  st['frame']+=1
  Path('/private/tmp/cine-render-progress.txt').write_text(str(st['frame']))
  if st['frame']>=288:
   u.unregister_slate_post_tick_callback(st['handle']);Path('/private/tmp/cine-render-done.txt').write_text('288 rendered frames');return
  cine['setframe'](st['frame']*30/24);st['ticks']=0;st['time']=time.monotonic();st['stage']=0
st['handle']=u.register_slate_post_tick_callback(render_tick)
