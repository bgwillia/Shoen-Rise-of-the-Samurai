import unreal as u
from pathlib import Path
L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem)
land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape))
src=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_InterruptedShoulders')
dest='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_ApproachCoverage'
m=u.load_asset(dest) or u.EditorAssetLibrary.duplicate_asset(src.get_path_name().split('.')[0],dest)
nodes={n.get_name():n for n in L.get_material_expressions(m)}
original={n.get_name():n.get_editor_property('code') for n in L.get_material_expressions(src) if isinstance(n,u.MaterialExpressionCustom)}
# Same route and existing gravel fan width; extend only its south taper.
nodes['MaterialExpressionCustom_14'].set_editor_property('code',original['MaterialExpressionCustom_14'].replace('smoothstep(-25,440,Q.x)','smoothstep(-25,P.y<-6500?690:440,Q.x)').replace('(1-smoothstep(440,490,Q.x))','(1-smoothstep(P.y<-6500?640:440,P.y<-6500?720:490,Q.x))'))
nodes['MaterialExpressionCustom_29'].set_editor_property('code',original['MaterialExpressionCustom_29'].replace('smoothstep(-25,440,Q.x)','smoothstep(-25,690,Q.x)'))
# Broaden the worn earth only through the approach, keeping the existing texture.
c=original['MaterialExpressionCustom_15']
c='float widen=1+(P.y<-6500?.48:0)*(1-smoothstep(30,690,Q.x));\n'+c
c=c.replace('float u=saturate(.5+Q.y/200);','float u=saturate(.5+Q.y/(200*widen));').replace('smoothstep(75,103,abs(Q.y))','smoothstep(75*widen,103*widen,abs(Q.y))')
nodes['MaterialExpressionCustom_15'].set_editor_property('code',c)
# Extend the approved grass coverage in offset lobes; exclude the road corridor.
c=original['MaterialExpressionCustom_24']
old='return lerp(existing,max(existing,greener),area);'
extra='''float prior=lerp(existing,max(existing,greener),area);
float2 delta=W.xy-float2(-24000,-7120);
float along=dot(delta,float2(-.42,-.907524));
float side=dot(delta,float2(.907524,-.42));
float width=lerp(335,95,smoothstep(-25,690,along));
float r1=length(float2((along-410)/215,(side-390)/220));
float r2=length(float2((along-710)/180,(side-305)/180));
float r3=length(float2((along-530)/150,(side+360)/145));
float rag=.07*sin(W.x*.027+W.y*.015)+.045*sin(W.y*.052);
float lobes=1-smoothstep(.60,1.0,min(min(r1,r2),r3)+rag);
float safe=smoothstep(width+65,width+110,abs(side));
float patch=lobes*safe*smoothstep(30,100,along)*(1-smoothstep(850,990,along));
return max(prior,patch*smoothstep(.23,.47,v)*connected);
'''
assert old in c
nodes['MaterialExpressionCustom_24'].set_editor_property('code',c.replace(old,extra))
L.recompile_material(m);land.set_editor_property('landscape_material',m)
u.EditorAssetLibrary.save_loaded_asset(m)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
Path('/private/tmp/approach-applied.txt').write_text(m.get_path_name())
