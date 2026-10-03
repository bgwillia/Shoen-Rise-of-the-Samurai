import unreal as u
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');D='/Game/Art/Environment/Ground/RiverGravel01';L=u.MaterialEditingLibrary
nt=u.AssetImportTask();nt.filename=str(R/'SourceArt/Environment/Ground/RiverGravel01/Textures/T_RiverGravel01_Normal.png');nt.destination_path=D;nt.automated=True;nt.replace_existing=True;nt.save=True;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([nt]);normal=u.load_asset(D+'/T_RiverGravel01_Normal');normal.set_editor_property('srgb',False);normal.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP);normal.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO);normal.set_editor_property('address_x',u.TextureAddress.TA_MIRROR);normal.set_editor_property('address_y',u.TextureAddress.TA_MIRROR)
# Replace brightness-derived bump with the aligned pebble normal, keeping bank blend.
for path in [D+'/M_RiverGravel_01',D+'/M_RiverGravel01_Bank']:
 m=u.load_asset(path);p=L.create_material_expression(m,u.MaterialExpressionWorldPosition)
 uv=L.create_material_expression(m,u.MaterialExpressionCustom);uv.set_editor_property('code','return float2(W.x*.9563-W.y*.2924,W.x*.2924+W.y*.9563)/78.0;');uv.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT2);inp=u.CustomInput();inp.set_editor_property('input_name','W');uv.set_editor_property('inputs',[inp]);L.connect_material_expressions(p,'',uv,'W')
 ts=L.create_material_expression(m,u.MaterialExpressionTextureSample);ts.set_editor_property('texture',normal);ts.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL);L.connect_material_expressions(uv,'',ts,'UVs')
 strength=L.create_material_expression(m,u.MaterialExpressionCustom);strength.set_editor_property('code','float2 xy=float2(N.x*.9563+N.y*.2924,-N.x*.2924+N.y*.9563)*.72; return normalize(float3(xy,max(.35,N.z)));');inp=u.CustomInput();inp.set_editor_property('input_name','N');strength.set_editor_property('inputs',[inp]);strength.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3);L.connect_material_expressions(ts,'RGB',strength,'N')
 old=L.get_material_property_input_node(m,u.MaterialProperty.MP_NORMAL)
 if path.endswith('_Bank'):L.connect_material_expressions(strength,'',old,'B')
 else:L.connect_material_property(strength,'',u.MaterialProperty.MP_NORMAL)
 L.recompile_material(m)
# Hand-place a few low existing fragments in the review square; no scatter system.
es=u.get_editor_subsystem(u.EditorActorSubsystem);aa=es.get_all_level_actors();patch=next(a for a in aa if a.get_actor_label()=='RiverGravel_01_1mReviewPatch');pp=patch.get_actor_location();mesh=u.load_asset('/Game/Art/Environment/Rocks/RiverRock02/RiverRock_02');stone=u.load_asset('/Game/Art/Environment/Rocks/RiverRock01/M_RiverRock01_DetailedStone')
for i,(x,y,s,rz) in enumerate([(-36,-22,.065,38),(-17,31,.05,14),(34,25,.075,81),(22,-30,.06,149),(-28,2,.048,59),(3,-8,.07,31),(11,40,.055,172),(-44,38,.07,61)]):
 a=es.spawn_actor_from_class(u.StaticMeshActor,pp+u.Vector(x,y,-.45),u.Rotator(yaw=rz));a.set_actor_label('RiverGravel01_ReviewFragment_'+str(i));a.set_folder_path('RiverGravel01');a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_material(0,stone);a.set_actor_scale3d(u.Vector(s,s*.87,s*.6));a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
pair=next(a for a in aa if a.get_actor_label()=='RiverGravel01_04-rocks-embedded');target=u.Vector(-23605,-6577,693);pair.set_actor_location(target+u.Vector(110,-270,175),False,False);pair.set_actor_rotation(u.MathLibrary.find_look_at_rotation(pair.get_actor_location(),target),False)
u.EditorAssetLibrary.save_directory(D);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec(open(str(R/'SourceArt/Environment/Ground/RiverGravel01/Scripts/capture_unreal.py')).read())
