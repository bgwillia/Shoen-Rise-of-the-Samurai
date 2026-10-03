import unreal as u
from pathlib import Path
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
aa=es.get_all_level_actors()
base=next(a for a in aa if a.get_actor_label()=='GrassToGravelTransition_01')
base.set_actor_rotation(u.Rotator(yaw=180),False)
# Correct the FBX axis reversal, then frame the planting on the left.
for a in aa:
 if isinstance(a,u.CameraActor):
  loc=(-5,245,170) if a.get_actor_label().startswith('01') else (5,310,475)
  a.set_actor_location(u.Vector(*loc),False,False);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(u.Vector(*loc),u.Vector(72,0,2)),False)
close=next(a for a in aa if a.get_actor_label()=='01-close-oblique')
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(close.get_actor_location(),close.get_actor_rotation());le.save_current_level()
exec(open('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/Ground/GrassToGravelTransition01/Scripts/capture.py').read())
