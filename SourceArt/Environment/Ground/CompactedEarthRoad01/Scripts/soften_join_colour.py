import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape));source=land.get_editor_property('landscape_material');D='/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_SoftColourJoins'
m=u.load_asset(D) or u.EditorAssetLibrary.duplicate_asset(source.get_path_name().split('.')[0],D)
c=next(n for n in L.get_material_expressions(m) if n.get_name()=='MaterialExpressionCustom_15')
c.set_editor_property('code','''float u=saturate(.5+Q.y/200);
float v=abs(frac(Q.x/800)*2-1);
float v2=abs(frac((Q.x+137)/800)*2-1);
float3 a=Texture2DSample(R,RSampler,float2(u,v)).rgb;
float3 b=Texture2DSample(R,RSampler,float2(1-u,v2)).rgb;
float breakup=.22+.12*sin(Q.x*.0023+Q.y*.013);
float3 road=lerp(a,b,breakup);
float3 soil=lerp(float3(.188,.150,.109),Texture2DSample(Soil,SoilSampler,P.xy/100).rgb,.70);
float shoulder=smoothstep(75,103,abs(Q.y));
road=lerp(road,soil,shoulder);
float2 guv=float2(P.x*.9563-P.y*.2924,P.x*.2924+P.y*.9563)/78;
float wet=(1-smoothstep(635,699,P.z+3*sin(P.x*.031)*sin(P.y*.022)))*.65;
float macro=1+.035*sin(P.x*.007+sin(P.y*.005))+.02*sin(P.y*.013);
float lightness=macro*(1-wet*.24);
float3 g=lerp(float3(.245,.203,.164),Texture2DSample(G,GSampler,guv).rgb,.78);
float3 gm=lerp(float3(.245,.203,.164),Texture2DSampleLevel(G,GSampler,guv,12).rgb,.78)*lightness;
float3 rm=lerp(Texture2DSampleLevel(R,RSampler,float2(u,v),6).rgb,Texture2DSampleLevel(R,RSampler,float2(1-u,v2),6).rgb,breakup);
float3 sm=lerp(float3(.188,.150,.109),Texture2DSampleLevel(Soil,SoilSampler,float2(.5,.5),12).rgb,.70);
rm=lerp(rm,sm,shoulder);
float join=1-smoothstep(40,520+35*sin(Q.y*.017),Q.x);
road*=lerp(float3(1,1,1),clamp(gm/max(rm,float3(.02,.02,.02)),.5,2.0),join);
g*=lerp(1,lightness,join);
float3 c=lerp(road,g,M.x);
return lerp(Base,c,M.z);''')
c.set_editor_property('desc','Match road midtone to adjacent gravel at both bridge joins; preserve grain and return to earth colour over five metres')
L.recompile_material(m);land.set_editor_property('landscape_material',m);u.EditorAssetLibrary.save_loaded_asset(m);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
cam=next(a for a in es.get_all_level_actors() if a.get_actor_label()=='LandBridgeSouth_Overhead')
u.AutomationLibrary.take_high_res_screenshot(1600,900,str(R/'artifacts/landbridge-colour/after-close.png'),camera=cam,delay=0,force_game_view=True)
