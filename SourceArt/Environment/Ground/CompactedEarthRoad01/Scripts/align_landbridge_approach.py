import unreal as u,json,math
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem)
land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape));source=land.get_editor_property('landscape_material');D='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_AlignedApproach'
m=u.load_asset(D) or u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0],D)
nodes={n.get_name():n for n in L.get_material_expressions(m)}
# Match the bridge's 0.42,0.9075 direction, then merge tangentially into the existing road.
start=(-23200.,-5480.);p0=(-22948.,-4935.4856);p1=(-22864.,-4753.9808);p2=(-22783.,-4700.);p3=(-22800.,-4300.)
pts=[(start[0]+(p0[0]-start[0])*i/40,start[1]+(p0[1]-start[1])*i/40) for i in range(41)]
for i in range(1,61):
 t=i/60;pts.append(tuple((1-t)**3*p0[j]+3*(1-t)**2*t*p1[j]+3*(1-t)*t*t*p2[j]+t**3*p3[j] for j in range(2)))
denseCount=len(pts)-1
old=json.loads((R/'artifacts/landbridge-road50/route.json').read_text())['segments'];oldJoin=357.34249+981.7328504628114
newLen=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]));segments=[];s=0
for a,b in zip(pts,pts[1:]):
 segments.append((*a,*b,s));s+=math.dist(a,b)
# Preserve longitudinal texture phase on the remainder of the existing road.
for seg in old[3:]:segments.append((*seg[:4],seg[4]+357.34249))
code='float best=1e20;float along=0;float side=0;float2 dir=float2(0,1);\n'
for idx,(ax,ay,bx,by,s) in enumerate(segments):
 scale=oldJoin/newLen if idx<denseCount else 1
 along=s*scale if idx<denseCount else s
 code+='''{float2 a=float2(%f,%f),d=float2(%f,%f);float len=length(d);float t=saturate(dot(P.xy-a,d)/dot(d,d));float2 q=P.xy-a-t*d;float ds=dot(q,q);if(ds<best){best=ds;along=%f+dot(P.xy-a,d)/len*%f;side=dot(q,float2(-d.y,d.x)/len);dir=d/len;}}\n'''%(ax,ay,bx-ax,by-ay,along,scale)
code+='return float4(along,side,dir);';nodes['MaterialExpressionCustom_13'].set_editor_property('code',code)
n=L.create_material_expression(m,u.MaterialExpressionCustom);n.set_editor_property('desc','Centered land bridge approach; removes former side kink from coverage');n.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT4)
ins=[]
for k in ['P','Q','Old']:
 z=u.CustomInput();z.set_editor_property('input_name',k);ins.append(z)
n.set_editor_property('inputs',ins)
n.set_editor_property('code','''float taper=smoothstep(-25,440,Q.x);
float width=lerp(335,95,taper);
float tiny=2.5*sin(Q.x*.015)+1.5*sin(Q.x*.037);
float f=saturate((width+40-abs(Q.y)+tiny)/68);f=f*f*(3-2*f);
float region=smoothstep(-5590,-5510,P.y)*(1-smoothstep(-4420,-4300,P.y));
region*=1-smoothstep(570,670,abs(P.x+23000));
return float4(Old.r,lerp(Old.g,f,region),Old.b,Old.a);''')
L.connect_material_expressions(nodes['MaterialExpressionWorldPosition_6'],'',n,'P');L.connect_material_expressions(nodes['MaterialExpressionCustom_13'],'',n,'Q');L.connect_material_expressions(nodes['MaterialExpressionCustom_26'],'',n,'Old')
for key,pin in [('MaterialExpressionCustom_3','Weights'),('MaterialExpressionCustom_4','Weights'),('MaterialExpressionCustom_14','W')]:L.connect_material_expressions(n,'',nodes[key],pin)
L.recompile_material(m);land.set_editor_property('landscape_material',m);u.EditorAssetLibrary.save_loaded_asset(m);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
c=next(a for a in es.get_all_level_actors() if a.get_actor_label()=='LandBridgeConnection_Overhead')
u.AutomationLibrary.take_high_res_screenshot(1400,900,str(R/'artifacts/landbridge-alignment/after-overhead.png'),camera=c,delay=0)
