import unreal as u,math,time
from pathlib import Path
RE=Path('/Users/brianwilliams/Desktop/Shoen-Rise-of-the-Samurai');ED='/Game/Art/Environment/RiverEdge01';V=u.Vector
re_es=u.get_editor_subsystem(u.EditorActorSubsystem);re_world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
t=u.AssetImportTask();t.filename=str(RE/'SourceArt/Environment/RiverEdge01/RiverEdge01_ShallowShelf.fbx');t.destination_path=ED;t.automated=True;t.replace_existing=True;t.save=True
opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_materials=False;opt.import_textures=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS;opt.static_mesh_import_data.vertex_color_import_option=u.VertexColorImportOption.REPLACE;t.options=opt;u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
mesh=u.load_asset(ED+'/RiverEdge01_ShallowShelf');mat=u.load_asset('/Game/Art/Environment/Ground/RiverGravel01/M_RiverGravel01_Continuous');mesh.set_material(0,mat)
a=re_es.spawn_actor_from_class(u.StaticMeshActor,V(-23600,-6300,650));a.set_actor_label('RiverEdge_01_ShallowShelf_6m');a.set_folder_path('RiverEdge_01');a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_cast_shadow(False);a.static_mesh_component.set_collision_profile_name('BlockAll');a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)
# Deliberately placed shoreline interruptions, using the approved rock family.
placements=[(-115,-274,2,.40,28),(-72,-285,3,.24,108),(52,-305,1,.32,157),(90,-340,3,.19,51),(224,-295,2,.28,211),(263,-315,4,.13,73),(345,-276,3,.25,314)]
land=next(x for x in re_es.get_all_level_actors() if isinstance(x,u.Landscape));bank=next(x for x in re_es.get_all_level_actors() if x.get_actor_label()=='RiverGravel01_ContinuousBank');bank.static_mesh_component.set_collision_enabled(u.CollisionEnabled.QUERY_ONLY)
ignore=[x for x in re_es.get_all_level_actors() if x not in [land,bank,a]]
for i,(s,t,n,scale,yaw) in enumerate(placements):
 x=-23600+s*.42-t*.907524;y=-6300+s*.907524+t*.42
 h=u.SystemLibrary.line_trace_single(re_world,V(x,y,20000),V(x,y,-5000),u.TraceTypeQuery.ECC_VISIBILITY,True,ignore,u.DrawDebugTrace.NONE,True).to_tuple()[5].z
 rock=u.load_asset('/Game/Art/Environment/Rocks/RiverRock%02d/RiverRock_%02d'%(n,n));r=re_es.spawn_actor_from_class(u.StaticMeshActor,V(x,y,h));r.set_actor_label('RiverEdge_01_Stone_%02d'%i);r.set_folder_path('RiverEdge_01');r.static_mesh_component.set_static_mesh(rock);r.set_actor_scale3d(V(scale,scale,scale));r.set_actor_rotation(u.Rotator(3 if i%2 else -5,yaw,2),False)
 center,ext=r.get_actor_bounds(False);r.set_actor_location(V(x,y,h-(center.z-ext.z-h)-ext.z*.28),False,False);r.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);bank.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
re_target=V(-23294,-6317,650)
re_views=[('01-low-oblique',re_target+V(650,-400,155),re_target),('02-overhead',re_target+V(0,0,1250),re_target),('03-rock-detail',V(-23065,-6440,790),V(-23301,-6332,650)),('04-gameplay',re_target+V(1300,-1700,1900),re_target+V(-80,0,0))]
re_cams=[]
for name,pos,target in re_views:
 c=re_es.spawn_actor_from_class(u.CameraActor,pos);c.set_actor_label('RiverEdge_01_'+name);c.set_folder_path('RiverEdge_01/Views');c.set_actor_rotation(u.MathLibrary.find_look_at_rotation(pos,target),False);c.camera_component.set_field_of_view(45);re_cams.append(c)
u.EditorAssetLibrary.save_directory(ED);u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
exec(open(str(RE/'SourceArt/Environment/RiverEdge01/capture_views.py')).read())
