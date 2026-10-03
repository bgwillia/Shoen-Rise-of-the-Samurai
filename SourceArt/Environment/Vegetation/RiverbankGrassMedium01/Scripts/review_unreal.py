import unreal as u,time,math
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');O=R/'artifacts/riverbankgrassmedium01';D='/Game/Art/Environment/Vegetation/Grass/RiverbankGrassMedium01';V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
# Remove only this asset's provisional review actors from the settlement.
for a in es.get_all_level_actors():
 if a.get_actor_label().startswith(('RiverbankGrass_Medium_01_Review_','RiverbankGrassMedium01_')):es.destroy_actor(a)
le.save_current_level();le.new_level(D+'/RiverbankGrassMedium01_Review');world=ed.get_editor_world()
plane=u.load_asset('/Engine/BasicShapes/Plane');medium=u.load_asset(D+'/RiverbankGrass_Medium_01');short=u.load_asset('/Game/Art/Environment/Vegetation/Grass/RiverbankGrass01/RiverbankGrass_01')
def place(label,mesh,loc,scale=(1,1,1),mat=None,yaw=0):
 a=es.spawn_actor_from_class(u.StaticMeshActor,V(*loc),u.Rotator(yaw=yaw));a.set_actor_label(label);c=a.static_mesh_component;c.set_static_mesh(mesh);a.set_actor_scale3d(V(*scale));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
 if mat:c.set_material(0,mat)
 return a
place('Approved_GrasslandGround_01',plane,(0,0,-.8),(800,800,1),u.load_asset('/Game/Art/Environment/Ground/GrasslandGround01/M_GrasslandGround_01'))
place('Approved_RiverbankSoil_01',plane,(0,0,-.5),(3.8,3.8,1),u.load_asset('/Game/Art/Environment/Ground/RiverbankSoil01/M_RiverbankSoil_01'))
place('RiverbankGrass_Medium_01',medium,(0,0,0),yaw=12)
place('Approved_RiverbankGrass_01',short,(0,-62,0),yaw=12)
place('RiverbankGrass_Medium_01_Context_02',medium,(-100,90,0),(.93,.93,.93),yaw=117)
place('RiverbankGrass_Medium_01_Context_03',medium,(100,95,0),(1.04,1.04,1.04),yaw=235)
place('Approved_Short_Context_02',short,(-85,35,0),yaw=42)
place('Approved_Short_Context_03',short,(65,85,0),yaw=154)
sun=es.spawn_actor_from_class(u.DirectionalLight,V(0,0,500),u.Rotator(pitch=-48,yaw=-35));sun.light_component.set_mobility(u.ComponentMobility.MOVABLE);sun.light_component.set_editor_property('intensity',3);sun.light_component.set_editor_property('light_source_angle',5)
sky=es.spawn_actor_from_class(u.SkyLight,V(0,0,500));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('intensity',1);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EngineResources/DefaultTextureCube'));sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
pp=es.spawn_actor_from_class(u.PostProcessVolume,V());pp.set_editor_property('unbound',True);q=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_auto_exposure_bias',True),('auto_exposure_bias',0),('override_bloom_intensity',True),('bloom_intensity',0)]:q.set_editor_property(k,v)
pp.set_editor_property('settings',q)
views=[('03-short-grass-comparison',(0,-22,23),(150,-210,105),45),('04-ground-context',(0,25,15),(370,-490,370),45),('05-strategy-camera',(0,25,15),(0,10000,17320.51),55),('06-unreal-close',(0,0,29),(115,-155,64),45)]
cams=[]
for name,target,offset,fov in views:
 target=V(*target);cam=es.spawn_actor_from_class(u.CameraActor,target+V(*offset));cam.set_actor_label(name);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False);cam.camera_component.set_field_of_view(fov);cam.camera_component.set_editor_property('post_process_blend_weight',0);cams.append(cam)
es.clear_actor_selection_set();le.save_current_level();u.EditorAssetLibrary.save_directory(D)
for cmd in ['Slate.bAllowThrottling 0','t.IdleWhenNotForeground 0','r.Streaming.FullyLoadUsedTextures 1']:u.SystemLibrary.execute_console_command(world,cmd)
gm_state={'i':0,'next':time.monotonic()+6,'pending':False}
def gm_tick(dt):
 if gm_state.get('busy'):return
 gm_state['busy']=True
 try:
  i=gm_state['i']
  if gm_state['pending']:
   if not gm_state['path'].exists():return
   gm_state.update(i=i+1,pending=False,next=time.monotonic()+2);i+=1
  if i>=len(cams):
   u.unregister_slate_post_tick_callback(gm_state['handle']);ed.set_level_viewport_camera_info(cams[0].get_actor_location(),cams[0].get_actor_rotation());return
  if time.monotonic()>=gm_state['next']:
   path=O/(views[i][0]+'.png');path.unlink(missing_ok=True);u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(path),camera=cams[i],delay=1);gm_state.update(pending=True,path=path)
 finally:gm_state['busy']=False
gm_state['handle']=u.register_slate_post_tick_callback(gm_tick)
