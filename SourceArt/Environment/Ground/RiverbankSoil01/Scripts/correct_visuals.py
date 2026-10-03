import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name().startswith('/Game/Art/Environment/Ground/RiverbankSoil01/'), 'Soil review must be the active level'
for a in es.get_all_level_actors():
 if isinstance(a,u.PostProcessVolume):
  q=a.get_editor_property('settings')
  for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_auto_exposure_bias',True),('auto_exposure_bias',0),('override_bloom_intensity',True),('bloom_intensity',0)]:q.set_editor_property(k,v)
  a.set_editor_property('settings',q)
 if isinstance(a,u.CameraActor):a.camera_component.set_editor_property('post_process_blend_weight',0)
 if isinstance(a,u.DirectionalLight):a.light_component.set_editor_property('intensity',3);a.light_component.set_mobility(u.ComponentMobility.MOVABLE)
 if isinstance(a,u.SkyLight):a.light_component.set_editor_property('intensity',.5);a.light_component.set_mobility(u.ComponentMobility.MOVABLE)
le.save_current_level()
exec((R/'SourceArt/Environment/Ground/RiverbankSoil01/Scripts/capture_unreal.py').read_text())
