import unreal as u,json,math
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem);V=u.Vector
land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape));m=land.get_editor_property('landscape_material');original=list(L.get_material_expressions(m));byname={n.get_name():n for n in original}
# Existing landscape material only. Original material assets, roads and gravel layers stay intact.
def node(cls,desc='BankStudy100_coverage'):
 n=L.create_material_expression(m,cls);n.set_editor_property('desc',desc);return n
def custom(code,names,typ=u.CustomMaterialOutputType.CMOT_FLOAT3,desc='BankStudy100_coverage'):
 n=node(u.MaterialExpressionCustom,desc);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);ii=[]
 for name in names:
  z=u.CustomInput();z.set_editor_property('input_name',name);ii.append(z)
 n.set_editor_property('inputs',ii);return n
def link(a,b,k,out=''):L.connect_material_expressions(a,out,b,k)
p=node(u.MaterialExpressionWorldPosition)
rows=json.loads(Path('/private/tmp/dry-banks.json').read_text());code='float best=1e20;float inland=0;float along=0;float water=0;\n'
for side in range(2):
 for r,t in zip(rows,rows[1:]):
  a=r['banks'][side];b=t['banks'][side];norm=[(a[3]+b[3])*.5,(a[4]+b[4])*.5]
  code+='''{float2 a=float2(%f,%f),b=float2(%f,%f),v=b-a;float t=saturate(dot(W.xy-a,v)/dot(v,v));float2 q=W.xy-lerp(a,b,t);float ds=dot(q,q);if(ds<best){best=ds;inland=dot(q,normalize(float2(%f,%f)));along=%f+t*250;water=lerp(%f,%f,t);}}\n'''%(a[0],a[1],b[0],b[1],norm[0],norm[1],r['s'],r['water'][2],t['water'][2])
code+='return float3(inland,along,water);'
coords=custom(code,['W'],desc='BankStudy100_actual_dry_shores');link(p,coords,'W')
# Exactly the approved soil/grass shading, at its original texture scale.
def surface(path):
 src=u.load_asset(path);ns=L.get_material_expressions(src)
 uvsrc=next(n for n in ns if isinstance(n,u.MaterialExpressionCustom) and 'W.xy' in n.get_editor_property('code'))
 uv=custom(uvsrc.get_editor_property('code'),['W'],u.CustomMaterialOutputType.CMOT_FLOAT2);link(p,uv,'W')
 tx=node(u.MaterialExpressionTextureObject);tx.set_editor_property('texture',next(n for n in ns if isinstance(n,u.MaterialExpressionTextureObject)).get_editor_property('texture'))
 c=custom(L.get_material_property_input_node(src,u.MaterialProperty.MP_BASE_COLOR).get_editor_property('code'),['T','UV','W']);link(tx,c,'T');link(uv,c,'UV');link(p,c,'W')
 n=custom(L.get_material_property_input_node(src,u.MaterialProperty.MP_NORMAL).get_editor_property('code'),['T','UV']);link(tx,n,'T');link(uv,n,'UV');return c,n
soil,sn=surface('/Game/Art/Environment/Ground/RiverbankSoil01/M_RiverbankSoil_01');grass,gn=surface('/Game/Art/Environment/Ground/GrasslandGround01/M_GrasslandGround_01')
source=u.load_asset('/Game/Art/Environment/Ground/MixedGround01/M_MixedGround_01');mixed=next(n for n in L.get_material_expressions(source) if isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('desc')=='MixedGround_01 soft connected coverage').get_editor_property('code')
# Connected patches at metre scale, with the same fine edge detail as MixedGround_01.
field=mixed[:mixed.rfind('return smoothstep')].replace('W.xy/16.0','W.xy/135.0')
field+='''
float wave=65*sin(W.x*.0023+W.y*.0017)+35*sin(W.y*.0051-W.x*.0011);
float d=Q.x-95;
float entry=smoothstep(25,155,d+wave*.38);
float full=smoothstep(110,820+180*sin(Q.y*.0013),d+wave);
float threshold=lerp(.55,.19,full);
return entry*smoothstep(threshold-.10,threshold+.10,v);
'''
mask=custom(field,['W','Q'],u.CustomMaterialOutputType.CMOT_FLOAT1,desc='BankStudy100_short_brown_mixed_then_green');link(p,mask,'W');link(coords,mask,'Q')
foot=custom('''float edge=100*sin(W.x*.0017+W.y*.0021)+60*sin(W.y*.0043);
float dry=smoothstep(65,120,Q.x)*smoothstep(14,32,W.z-Q.z);
float ends=smoothstep(0,550,Q.y+edge)*(1-smoothstep(9450,10000,Q.y+edge));
float outside=1-smoothstep(3950,5000,Q.x+edge*2);
return dry*ends*outside;''',['W','Q'],u.CustomMaterialOutputType.CMOT_FLOAT1,desc='BankStudy100_100m_length_50m_inland_dry_only');link(p,foot,'W');link(coords,foot,'Q')
def mix(a,b,alpha):
 n=node(u.MaterialExpressionLinearInterpolate);link(a,n,'A');link(b,n,'B');link(alpha,n,'Alpha');return n
surface_color=mix(soil,grass,mask)
# Insert under the pre-existing road and gravel compositing, leaving those upper layers unchanged.
base=byname['MaterialExpressionCustom_2'];color=mix(base,surface_color,foot);link(color,byname['MaterialExpressionCustom_3'],'Base')
# Preserve existing landscape normals at distance; add approved subtle surface normal only on this dry treatment.
oldnormal=L.get_inputs_for_material_expression(m,byname['MaterialExpressionCustom_4'])[0]
normal=mix(oldnormal,mix(sn,gn,mask),foot);link(normal,byname['MaterialExpressionCustom_4'],'Base')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
# Only two study cameras are added. No ground, grass, rock or water actors are changed.
views=[('BanksGround_01-overview',(-18500,-16500,14500),(-23600,-6300,850)),('BanksGround_02-close',(-21800,-8550,2150),(-23600,-6400,730))]
for name,loc,target in views:
 c=next((a for a in es.get_all_level_actors() if a.get_actor_label()==name),None) or es.spawn_actor_from_class(u.CameraActor,V(*loc));c.set_actor_label(name);c.set_folder_path('GroundBankStudy/Views');c.set_actor_location(V(*loc),False,False);c.set_actor_rotation(u.MathLibrary.find_look_at_rotation(V(*loc),V(*target)),False);c.camera_component.set_field_of_view(55);c.camera_component.set_editor_property('post_process_blend_weight',0)
le.save_current_level();le.eject_pilot_level_actor();le.editor_set_viewport_realtime(True)
exec((R/'SourceArt/Environment/Ground/SoilToGrasslandTransition01/Scripts/capture_banks.py').read_text(),{'__name__':'banks_capture'})
