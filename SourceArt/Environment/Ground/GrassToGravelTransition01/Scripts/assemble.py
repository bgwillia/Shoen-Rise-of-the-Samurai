import unreal as u, time
from pathlib import Path
R=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai'); O=R/'artifacts/grasstograveltransition01'; D='/Game/Art/Environment/Ground/GrassToGravelTransition01'
es=u.get_editor_subsystem(u.EditorActorSubsystem); le=u.get_editor_subsystem(u.LevelEditorSubsystem)
# A separate, hand-assembled review level; preserve the current scene.
le.save_current_level()
u.EditorAssetLibrary.make_directory(D)

if not u.EditorAssetLibrary.does_asset_exist(D+'/GrassToGravelTransition_01'):le.new_level(D+'/GrassToGravelTransition_01')
else:le.load_level(D+'/GrassToGravelTransition_01')
V=u.Vector
# Hand-authored low, irregular perimeter. Existing materials remain untouched.
points=[(-34,-39),(-23,-48),(1,-45),(22,-52),(43,-47),(65,-51),(91,-45),(112,-51),(137,-43),(157,-48),(176,-37),(184,-18),(179,1),(186,20),(172,39),(148,47),(125,43),(102,51),(78,46),(53,50),(30,43),(7,49),(-17,41),(-30,23),(-26,2),(-35,-18)]
obj=R/'SourceArt/Environment/Ground/GrassToGravelTransition01/GrassToGravelTransition_01.obj'
# OBJ centimetres imported at one-to-one scale; a single ground surface avoids overlapping seams.
s=['o GrassToGravelTransition_01','v 75 0 0']+['v %s %s 0'%(x,y) for x,y in points]
s+=['vt .5 .5']+['vt %s %s'%((x+35)/221,(y+52)/104) for x,y in points]
s+=['vn 0 0 1']
for i in range(len(points)):
 a=i+2;b=(i+1)%len(points)+2;s.append('f 1/1/1 %d/%d/1 %d/%d/1'%(a,a,b,b))
obj.write_text('\n'.join(s))
t=u.AssetImportTask(); t.filename=str(obj.with_suffix('.fbx'));t.destination_path=D;t.destination_name="SM_GrassToGravelTransition_01";t.automated=True;t.save=True
opt=u.FbxImportUI(); opt.import_mesh=True;opt.import_materials=False;opt.import_textures=False;opt.import_as_skeletal=False;opt.static_mesh_import_data.set_editor_property('convert_scene',False);t.options=opt
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
mesh=u.load_asset(t.imported_object_paths[0]); O.joinpath('mesh.txt').write_text(str(mesh.get_bounds()))
def place(label,asset,loc,scale=(1,1,1),yaw=0,material=None):
 a=es.spawn_actor_from_class(u.StaticMeshActor,V(*loc),u.Rotator(yaw=yaw));a.set_actor_label(label);a.set_folder_path('GrassToGravelTransition_01');a.static_mesh_component.set_static_mesh(asset);a.set_actor_scale3d(V(*scale))
 if material:a.static_mesh_component.set_material(0,material)
 return a
base=place('GrassToGravelTransition_01',mesh,(0,0,0),material=u.load_asset('/Game/Art/Environment/Ground/RiverbankSoil01/M_RiverbankSoil01_ReviewTransition'))
g=u.load_asset('/Game/Art/Environment/Vegetation/Grass/RiverbankGrass01/RiverbankGrass_01');O.joinpath('grass.txt').write_text(str(g.get_bounds()))
placements=[(-12,-27,1.03,18),(-7,20,.94,137),(12,31,1.08,72),(17,-9,.97,236),(34,-31,1.04,318),(41,16,.92,96),(62,32,.98,183),(74,-13,.90,42),(97,19,.92,267)]
for i,(x,y,s,yaw) in enumerate(placements):place('RiverbankGrass_01_%02d'%(i+1),g,(x,y,-.35),(s,s,s),yaw)
sun=es.spawn_actor_from_class(u.DirectionalLight,V(0,0,500),u.Rotator(pitch=-48,yaw=-35));sun.light_component.set_editor_property('intensity',3);sun.light_component.set_editor_property('light_source_angle',5);sun.light_component.set_mobility(u.ComponentMobility.MOVABLE)
sky=es.spawn_actor_from_class(u.SkyLight,V(0,0,500));sky.light_component.set_editor_property('intensity',.65);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EngineResources/DefaultTextureCube'));sky.light_component.set_editor_property('lower_hemisphere_is_black',False);sky.light_component.set_mobility(u.ComponentMobility.MOVABLE)
pp=es.spawn_actor_from_class(u.PostProcessVolume,V());pp.set_editor_property('unbound',True);q=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL),('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False),('override_auto_exposure_bias',True),('auto_exposure_bias',.5),('override_bloom_intensity',True),('bloom_intensity',0)]:q.set_editor_property(k,v)
pp.set_editor_property('settings',q)
for name,loc,target in [('01-close-oblique',(160,-222,157),(66,0,2)),('02-elevated-strategy',(180,-280,460),(72,0,0))]:
 c=es.spawn_actor_from_class(u.CameraActor,V(*loc));c.set_actor_label(name);c.set_actor_rotation(u.MathLibrary.find_look_at_rotation(V(*loc),V(*target)),False);c.camera_component.set_field_of_view(45);c.camera_component.set_editor_property('post_process_blend_weight',0)
u.EditorAssetLibrary.save_directory(D);le.save_current_level();es.clear_actor_selection_set()
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for cmd in ['Slate.bAllowThrottling 0','t.IdleWhenNotForeground 0','r.Streaming.FullyLoadUsedTextures 1']:u.SystemLibrary.execute_console_command(world,cmd)
exec((R/'SourceArt/Environment/Ground/GrassToGravelTransition01/Scripts/capture.py').read_text())
