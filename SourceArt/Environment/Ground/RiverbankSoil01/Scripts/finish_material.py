import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/RiverbankSoil01';L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name().startswith(D+'/'), 'Soil review must be active'
for name in ['M_RiverbankSoil_01','M_RiverbankSoil01_ReviewTransition']:
 m=u.load_asset(D+'/'+name)
 for n in L.get_material_expressions(m):
  if isinstance(n,u.MaterialExpressionCustom):
   code=n.get_editor_property('code')
   if 'W.xy/100.0' in code:n.set_editor_property('code','return (W.xy+float2(1.8*sin(W.y*.019),1.8*sin(W.x*.023)))/100.0+float2(0,.5);')
   if 'lerp(float3(.188,.150,.109),c,.85)' in code:n.set_editor_property('code',code.replace('c,.85','c,.70'))
 L.recompile_material(m)
actors=es.get_all_level_actors()
cam=next(a for a in actors if a.get_actor_label()=='RiverbankSoil01_01-overhead-1m');cam.set_actor_location(u.Vector(-650,0,235),False,False)
# Put the saved editor viewport on the usable grass/soil/gravel context view.
cam=next(a for a in actors if a.get_actor_label()=='RiverbankSoil01_04-gravel-transition')
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())
u.EditorAssetLibrary.save_directory(D);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec((R/'SourceArt/Environment/Ground/RiverbankSoil01/Scripts/capture_unreal.py').read_text())
