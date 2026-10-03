import unreal as u
from pathlib import Path
L=u.MaterialEditingLibrary
m=u.load_asset('/Game/Art/Environment/RoadsPaths01/M_RP01_TributaryFordSurface')
nodes=list(L.get_material_expressions(m))
def node(cls,label):
 n=next((n for n in L.get_material_expressions(m) if n.get_editor_property('desc')==label),None)
 if n is None:n=L.create_material_expression(m,cls);n.set_editor_property('desc',label)
 return n
def custom(label,code,inputs,typ):
 n=node(u.MaterialExpressionCustom,label);arr=[]
 for name in inputs:
  i=u.CustomInput();i.set_editor_property('input_name',name);arr.append(i)
 n.set_editor_property('inputs',arr);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);return n
w=next(n for n in nodes if isinstance(n,u.MaterialExpressionWorldPosition));t=next(n for n in nodes if isinstance(n,u.MaterialExpressionTime))
oldnormal=next(n for n in nodes if n.get_name()=='MaterialExpressionLinearInterpolate_0')
oldrough=next(n for n in nodes if n.get_editor_property('desc')=='LandCrossingWater_01 restrained reflection')
uv=custom('Bend calm continuous coordinates','float2 p=W.xy-float2(.907524,-.42)*T*6; return p*.011+float2(sin(p.y*.005),sin(p.x*.004))*.018;',['W','T'],u.CustomMaterialOutputType.CMOT_FLOAT2)
L.connect_material_expressions(w,'',uv,'W');L.connect_material_expressions(t,'',uv,'T')
tex=next(n for n in nodes if isinstance(n,u.MaterialExpressionTextureSample))
fine=node(u.MaterialExpressionTextureSample,'Bend calm existing ripple texture');fine.set_editor_property('texture',tex.get_editor_property('texture'));fine.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL);L.connect_material_expressions(uv,'',fine,'Coordinates')
mask='float2 q=W.xy-float2(-23600,-6300); float k=1-smoothstep(2200,3200,length(q));\n'
n=custom('Bend calm normal transition',mask+'''float calm=smoothstep(.05,.7,sin(q.x*.006)*sin(q.y*.004));
float strength=lerp(.075,.035,calm);
float3 quiet=normalize(float3(N.xy*strength,1));
return normalize(lerp(Old,quiet,k));''',['W','N','Old'],u.CustomMaterialOutputType.CMOT_FLOAT3)
L.connect_material_expressions(w,'',n,'W');L.connect_material_expressions(fine,'RGB',n,'N');L.connect_material_expressions(oldnormal,'',n,'Old');L.connect_material_property(n,'',u.MaterialProperty.MP_NORMAL)
r=custom('Bend soft reflection transition',mask+'return lerp(Old,.36,k);',['W','Old'],u.CustomMaterialOutputType.CMOT_FLOAT1)
L.connect_material_expressions(w,'',r,'W');L.connect_material_expressions(oldrough,'',r,'Old');L.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
oldspec=L.get_material_property_input_node(m,u.MaterialProperty.MP_SPECULAR)
if oldspec.get_editor_property('desc')!='Bend restrained specular':
 s=custom('Bend restrained specular',mask+'return lerp(Old,.22,k);',['W','Old'],u.CustomMaterialOutputType.CMOT_FLOAT1)
 L.connect_material_expressions(w,'',s,'W');L.connect_material_expressions(oldspec,'',s,'Old');L.connect_material_property(s,'',u.MaterialProperty.MP_SPECULAR)
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
