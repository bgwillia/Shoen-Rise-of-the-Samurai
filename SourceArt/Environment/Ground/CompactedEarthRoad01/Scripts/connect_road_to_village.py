import unreal as u,json,math
from pathlib import Path
rows=json.loads(Path('/private/tmp/connection-splines.json').read_text());by={a['name']:a for a in rows};base=json.loads(Path('/private/tmp/village-connection-material.json').read_text())
oldend=(-23829.4069295,-12104.3059783)
pts=[oldend]+[tuple(by['RP01_Village_FordLumberBranch_%03d'%i]['p'][:2]) for i in range(62,-1,-1)]
junction=len(pts)-1
pts += [tuple(by['RP01_MainRoad_ProvinceToOutlying_%03d'%i]['p'][:2]) for i in range(160,249) if 'RP01_MainRoad_ProvinceToOutlying_%03d'%i in by]
# Round only the meeting of the two established routes, within the existing junction.
p=pts[junction];a=pts[junction-3];b=pts[junction+3]
fillet=[tuple((1-t)**2*a[k]+2*(1-t)*t*p[k]+t*t*b[k] for k in range(2)) for t in [.2,.4,.6,.8]]
pts=pts[:junction-2]+fillet+pts[junction+3:]
# Sample a smooth interpolation of the existing centreline; never displace terrain.
sampled=[pts[0]]
for i in range(len(pts)-1):
 p0=pts[max(i-1,0)];p1=pts[i];p2=pts[i+1];p3=pts[min(i+2,len(pts)-1)]
 if math.dist(p1,p2)>1000: # existing wooden bridge span remains straight
  sampled.append(p2);continue
 for j in range(1,4):
  t=j/3;sampled.append(tuple(.5*((2*p1[k])+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t*t*t) for k in range(2)))
segments=[];station=5223.57306
for a,b in zip(sampled,sampled[1:]):
 l=math.dist(a,b);segments.append((a,b,station,l));station+=l
end=station
src='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_VillageRoad40_ConnectedGrass';dest='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_VillageEntrance_ConnectedRoad'
m=u.load_asset(dest) or u.EditorAssetLibrary.duplicate_asset(src,dest);L=u.MaterialEditingLibrary;nodes={n.get_name():n for n in L.get_material_expressions(m)}
extra=''
for a,b,s,l in segments:
 extra+='''{float2 a=float2(%f,%f),d=float2(%f,%f);float len=length(d);float t=saturate(dot(P.xy-a,d)/dot(d,d));float2 q=P.xy-a-t*d;float ds=dot(q,q);if(ds<best){best=ds;along=%f+dot(P.xy-a,d)/len;side=sqrt(ds)*(dot(q,float2(-d.y,d.x))<0?-1:1);dir=d/len;}}\n'''%(a[0],a[1],b[0]-a[0],b[1]-a[1],s)
nodes['MaterialExpressionCustom_13'].set_editor_property('code',base['MaterialExpressionCustom_13'].replace('return float4(along,side,dir);}',extra+'return float4(along,side,dir);}',1))
# Continue the original world-scaled surface across the old end fade.
c=base['MaterialExpressionCustom_14'].replace('smoothstep(4823.57306,5223.57306,Q.x)',f'smoothstep({end-600:.6f},{end:.6f},Q.x)')
# Preserve the separate wooden bridge and its deck; no road painted on its river bed.
bridge='(smoothstep(-10820,-10500,P.x)*(1-smoothstep(-6920,-6630,P.x))*(1-smoothstep(-24000,-23500,P.y)))'
c=c.replace('return float3(keep,t,footprint*end*','return float3(keep,t,footprint*end*(1-'+bridge+')*')
# Slow width changes over the new length, joining the previous profile gently.
profile='float extraWidth=1+step(P.y,-6500)*smoothstep(4800,5600,Q.x)*(.035*sin((Q.x-5200)*.0011)-.025*sin((Q.x-5200)*.0023));\nrefinedWidth*=extraWidth;\n'
pos=c.index('float length=');c=c[:pos]+profile+c[pos:];nodes['MaterialExpressionCustom_14'].set_editor_property('code',c)
c=base['MaterialExpressionCustom_15'];pos=c.index('float widen=');c=c[:pos]+profile+c[pos:];nodes['MaterialExpressionCustom_15'].set_editor_property('code',c)
for key in ['MaterialExpressionCustom_24','MaterialExpressionCustom_25']:
 c=base[key].replace('smoothstep(4350,5223.57306,Road.x)',f'smoothstep({end-950:.6f},{end:.6f},Road.x)')
 # Gradually meet the original terrain outside the road corridor, using existing grass and soil.
 old='float band=1-smoothstep(edgeWidth-120,edgeWidth,abs(Road.y));'
 new=old+'''\nfloat onward=smoothstep(4800,5700,Road.x);\nfloat softBand=1-smoothstep(370,980,abs(Road.y));\nband=lerp(band,softBand,onward);\n'''
 c=c.replace(old,new)
 c=c.replace('float extension=', 'float extension=')
 # No new grassy cover on the wooden-bridge span or below river level nearby.
 c=c.replace('float edgeWidth=',f'extension*=1-{bridge.replace("P.","W.")};\nfloat edgeWidth=')
 nodes[key].set_editor_property('code',c)
# Replace the old wide raster road beneath this surface, rather than drawing a strip on it.
c=base['MaterialExpressionCustom_29']
c=c.replace('return float4(Old.r,lerp(Old.g,f,region),Old.b,Old.a);','float4 oldWeights=float4(Old.r,lerp(Old.g,f,region),Old.b,Old.a);')
c+=f"\nfloat replaceOld=smoothstep(4800,5650,Q.x)*(1-smoothstep({end-900:.6f},{end:.6f},Q.x))*step(P.y,-6500)*(1-smoothstep(350,680,abs(Q.y)))*(1-{bridge});\nreturn lerp(oldWeights,float4(0,0,0,oldWeights.a),replaceOld);"
nodes['MaterialExpressionCustom_29'].set_editor_property('code',c)
L.recompile_material(m)
land=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.Landscape));land.set_editor_property('landscape_material',m)
u.EditorAssetLibrary.save_loaded_asset(m);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
Path('/private/tmp/village-connection-built.json').write_text(json.dumps({'end':end,'segments':segments,'material':dest,'endpoint':sampled[-1]}))
