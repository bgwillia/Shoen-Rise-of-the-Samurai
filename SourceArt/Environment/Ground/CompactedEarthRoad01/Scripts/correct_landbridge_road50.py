import unreal as u,json,math
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');O=R/'artifacts/landbridge-road50';L=u.MaterialEditingLibrary
m=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_Surface')
ns=L.get_material_expressions(m)
coord=next(n for n in ns if isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('desc').startswith('Existing 50m'))
segs=json.loads((O/'route.json').read_text())['segments'];a=(-23200.,-5480.);b=segs[0][:2];join=math.dist(a,b)
ss=[[*a,*b,0]]+[[*v[:4],v[4]+join] for v in segs]
code='float best=1e20;float along=0;float side=0;float2 dir=float2(0,1);\n'
for ax,ay,bx,by,s in ss:
 code+='''{float2 a=float2(%f,%f),b=float2(%f,%f),d=b-a;float len=length(d);float t=saturate(dot(P.xy-a,d)/dot(d,d));float2 q=P.xy-a-t*d;float ds=dot(q,q);if(ds<best){best=ds;along=%f+dot(P.xy-a,d)/len;side=dot(q,float2(-d.y,d.x)/len);dir=d/len;}}\n'''%(ax,ay,bx,by,s)
code+='return float4(along,side,dir);';coord.set_editor_property('code',code)
mask=next(n for n in ns if isinstance(n,u.MaterialExpressionCustom) and 'float length=400' in n.get_editor_property('code'))
code=mask.get_editor_property('code').replace('4850,5000',f'{4850+join},{5000+join}').replace('W.g*end*(1-smoothstep(200,270,abs(Q.y)))',f'max(W.g,(1-smoothstep(85+4*sin(Q.x*.039),110+4*sin(Q.x*.039),abs(Q.y)))*(1-smoothstep({join},{join+45},Q.x)))*end*(1-smoothstep(200,270,abs(Q.y)))')
mask.set_editor_property('code',code)
col=next(n for n in ns if isinstance(n,u.MaterialExpressionCustom) and 'float breakup=' in n.get_editor_property('code'))
tex=L.create_material_expression(m,u.MaterialExpressionTextureObject);tex.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/RiverbankSoil01/T_RiverbankSoil01_BaseColor'))
inputs=list(col.get_editor_property('inputs'));e=u.CustomInput();e.set_editor_property('input_name','Soil');inputs.append(e);col.set_editor_property('inputs',inputs);L.connect_material_expressions(tex,'',col,'Soil')
code=col.get_editor_property('code').replace('float3 road=lerp(a,b,breakup);','''float3 road=lerp(a,b,breakup);
float3 soil=lerp(float3(.188,.150,.109),Texture2DSample(Soil,SoilSampler,P.xy/100).rgb,.70);
road=lerp(road,soil,smoothstep(75,103,abs(Q.y)));''');col.set_editor_property('code',code)
norm=next(n for n in ns if isinstance(n,u.MaterialExpressionCustom) and 'float2 side=float2(-Q.w,Q.z)' in n.get_editor_property('code'));norm.set_editor_property('code',norm.get_editor_property('code').replace('M.z*(1-M.x*.65)','M.z*(1-M.x*.65)*(1-smoothstep(80,100,abs(Q.y)))'))
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
es=u.get_editor_subsystem(u.EditorActorSubsystem)
for c in es.get_all_level_actors():
 if c.get_actor_label()=='LandBridgeRoad50_01-connection-close':
  loc=u.Vector(-22250,-6090,1350);target=u.Vector(-23080,-5300,700);c.set_actor_location(loc,False,False);c.set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,target),False);c.camera_component.set_field_of_view(55)
 if c.get_actor_label()=='LandBridgeRoad50_02-full-stretch-strategy':
  loc=u.Vector(-19600,-6900,6500);target=u.Vector(-23400,-3350,730);c.set_actor_location(loc,False,False);c.set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,target),False);c.camera_component.set_field_of_view(60)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec((R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Scripts/capture_landbridge_road50.py').read_text(),{'__name__':'__main__'})
