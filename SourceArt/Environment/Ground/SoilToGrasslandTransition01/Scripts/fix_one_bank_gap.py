import unreal as u,json
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
land=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape));m=land.get_editor_property('landscape_material');ns=L.get_material_expressions(m)
foot=next(n for n in ns if n.get_editor_property('desc')=='BankStudy100_100m_length_50m_inland_dry_only');soil=next(n for n in ns if n.get_name()=='MaterialExpressionCustom_19');coords=next(n for n in ns if n.get_editor_property('desc')=='BankStudy100_actual_dry_shores')
backup={'material':m.get_path_name(),'foot':foot.get_editor_property('code'),'soil':soil.get_editor_property('code')};(R/'artifacts/riverbanks-ground/gap-fix/material-before.json').write_text(json.dumps(backup,indent=2))
region='''float section=smoothstep(2400,2650,Q.y)*(1-smoothstep(4100,4350,Q.y));
section*=smoothstep(80,200,W.y-(.5*(W.x+24976)-6872));
section*=smoothstep(-650,-500,Q.x)*(1-smoothstep(230,380,Q.x));\n'''
code=foot.get_editor_property('code').replace('return dry*ends*outside;',region+'return max(dry*ends*outside,section);')
foot.set_editor_property('code',code)
inputs=list(soil.get_editor_property('inputs'))
for name in ['Q','G']:
 e=u.CustomInput();e.set_editor_property('input_name',name);inputs.append(e)
soil.set_editor_property('inputs',inputs)
texture=L.create_material_expression(m,u.MaterialExpressionTextureObject);texture.set_editor_property('texture',u.load_asset('/Game/Art/Environment/Ground/RiverGravel01/T_RiverGravel01_BaseColor'));texture.set_editor_property('desc','One circled section: existing riverbed gravel')
L.connect_material_expressions(texture,'',soil,'G');L.connect_material_expressions(coords,'',soil,'Q')
old=soil.get_editor_property('code');old=old.replace('return lerp','float3 earth=lerp')
soil.set_editor_property('code',old+'\n'+region+'''float2 guv=float2(W.x*.9563-W.y*.2924,W.x*.2924+W.y*.9563)/78;
float3 gravel=lerp(float3(.245,.203,.164),Texture2DSample(G,GSampler,guv).rgb,.78);
float above=smoothstep(2,18,W.z-Q.z);
gravel*=lerp(.84,1,above);
return lerp(earth,lerp(gravel,earth,above),section);''')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
# Match the supplied top-down angle and frame the crossing toward the lower right.
le.eject_pilot_level_actor();c=es.spawn_actor_from_class(u.CameraActor,u.Vector(-21600,-4900,6100),u.Rotator(pitch=-90,yaw=90));c.set_actor_label('BankGap_OneSection_SameAngle');c.set_folder_path('GroundBankStudy/Views');c.camera_component.set_field_of_view(90);c.camera_component.set_editor_property('post_process_blend_weight',0)
le.save_current_level();le.editor_set_viewport_realtime(True)
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(c.get_actor_location(),c.get_actor_rotation())
import time
st={'at':time.monotonic()+8}
def capture(dt):
 if time.monotonic()<st['at']:return
 u.unregister_slate_post_tick_callback(st['handle']);st['task']=u.AutomationLibrary.take_high_res_screenshot(2004,1076,str(R/'artifacts/riverbanks-ground/gap-fix/one-section-after.png'),camera=c,delay=0)
st['handle']=u.register_slate_post_tick_callback(capture)
