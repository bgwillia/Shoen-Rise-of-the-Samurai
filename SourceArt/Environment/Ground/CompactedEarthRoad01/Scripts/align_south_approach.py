import unreal as u,math
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem)
land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape));source=land.get_editor_property('landscape_material');D='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_BothApproaches'
m=u.load_asset(D) or u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0],D);nodes={n.get_name():n for n in L.get_material_expressions(m)}
start=(-24000.,-7120.);p0=(-24252.,-7664.5144);p1=(-24378.,-7936.7716);p2=(-24643.,-8270.);p3=(-24630.404278,-8497.472287)
pts=[(start[0]+(p0[0]-start[0])*i/40,start[1]+(p0[1]-start[1])*i/40) for i in range(41)]
for i in range(1,71):
 t=i/70;pts.append(tuple((1-t)**3*p0[j]+3*(1-t)**2*t*p1[j]+3*(1-t)*t*t*p2[j]+t**3*p3[j] for j in range(2)))
code='if(P.y<-6500){float best=1e20;float along=0;float side=0;float2 dir=float2(0,-1);\n';s=0
for a,b in zip(pts,pts[1:]):
 code+='''{float2 a=float2(%f,%f),d=float2(%f,%f);float len=length(d);float t=saturate(dot(P.xy-a,d)/dot(d,d));float2 q=P.xy-a-t*d;float ds=dot(q,q);if(ds<best){best=ds;along=%f+dot(P.xy-a,d)/len;side=dot(q,float2(-d.y,d.x)/len);dir=d/len;}}\n'''%(a[0],a[1],b[0]-a[0],b[1]-a[1],s)
 s+=math.dist(a,b)
code+='return float4(along,side,dir);}\n'
coord=nodes['MaterialExpressionCustom_13'];coord.set_editor_property('code',code+coord.get_editor_property('code'))
# Coverage changes only the south approach, eliminating its old sideways alignment.
prior=next(n for name,n in nodes.items() if name=='MaterialExpressionCustom_28')
n=L.create_material_expression(m,u.MaterialExpressionCustom);n.set_editor_property('desc','Opposite approach follows land bridge axis for six metres');n.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT4)
ins=[]
for k in ['P','Q','Old']:
 z=u.CustomInput();z.set_editor_property('input_name',k);ins.append(z)
n.set_editor_property('inputs',ins)
n.set_editor_property('code','''float width=lerp(335,95,smoothstep(-25,440,Q.x));
float tiny=2.5*sin(Q.x*.015)+1.5*sin(Q.x*.037);
float f=saturate((width+40-abs(Q.y)+tiny)/68);f=f*f*(3-2*f);
float region=(1-smoothstep(-7100,-6990,P.y))*smoothstep(-8497,-8360,P.y);
region*=1-smoothstep(620,720,abs(P.x+24300));
return float4(Old.r,lerp(Old.g,f,region),Old.b,Old.a);''')
L.connect_material_expressions(nodes['MaterialExpressionWorldPosition_6'],'',n,'P');L.connect_material_expressions(coord,'',n,'Q');L.connect_material_expressions(prior,'',n,'Old')
for name,pin in [('MaterialExpressionCustom_3','Weights'),('MaterialExpressionCustom_4','Weights'),('MaterialExpressionCustom_14','W')]:L.connect_material_expressions(n,'',nodes[name],pin)
mask=nodes['MaterialExpressionCustom_14'];c=mask.get_editor_property('code');c=c.replace('return float3(keep,t,footprint*end*(1-smoothstep(bound-50,bound,abs(Q.y))));',f'''if(P.y<-6500){{end=smoothstep(-120,-55,Q.x)*(1-smoothstep({s-280:.5f},{s:.5f},Q.x));}}
return float3(keep,t,footprint*end*(1-smoothstep(bound-50,bound,abs(Q.y))));''');mask.set_editor_property('code',c)
L.recompile_material(m);land.set_editor_property('landscape_material',m);u.EditorAssetLibrary.save_loaded_asset(m);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
c=next(a for a in es.get_all_level_actors() if a.get_actor_label()=='LandBridgeSouth_Overhead')
u.AutomationLibrary.take_high_res_screenshot(1400,900,str(R/'artifacts/landbridge-south-alignment/after-overhead.png'),camera=c,delay=0,force_game_view=True)
