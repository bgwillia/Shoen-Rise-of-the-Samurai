import unreal as u
from pathlib import Path
L=u.MaterialEditingLibrary
m=u.load_asset('/Game/Art/Environment/RoadsPaths01/M_RP01_TributaryFordSurface')
nodes=list(L.get_material_expressions(m))
def named(label):return next(n for n in L.get_material_expressions(m) if n.get_editor_property('desc')==label)
world=next(n for n in nodes if isinstance(n,u.MaterialExpressionWorldPosition))
time=next((n for n in nodes if isinstance(n,u.MaterialExpressionTime)),None) or L.create_material_expression(m,u.MaterialExpressionTime)
local='float2 q=W.xy-float2(-23600,-6300); float k=1-smoothstep(1100,2100,length(q));\n'
# Existing normal texture: slow advection, gently warped scale, short stone wakes.
uv=named('LandCrossingWater_01 small ripple scale')
inp=[]
for name in ['W','T']:
 x=u.CustomInput();x.set_editor_property('input_name',name);inp.append(x)
uv.set_editor_property('inputs',inp)
L.connect_material_expressions(world,'',uv,'W');L.connect_material_expressions(time,'',uv,'T')
uv.set_editor_property('code',local+'''
float2 flow=float2(.907524,-.42);
float2 p=q-flow*T*9;
float2 warp=float2(sin(p.y*.008+p.x*.003),sin(p.x*.007-p.y*.002))*15;
float2 stones[3]={float2(-23762.94,-6463.35),float2(-23160,-6760),float2(-23371.6,-6485.04)};
for(int i=0;i<3;i++){
 float2 d=W.xy-stones[i]; float along=dot(d,flow); float crossflow=dot(d,float2(.42,.907524));
 float wake=exp(-abs(crossflow)/(25+max(along,0)*.24))*smoothstep(-45,20,along)*(1-smoothstep(55,250,along));
 warp+=float2(.42,.907524)*sin(along*.045-T*1.3)*wake*18;
}
float2 tuned=(p+warp)*.007;
return lerp(W.xy*.0007,tuned,k);
''')
# The existing panner remains for the river outside the small ford influence.
panner=next(n for n in nodes if isinstance(n,u.MaterialExpressionPanner))
panner.set_editor_property('speed_x',.003);panner.set_editor_property('speed_y',.018)
# Cancel the existing panner only inside this localized UV treatment.
uv.set_editor_property('code',uv.get_editor_property('code').replace('return lerp(W.xy*.0007,tuned,k);','return lerp(W.xy*.0007,tuned-float2(.003,.018)*T,k);'))
strength=named('LandCrossingWater_01 ripple restraint')
strength.set_editor_property('code',local+'''float patch=sin(q.x*.006+sin(q.y*.004))*sin(q.y*.005-q.x*.002);
float calm=smoothstep(.15,.7,patch);
return lerp(.16,lerp(.24,.08,calm),k);''')
rough=named('LandCrossingWater_01 restrained reflection')
rough.set_editor_property('code',local+'''float patch=sin(q.x*.006+sin(q.y*.004))*sin(q.y*.005-q.x*.002);
return lerp(.18,lerp(.28,.22,smoothstep(.15,.7,patch)),k);''')
# A weaker, differently scaled sample breaks the existing texture's parallel crests.
def node(cls,label):
 n=next((n for n in L.get_material_expressions(m) if n.get_editor_property('desc')==label),None)
 if n is None:n=L.create_material_expression(m,cls);n.set_editor_property('desc',label)
 return n
uv2=node(u.MaterialExpressionCustom,'Ford secondary ripple coordinates')
i=u.CustomInput();i.set_editor_property('input_name','UV');uv2.set_editor_property('inputs',[i]);uv2.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT2)
uv2.set_editor_property('code','return float2(UV.x*.93-UV.y*.37,UV.x*.37+UV.y*.93)*1.73+float2(.31,.67);')
L.connect_material_expressions(panner,'',uv2,'UV')
tex=next(n for n in nodes if isinstance(n,u.MaterialExpressionTextureSample))
tex2=node(u.MaterialExpressionTextureSample,'Ford weak secondary normal');tex2.set_editor_property('texture',tex.get_editor_property('texture'));tex2.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL)
L.connect_material_expressions(uv2,'',tex2,'Coordinates')
mix=node(u.MaterialExpressionLinearInterpolate,'Ford irregular normal mix');mix.set_editor_property('const_alpha',.28)
L.connect_material_expressions(tex,'RGB',mix,'A');L.connect_material_expressions(tex2,'RGB',mix,'B')
normal=L.get_material_property_input_node(m,u.MaterialProperty.MP_NORMAL);L.connect_material_expressions(mix,'',normal,'B')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
fw_pass='motion-final'
exec(Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/LandCrossingWater01/capture_views.py').read_text())
