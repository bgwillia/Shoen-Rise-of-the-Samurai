import unreal as u,math,json
from pathlib import Path
L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);ed=u.get_editor_subsystem(u.UnrealEditorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem);V=u.Vector
actors=es.get_all_level_actors();land=next(a for a in actors if isinstance(a,u.Landscape))
src=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_ApproachCoverage')
dest='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_VillageRoad40_ConnectedGrass'
m=u.load_asset(dest) or u.EditorAssetLibrary.duplicate_asset(src.get_path_name().split('.')[0],dest)
nodes={n.get_name():n for n in L.get_material_expressions(m)}
original={n.get_name():n.get_editor_property('code') for n in L.get_material_expressions(src) if isinstance(n,u.MaterialExpressionCustom)}
# Continue the existing south route from its finished approach, using existing road vertices.
pts=[(-24630.404278,-8497.472287)]
for i in range(76,59,-1):
 a=next(a for a in actors if a.get_actor_label()=='RP01_Village_FordLumberBranch_%03d'%i);p=a.get_actor_location();pts.append((p.x,p.y))
segments=[];along=1523.57306;end=5223.57306
for a,b in zip(pts,pts[1:]):
 length=math.dist(a,b)
 if along+length>end:
  t=(end-along)/length;b=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t);length=end-along
 segments.append((a,b,along,length));along+=length
 if along>=end:break
extra=''
for a,b,s,length in segments:
 extra+='''{float2 a=float2(%f,%f),d=float2(%f,%f);float len=length(d);float t=saturate(dot(P.xy-a,d)/dot(d,d));float2 q=P.xy-a-t*d;float ds=dot(q,q);if(ds<best){best=ds;along=%f+dot(P.xy-a,d)/len;side=dot(q,float2(-d.y,d.x)/len);dir=d/len;}}\n'''%(a[0],a[1],b[0]-a[0],b[1]-a[1],s)
c=original['MaterialExpressionCustom_13'];c=c.replace('return float4(along,side,dir);}',extra+'return float4(along,side,dir);}',1);nodes['MaterialExpressionCustom_13'].set_editor_property('code',c)
c=original['MaterialExpressionCustom_14'].replace('smoothstep(1243.57306,1523.57306,Q.x)','smoothstep(4823.57306,5223.57306,Q.x)')
# Continue the existing two metre road coverage with a short end fade.
c=c.replace('float footprint=max(W.g,fan);','float continuation=smoothstep(1120,1370,Q.x)*(1-smoothstep(4823.57306,5223.57306,Q.x))*step(P.y,-6500);\nfloat corridor=1-smoothstep(92,125,abs(Q.y));\nfloat footprint=lerp(max(W.g,fan),corridor,continuation);')
nodes['MaterialExpressionCustom_14'].set_editor_property('code',c)
c=original['MaterialExpressionCustom_15'].replace('smoothstep(350,490,Q.x)*step(-6500,P.y)','smoothstep(350,490,Q.x)*max(step(-6500,P.y),smoothstep(1120,1370,Q.x))')
nodes['MaterialExpressionCustom_15'].set_editor_property('code',c)
# Reuse the approved soil/short-grass material branches and masks.
for key in ['MaterialExpressionCustom_24','MaterialExpressionCustom_25']:
 n=nodes[key];ins=list(n.get_editor_property('inputs'))
 if not any(str(i.get_editor_property('input_name'))=='Road' for i in ins):
  i=u.CustomInput();i.set_editor_property('input_name','Road');ins.append(i);n.set_editor_property('inputs',ins)
 L.connect_material_expressions(nodes['MaterialExpressionCustom_13'],'',n,'Road')
area='float extension=smoothstep(1120,1450,Road.x)*(1-smoothstep(4350,5223.57306,Road.x))*step(W.y,-6500);\nfloat edgeWidth=650+55*sin(Road.x*.006)+30*sin(Road.x*.014);\nfloat band=1-smoothstep(edgeWidth-120,edgeWidth,abs(Road.y));\n'
c=original['MaterialExpressionCustom_24'];pos=c.rfind('return ');c=c[:pos]+area+c[pos:];c=c.replace('return max(prior,patch*smoothstep(.23,.47,v)*connected);','float old=max(prior,patch*smoothstep(.23,.47,v)*connected);\nfloat cover=smoothstep(.19,.31,v);\nfloat verge=smoothstep(135,205,abs(Road.y));\nreturn lerp(old,cover*verge,extension*band);')
nodes['MaterialExpressionCustom_24'].set_editor_property('code',c)
c=original['MaterialExpressionCustom_25'];pos=c.rfind('return ');c=c[:pos]+area+c[pos:];c=c.replace('return max(dry*ends*outside,section);','return max(max(dry*ends*outside,section),extension*band);');nodes['MaterialExpressionCustom_25'].set_editor_property('code',c)
L.recompile_material(m);land.set_editor_property('landscape_material',m);u.EditorAssetLibrary.save_loaded_asset(m)
# Five separated groups, upright, on terrain-traced ground; no rocks added.
world=ed.get_editor_world();ignore=[a for a in actors if not isinstance(a,u.Landscape)]
short=u.load_asset('/Game/Art/Environment/Vegetation/Grass/RiverbankGrass01/RiverbankGrass_01');tall=u.load_asset('/Game/Art/Environment/Vegetation/Grass/RiverbankGrassMedium01/RiverbankGrass_Medium_01')
def at(s,offset):
 for a,b,start,length in segments:
  if s<=start+length:
   t=max(0,min(1,(s-start)/length));dx=(b[0]-a[0])/length;dy=(b[1]-a[1])/length
   return a[0]+(b[0]-a[0])*t-dy*offset,a[1]+(b[1]-a[1])*t+dx*offset
 raise RuntimeError('Placement outside road section')
records=[]
groups=[(1750,265),(2460,-310),(3120,350),(3960,-280),(4550,320)]
shapes=[(-45,0),(0,12),(32,-15),(60,32),(-15,47),(28,65)]
for gi,(s,side) in enumerate(groups):
 for j,(ds,do) in enumerate(shapes):
  x,y=at(s+ds,side+do);hit=u.SystemLibrary.line_trace_single(world,V(x,y,5000),V(x,y,-2000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True)
  h=hit.to_tuple();assert h[0],(x,y);z=h[5].z
  label='VillageRoad40_Grass_%02d_%02d'%(gi,j)
  a=next((a for a in actors if a.get_actor_label()==label),None) or es.spawn_actor_from_class(u.StaticMeshActor,V(x,y,z-1.5))
  isTall=(j==4 and gi in [0,2,4]);mesh=tall if isTall else short
  a.get_component_by_class(u.StaticMeshComponent).set_static_mesh(mesh);a.set_actor_location(V(x,y,z-(2.2 if isTall else 1.2)),False,False)
  a.set_actor_rotation(u.Rotator(pitch=0,yaw=(gi*79+j*137)%360,roll=0),False);scale=.94+.035*((gi+j)%5);a.set_actor_scale3d(V(scale,scale,scale));a.set_actor_label(label);a.set_folder_path('Environment/VillageRoad40')
  records.append({'label':label,'terrainZ':z,'rootZ':a.get_actor_location().z,'sideClearance':abs(side+do)})
for label,loc,target,fov in [('VillageRoad40_Overview',(-18100,-9150,9500),(-24000,-9000,740),48),('VillageRoad40_Gameplay',(-21900,-10800,3100),(-24350,-10050,835),50)]:
 cam=next((a for a in actors if a.get_actor_label()==label),None) or es.spawn_actor_from_class(u.CameraActor,V(*loc))
 cam.set_actor_location(V(*loc),False,False);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(V(*loc),V(*target)),False);cam.set_actor_label(label);cam.get_component_by_class(u.CameraComponent).set_field_of_view(fov)
le.save_current_level()
Path('/private/tmp/village-road-built.json').write_text(json.dumps({'end':end,'segments':segments,'plants':records}))
