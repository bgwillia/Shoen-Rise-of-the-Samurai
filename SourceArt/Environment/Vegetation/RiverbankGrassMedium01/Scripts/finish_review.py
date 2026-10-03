exec(open('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/Vegetation/RiverbankGrassMedium01/Scripts/import_unreal.py').read())
import unreal as u,time,math
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');O=R/'artifacts/riverbankgrassmedium01';D='/Game/Art/Environment/Vegetation/Grass/RiverbankGrassMedium01';V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=es.get_all_level_actors()
for a in actors:
 if isinstance(a,u.DirectionalLight):a.set_actor_rotation(u.Rotator(pitch=-48,yaw=130),False)
mesh=u.load_asset(D+'/RiverbankGrass_Medium_01');body=mesh.get_editor_property('body_setup');u.get_editor_subsystem(u.StaticMeshEditorSubsystem).remove_collisions(mesh)
O.joinpath('import-result.txt').write_text('Asset: '+mesh.get_path_name()+'\nBounds (cm): '+str(mesh.get_bounds())+'\nCollision primitives: '+str(u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_simple_collision_count(mesh))+'\nReview instances: '+str([(a.get_actor_label(),str(a.static_mesh_component.get_collision_enabled())) for a in actors if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh==mesh]))
u.EditorAssetLibrary.save_directory(D);le.save_current_level()
cams=sorted([a for a in actors if isinstance(a,u.CameraActor)],key=lambda a:a.get_actor_label());views=[(c,c.get_actor_label()) for c in cams]
pan=es.spawn_actor_from_class(u.CameraActor,V());pan.set_actor_label('MotionReview');pan.camera_component.set_field_of_view(55);pan.camera_component.set_editor_property('post_process_blend_weight',0)
# Brief rendered pan at normal strategy distance, then at closer inspection zoom.
for distance,name in [(20000,'strategy'),(1800,'closer')]:
 for i in range(10):views.append((pan,'motion-'+name+'-%02d'%i,distance,i))
st={'i':0,'next':time.monotonic()+4,'pending':False}
def mtick(dt):
 if st.get('busy'):return
 st['busy']=True
 try:
  i=st['i']
  if st['pending']:
   if not st['path'].exists():return
   st.update(i=i+1,pending=False,next=time.monotonic()+.1);i+=1
  if i>=len(views):
   u.unregister_slate_post_tick_callback(st['handle']);es.destroy_actor(pan);ed.set_level_viewport_camera_info(cams[0].get_actor_location(),cams[0].get_actor_rotation());O.joinpath('review-complete.txt').write_text('Final asset rendered in Unreal: four views and two ten-frame camera pans.');return
  if time.monotonic()>=st['next']:
   v=views[i];cam=v[0]
   if len(v)>2:
    d,j=v[2:];target=V((j-4.5)*d*.0015,20,15);pos=target+V(d*.1,d*.49,d*.866);cam.set_actor_location(pos,False,False);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(pos,target),False)
   p=O/(v[1]+'.png');p.unlink(missing_ok=True);u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(p),camera=cam,delay=.15);st.update(pending=True,path=p)
 finally:st['busy']=False
st['handle']=u.register_slate_post_tick_callback(mtick)
