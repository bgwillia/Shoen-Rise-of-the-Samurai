import unreal as u,json,math,ast
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary
es=u.get_editor_subsystem(u.EditorActorSubsystem);land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape));source=land.get_editor_property('landscape_material')
D='/Game/Art/Environment/Ground/CompactedEarthRoad01'
m=u.load_asset(D+'/M_LandBridgeRoad50_SmoothBend') or u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0],D+'/M_LandBridgeRoad50_SmoothBend')
# Densely evaluate the existing authored Catmull curve; do not move control points.
layout=R/'SourceArt/Environment/RoadsPaths01';tree=ast.parse((layout/'build.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='catmull');src=ast.unparse(fn).replace(' / 3',' / 0.1');ns={'math':math};exec(src,ns)
route=next(r for r in json.loads((layout/'layout.json').read_text())['routes'] if r['name']=='Village_FordLumberBranch');pts=ns['catmull'](route['points']);pts=[(x*100,y*100) for x,y in pts if -5250<y*100<-3500 and -24000<x*100<-22000]
code='float best=1e20;float2 nearest=P.xy;\n'
for a,b in zip(pts,pts[1:]):
 code+='''{float2 a=float2(%f,%f),d=float2(%f,%f);float t=saturate(dot(P.xy-a,d)/dot(d,d));float2 c=a+t*d;float ds=dot(P.xy-c,P.xy-c);if(ds<best){best=ds;nearest=c;}}\n'''%(a[0],a[1],b[0]-a[0],b[1]-a[1])
code+='''float radius=95+155*exp(-dot(nearest-float2(-23600,-6300),nearest-float2(-23600,-6300))/2200000);
float wav=2.5*sin(nearest.y*.015+P.x*.003)+1.5*sin(nearest.y*.037-P.x*.007);
float f=saturate((radius+40-sqrt(best)+wav)/68);f=f*f*(3-2*f);
float area=smoothstep(-5080,-4920,P.y)*(1-smoothstep(-3940,-3780,P.y));
area*=1-smoothstep(300,380,abs(P.x+22825));
return float4(Old.r,lerp(Old.g,f,area),Old.b,Old.a);'''
weights=next(n for n in L.get_material_expressions(m) if isinstance(n,u.MaterialExpressionTextureSample) and 'RoadsPaths_01_surface' in str(n.get_editor_property('texture')))
n=next((x for x in L.get_material_expressions(m) if isinstance(x,u.MaterialExpressionCustom) and str(x.get_editor_property('desc')).startswith('Local bend:')),None) or L.create_material_expression(m,u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('desc','Local bend: unchanged Catmull route sampled at 10cm, continuous width, 4cm edge variation, unchanged 68cm coverage falloff');n.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT4)
ins=[]
for k in ['P','Old']:
 e=u.CustomInput();e.set_editor_property('input_name',k);ins.append(e)
n.set_editor_property('inputs',ins);p=L.create_material_expression(m,u.MaterialExpressionWorldPosition);L.connect_material_expressions(p,'',n,'P');L.connect_material_expressions(weights,'RGBA',n,'Old')
changed=[]
for c in L.get_material_expressions(m):
 if not isinstance(c,u.MaterialExpressionCustom) or c==n:continue
 names=L.get_material_expression_input_names(c)
 nodes=L.get_inputs_for_material_expression(m,c)
 for name,node in zip(names,nodes):
  if node==weights and name!='Ruts':
   assert L.connect_material_expressions(n,'',c,name);changed.append((c.get_name(),name))
L.recompile_material(m);land.set_editor_property('landscape_material',m);u.EditorAssetLibrary.save_loaded_asset(m);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(R/'artifacts/road-bend-boundary/change.txt').write_text(str(changed)+'\nDense curve segments: '+str(len(pts)-1))
s=(R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Scripts/capture_landbridge_road50.py').read_text().replace('LandBridgeRoad50_','BendBoundary01_').replace('artifacts/landbridge-road50','artifacts/road-bend-boundary/after');exec(s,{'__name__':'__main__'})
