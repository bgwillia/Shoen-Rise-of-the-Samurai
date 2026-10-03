import unreal as u,json,time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');O=R/'artifacts/landbridge-road50';D='/Game/Art/Environment/Ground/CompactedEarthRoad01';L=u.MaterialEditingLibrary;V=u.Vector
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem);land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape))
source=land.get_editor_property('landscape_material');m=u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0],D+'/M_LandBridgeRoad50_Surface')
oldc=L.get_material_property_input_node(m,u.MaterialProperty.MP_BASE_COLOR);oldo=L.get_material_property_input_node_output_name(m,u.MaterialProperty.MP_BASE_COLOR);oldn=L.get_material_property_input_node(m,u.MaterialProperty.MP_NORMAL);oldno=L.get_material_property_input_node_output_name(m,u.MaterialProperty.MP_NORMAL)
weights=next(n for n in L.get_material_expressions(m) if isinstance(n,u.MaterialExpressionTextureSample) and 'RoadsPaths_01_surface' in str(n.get_editor_property('texture')))
def node(c):return L.create_material_expression(m,c)
def link(a,o,b,i):L.connect_material_expressions(a,o,b,i)
def custom(code,ins,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);items=[]
 for k in ins:
  e=u.CustomInput();e.set_editor_property('input_name',k);items.append(e)
 n.set_editor_property('inputs',items);return n
p=node(u.MaterialExpressionWorldPosition)
segs=json.loads((O/'route.json').read_text())['segments'];code='float best=1e20;float along=0;float side=0;float2 dir=float2(0,1);\n'
for ax,ay,bx,by,s in segs:
 code+='''{float2 a=float2(%f,%f),b=float2(%f,%f),d=b-a;float len=length(d);float t=saturate(dot(P.xy-a,d)/dot(d,d));float2 q=P.xy-a-t*d;float ds=dot(q,q);if(ds<best){best=ds;along=%f+dot(P.xy-a,d)/len;side=dot(q,float2(-d.y,d.x)/len);dir=d/len;}}\n'''%(ax,ay,bx,by,s)
code+='return float4(along,side,dir);'
coord=custom(code,['P'],u.CustomMaterialOutputType.CMOT_FLOAT4);coord.set_editor_property('desc','Existing 50m road alignment, read from its authored Catmull route');link(p,'',coord,'P')
road=node(u.MaterialExpressionTextureObject);road.set_editor_property('texture',u.load_asset(D+'/T_CompactedEarthRoad01_BaseColor'))
grav=node(u.MaterialExpressionTextureObject);grav.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/RiverGravel01/T_RiverGravel01_BaseColor'))
mask=custom('''float length=400+65*sin(Q.y*.023)+30*sin(Q.y*.061+1.1);
float t=smoothstep(35,length,Q.x+17*sin(Q.y*.073));
float2 uv=float2(P.x*.9563-P.y*.2924,P.x*.2924+P.y*.9563)/78;
float3 g=Texture2DSample(G,GSampler,uv).rgb;
float h=saturate((dot(g,float3(.3,.59,.11))-.065)*3.3);
float keep=smoothstep(lerp(-.15,1.15,t)-.045,lerp(-.15,1.15,t)+.045,h);
float end=smoothstep(0,40,Q.x)*(1-smoothstep(4850,5000,Q.x));
return float3(keep,t,W.g*end*(1-smoothstep(200,270,abs(Q.y))));''',['Q','P','G','W']);link(coord,'',mask,'Q');link(p,'',mask,'P');link(grav,'',mask,'G');link(weights,'RGB',mask,'W')
color=custom('''float u=saturate(.5+Q.y/200);
float v=abs(frac(Q.x/800)*2-1);
float v2=abs(frac((Q.x+137)/800)*2-1);
float3 a=Texture2DSample(R,RSampler,float2(u,v)).rgb;
float3 b=Texture2DSample(R,RSampler,float2(1-u,v2)).rgb;
float breakup=.22+.12*sin(Q.x*.0023+Q.y*.013);
float3 road=lerp(a,b,breakup);
float2 guv=float2(P.x*.9563-P.y*.2924,P.x*.2924+P.y*.9563)/78;
float3 g=lerp(float3(.245,.203,.164),Texture2DSample(G,GSampler,guv).rgb,.78);
float3 c=lerp(road,g,M.x);
return lerp(Base,c,M.z);''',['Q','P','R','G','M','Base'])
for a,o,k in [(coord,'','Q'),(p,'','P'),(road,'','R'),(grav,'','G'),(mask,'','M'),(oldc,oldo,'Base')]:link(a,o,color,k)
L.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
# Preserve terrain's world normal; subtle detail follows the existing road axis.
normal=custom('''float2 uv=float2(saturate(.5+Q.y/200),abs(frac(Q.x/800)*2-1));float2 e=float2(.0009,.00045);
float gx=dot(Texture2DSample(R,RSampler,uv-float2(e.x,0)).rgb-Texture2DSample(R,RSampler,uv+float2(e.x,0)).rgb,float3(.3,.59,.11));
float gy=dot(Texture2DSample(R,RSampler,uv-float2(0,e.y)).rgb-Texture2DSample(R,RSampler,uv+float2(0,e.y)).rgb,float3(.3,.59,.11));
float2 side=float2(-Q.w,Q.z);float2 xy=(side*gx+Q.zw*gy)*.32;
return normalize(Base+float3(xy,0)*M.z*(1-M.x*.65));''',['Q','R','M','Base']);link(coord,'',normal,'Q');link(road,'',normal,'R');link(mask,'',normal,'M');link(oldn,oldno,normal,'Base');L.connect_material_property(normal,'',u.MaterialProperty.MP_NORMAL)
L.recompile_material(m);land.set_editor_property('landscape_material',m)
# Only the landscape material changes. Existing crossing meshes and treatments stay assigned as-is.
u.EditorAssetLibrary.save_asset(D+'/M_LandBridgeRoad50_Surface');le.save_current_level()
mid=segs[len(segs)//2];start=segs[0]
views=[('01-connection-close',V(start[0]+460,start[1]-460,1100),V(start[0]+30,start[1]+150,720)),('02-full-stretch-strategy',V(mid[0]+2600,mid[1]-2900,4800),V(mid[0],mid[1],800))]
for name,loc,target in views:
 c=es.spawn_actor_from_class(u.CameraActor,loc,u.MathLibrary.find_look_at_rotation(loc,target));c.set_actor_label('LandBridgeRoad50_'+name);c.set_folder_path('RoadsPaths_01/Cameras');c.camera_component.set_field_of_view(55 if 'strategy' in name else 50)
le.save_current_level();le.editor_set_viewport_realtime(True)
exec((R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Scripts/capture_landbridge_road50.py').read_text(),{'__name__':'__main__'})
