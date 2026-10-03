import unreal as u,json
from pathlib import Path
L=u.MaterialEditingLibrary;m=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_VillageEntrance_ConnectedRoad');nodes={n.get_name():n for n in L.get_material_expressions(m)}
n=nodes['MaterialExpressionCustom_29'];c=n.get_editor_property('code');c=c.replace('return lerp(oldWeights,float4(0,0,0,oldWeights.a),replaceOld);','''float existingSpur=1-smoothstep(.55,1.25,length((P.xy-float2(-15700,-28900))/float2(650,900)));
replaceOld*=1-existingSpur;
return lerp(oldWeights,float4(0,0,0,oldWeights.a),replaceOld);''');n.set_editor_property('code',c)
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
# Existing raised earth approach meshes use earth shoulders, without grassy cliff faces.
p='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_VillageEntrance_EarthApproach';am=u.load_asset(p) or u.EditorAssetLibrary.duplicate_asset(m.get_path_name().split('.')[0],p)
ns={n.get_name():n for n in L.get_material_expressions(am)}
ns['MaterialExpressionCustom_24'].set_editor_property('code','return 0;');ns['MaterialExpressionCustom_25'].set_editor_property('code','return 1;')
L.recompile_material(am);u.EditorAssetLibrary.save_loaded_asset(am)
es=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in es.get_all_level_actors():
 if a.get_actor_label().startswith('BridgeStudy_Approach_'):a.get_component_by_class(u.SplineMeshComponent).set_material(0,am)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
Path('/private/tmp/connection-final-saved.txt').write_text('Road and existing earth approach materials saved; geometry unchanged.')
