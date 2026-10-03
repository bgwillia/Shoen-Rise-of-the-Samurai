import unreal as u
from pathlib import Path
import json
L=u.MaterialEditingLibrary
es=u.get_editor_subsystem(u.EditorActorSubsystem)
land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape))
source=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_SoftColourJoins')
dest='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_InterruptedShoulders'
m=u.load_asset(dest) or u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0],dest)
n=next(n for n in L.get_material_expressions(m) if n.get_name()=='MaterialExpressionCustom_15')
original=next(n for n in L.get_material_expressions(source) if n.get_name()=='MaterialExpressionCustom_15').get_editor_property('code')
addition='''
// North approach: continue to the existing road-pattern endpoint; footprint owns the end fade.
float section=smoothstep(350,490,Q.x)*step(-6500,P.y);
float phase=Q.y<0?1.7:5.1;
float pocket=.5+.30*sin(Q.x*.018+phase)+.20*sin(Q.x*.039+phase*2.3);
float remain=smoothstep(.40,.76,pocket);
float inner=lerp(64,48,remain)+4*sin(Q.x*.053+phase);
float edge=smoothstep(32,inner,abs(Q.y));
float replace=section*edge*(.90-.53*remain);
float cu=.5+clamp(Q.y,-80,80)/600;
float3 packed=lerp(Texture2DSample(R,RSampler,float2(cu,v)).rgb,Texture2DSample(R,RSampler,float2(1-cu,v2)).rgb,breakup);
// Replace the continuous stone strips with existing packed-earth detail;
// retain staggered gravel pockets, without widening the road mask.
road=lerp(road,packed*.93,replace);
'''
n.set_editor_property('code',original.replace('float3 soil=',addition+'\nfloat3 soil='))
L.recompile_material(m)
land.set_editor_property('landscape_material',m)
u.EditorAssetLibrary.save_loaded_asset(m)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
Path('/private/tmp/shoulder-applied.txt').write_text(m.get_path_name())
