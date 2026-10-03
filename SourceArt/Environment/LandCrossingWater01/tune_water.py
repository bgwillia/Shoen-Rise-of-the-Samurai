import unreal as u
from pathlib import Path
L=u.MaterialEditingLibrary
m=u.load_asset('/Game/Art/Environment/RoadsPaths01/M_RP01_TributaryFordSurface')
nodes=list(L.get_material_expressions(m))
world=next(n for n in nodes if n.get_class().get_name()=='MaterialExpressionWorldPosition')
local='float k=1-smoothstep(1100,2100,length(W.xy-float2(-23600,-6300)));\n'
def custom(label,code,typ):
 n=next((n for n in L.get_material_expressions(m) if n.get_editor_property('desc')==label),None)
 if not n:n=L.create_material_expression(m,u.MaterialExpressionCustom)
 n.set_editor_property('desc',label);n.set_editor_property('code',code);n.set_editor_property('output_type',typ)
 inp=u.CustomInput();inp.set_editor_property('input_name','W');n.set_editor_property('inputs',[inp]);L.connect_material_expressions(world,'',n,'W');return n
fade=next(n for n in nodes if isinstance(n,u.MaterialExpressionDepthFade))
fade.set_editor_property('fade_distance_default',180.0)
op=L.get_material_property_input_node(m,u.MaterialProperty.MP_OPACITY)
op.set_editor_property('code',local+'''float2 q=W.xy-float2(-23600,-6300);
float t=dot(q,float2(.42,.907524));float s=dot(q,float2(-.907524,.42));
float f=(1-smoothstep(750,1200,abs(t)))*(1-smoothstep(180,340,abs(s)));
float shore=smoothstep(-180,-110,t)*(1-smoothstep(350,420,t))*smoothstep(-570,-410,s)*(1-smoothstep(-220,-170,s));
float old=saturate(Base*7.2/.94)*.94*(1-f*.86)*(1-shore*.55);
float depth=Base/.94*180;
float silty=.96*(1-exp(-depth/65))*(1-f*.45);
return lerp(old,silty,k);''')
color=custom('LandCrossingWater_01 earth-green',local+'return lerp(float3(.095,.15,.155),float3(.08,.105,.09),k);',u.CustomMaterialOutputType.CMOT_FLOAT3)
L.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
rough=custom('LandCrossingWater_01 restrained reflection',local+'return lerp(.18,.25,k);',u.CustomMaterialOutputType.CMOT_FLOAT1)
L.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
uv=custom('LandCrossingWater_01 small ripple scale',local+'return W.xy*lerp(.0007,.009,k);',u.CustomMaterialOutputType.CMOT_FLOAT2)
panner=next(n for n in nodes if isinstance(n,u.MaterialExpressionPanner));L.connect_material_expressions(uv,'',panner,'Coordinate')
normal=L.get_material_property_input_node(m,u.MaterialProperty.MP_NORMAL)
strength=custom('LandCrossingWater_01 ripple restraint',local+'return lerp(.16,.28,k);',u.CustomMaterialOutputType.CMOT_FLOAT1)
L.connect_material_expressions(strength,'',normal,'Alpha')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
fw_pass='final'
exec(Path(__file__).with_name('capture_views.py').read_text())
