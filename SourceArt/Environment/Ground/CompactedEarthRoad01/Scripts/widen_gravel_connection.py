import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary
m=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_LandBridgeRoad50_Surface')
mask=next(n for n in L.get_material_expressions(m) if isinstance(n,u.MaterialExpressionCustom) and 'float length=400' in n.get_editor_property('code'))
mask.set_editor_property('code','''float length=365+45*sin(Q.y*.023)+25*sin(Q.y*.061+1.1);
float t=smoothstep(10,length,Q.x-.24*abs(Q.y)+17*sin(Q.y*.073));
float2 uv=float2(P.x*.9563-P.y*.2924,P.x*.2924+P.y*.9563)/78;
float3 g=Texture2DSample(G,GSampler,uv).rgb;
float h=saturate((dot(g,float3(.3,.59,.11))-.065)*3.3);
float keep=smoothstep(lerp(-.15,1.15,t)-.045,lerp(-.15,1.15,t)+.045,h);
float taper=smoothstep(-25,440,Q.x);
float width=lerp(335,95,taper);
float irregular=11*sin(Q.x*.028+Q.y*.017)+6*sin(Q.x*.061-Q.y*.024);
float fan=(1-smoothstep(width-32,width+18,abs(Q.y)+irregular))*(1-smoothstep(440,490,Q.x));
float footprint=max(W.g,fan);
float end=smoothstep(-120,-55,Q.x)*(1-smoothstep(5207.34249,5357.34249,Q.x));
float bound=lerp(430,270,smoothstep(420,550,Q.x));
return float3(keep,t,footprint*end*(1-smoothstep(bound-50,bound,abs(Q.y))));''')
mask.set_editor_property('desc','Wide gravel apron funnels into existing road; irregular 3–5m coverage transition, original stone scale')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
out=R/'artifacts/landbridge-road50/wide-gravel-connection';out.mkdir(exist_ok=True)
s=(R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Scripts/capture_landbridge_road50.py').read_text().replace('artifacts/landbridge-road50','artifacts/landbridge-road50/wide-gravel-connection')
exec(s,{'__name__':'__main__'})
