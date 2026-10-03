import unreal as u,time
from pathlib import Path
try:u.unregister_slate_post_tick_callback(cer_state['handle'])
except:pass
out=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/artifacts/compactedearthroad01')
es=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
fcams=sorted([a for a in es.get_all_level_actors() if isinstance(a,u.CameraActor) and a.get_actor_label().startswith('CompactedEarthRoad01_')],key=lambda a:a.get_actor_label())
fc={'i':0,'next':time.monotonic()+1,'pending':None,'keep':[]}
def ft(dt):
 if time.monotonic()<fc['next']:return
 if fc['pending']:
  cap,rt,name=fc['pending'];u.RenderingLibrary.export_render_target(world,rt,str(out),name+'.png');fc['keep'].append(rt);es.destroy_actor(cap);fc.update(i=fc['i']+1,pending=None,next=time.monotonic()+1);return
 if fc['i']==2:
  u.unregister_slate_post_tick_callback(fc['handle']);u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(out/'03-strategy.png'),camera=fcams[2],delay=.1);return
 cam=fcams[fc['i']];rt=u.RenderingLibrary.create_render_target2d(world,1600,1000,u.TextureRenderTargetFormat.RTF_RGBA8);rt.set_editor_property('target_gamma',2.2)
 cap=es.spawn_actor_from_class(u.SceneCapture2D,cam.get_actor_location(),cam.get_actor_rotation());sc=cap.capture_component2d;sc.set_editor_property('texture_target',rt);sc.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR);sc.set_editor_property('fov_angle',45);sc.set_editor_property('capture_every_frame',True)
 fc.update(pending=(cap,rt,cam.get_actor_label().replace('CompactedEarthRoad01_','')),next=time.monotonic()+3)
fc['handle']=u.register_slate_post_tick_callback(ft)
