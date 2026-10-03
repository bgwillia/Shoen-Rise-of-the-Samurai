import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/CompactedEarthRoad01';L=u.MaterialEditingLibrary
m=u.load_asset(D+'/M_CompactedEarthRoad_01')
t=u.AssetImportTask();t.filename=str(R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Textures/T_CompactedEarthRoad01_BaseColor.png');t.destination_path=D;t.automated=True;t.replace_existing=True;t.save=True
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);tex=u.load_asset(D+'/T_CompactedEarthRoad01_BaseColor');tex.set_editor_property('srgb',True);tex.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO);tex.set_editor_property('address_x',u.TextureAddress.TA_CLAMP);tex.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
L.delete_all_material_expressions(m)
def node(c):return L.create_material_expression(m,c)
def link(a,o,b,i):L.connect_material_expressions(a,o,b,i)
def custom(code,ins,typ=u.CustomMaterialOutputType.CMOT_FLOAT3):
 n=node(u.MaterialExpressionCustom);n.set_editor_property('code',code);n.set_editor_property('output_type',typ);entries=[]
 for name in ins:
  e=u.CustomInput();e.set_editor_property('input_name',name);entries.append(e)
 n.set_editor_property('inputs',entries);return n
p=node(u.MaterialExpressionWorldPosition)
r=node(u.MaterialExpressionTextureObject);r.set_editor_property('texture',tex)
s=node(u.MaterialExpressionTextureObject);s.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/RiverbankSoil01/T_RiverbankSoil01_BaseColor'))
code='''float2 uv=float2(P.x/200+.5,.5-P.y/400);
float3 road=Texture2DSample(R,RSampler,uv).rgb;
float2 suv=(P.xy+float2(1.8*sin(P.y*.019),1.8*sin(P.x*.023)))/100+float2(0,.5);
float3 soil=lerp(float3(.188,.150,.109),Texture2DSample(S,SSampler,suv).rgb,.70);
float x=abs(P.x+2*sin(P.y*.055)+1.5*sin(P.y*.113));
float fade=(1-smoothstep(80,102,x))*(1-smoothstep(187,202,abs(P.y)));
return lerp(soil,road,fade);'''
c=custom(code,['P','R','S'])
for a,k in [(p,'P'),(r,'R'),(s,'S')]:link(a,'',c,k)
L.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
n=custom('''float2 uv=float2(P.x/200+.5,.5-P.y/400);float2 e=float2(.0009,.00045);
float gx=dot(Texture2DSample(T,TSampler,uv-float2(e.x,0)).rgb-Texture2DSample(T,TSampler,uv+float2(e.x,0)).rgb,float3(.3,.59,.11));
float gy=dot(Texture2DSample(T,TSampler,uv-float2(0,e.y)).rgb-Texture2DSample(T,TSampler,uv+float2(0,e.y)).rgb,float3(.3,.59,.11));
return normalize(float3(gx*.6,-gy*.6,1));''',['P','T']);link(p,'',n,'P');link(r,'',n,'T');L.connect_material_property(n,'',u.MaterialProperty.MP_NORMAL)
for val,prop in [(.92,u.MaterialProperty.MP_ROUGHNESS),(.16,u.MaterialProperty.MP_SPECULAR)]:
 v=node(u.MaterialExpressionConstant);v.set_editor_property('r',val);L.connect_material_property(v,'',prop)
L.recompile_material(m)
es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
for a in es.get_all_level_actors():
 if a.get_actor_label()=='CompactedEarthRoad01_01-overhead':a.set_actor_location(u.Vector(0,0,1200),False,False)
le.editor_set_viewport_realtime(True)
u.EditorAssetLibrary.save_directory(D);le.save_current_level()
exec((R/'SourceArt/Environment/Ground/CompactedEarthRoad01/Scripts/capture_unreal.py').read_text())
