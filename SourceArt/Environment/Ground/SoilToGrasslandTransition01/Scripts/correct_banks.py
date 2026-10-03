import unreal as u,json
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem)
m=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape)).get_editor_property('landscape_material');nodes=L.get_material_expressions(m)
coords=next(n for n in nodes if n.get_editor_property('desc')=='BankStudy100_actual_dry_shores');rows=json.loads(Path('/private/tmp/dry-banks.json').read_text())
code='float best=1e20;float inland=0;float along=0;float water=0;\n'
for i,(r,t) in enumerate(zip(rows,rows[1:])):
 a=r['water'];b=t['water'];widths=[r['banks'][0][-1],r['banks'][1][-1],t['banks'][0][-1],t['banks'][1][-1]]
 code+='''{float2 a=float2(%f,%f),b=float2(%f,%f),v=b-a;float raw=dot(W.xy-a,v)/dot(v,v);float t=saturate(raw);float2 q=W.xy-lerp(a,b,t);float ds=dot(q,q);if(ds<best){best=ds;float side=dot(q,normalize(float2(-v.y,v.x)));float width=side<0?lerp(%f,%f,t):lerp(%f,%f,t);inland=abs(side)-width;along=%f+raw*250;water=lerp(%f,%f,t);}}\n'''%(a[0],a[1],b[0],b[1],widths[0],widths[2],widths[1],widths[3],r['s'],a[2],b[2])
code+='return float3(inland,along,water);';coords.set_editor_property('code',code)
foot=next(n for n in nodes if n.get_editor_property('desc')=='BankStudy100_100m_length_50m_inland_dry_only')
foot.set_editor_property('code','''float edge=190*sin(W.x*.0017+W.y*.0021)+140*sin(W.y*.0043+W.x*.0028);
float nearWater=smoothstep(14,32,W.z-Q.z);
float dry=smoothstep(60,115,Q.x)*lerp(nearWater,1,smoothstep(200,550,Q.x))*smoothstep(440,468,W.z);
float ends=smoothstep(-120,850,Q.y+edge)*(1-smoothstep(9050,10000,Q.y+edge));
float outside=1-smoothstep(3100,4800,Q.x+edge*2);
return dry*ends*outside;''')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec((R/'SourceArt/Environment/Ground/SoilToGrasslandTransition01/Scripts/capture_banks.py').read_text(),{'__name__':'banks_capture_final'})
