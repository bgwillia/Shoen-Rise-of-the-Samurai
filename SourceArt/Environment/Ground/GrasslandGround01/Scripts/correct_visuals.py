import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/GrasslandGround01';L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name().startswith(D+'/')
m=u.load_asset(D+'/M_GrasslandGround_01')
for n in L.get_material_expressions(m):
 if isinstance(n,u.MaterialExpressionCustom):
  code=n.get_editor_property('code')
  if '/100.0' in code:n.set_editor_property('code',code.replace('/100.0','/80.0'))
  if 'return c*macro;' in code:n.set_editor_property('code',code.replace('return c*macro;','return lerp(float3(.075,.12,.05),c,.68)*macro;'))
  if 'd*1.5' in code:n.set_editor_property('code',code.replace('d*1.5','d*.65'))
L.recompile_material(m)
for a in es.get_all_level_actors():
 if isinstance(a,u.DirectionalLight):a.set_actor_rotation(u.Rotator(pitch=-48,yaw=130),False)
 if isinstance(a,u.SkyLight):a.light_component.set_editor_property('intensity',.8)
 if a.get_actor_label()=='GrasslandGround01_02-close-with-clump':
  u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(a.get_actor_location(),a.get_actor_rotation())
u.EditorAssetLibrary.save_directory(D);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec((R/'SourceArt/Environment/Ground/GrasslandGround01/Scripts/capture_unreal.py').read_text())
