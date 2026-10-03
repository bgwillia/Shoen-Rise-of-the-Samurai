import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai')
D='/Game/Art/Environment/Ground/CompactedEarthRoad01'
O=R/'artifacts/compactedearthroad01'
L=u.MaterialEditingLibrary; V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem); le=u.get_editor_subsystem(u.LevelEditorSubsystem)
le.new_level(D+'/CompactedEarthRoad01_Review')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
m=u.AssetToolsHelpers.get_asset_tools().create_asset('M_CompactedEarthRoad_01',D,u.Material,u.MaterialFactoryNew())
a=es.spawn_actor_from_class(u.StaticMeshActor,V());a.set_actor_label('CompactedEarthRoad_01_2m_x_4m_SoilBlendedSample');a.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'));a.set_actor_scale3d(V(4,6,1));a.static_mesh_component.set_material(0,m)
sun=es.spawn_actor_from_class(u.DirectionalLight,V(0,0,500),u.Rotator(pitch=-48,yaw=-35));sun.light_component.set_editor_property('intensity',3.0);sun.light_component.set_editor_property('light_source_angle',4)
sky=es.spawn_actor_from_class(u.SkyLight,V(0,0,500));sky.light_component.set_editor_property('intensity',.5);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EngineResources/DefaultTextureCube'));sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
pp=es.spawn_actor_from_class(u.PostProcessVolume,V());pp.set_editor_property('unbound',True);settings=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_bias',True),('auto_exposure_bias',0),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_bloom_intensity',True),('bloom_intensity',0)]:settings.set_editor_property(k,v)
pp.set_editor_property('settings',settings)
for name,target,off in [('01-overhead',(0,0,0),(0,0,850)),('02-low-oblique',(0,0,0),(90,-405,200)),('03-strategy',(0,0,0),(1100,-1600,1800))]:
 target=V(*target);cam=es.spawn_actor_from_class(u.CameraActor,target+V(*off));cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False);cam.set_actor_label('CompactedEarthRoad01_'+name);cam.camera_component.set_field_of_view(45);cam.camera_component.set_editor_property('post_process_blend_weight',0)
for a in es.get_all_level_actors():
 if a.get_actor_label()=='CompactedEarthRoad01_01-overhead':a.set_actor_rotation(u.Rotator(pitch=-90,yaw=-90,roll=0),False)
u.EditorAssetLibrary.save_directory(D);le.save_current_level();es.clear_actor_selection_set()
for cmd in ['Slate.bAllowThrottling 0','t.IdleWhenNotForeground 0','r.Streaming.FullyLoadUsedTextures 1']:u.SystemLibrary.execute_console_command(world,cmd)
O.joinpath('built.txt').write_text('Saved M_CompactedEarthRoad_01 and review map. Road footprint approximately 200 by 400 cm within 400 by 600 cm flush soil context.')
exec((R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Scripts/install_texture.py').read_text())
