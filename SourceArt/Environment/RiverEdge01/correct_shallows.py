import unreal as u
L=u.MaterialEditingLibrary
m=u.load_asset('/Game/Art/Environment/RoadsPaths01/M_RP01_TributaryFordSurface')
n=L.get_material_property_input_node(m,u.MaterialProperty.MP_OPACITY)
n.set_editor_property('code','''float2 q=W.xy-float2(-23600,-6300);
float t=dot(q,float2(.42,.907524));float s=dot(q,float2(-.907524,.42));
float f=(1-smoothstep(750,1200,abs(t)))*(1-smoothstep(180,340,abs(s)));
float shore=smoothstep(-180,-110,t)*(1-smoothstep(350,420,t))*smoothstep(-570,-410,s)*(1-smoothstep(-220,-170,s));
return Base*(1-f*.86)*(1-shore*.55);''')
L.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
es=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in es.get_all_level_actors():
 if a.get_actor_label().startswith('RiverEdge_01_Stone_'):
  p=a.get_actor_location();a.set_actor_location(p-u.Vector(0,0,14),False,False)
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec(open('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai/SourceArt/Environment/RiverEdge01/capture_views.py').read())
