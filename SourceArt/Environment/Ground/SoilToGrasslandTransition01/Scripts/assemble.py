import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/SoilToGrasslandTransition01';L=u.MaterialEditingLibrary;V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
# Keep the approved shader treatments unchanged; author only this sample's coverage.
u.EditorAssetLibrary.make_directory(D)
m=u.load_asset(D+'/M_SoilToGrasslandTransition_01') or u.EditorAssetLibrary.duplicate_asset('/Game/Art/Environment/Ground/MixedGround01/M_MixedGround_01',D+'/M_SoilToGrasslandTransition_01')
mask=next(n for n in L.get_material_expressions(m) if isinstance(n,u.MaterialExpressionCustom) and ('soft connected coverage' in n.get_editor_property('desc') or 'Short soil entry' in n.get_editor_property('desc')))
source=u.load_asset('/Game/Art/Environment/Ground/MixedGround01/M_MixedGround_01')
code=next(n for n in L.get_material_expressions(source) if isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('desc')=='MixedGround_01 soft connected coverage').get_editor_property('code')
code=code[:code.rfind('return smoothstep')]+'''
float2 p=W.xy;
// Unequal soil tongues and joined green incursions, confined to this sample.
float bend=10*sin(p.y*.049)+6*sin(p.y*.113+1.2);
float edge=p.x+bend;
float entry=smoothstep(-22,18,edge);
float fill=smoothstep(12,170,edge+12*sin(p.y*.033+.8));
float threshold=lerp(.55,.24,fill);
float green=smoothstep(threshold-.115,threshold+.115,v);
return entry*green;
'''
mask.set_editor_property('code',code);mask.set_editor_property('desc','Short soil entry; irregular overlapping grass coverage for this sample only');L.recompile_material(m)
# Copy only the little review stage, with no changes to its original patch.
le.load_level('/Game/Art/Environment/Ground/GrassToGravelTransition01/GrassToGravelTransition_01')
u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),D+'/SoilToGrasslandTransition_01')
le.load_level(D+'/SoilToGrasslandTransition_01')
aa=es.get_all_level_actors()
base=next(a for a in aa if a.get_actor_label()=='GrassToGravelTransition_01');base.set_actor_label('SoilToGrasslandTransition_01');base.static_mesh_component.set_material(0,m)
# Hand-authored loose groups: green ground coverage carries the gradient.
placements=[(12,22,1.02,18),(31,28,.93,148),(49,-24,1.08,72),(66,-17,.96,233),(85,30,1.04,318),(108,19,.91,97),(123,-27,.98,183),(148,-19,1.05,42),(156,25,.94,267)]
clumps=sorted([a for a in aa if a.get_actor_label().startswith('RiverbankGrass_01_')],key=lambda a:a.get_actor_label())
for a,(x,y,s,yaw) in zip(clumps,placements):a.set_actor_location(V(x,y,-.35),False,False);a.set_actor_scale3d(V(s,s,s));a.set_actor_rotation(u.Rotator(yaw=yaw),False)
for a in aa:
 if isinstance(a,u.StaticMeshActor):a.set_folder_path('SoilToGrasslandTransition_01')
 if isinstance(a,u.CameraActor):
  name=a.get_actor_label()
  if name.startswith('01'):loc=(-5,245,170)
  elif name.startswith('02'):loc=(5,310,475)
  else:loc=(1172,1600,1800)
  a.set_actor_location(V(*loc),False,False);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(V(*loc),V(72,0,2)),False)
close=next(a for a in aa if a.get_actor_label().startswith('01'))
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(close.get_actor_location(),close.get_actor_rotation())
u.EditorAssetLibrary.save_directory(D);le.save_current_level();es.clear_actor_selection_set();le.editor_set_viewport_realtime(True)
exec((R/'SourceArt/Environment/Ground/SoilToGrasslandTransition01/Scripts/capture.py').read_text())
