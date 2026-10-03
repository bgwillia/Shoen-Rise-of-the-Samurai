import unreal as u,json,time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');L=u.MaterialEditingLibrary;es=u.get_editor_subsystem(u.EditorActorSubsystem);le=u.get_editor_subsystem(u.LevelEditorSubsystem)
m=next(a for a in es.get_all_level_actors() if isinstance(a,u.Landscape)).get_editor_property('landscape_material');ns=L.get_material_expressions(m)
foot=next(n for n in ns if n.get_editor_property('desc')=='BankStudy100_100m_length_50m_inland_dry_only');soil=next(n for n in ns if n.get_name()=='MaterialExpressionCustom_19')
# Close the entire shore gap on both banks, including the confluence-side circled ribbons.
# The expanded band is soil above the local waterline and existing gravel below it.
region='''float section=smoothstep(0,180,Q.y)*(1-smoothstep(9820,10000,Q.y));
section*=1-smoothstep(-19500,-19200,W.x);
section*=smoothstep(-900,-750,Q.x)*(1-smoothstep(500,700,Q.x));\n'''
backup=json.loads((R/'artifacts/riverbanks-ground/gap-fix/material-before.json').read_text())
foot.set_editor_property('code',backup['foot'].replace('return dry*ends*outside;',region+'return max(dry*ends*outside,section);'))
soilcode=backup['soil'].replace('return lerp','float3 earth=lerp')
soil.set_editor_property('code',soilcode+'\n'+region+'''float2 guv=float2(W.x*.9563-W.y*.2924,W.x*.2924+W.y*.9563)/78;
float3 gravel=lerp(float3(.245,.203,.164),Texture2DSample(G,GSampler,guv).rgb,.78);
float above=smoothstep(2,18,W.z-Q.z);
gravel*=lerp(.84,1,above);
return lerp(earth,lerp(gravel,earth,above),section);''')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
le.eject_pilot_level_actor();le.editor_set_viewport_realtime(True)
c=next(a for a in es.get_all_level_actors() if a.get_actor_label()=='BankGap_OneSection_SameAngle');c.set_actor_location(u.Vector(-21600,-4900,6100),False,False);c.set_actor_rotation(u.Rotator(pitch=-90,yaw=90),False)
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(c.get_actor_location(),c.get_actor_rotation());le.save_current_level()
s={'at':time.monotonic()+6}
def capture(dt):
 if time.monotonic()<s['at']:return
 u.unregister_slate_post_tick_callback(s['h']);s['task']=u.AutomationLibrary.take_high_res_screenshot(2004,1076,str(R/'artifacts/riverbanks-ground/gap-fix/all-ribbons-after.png'),camera=c,delay=0)
s['h']=u.register_slate_post_tick_callback(capture)
