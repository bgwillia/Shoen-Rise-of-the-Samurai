import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/MixedGround01';L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_path_name().startswith(D+'/')
m=u.load_asset(D+'/M_MixedGround_01');n=next(n for n in L.get_material_expressions(m) if isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('desc')=='MixedGround_01 soft connected coverage')
code=n.get_editor_property('code').replace('/27.0+float2(3.7,8.2)','/16.0+float2(3.7,8.81)').replace('f.noise(q)*.78+f.noise(q*2.7+7.3)*.22','f.noise(q)*.65+f.noise(q*2.7+7.3)*.25+f.noise(q*7.1-13)*.10').replace('smoothstep(.42,.59,v)','smoothstep(.38,.62,v)');n.set_editor_property('code',code);L.recompile_material(m)
actors=es.get_all_level_actors();clump=next(a for a in actors if a.get_actor_label()=='Approved_RiverbankGrass_01_Unchanged');clump.set_actor_location(u.Vector(0,5,-.4),False,False)
cam=next(a for a in actors if a.get_actor_label()=='MixedGround01_03-with-clump');target=u.Vector(0,5,4);cam.set_actor_location(target+u.Vector(32,-80,45),False,False);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(cam.get_actor_location(),target),False)
u.EditorAssetLibrary.save_directory(D);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec((R/'SourceArt/Environment/Ground/MixedGround01/Scripts/capture_unreal.py').read_text())
