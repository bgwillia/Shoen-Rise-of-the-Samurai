import unreal as u
from pathlib import Path
L=u.MaterialEditingLibrary;D='/Game/Art/Environment/Ground/RiverGravel01';m=u.load_asset(D+'/M_RiverGravel_01');c=L.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR)
code=c.get_editor_property('code').replace('return c*macro*(1-Wet*.24);','float3 fresh=c*macro*(1-Wet*.24); float2 q=(W.xy-float2(-23530,-6610))/float2(600,500); float blend=1-smoothstep(.64,1.0,length(q)+.025*sin(W.x*.036)*sin(W.y*.028)); float3 old=Texture2DSample(F,FSampler,W.xy/320.0).rgb*float3(.62,.65,.64); return lerp(old,fresh,blend);')
c.set_editor_property('code',code);inputs=list(c.get_editor_property('inputs'));e=u.CustomInput();e.set_editor_property('input_name','F');inputs.append(e);c.set_editor_property('inputs',inputs);f=L.create_material_expression(m,u.MaterialExpressionTextureObject);f.set_editor_property('texture',u.load_asset('/Game/Art/Environment/WaterBase01/Textures/gravel_ground_01_diff_2k'));L.connect_material_expressions(f,'',c,'F');L.recompile_material(m)
es=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in es.get_all_level_actors():
 if a.get_actor_label().startswith('RP01_SubmergedGravelBed_'):a.get_component_by_class(u.SplineMeshComponent).set_material(0,m)
u.EditorAssetLibrary.save_loaded_asset(m);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec(open('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/Ground/RiverGravel01/Scripts/capture_unreal.py').read())
